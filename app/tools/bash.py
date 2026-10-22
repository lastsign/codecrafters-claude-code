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
        if not command.strip():
            return "empty command"

        try:
            r = subprocess.run(
                ["bash", "-c", command],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=ROOT,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return "command timed out"
        except OSError as e:
            return f"failed to run command: {e}"
        out = r.stdout + r.stderr + error
        return out if r.returncode == 0 else f"exit code {r.returncode}\n{out}"
