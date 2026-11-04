from datetime import datetime
from pathlib import Path


# Only allow accessing files within the project repository
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_current_time():
    now = datetime.now().astimezone()

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": now.strftime("%Z"),
    }


def list_project_files():
    files = []

    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue

        relative = path.relative_to(PROJECT_ROOT)

        # Skip sensitive files and environments
        if any(
            part in {".git", ".venv", "__pycache__", ".env"}
            for part in relative.parts
        ):
            continue

        files.append(str(relative))

        if len(files) >= 100:
            break

    return files


def read_project_file(filename):
    requested = (PROJECT_ROOT / filename).resolve()

    # Prevent directory traversal outside repository
    if not requested.is_relative_to(PROJECT_ROOT):
        raise ValueError("Access outside the project root is denied.")

    if not requested.is_file():
        raise FileNotFoundError("File not found.")

    if requested.stat().st_size > 100_000:
        raise ValueError("File is too large to read.")

    return requested.read_text(encoding="utf-8")
