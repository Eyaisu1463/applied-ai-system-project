# Model Card: PawPal+ Applied AI System

## System Overview & Architecture
PawPal+ is an Applied AI System designed to assist pet owners with health, feeding, and care recommendations. It integrates a local Retrieval-Augmented Generation (RAG) engine over structured veterinary rules and safety guardrails to evaluate symptom urgency.

## Limitations & Biases
- **Knowledge Base Scope:** The system relies on a curated local dataset (`knowledge_base.json`) covering core toxic foods, vaccination schedules, and emergency symptoms. It cannot diagnose rare medical conditions.
- **Non-Diagnostic Nature:** PawPal+ provides informational guidance only and is not a replacement for licensed veterinary diagnosis.

## Misuse & Risk Prevention
- **Emergency Safety Guardrails:** Queries containing high-risk keywords (e.g., *chocolate, collapse, lethargic, poison*) immediately trigger visual alert disclaimers prioritizing emergency veterinary intervention.
- **Input Validation:** Blank queries or empty pet names are rejected gracefully without invoking downstream processing.

## Reliability & Testing Summary
- Automated reliability harness (`evaluate_system.py`) executes edge-case tests measuring system behavior against expected outcomes.
- **Pass Rate:** 4/4 automated tests passed successfully across input validation, routine guidance, toxic food alerts, and emergency triage.

## Reflection on AI Collaboration
- **Accepted Suggestion:** Utilizing a structured JSON lookup schema (`knowledge_base.json`) for deterministic RAG retrieval, ensuring zero-hallucination guardrail triggers for toxic foods.
- **Revised Suggestion:** AI initially suggested an unconstrained external LLM API for dynamic symptom diagnosis. I revised this to a rule-backed keyword guardrail system with explicit disclaimers to prevent medical misdirection.
