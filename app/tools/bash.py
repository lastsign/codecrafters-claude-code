import os
import shlex
import subprocess
from pathlib import Path

from app.tools.sandbox import Sandbox

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
    sandbox = None
    try:
        sandbox = Sandbox()
    except FileNotFoundError:
        error = "bubblewrap is not available in that environment"
    if sandbox:
        try:
            out, returncode = sandbox.run(command)
        except TimeoutError:
            return "command timed out"
        except RuntimeError as e:
            return str(e)
        finally:
            sandbox.close()
        return out if returncode == 0 else f"exit code {returncode}\n{out}"
    else:
        try:
            args = shlex.split(command)
        except ValueError as e:
            return f"parse error: {e}"

        if not args:
            return "empty command"
        name = args[0]
        if name not in ALLOWED:
            return f"command not allowed: {name}"

        if name == "rm":
            return rm(args[1:])

        if name != "echo":
            for a in args[1:]:
                if not a.startswith("-") and not inside_root(a):
                    return f"path outside project is not allowed: {a}"
        try:
            r = subprocess.run(
                args, capture_output=True, text=True, timeout=30, cwd=ROOT, check=False
            )
        except subprocess.TimeoutExpired:
            return "command timed out"
        out = r.stdout + r.stderr + error
        return out if r.returncode == 0 else f"exit code {r.returncode}\n{out}"
