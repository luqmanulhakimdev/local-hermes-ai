import unittest
from unittest.mock import MagicMock, patch

import requests

from src.rag.embeddings import EMBEDDING_MODEL, OLLAMA_EMBED_URL, embed_text


class TestEmbeddings(unittest.TestCase):

    @patch("requests.post")
    def test_embed_text_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "embeddings": [[0.12, 0.34, 0.56]]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        vector = embed_text("Hello world")

        self.assertEqual(vector, [0.12, 0.34, 0.56])
        mock_post.assert_called_once_with(
            OLLAMA_EMBED_URL,
            json={
                "model": EMBEDDING_MODEL,
                "input": "Hello world",
            },
            timeout=120,
        )

    def test_empty_or_whitespace_text_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            embed_text("")
        self.assertIn("Text cannot be empty.", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            embed_text("   \n\t  ")
        self.assertIn("Text cannot be empty.", str(ctx.exception))

    @patch("requests.post")
    def test_embed_text_no_embeddings_in_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"embeddings": []}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            embed_text("Test query")
        self.assertIn("Ollama did not return embeddings.", str(ctx.exception))

    @patch("requests.post")
    def test_embed_text_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            embed_text("Query with error")


if __name__ == "__main__":
    unittest.main()

