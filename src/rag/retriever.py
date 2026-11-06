import math

from src.rag.embeddings import embed_text


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """Calculate cosine similarity between two vectors."""

    if len(vector_a) != len(vector_b):
        raise ValueError("Vectors must have the same dimension.")

    if not vector_a or not vector_b:
        raise ValueError("Vectors cannot be empty.")

    dot_product = sum(
        a * b for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        raise ValueError("Vectors cannot have zero magnitude.")

    return dot_product / (magnitude_a * magnitude_b)


def retrieve(
    query: str,
    chunks: list[str],
    top_k: int = 3,
) -> list[tuple[str, float]]:
    """Retrieve the most relevant chunks for a query."""

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if not chunks:
        return []

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    query_vector = embed_text(query)

    results = []

    for chunk in chunks:
        chunk_vector = embed_text(chunk)

        score = cosine_similarity(
            query_vector,
            chunk_vector,
        )

        results.append((chunk, score))

    results.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return results[:top_k]
