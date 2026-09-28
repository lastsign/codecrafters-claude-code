from app.tools.sandbox import Sandbox

if __name__ == "__main__":
    sb = Sandbox()
    try:
        while True:
            cmd = input("sbx> ")
            try:
                out, code = sb.run(cmd, timeout=10)
                print(out, end="")
                print(f"[exit {code}]")
            except TimeoutError as e:
                print(e)
    except KeyboardInterrupt, EOFError:
        pass
    finally:
        sb.close()
