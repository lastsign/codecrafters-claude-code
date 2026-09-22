import os
import shlex
import subprocess
from pathlib import Path

ALLOWED = {"rm", "ls", "cat", "grep", "echo"}


def bash(command: str) -> str:
    args = shlex.split(command) if isinstance(command, str) else list(command)

    name = os.path.basename(args[0])
    if name not in ALLOWED:
        return f"command not allowed: {name}"

    if os.path.basename(args[0]) == "rm" and not Path(args[-1]).is_file():
        return ""

    result = subprocess.run(args, capture_output=True, shell=False, check=True)
    if result.stderr:
        return str(result.stderr)
    return str(result.stdout)

if __name__ == "__main__":
    res = bash("ls")
    print(res)
