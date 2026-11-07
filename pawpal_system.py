import json
import os

class PawPalSystem:
    def __init__(self, kb_path="knowledge_base.json"):
        self.load_knowledge_base(kb_path)

    def load_knowledge_base(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8-sig") as f:
                self.kb = json.load(f)
        else:
            self.kb = {"toxic_foods": [], "vaccination_guidelines": [], "emergency_signs": []}

    def validate_input(self, pet_name, query):
        if not pet_name or not pet_name.strip():
            return False, "Error: Pet name cannot be empty."
        if not query or not query.strip():
            return False, "Error: Query cannot be empty."
        return True, "Valid"

    def retrieve_rag_context(self, query):
        query_lower = query.lower()
        context = []
        for category, items in self.kb.items():
            for item in items:
                if any(keyword in query_lower for keyword in category.split("_")) or any(w in query_lower for w in item.lower().split()[:5]):
                    context.append(item)
        if not context:
            context = self.kb.get("emergency_signs", [])
        return context

    def run_agentic_workflow(self, pet_name, query):
        is_valid, msg = self.validate_input(pet_name, query)
        if not is_valid:
            return {"status": "FAIL", "output": msg}

        retrieved_docs = self.retrieve_rag_context(query)
        risk_keywords = ["chocolate", "lethargic", "collapse", "poison", "bleeding", "grapes", "onion"]
        is_emergency = any(kw in query.lower() for kw in risk_keywords)

        response_body = f"Care Plan for {pet_name}:\n"
        response_body += f"- Analyzed query: '{query}'\n"
        response_body += f"- Retrieved {len(retrieved_docs)} reference rule(s) from knowledge base.\n"
        
        if is_emergency:
            response_body += "🚨 [GUARDRAIL ALERT]: High-risk symptoms or toxic elements detected! Please contact your veterinarian immediately.\n"
        
        response_body += "Retrieved Guidance:\n" + "\n".join([f"  • {doc}" for doc in retrieved_docs])

        return {
            "status": "PASS",
            "confidence": 0.95 if not is_emergency else 0.99,
            "output": response_body
        }

if __name__ == "__main__":
    app = PawPalSystem()
    print("PawPal+ AI System initialized successfully.")
