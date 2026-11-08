"""PawPal+: a retrieval-based pet care assistant with safety guardrails.

Pipeline for every question:
  1. Input guardrail   - reject empty or oversized input before doing any work.
  2. Retrieval (RAG)   - score every rule in knowledge_base.json against the question
                         (exact keyword matches, plus typo-tolerant fuzzy matches).
  3. Risk scan         - an independent safety net that looks for toxins and emergency
                         signs even if the knowledge base has no matching rule.
  4. Answer composer   - builds the answer *from the retrieved rules*, decides whether
                         to raise an emergency alert, and computes a confidence score.
Every step is written to pawpal.log and recorded in a trace returned with the answer.
"""

import argparse
import json
import logging
import os
import re
from difflib import SequenceMatcher

logger = logging.getLogger("pawpal")

KB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base.json")

MAX_PET_NAME = 50
MAX_QUERY = 500
FUZZY_CUTOFF = 0.85        # how similar a misspelled word must be to count as a match
FUZZY_WEIGHT = 0.75        # a fuzzy match counts for less than an exact match
LOW_CONFIDENCE = 0.5

# Independent safety net: these words trigger an alert even with no matching rule.
RISK_TERMS = [
    "chocolate", "grape", "grapes", "raisin", "raisins", "onion", "onions", "garlic",
    "xylitol", "poison", "poisoned", "poisoning", "toxic", "lethargic", "collapse",
    "collapsed", "seizure", "seizures", "bleeding", "unconscious",
]
ALERT_CATEGORIES = {"toxic_food", "emergency"}

DISCLAIMER = ("PawPal+ gives general information only and is not a substitute "
              "for a licensed veterinarian.")


def tokenize(text):
    return re.findall(r"[a-z]+", text.lower())


def word_match(word, term):
    """Return 1.0 for an exact match, FUZZY_WEIGHT for a close misspelling, else 0."""
    if word == term:
        return 1.0
    if len(word) >= 4 and len(term) >= 4 and SequenceMatcher(None, word, term).ratio() >= FUZZY_CUTOFF:
        return FUZZY_WEIGHT
    return 0.0


class PawPalSystem:
    def __init__(self, kb_path=KB_PATH):
        self.entries = self.load_knowledge_base(kb_path)

    # ---------- knowledge base ----------
    def load_knowledge_base(self, path):
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error("Knowledge base not found at %s; continuing with no rules.", path)
            return []
        except json.JSONDecodeError as e:
            logger.error("Knowledge base is not valid JSON (%s); continuing with no rules.", e)
            return []

        entries = []
        for entry in data.get("entries", []):
            if all(k in entry for k in ("id", "category", "keywords", "text")):
                entries.append(entry)
            else:
                logger.warning("Skipping malformed knowledge base entry: %s", entry)
        logger.info("Loaded %d knowledge base entries.", len(entries))
        return entries

    # ---------- step 1: input guardrail ----------
    def validate_input(self, pet_name, query):
        if not pet_name or not pet_name.strip():
            return False, "Error: Pet name cannot be empty."
        if len(pet_name) > MAX_PET_NAME:
            return False, f"Error: Pet name must be {MAX_PET_NAME} characters or fewer."
        if not query or not query.strip():
            return False, "Error: Query cannot be empty."
        if len(query) > MAX_QUERY:
            return False, f"Error: Query must be {MAX_QUERY} characters or fewer."
        if not re.search(r"[A-Za-z]", query):
            return False, "Error: Query must contain words."
        return True, "Valid"

    # ---------- step 2: retrieval ----------
    def retrieve(self, query, top_k=3):
        """Score each rule by how many question words match its keywords."""
        words = tokenize(query)
        scored = []
        for entry in self.entries:
            score = 0.0
            for word in words:
                score += max((word_match(word, kw) for kw in entry["keywords"]), default=0.0)
            if score > 0:
                scored.append((score, entry))
        if not scored:
            return []
        scored.sort(key=lambda pair: pair[0], reverse=True)
        best = scored[0][0]
        # keep only rules that are close to the best match, so weak side matches are dropped
        return [(s, e) for s, e in scored if s >= 0.6 * best][:top_k]

    # ---------- step 3: risk scan ----------
    def scan_risks(self, query):
        found = set()
        for word in tokenize(query):
            for term in RISK_TERMS:
                if word_match(word, term):
                    found.add(term)
        return sorted(found)

    # ---------- step 4: compose ----------
    def ask(self, pet_name, query):
        trace = []
        is_valid, msg = self.validate_input(pet_name, query)
        trace.append(f"input_guardrail: {'ok' if is_valid else msg}")
        if not is_valid:
            logger.warning("Rejected input (pet=%r): %s", pet_name, msg)
            return {"status": "rejected", "emergency": False, "confidence": 0.0,
                    "sources": [], "output": msg, "trace": trace}

        pet = pet_name.strip()
        matches = self.retrieve(query)
        trace.append("retrieve: " + (", ".join(f"{e['id']} (score {s:.2f})" for s, e in matches)
                                     if matches else "no matching rules"))

        risks = self.scan_risks(query)
        trace.append(f"risk_scan: {risks if risks else 'none'}")

        emergency = bool(risks) or any(e["category"] in ALERT_CATEGORIES for _, e in matches)
        confidence = round(min(1.0, matches[0][0] / 2), 2) if matches else 0.0

        lines = [f"PawPal+ answer for {pet}", f"Question: {query.strip()}"]
        if emergency:
            lines.append("[!] EMERGENCY ALERT: possible toxin or emergency sign detected. "
                         "Contact your veterinarian or an animal poison control hotline now.")

        if matches:
            lines.append("Answer:")
            for _, e in matches:
                if e["category"] == "toxic_food":
                    lines.append(f"  - Keep {pet} away from this. {e['text']}")
                else:
                    lines.append(f"  - {e['text']}")
            if confidence < LOW_CONFIDENCE:
                lines.append("Low confidence: your question only partly matched my rules. "
                             "Please rephrase or check with your vet.")
            status = "ok"
        else:
            lines.append("Answer: I don't have verified information on that. "
                         "Please ask your veterinarian.")
            status = "no_match"

        sources = [e["id"] for _, e in matches]
        lines.append(f"Sources: {', '.join(sources) if sources else 'none'}")
        lines.append(f"Confidence: {confidence:.2f}")
        lines.append(f"Note: {DISCLAIMER}")
        trace.append(f"compose: status={status} emergency={emergency} confidence={confidence:.2f}")

        logger.info("pet=%r query=%r status=%s emergency=%s confidence=%.2f sources=%s",
                    pet, query, status, emergency, confidence, sources)
        return {"status": status, "emergency": emergency, "confidence": confidence,
                "sources": sources, "output": "\n".join(lines), "trace": trace}


DEMO_QUESTIONS = [
    ("Max", "Can Max eat chocolate brownies?"),
    ("Luna", "When should Luna get her booster shots?"),
    ("Bella", "How much should I walk my dog?"),
]


def print_result(result, show_trace):
    print(result["output"])
    if show_trace:
        print("Trace:")
        for step in result["trace"]:
            print(f"  {step}")


def main():
    logging.basicConfig(filename="pawpal.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ask PawPal+ a pet care question.")
    parser.add_argument("--pet", help="your pet's name")
    parser.add_argument("--query", help="your question")
    parser.add_argument("--trace", action="store_true", help="show each pipeline step")
    args = parser.parse_args()

    app = PawPalSystem()
    if args.pet is not None or args.query is not None:
        print_result(app.ask(args.pet or "", args.query or ""), args.trace)
    else:
        print("No --pet/--query given, running demo questions.\n")
        for pet, query in DEMO_QUESTIONS:
            print_result(app.ask(pet, query), args.trace)
            print()


if __name__ == "__main__":
    main()
