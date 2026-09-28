import os
import shlex
import subprocess
from pathlib import Path

from sandbox import sandbox

ALLOWED = {"rm", "ls", "cat", "grep", "echo"}
ROOT = Path.cwd().resolve()
PROTECTED = {ROOT / ".git"}


def inside_root(arg: str) -> bool:
    p = (ROOT / arg).resolve()
    return (
        p != ROOT
        and ROOT in p.parents
        and not any(p == d or d in p.parents for d in PROTECTED)
    )


def rm(targets: list[str]) -> str:
    if not targets:
        return "rm: missing operand"
    for t in targets:
        if t.startswith("-"):
            return f"rm options are not allowed ({t})"
        if not inside_root(t):
            return f"rm path outside project is not allowed: {t}"
        if not Path(t).is_file():
            return f"rm only regular files can be deleted: {t}"

    for t in targets:
        os.remove(t)
    return ""


def bash(command: str) -> str:
    try:
        out, returncode = sandbox.run(command)
    except TimeoutError:
        return "command timed out"
    finally:
        sandbox.close()
    return out if returncode == 0 else f"exit code {returncode}\n{out}"
