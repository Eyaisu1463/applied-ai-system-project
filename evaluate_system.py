"""Reliability harness for PawPal+.

Runs the system on predefined inputs and checks more than the status: whether the
emergency alert fired, which rules were retrieved, and which must NOT be retrieved.
"""

import logging
import sys

from pawpal_system import PawPalSystem

TEST_CASES = [
    {"name": "Toxic food (chocolate)", "pet": "Max", "query": "Can Max eat chocolate brownies?",
     "status": "ok", "emergency": True, "sources": ["toxic-chocolate"], "not_sources": ["toxic-grapes"]},
    {"name": "Empty pet name", "pet": "", "query": "What are vaccination schedules?",
     "status": "rejected"},
    {"name": "Empty query", "pet": "Luna", "query": "   ",
     "status": "rejected"},
    {"name": "Oversized query", "pet": "Luna", "query": "why " * 200,
     "status": "rejected"},
    {"name": "Routine vaccination", "pet": "Luna", "query": "When should Luna get her booster shots?",
     "status": "ok", "emergency": False, "sources": ["vacc-booster"]},
    {"name": "Emergency symptoms", "pet": "Charlie", "query": "Charlie collapsed and is breathing heavily!",
     "status": "ok", "emergency": True, "sources": ["emergency-signs"]},
    {"name": "Misspelled toxin", "pet": "Rex", "query": "My dog ate chocolat",
     "status": "ok", "emergency": True, "sources": ["toxic-chocolate"]},
    {"name": "Hidden toxin (xylitol)", "pet": "Coco", "query": "Is sugar free gum with xylitol bad?",
     "status": "ok", "emergency": True, "sources": ["toxic-xylitol"]},
    {"name": "Routine exercise", "pet": "Bella", "query": "How much should I walk my dog?",
     "status": "ok", "emergency": False, "sources": ["exercise-dog"], "not_sources": ["emergency-signs"]},
    {"name": "Cat play", "pet": "Nala", "query": "How often should I play with my cat?",
     "status": "ok", "emergency": False, "sources": ["exercise-cat"]},
    {"name": "Out of scope", "pet": "Milo", "query": "What is the capital of France?",
     "status": "no_match", "emergency": False},
    {"name": "Breed name, not food", "pet": "Hershey", "query": "My chocolate lab needs more exercise",
     "status": "ok", "emergency": False, "sources": ["exercise-dog"], "known_limitation": True},
]


def check(case, result):
    """Return a list of reasons the case failed (empty list = passed)."""
    problems = []
    if result["status"] != case["status"]:
        problems.append(f"status {result['status']} != {case['status']}")
    if "emergency" in case and result["emergency"] != case["emergency"]:
        problems.append(f"emergency {result['emergency']} != {case['emergency']}")
    for src in case.get("sources", []):
        if src not in result["sources"]:
            problems.append(f"missing source {src}")
    for src in case.get("not_sources", []):
        if src in result["sources"]:
            problems.append(f"unexpected source {src}")
    return problems


def run_tests():
    logging.basicConfig(filename="pawpal.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    app = PawPalSystem()
    passed, unexpected_failures, confidences = 0, 0, []

    print("--- Running PawPal+ Reliability Evaluation ---")
    for i, case in enumerate(TEST_CASES, 1):
        result = app.ask(case["pet"], case["query"])
        problems = check(case, result)
        if result["status"] == "ok":
            confidences.append(result["confidence"])

        if not problems:
            passed += 1
            label = "PASS"
        elif case.get("known_limitation"):
            label = "FAIL (known limitation)"
        else:
            label = "FAIL"
            unexpected_failures += 1

        detail = f"emergency={result['emergency']} conf={result['confidence']:.2f}"
        print(f"Test {i:2}: {label:<24} {case['name']:<24} {detail}")
        for p in problems:
            print(f"           -> {p}")

    total = len(TEST_CASES)
    avg = sum(confidences) / len(confidences) if confidences else 0.0
    print(f"\nEvaluation Summary: {passed}/{total} tests passed "
          f"({unexpected_failures} unexpected failure(s)).")
    print(f"Average confidence on answered questions: {avg:.2f}")
    return unexpected_failures


if __name__ == "__main__":
    sys.exit(1 if run_tests() else 0)
