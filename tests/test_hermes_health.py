import unittest
from unittest.mock import MagicMock, patch

from src.hermes.config import HermesConfig
from src.hermes.health import check_hermes


class TestHermesHealth(unittest.TestCase):
    @patch("pathlib.Path.is_file")
    @patch("os.access")
    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    def test_health_check_healthy(self, mock_urlopen, mock_run, mock_access, mock_is_file):
        mock_is_file.return_value = True
        mock_access.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="Hermes Agent v0.22.6")
        mock_urlopen.return_value.__enter__.return_value.status = 200

        config = HermesConfig(executable_path="/mock/hermes")
        report = check_hermes(config)

        self.assertEqual(report["status"], "ok")
        self.assertTrue(report["executable_exists"])
        self.assertIn("v0.22.6", report["version"])
        self.assertTrue(report["ollama_reachable"])

    @patch("pathlib.Path.is_file")
    def test_health_check_executable_missing(self, mock_is_file):
        mock_is_file.return_value = False
        config = HermesConfig(executable_path="/nonexistent/hermes")
        report = check_hermes(config)

        self.assertEqual(report["status"], "unavailable")
        self.assertFalse(report["executable_exists"])

    @patch("pathlib.Path.is_file")
    @patch("os.access")
    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    def test_health_check_ollama_unreachable_degraded(self, mock_urlopen, mock_run, mock_access, mock_is_file):
        mock_is_file.return_value = True
        mock_access.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="Hermes Agent v0.22.6")
        mock_urlopen.side_effect = Exception("Connection refused")

        config = HermesConfig(executable_path="/mock/hermes")
        report = check_hermes(config)

        self.assertEqual(report["status"], "degraded")
        self.assertFalse(report["ollama_reachable"])


if __name__ == "__main__":
    unittest.main()
