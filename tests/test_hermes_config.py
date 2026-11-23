import unittest

from src.hermes.config import HermesConfig
from src.hermes.errors import HermesConfigError


class TestHermesConfig(unittest.TestCase):
    def test_default_config_is_valid(self):
        config = HermesConfig()
        self.assertTrue(config.enabled)
        self.assertEqual(config.executable_path, "/home/luqmanul/.local/bin/hermes")
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.max_output_size, 20_000)
        self.assertEqual(config.max_request_size, 10_000)
        self.assertEqual(config.ollama_base_url, "http://localhost:11434")
        self.assertEqual(config.ollama_model, "qwen3:4b-instruct-2507-q4_K_M")

    def test_custom_valid_config(self):
        config = HermesConfig(
            enabled=False,
            executable_path="/usr/bin/hermes",
            timeout=30,
            max_output_size=5_000,
            max_request_size=2_000,
            ollama_base_url="http://127.0.0.1:11434",
            ollama_model="custom-model",
        )
        self.assertFalse(config.enabled)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_output_size, 5_000)
        self.assertEqual(config.max_request_size, 2_000)

    def test_invalid_timeout_raises_error(self):
        with self.assertRaises(HermesConfigError):
            HermesConfig(timeout=0)
        with self.assertRaises(HermesConfigError):
            HermesConfig(timeout=-10)
        with self.assertRaises(HermesConfigError):
            HermesConfig(timeout="60")  # type: ignore

    def test_invalid_max_output_size_raises_error(self):
        with self.assertRaises(HermesConfigError):
            HermesConfig(max_output_size=0)
        with self.assertRaises(HermesConfigError):
            HermesConfig(max_output_size=-1)

    def test_invalid_max_request_size_raises_error(self):
        with self.assertRaises(HermesConfigError):
            HermesConfig(max_request_size=0)

    def test_invalid_executable_path_raises_error(self):
        with self.assertRaises(HermesConfigError):
            HermesConfig(executable_path="")
        with self.assertRaises(HermesConfigError):
            HermesConfig(executable_path="   ")

    def test_invalid_ollama_base_url_raises_error(self):
        with self.assertRaises(HermesConfigError):
            HermesConfig(ollama_base_url="")
        with self.assertRaises(HermesConfigError):
            HermesConfig(ollama_base_url="ftp://localhost")

    def test_invalid_ollama_model_raises_error(self):
        with self.assertRaises(HermesConfigError):
            HermesConfig(ollama_model="")


if __name__ == "__main__":
    unittest.main()
