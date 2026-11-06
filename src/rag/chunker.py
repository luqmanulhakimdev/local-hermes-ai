from pathlib import Path


def load_document(path: str) -> str:
    """Load a text document."""
    return Path(path).read_text(encoding="utf-8")


def chunk_text(
    text: str,
    chunk_size: int = 100,
    overlap: int = 20,
) -> list[str]:
    """
    Split text into overlapping word-based chunks.

    chunk_size:
        Maximum number of words per chunk.

    overlap:
        Number of overlapping words between chunks.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if overlap < 0:
        raise ValueError("overlap cannot be negative.")

    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size.")

    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk.strip())

        if end >= len(words):
            break

        start = end - overlap

    return chunks
