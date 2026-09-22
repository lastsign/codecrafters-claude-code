import json
import os


def get_tools():
    script_path = os.path.dirname(os.path.abspath(__file__))
    tools_path = os.path.join(script_path, "tools.json")

    with open(tools_path) as f:
        return json.load(f)


if __name__ == "__main__":
    print(get_tools())
