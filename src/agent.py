import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b"

# System prompt: AI identity and rules
SYSTEM_PROMPT = """
You are Local Hermes AI.
You are a friendly and helpful personal assistant.

Guidelines:
1. Respond clearly and concisely.
2. Use simple, easily understood language.
3. Remember information provided by the user during the conversation.
4. Provide direct answers without unnecessary filler.
"""

# Conversation history
messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]


def ask_ai(question):
    # Save user message
    messages.append({
        "role": "user",
        "content": question
    })

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=(10, 300)
    )

    response.raise_for_status()

    result = response.json()
    answer = result["message"]["content"]

    # Save assistant response
    messages.append({
        "role": "assistant",
        "content": answer
    })

    return answer


def main():
    print("=" * 45)
    print("          LOCAL HERMES AI AGENT")
    print("=" * 45)

    name = input("\nEnter your name: ").strip()

    if not name:
        name = "Friend"

    print(f"\nHello {name}! Nice to meet you.")
    print("I am ready to be your personal AI assistant.")
    print("\nType 'exit' to quit.")
    print("Type 'reset' to clear conversation history.\n")

    while True:
        question = input(f"{name}: ").strip()

        if question.lower() == "exit":
            print("\nAI: Goodbye!")
            break

        if question.lower() == "reset":
            messages.clear()
            messages.append({
                "role": "system",
                "content": SYSTEM_PROMPT
            })
            print("\nAI: Conversation history has been reset.\n")
            continue

        if not question:
            continue

        try:
            answer = ask_ai(question)
            print(f"\nAI: {answer}\n")

        except requests.exceptions.RequestException as error:
            print(f"\n[ERROR] Could not connect to Ollama: {error}")

            # Remove the user message that failed to send
            if messages and messages[-1]["role"] == "user":
                messages.pop()

        except (KeyError, ValueError) as error:
            print(f"\n[ERROR] Invalid Ollama response: {error}")


if __name__ == "__main__":
    main()
