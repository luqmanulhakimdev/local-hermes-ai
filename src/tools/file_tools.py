from pathlib import Path
import os
import stat


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = (PROJECT_ROOT / "documents").resolve()

ALLOWED_EXTENSIONS = {".md", ".txt"}
MAX_FILE_SIZE = 1_000_000


def _validate_document_path(path: str) -> Path:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("File path must not be empty")

    candidate = (PROJECT_ROOT / path).resolve()

    try:
        candidate.relative_to(DOCUMENTS_DIR)
    except ValueError:
        raise ValueError("File access is restricted to documents/")

    if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Only Markdown and text files are allowed")

    return candidate



def read_file(path: str) -> str:
    file_path = _validate_document_path(path)

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        file_descriptor = os.open(file_path, flags)
    except FileNotFoundError:
        raise FileNotFoundError(f"Document not found: {path}")
    except OSError as error:
        if error.errno == 40:  # Too many levels of symbolic links
            raise ValueError("Symbolic links are not allowed") from error
        raise

    try:
        file_stat = os.fstat(file_descriptor)

        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("Document must be a regular file")

        if file_stat.st_size > MAX_FILE_SIZE:
            raise ValueError("Document exceeds the maximum allowed size")

        with os.fdopen(file_descriptor, "rb") as file:
            file_descriptor = -1
            content = file.read(MAX_FILE_SIZE + 1)

        if len(content) > MAX_FILE_SIZE:
            raise ValueError("Document exceeds the maximum allowed size")

        return content.decode("utf-8")

    finally:
        if file_descriptor != -1:
            os.close(file_descriptor)



def list_files(directory: str = "documents") -> list[str]:
    if not isinstance(directory, str) or not directory.strip():
        raise ValueError("Directory must not be empty")

    target = (PROJECT_ROOT / directory).resolve()

    try:
        target.relative_to(DOCUMENTS_DIR)
    except ValueError:
        raise ValueError("Directory access is restricted to documents/")

    if not target.is_dir():
        raise NotADirectoryError(f"Directory not found: {directory}")

    results = []

    for path in target.rglob("*"):
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        try:
            resolved_path = path.resolve()
            resolved_path.relative_to(DOCUMENTS_DIR)
        except (ValueError, OSError, RuntimeError):
            continue

        if not resolved_path.is_file():
            continue

        if resolved_path.stat().st_size > MAX_FILE_SIZE:
            continue

        results.append(
            str(resolved_path.relative_to(PROJECT_ROOT))
        )

    return sorted(results)

