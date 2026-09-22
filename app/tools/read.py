from pathlib import Path


def propagate_folder(file_path: Path) -> str:
    if file_path.is_dir():
        contents = {}
        for file in file_path.iterdir():
            if file.is_dir():
                contents[str(file)] = propagate_folder(file)
            else:
                with file.open() as f:
                    contents[str(file)] = f.read()
        return contents


def read(file_path: str) -> str:
    q = Path(file_path)

    if not q.exists():
        return f"[Errno 2] No such file or directory: '{file_path}'"

    if q.is_dir():
        contents = propagate_folder(q)
        return contents

    with q.open() as f:
        return f.read()


if __name__ == "__main__":
    print(read("app"))
