import os
import queue
import subprocess
import threading
import time
import uuid
from pathlib import Path


def sbx_cmd(*cmd, cwd=None):
    cwd = cwd or os.getcwd()
    return [
        "bwrap",
        "--unshare-all",
        "--share-net",
        "--new-session",
        "--die-with-parent",
        "--ro-bind",
        "/",
        "/",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
        "--tmpfs",
        "/tmp",
        "--bind",
        cwd,
        cwd,
        "--chdir",
        cwd,
        *cmd,
    ]


class Sandbox:
    def __init__(self, cwd=None):
        self.cwd = cwd or os.getcwd()

    def _start(self):
        self.p = subprocess.Popen(
            sbx_cmd("bash"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.q = queue.Queue()
        threading.Thread(
            target=self._reader, args=(self.p, self.q), daemon=True
        ).start()

    @staticmethod
    def _reader(p, q: queue.Queue):
        for line in p.stdout:
            q.put(line)
        q.put(None)

    def close(self):
        self.p.kill()
        self.p.wait()

    def restart(self):
        self.close()
        self._start()

    def run(self, cmd: str, timeout: float = 30) -> tuple[str, int]:
        marker = uuid.uuid4().hex
        self.p.stdin.write(f"{cmd}\necho {marker} $?\n")
        self.p.stdin.flush()

        out = []
        deadline = time.monotonic() + timeout
        while True:
            try:
                line = self.q.get(timeout=max(deadline - time.monotonic(), 0))
            except queue.Empty:
                self.restart()
                raise TimeoutError(
                    f"command timed out after {timeout}s sandbox restarted"
                )
            if line is None:
                raise RuntimeError("sandbox died")
            i = line.find(marker)
            if i != -1:
                out.append(line[:i])
                return "".join(out), int(line[i:].split()[1])
            out.append(line)


sandbox = Sandbox()


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
