import os
import queue
import subprocess
import threading
import time
import uuid


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
        self._start()

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
