from src.rag.vector_store import VectorStore
from src.rag.qa import answer_question


RETRIEVAL_TEST_CASES = [
    {
        "question": "What is a token in Large Language Models?",
        "expected_sources": ["llm-basics.md"],
    },
    {
        "question": "What is a Large Language Model?",
        "expected_sources": ["llm-basics.md"],
    },
    {
        "question": "How does Retrieval-Augmented Generation work?",
        "expected_sources": ["ai-engineering.md"],
    },
    {
        "question": "What is AI Engineering?",
        "expected_sources": ["ai-engineering.md"],
    },
    {
        "question": "What is the capital of Japan?",
        "expected_sources": [],
    },
    {
        "question": "Who was the first president of Indonesia?",
        "expected_sources": [],
    },
]


ANSWER_TEST_CASES = [
    {
        "question": "What is a token in Large Language Models?",
        "expected_source": "llm-basics.md",
        "expected_keywords": [
            "token",
            "unit",
            "text",
            "word",
        ],
    },
    {
        "question": "What is a Large Language Model?",
        "expected_source": "llm-basics.md",
        "expected_keywords": [
            "model",
            "language",
            "text",
        ],
    },
    {
        "question": "What is AI Engineering?",
        "expected_source": "ai-engineering.md",
        "expected_keywords": [
            "AI",
            "engineering",
            "application",
        ],
    },
    {
        "question": "What is Retrieval-Augmented Generation?",
        "expected_source": "ai-engineering.md",
        "expected_keywords": [
            "retrieval",
            "generation",
        ],
    },
]


NEGATIVE_ANSWER_CASES = [
    "What is the capital of Japan?",
    "Who was the first president of Indonesia?",
]


def keyword_coverage(
    answer: str,
    expected_keywords: list[str],
) -> float:
    """Calculate the percentage of expected keywords found in an answer."""

    answer_lower = answer.lower()

    matched = sum(
        1
        for keyword in expected_keywords
        if keyword.lower() in answer_lower
    )

    if not expected_keywords:
        return 1.0

    return matched / len(expected_keywords)


def evaluate_retrieval(
    store: VectorStore,
    test_cases: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """Evaluate document retrieval using source-level Precision@K and Recall@K."""

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    results = []

    for test_case in test_cases:
        question = test_case["question"]
        expected_sources = set(test_case["expected_sources"])

        retrieved = store.search(
            question,
            top_k=top_k,
            threshold=0.65,
        )

        # Evaluate unique document sources instead of individual chunks.
        retrieved_sources = {
            item["source"]
            for item in retrieved
        }

        retrieved_details = [
            {
                "source": item["source"],
                "score": item["score"],
            }
            for item in retrieved
        ]

        if expected_sources:
            relevant_sources = (
                expected_sources & retrieved_sources
            )

            precision = (
                len(relevant_sources) / len(retrieved_sources)
                if retrieved_sources
                else 0.0
            )

            recall = (
                len(relevant_sources)
                / len(expected_sources)
            )

        else:
            # For no-answer cases, an empty retrieval is considered successful.
            precision = (
                1.0
                if not retrieved_sources
                else 0.0
            )

            recall = (
                1.0
                if not retrieved_sources
                else 0.0
            )

        results.append({
            "question": question,
            "expected_sources": sorted(expected_sources),
            "retrieved_sources": sorted(retrieved_sources),
            "precision": precision,
            "recall": recall,
            "retrieved_details": retrieved_details,
        })

    return results


def evaluate_answer_quality(test_cases: list[dict] = None) -> list[dict]:
    """Evaluate generated answers using expected keyword coverage."""

    cases = test_cases if test_cases is not None else ANSWER_TEST_CASES
    results = []

    print("\n========== ANSWER QUALITY EVALUATION ==========\n")

    for test_case in cases:
        question = test_case["question"]

        answer = answer_question(question)

        score = keyword_coverage(
            answer,
            test_case["expected_keywords"],
        )

        result = {
            "question": question,
            "expected_source": test_case["expected_source"],
            "keyword_coverage": score,
            "answer": answer,
        }

        results.append(result)

        print(f"Question: {question}")
        print(
            f"Expected source: "
            f"{test_case['expected_source']}"
        )
        print(
            f"Keyword coverage: "
            f"{score:.2f}"
        )
        print(f"Answer: {answer}")
        print("-" * 40)

    average_score = (
        sum(
            result["keyword_coverage"]
            for result in results
        ) / len(results)
        if results
        else 0.0
    )

    print("\n========== ANSWER QUALITY SUMMARY ==========")
    print(
        f"Average keyword coverage: "
        f"{average_score:.2f}"
    )

    return results


def evaluate_negative_answers(negative_cases: list[str] = None) -> list[dict]:
    """Evaluate whether unsupported questions are rejected."""

    cases = negative_cases if negative_cases is not None else NEGATIVE_ANSWER_CASES
    results = []

    print("\n========== NEGATIVE ANSWER EVALUATION ==========\n")

    expected_phrase = (
        "No relevant information found."
    )

    for question in cases:
        answer = answer_question(question)

        passed = expected_phrase in answer

        result = {
            "question": question,
            "answer": answer,
            "passed": passed,
        }

        results.append(result)

        status = "PASS" if passed else "FAIL"

        print(f"[{status}] {question}")
        print(f"Answer: {answer}")
        print("-" * 40)

    passed_count = sum(
        result["passed"]
        for result in results
    )

    print("\n========== NEGATIVE ANSWER SUMMARY ==========")
    print(
        f"Passed: "
        f"{passed_count}/{len(results)}"
    )

    return results


def print_retrieval_results(results: list[dict]) -> None:
    """Print detailed retrieval evaluation results."""

    print("\n========== RETRIEVAL EVALUATION ==========\n")

    for index, result in enumerate(results, start=1):
        print(f"Test Case {index}")
        print(f"Question: {result['question']}")
        print(f"Expected: {result['expected_sources']}")
        print(f"Retrieved: {result['retrieved_sources']}")

        for item in result["retrieved_details"]:
            print(
                f"  - {item['source']}: "
                f"{item['score']:.4f}"
            )

        print(
            f"Precision@3: "
            f"{result['precision']:.2f}"
        )

        print(
            f"Recall@3: "
            f"{result['recall']:.2f}"
        )

        print("-" * 40)

    if not results:
        return

    average_precision = sum(
        result["precision"]
        for result in results
    ) / len(results)

    average_recall = sum(
        result["recall"]
        for result in results
    ) / len(results)

    print("\n========== RETRIEVAL SUMMARY ==========")
    print(f"Total test cases: {len(results)}")
    print(
        f"Average Precision@3: "
        f"{average_precision:.2f}"
    )
    print(
        f"Average Recall@3: "
        f"{average_recall:.2f}"
    )


def main() -> None:
    store = VectorStore()

    retrieval_results = evaluate_retrieval(
        store=store,
        test_cases=RETRIEVAL_TEST_CASES,
        top_k=3,
    )

    print_retrieval_results(retrieval_results)

    evaluate_answer_quality()

    evaluate_negative_answers()


if __name__ == "__main__":
    main()
