import json
from pathlib import Path


def get_tools():
    tools_path = Path(__file__).absolute().parent / "tools.json"

    with open(tools_path) as f:
        return json.load(f)
