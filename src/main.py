
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

    # 1. Menerima nama pengguna
    name = input("\nMasukkan nama kamu: ").strip()

    # Validasi nama
    if not name:
        name = "User"

    # 2. Menampilkan sapaan
    print(f"\nHalo, {name}! Selamat datang di Local Hermes AI.")
    print("Silakan tanyakan sesuatu kepada AI.")

    question = input("\nYou: ").strip()

    if not question:
        print("Kamu belum memasukkan pertanyaan.")
        return

    # 3. Menangani error Ollama
    try:
        ask_ai(question)

    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Tidak dapat terhubung ke Ollama.")
        print("Pastikan Ollama sedang berjalan:")
        print("sudo systemctl start ollama")

    except requests.exceptions.Timeout:
        print("\n[ERROR] Request ke Ollama mengalami timeout.")

    except requests.exceptions.HTTPError as error:
        print(f"\n[ERROR] HTTP Error: {error}")

    except requests.exceptions.RequestException as error:
        print(f"\n[ERROR] Terjadi masalah koneksi: {error}")

    except Exception as error:
        print(f"\n[ERROR] Terjadi kesalahan: {error}")


if __name__ == "__main__":
    main()
