import json
import time

from app.agent import SupportAgent


def load_test_cases(path: str):
    """
    Load evaluation test cases from a JSON file.
    """

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def check_keywords(answer: str, keywords: list[str]) -> bool:
    """
    Check whether all expected keywords or phrases
    appear in the agent's answer.
    """

    answer_lower = answer.lower()

    return all(
        keyword.lower() in answer_lower
        for keyword in keywords
    )


def check_any_phrase(answer: str, phrases: list[str]) -> bool:
    """
    Check whether at least one acceptable phrase
    appears in the answer.
    """

    answer_lower = answer.lower()

    return any(
        phrase.lower() in answer_lower
        for phrase in phrases
    )


def check_forbidden_text(
    answer: str,
    forbidden_items: list[str]
) -> bool:
    """
    Return True if none of the forbidden
    text appears in the answer.
    """

    answer_lower = answer.lower()

    return all(
        item.lower() not in answer_lower
        for item in forbidden_items
    )


def evaluate_test(
    agent: SupportAgent,
    test_case: dict
):
    """
    Run one test case and return its result.
    """

    question = test_case["question"]

    print(f"\nRunning: {test_case['id']}")
    print(f"Question: {question}")

    try:

        answer = agent.answer(question)

        # Small delay to reduce API rate-limit issues.
        time.sleep(5)

    except Exception as error:

        return {
            "id": test_case["id"],
            "passed": False,
            "answer": f"ERROR: {error}"
        }

    passed = True
    failure_reasons = []

    # ---------------------------------
    # EXPECTED KEYWORDS
    # ---------------------------------

    if "expected_keywords" in test_case:

        keyword_result = check_keywords(
            answer,
            test_case["expected_keywords"]
        )

        if not keyword_result:

            passed = False

            failure_reasons.append(
                "Missing required keyword(s)"
            )

    # ---------------------------------
    # ACCEPTABLE PHRASES
    # ---------------------------------

    if "expected_any" in test_case:

        any_result = check_any_phrase(
            answer,
            test_case["expected_any"]
        )

        if not any_result:

            passed = False

            failure_reasons.append(
                "Missing acceptable phrase"
            )

    # ---------------------------------
    # FORBIDDEN TEXT
    # ---------------------------------

    if "must_not_contain" in test_case:

        forbidden_result = check_forbidden_text(
            answer,
            test_case["must_not_contain"]
        )

        if not forbidden_result:

            passed = False

            failure_reasons.append(
                "Contains forbidden information"
            )

    return {
        "id": test_case["id"],
        "passed": passed,
        "answer": answer,
        "failure_reasons": failure_reasons
    }


def main():

    print("=" * 50)
    print("ASTER & ROW SUPPORT AGENT EVALUATION")
    print("=" * 50)

    # ---------------------------------
    # LOAD TEST CASES
    # ---------------------------------

    test_cases = load_test_cases(
        "tests/test_cases.json"
    )

    print(
        f"\nLoaded {len(test_cases)} test cases."
    )

    # ---------------------------------
    # INITIALIZE AGENT
    # ---------------------------------

    agent = SupportAgent(
        knowledge_base_path="knowledge-base",
        orders_path="data/orders.json"
    )

    results = []

    # ---------------------------------
    # RUN TESTS
    # ---------------------------------

    for test_case in test_cases:

        result = evaluate_test(
            agent,
            test_case
        )

        results.append(result)

        status = (
            "PASS"
            if result["passed"]
            else "FAIL"
        )

        print(f"\n{status}: {result['id']}")

        print("Answer:")
        print(result["answer"])

        if not result["passed"]:

            print("\nFailure reason:")

            for reason in result.get(
                "failure_reasons",
                []
            ):

                print(f"- {reason}")

        print("-" * 50)

    # ---------------------------------
    # SUMMARY
    # ---------------------------------

    total = len(results)

    passed_count = sum(
        result["passed"]
        for result in results
    )

    failed_count = total - passed_count

    accuracy = (
        (passed_count / total * 100)
        if total > 0
        else 0
    )

    print("\n")
    print("=" * 50)
    print("EVALUATION SUMMARY")
    print("=" * 50)

    print(f"Total tests: {total}")
    print(f"Passed:      {passed_count}")
    print(f"Failed:      {failed_count}")
    print(f"Score:       {accuracy:.1f}%")

    print("=" * 50)

    # ---------------------------------
    # SHOW FAILED TESTS
    # ---------------------------------

    if failed_count > 0:

        print("\nFAILED TESTS:")

        for result in results:

            if not result["passed"]:

                print(
                    f"- {result['id']}"
                )


if __name__ == "__main__":

    main()