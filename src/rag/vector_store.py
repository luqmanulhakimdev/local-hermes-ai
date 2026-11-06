import json
from pathlib import Path
import sqlite3

from src.rag.embeddings import embed_text
from src.rag.retriever import cosine_similarity


class VectorStore:
    def __init__(self, db_path: str = "data/rag.db"):
        self.db_path = db_path
        self._initialize()

    def _initialize(self):
        """Create the database table if it does not exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    UNIQUE(source, chunk_index)
                )
            """)

    def add_chunks(self, chunks: list[str], source: str):
        """Generate and save embeddings for document chunks."""
        if not source.strip():
            raise ValueError("Source cannot be empty.")

        with sqlite3.connect(self.db_path) as connection:
            # Replace previous chunks from the same source.
            connection.execute(
                "DELETE FROM document_chunks WHERE source = ?",
                (source,),
            )

            for index, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                vector = embed_text(chunk)

                connection.execute("""
                    INSERT INTO document_chunks
                    (source, chunk_index, content, embedding)
                    VALUES (?, ?, ?, ?)
                """, (
                    source,
                    index,
                    chunk,
                    json.dumps(vector),
                ))

    def search(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.0,
    ):
        """Find the most relevant saved chunks."""
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        query_vector = embed_text(query)

        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute("""
                SELECT content, embedding, source
                FROM document_chunks
            """).fetchall()

        results = []

        for content, saved_embedding, source in rows:
            chunk_vector = json.loads(saved_embedding)
            score = cosine_similarity(query_vector, chunk_vector)

            if score >= threshold:
                results.append({
                    "content": content,
                    "score": score,
                    "source": source,
                })

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return results[:top_k]
