import requests


OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "nomic-embed-text"


def embed_text(text: str) -> list[float]:
    """Convert text into an embedding vector."""

    if not text.strip():
        raise ValueError("Text cannot be empty.")

    response = requests.post(
        OLLAMA_EMBED_URL,
        json={
            "model": EMBEDDING_MODEL,
            "input": text,
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    embeddings = data.get("embeddings")

    if not embeddings:
        raise ValueError("Ollama did not return embeddings.")

    return embeddings[0]
