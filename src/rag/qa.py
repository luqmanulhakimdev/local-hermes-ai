import requests

from src.rag.vector_store import VectorStore


OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"


SYSTEM_PROMPT = """You are a local RAG assistant.

Answer using only the provided context.

Rules:
- Be concise and direct.
- Use only information from the context.
- Do not invent facts.
- If the answer is unavailable in the context, say so.
- Prefer answers under 100 words.
"""


def build_context(results: list[dict]) -> str:
    """Build context from retrieved chunks."""

    parts = []

    for index, result in enumerate(results, start=1):
        parts.append(
            f"[Context {index}]\n"
            f"Source: {result['source']}\n"
            f"Similarity: {result['score']:.4f}\n"
            f"Content: {result['content']}"
        )

    return "\n\n".join(parts)


def answer_question(
    question: str,
    top_k: int = 3,
    store: VectorStore = None,
) -> str:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if store is None:
        store = VectorStore()

    results = store.search(
        question,
        top_k=top_k,
        threshold=0.65,
    )

    if not results:
        return "No relevant information found."

    context = build_context(results)

    prompt = f"""Context:

{context}

Question:
{question}

Answer based only on the context above.
"""

    response = requests.post(
        OLLAMA_CHAT_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        },
        timeout=(10, 300),
    )

    response.raise_for_status()
    data = response.json()

    answer = data["message"]["content"].strip()

    # Collect unique document sources.
    sources = {}

    for result in results:
        source = result["source"]
        sources[source] = max(
            sources.get(source, 0),
            result["score"],
        )

    citation_lines = [
        f"- {source} (similarity: {score:.4f})"
        for source, score in sources.items()
    ]

    citations = "\n".join(citation_lines)

    return f"{answer}\n\nSources:\n{citations}"
