from src.rag.qa import answer_question


def main():
    print("=" * 50)
    print("       LOCAL RAG ASSISTANT")
    print("=" * 50)
    print("Knowledge base: SQLite")
    print("Model: Qwen3 Instruct")
    print("Type 'help' for instructions.")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()

            if question.lower() in ["exit", "quit"]:
                print("Assistant: Goodbye!")
                break

            if not question:
                continue

            if question.lower() == "help":
                print("\nCommands:")
                print("  help  - Show help instructions")
                print("  exit  - Exit the application\n")
                continue

            print("\nAssistant: Searching for answers...\n")

            answer = answer_question(
                question,
                top_k=3,
            )

            print(f"{answer}\n")

        except KeyboardInterrupt:
            print("\nAssistant: Goodbye!")
            break

        except Exception as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()
