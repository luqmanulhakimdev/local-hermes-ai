"""Lightweight health check for Hermes integration and dependencies."""

import os
from pathlib import Path
import subprocess
import urllib.request

from src.hermes.config import HermesConfig


def check_hermes(config: HermesConfig | None = None) -> dict:
    """Inspect local Hermes executable, version, and Ollama endpoint availability."""
    config = config or HermesConfig()

    exe_path = Path(config.executable_path)
    executable_exists = exe_path.is_file() and os.access(exe_path, os.X_OK)

    if not executable_exists:
        return {
            "status": "unavailable",
            "executable_exists": False,
            "version": None,
            "ollama_reachable": False,
            "details": f"Hermes executable not found or not executable: {config.executable_path}",
        }

    version_str = None
    try:
        proc = subprocess.run(
            [config.executable_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
        if proc.returncode == 0:
            version_str = proc.stdout.strip().split("\n")[0]
    except Exception as e:
        version_str = f"Error obtaining version: {e}"

    ollama_reachable = False
    try:
        url = f"{config.ollama_base_url.rstrip('/')}/api/tags"
        req = urllib.request.Request(url, headers={"User-Agent": "LocalHermesAI-HealthCheck"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                ollama_reachable = True
    except Exception:
        ollama_reachable = False

    status = "ok" if (executable_exists and ollama_reachable) else "degraded"

    return {
        "status": status,
        "executable_exists": True,
        "version": version_str,
        "ollama_reachable": ollama_reachable,
        "details": f"Hermes {version_str}; Ollama reachable={ollama_reachable}",
    }
