import shlex
import subprocess
from pathlib import Path

from app.tools.sandbox import Sandbox

ROOT = Path.cwd().resolve()


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

        try:
            r = subprocess.run(
                args, capture_output=True, text=True, timeout=30, cwd=ROOT, check=False
            )
        except subprocess.TimeoutExpired:
            return "command timed out"
        out = r.stdout + r.stderr + error
        return out if r.returncode == 0 else f"exit code {r.returncode}\n{out}"
