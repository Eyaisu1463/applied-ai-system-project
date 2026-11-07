from pawpal_system import PawPalSystem

def run_tests():
    app = PawPalSystem()
    test_cases = [
        {"pet": "Max", "query": "Can Max eat chocolate brownies?", "expected_status": "PASS"},
        {"pet": "", "query": "What are vaccination schedules?", "expected_status": "FAIL"},
        {"pet": "Luna", "query": "When should Luna get her booster shots?", "expected_status": "PASS"},
        {"pet": "Charlie", "query": "Charlie collapsed and is breathing heavily!", "expected_status": "PASS"}
    ]

    passed = 0
    print("--- Running PawPal+ Reliability Evaluation ---")
    for i, test in enumerate(test_cases, 1):
        result = app.run_agentic_workflow(test["pet"], test["query"])
        status = result["status"]
        
        match = (status == test["expected_status"])
        if match:
            passed += 1
            print(f"Test {i}: PASSED (Expected {test['expected_status']}, Got {status})")
        else:
            print(f"Test {i}: FAILED (Expected {test['expected_status']}, Got {status})")

    print(f"\nEvaluation Summary: {passed}/{len(test_cases)} tests passed successfully.")

if __name__ == "__main__":
    run_tests()
