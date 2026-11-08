# PawPal+: Applied AI System

## 1. Project Identification & Base System Summary
- **Base Project:** PawPal+ (Module 2 Mini-Project)
- **Original Summary:** PawPal+ was originally a lightweight Python prototype designed to store simple pet profiles (name, species, age) and print basic feeding and exercise tips. It relied on hardcoded static strings without context retrieval or safety validations.
- **Applied AI Extensions:** I extended this prototype into a production-ready Applied AI System by implementing:
  1. **A RAG (Retrieval-Augmented Generation) Engine:** Queries a local structured knowledge base (`knowledge_base.json`) to fetch verified veterinary guidelines before generating care plans.
  2. **An Agentic Workflow & Guardrail System:** Performs automated input validation, scans for toxic foods/emergency symptoms, and appends mandatory safety disclaimers.
  3. **An Automated Reliability Test Harness (`evaluate_system.py`):** Runs edge-case test suites to evaluate reliability and outputs reproducible pass/fail test metrics.

---

## 2. System Architecture
The system processes user requests through a modular pipeline:
- **Step 1 (Input Guardrail):** Validates that input parameters are non-empty. Rejects invalid inputs gracefully.
- **Step 2 (RAG Retrieval):** Queries `knowledge_base.json` for verified domain guidelines (toxic foods, vaccination schedules, emergency signs).
- **Step 3 (Agentic Triage):** Scans queries for high-risk elements (*chocolate, collapse, lethargic, poison*), adding emergency alerts and confidence scores.
- **Step 4 (Structured Output):** Returns formatted guidance or safety warnings.

> **Diagram Source:** The raw Mermaid architecture diagram is saved at `diagrams/architecture.mmd`. Supplementary visual assets reside in `/assets`.

---

## 3. Setup & Installation Instructions

```bash
# 1. Clone the repository
git clone [https://github.com/Eyaisu1463/applied-ai-system-project.git](https://github.com/Eyaisu1463/applied-ai-system-project.git)
cd applied-ai-system-project

# 2. Create and activate a virtual environment
python -m venv .venv

# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Mac/Linux:
# source .venv/bin/activate

# 3. Run the main system script
python pawpal_system.py

# 4. Run the automated reliability test harness
python evaluate_system.py