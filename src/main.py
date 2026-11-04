import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b"


def ask_ai(question):
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "/no_think\n" + question
            }
        ],
        "stream": True
    }

    print("\nAI: ", end="", flush=True)

    with requests.post(
        OLLAMA_URL,
        json=payload,
        stream=True,
        timeout=(10, 300)
    ) as response:

        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                import json
                data = json.loads(line)

                content = data.get("message", {}).get("content", "")
                print(content, end="", flush=True)

    print("\n")


def main():
    print("=" * 40)
    print("       LOCAL HERMES AI CHATBOT")
    print("=" * 40)

    # 1. Receive user name
    name = input("\nEnter your name: ").strip()

    # Validate name
    if not name:
        name = "User"

    # 2. Display greeting
    print(f"\nHello, {name}! Welcome to Local Hermes AI.")
    print("Feel free to ask the AI anything.")

    question = input("\nYou: ").strip()

    if not question:
        print("You have not entered a question.")
        return

    # 3. Handle Ollama errors
    try:
        ask_ai(question)

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to Ollama.")
        print("Ensure Ollama is running:")
        print("sudo systemctl start ollama")

    except requests.exceptions.Timeout:
        print("\n[ERROR] Request to Ollama timed out.")

    except requests.exceptions.HTTPError as error:
        print(f"\n[ERROR] HTTP Error: {error}")

    except requests.exceptions.RequestException as error:
        print(f"\n[ERROR] Connection error: {error}")

    except Exception as error:
        print(f"\n[ERROR] An error occurred: {error}")


if __name__ == "__main__":
    main()
