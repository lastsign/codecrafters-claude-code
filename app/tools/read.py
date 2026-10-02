from pathlib import Path


def read(file_path: str) -> str:
    p = Path(file_path).resolve()

    if not p.exists():
        return f"[Errno 2] No such file or directory: '{p}'"
    try:
        return f"File: {p}\n\n{p.read_text()}"
    except IsADirectoryError:
        return f"Error: {p} is a directory, not a file"
    except OSError as e:
        return f"Error reading {p}: {e}"
