from pathlib import Path

from src.rag.chunker import load_document, chunk_text
from src.rag.vector_store import VectorStore


SUPPORTED_EXTENSIONS = {".md", ".txt"}


def ingest_directory(directory: str = "documents", db_path: str = "data/rag.db"):
    """Load documents, split them into chunks, and save them to SQLite."""
    documents_path = Path(directory)

    if not documents_path.exists():
        raise FileNotFoundError(
            f"Directory not found: {directory}"
        )

    files = sorted(
        path
        for path in documents_path.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        print("No .md or .txt documents found.")
        return 0

    store = VectorStore(db_path=db_path)
    total_chunks = 0

    for file_path in files:
        text = load_document(str(file_path))
        chunks = chunk_text(text)

        if not chunks:
            print(f"SKIP: {file_path} (empty document)")
            continue

        source = file_path.relative_to(documents_path).as_posix()

        store.add_chunks(chunks, source)

        total_chunks += len(chunks)

        print(
            f"INGESTED: {source} "
            f"({len(chunks)} chunks)"
        )

    print("\n--- INGESTION SUMMARY ---")
    print(f"Total documents: {len(files)}")
    print(f"Total chunks: {total_chunks}")
    return total_chunks


if __name__ == "__main__":
    ingest_directory()
