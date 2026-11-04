from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.memory import Memory


class TestMemory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_agent.db"
        self.memory = Memory(db_path=self.db_path)

    def tearDown(self):
        self.memory.close()
        self.temp_dir.cleanup()

    def test_save_and_get_recent_messages(self):
        self.memory.save_message("user", "Hello")
        self.memory.save_message("assistant", "Hi there!")

        messages = self.memory.get_recent_messages(limit=10)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], {"role": "user", "content": "Hello"})
        self.assertEqual(messages[1], {"role": "assistant", "content": "Hi there!"})

    def test_get_recent_messages_limit(self):
        for i in range(10):
            self.memory.save_message("user", f"Message {i}")

        messages = self.memory.get_recent_messages(limit=5)
        self.assertEqual(len(messages), 5)
        # Should be the most recent 5 in chronological order: 5, 6, 7, 8, 9
        self.assertEqual(messages[0]["content"], "Message 5")
        self.assertEqual(messages[-1]["content"], "Message 9")

    def test_remember_and_get_memories(self):
        self.memory.remember("username", "Luqman")
        self.memory.remember("framework", "Hermes")

        memories = self.memory.get_memories()
        self.assertEqual(memories, {"username": "Luqman", "framework": "Hermes"})

    def test_remember_update_existing_key(self):
        self.memory.remember("color", "blue")
        self.memory.remember("color", "green")

        memories = self.memory.get_memories()
        self.assertEqual(memories, {"color": "green"})

    def test_forget_existing_and_non_existing_key(self):
        self.memory.remember("temp_key", "temp_value")
        self.assertTrue(self.memory.forget("temp_key"))
        self.assertNotIn("temp_key", self.memory.get_memories())

        # Forgetting non-existent key returns False
        self.assertFalse(self.memory.forget("unknown_key"))

    def test_clear_history(self):
        self.memory.save_message("user", "Clear me")
        self.memory.remember("persist", "stay")

        self.memory.clear_history()

        self.assertEqual(self.memory.get_recent_messages(), [])
        self.assertEqual(self.memory.get_memories(), {"persist": "stay"})

    def test_close_connection(self):
        self.memory.close()
        with self.assertRaises(sqlite3.ProgrammingError):
            self.memory.save_message("user", "Fail")


if __name__ == "__main__":
    unittest.main()

