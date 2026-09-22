from pathlib import Path


def write(file_path: str, content: str) -> None:
    q = Path(Path.cwd() / file_path)

    with q.open(mode="w") as f:
        f.write(content)
