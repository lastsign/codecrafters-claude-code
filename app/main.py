import argparse
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from app.tools.read import read

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


local_tools = {"read": read}


def call_tool(tool):
    print(tool)
    func = tool.get("function", {})
    name = func.get("name")
    arguments = func.get("arguments")
    arguments = eval(arguments)
    callable = local_tools.get(name)
    if callable:
        return callable(**arguments)


def call_tools(tools):
    results = []
    for tool in tools:
        res = call_tool(tool)
        results.append(res)
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "read",
                "description": "Read and return the contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "The path to the file to read",
                        }
                    },
                    "required": ["file_path"],
                },
            },
        }
    ]

    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=[{"role": "user", "content": args.p}],
        tools=tools,
    )

    if not chat.choices or len(chat.choices) == 0:
        raise RuntimeError("no choices in response")

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # TODO: Uncomment the following line to pass the first stage
    choice = chat.choices[0]
    if not choice.message and choice.tool_calls:
        if len(choice.tool_calls) > 1:
            res = call_tools(choice.tool_calls)
            # print(res)
        elif len(choice.tool_calls) == 1:
            res = call_tool(choice.tool_calls[0])
            # print(res)
    else:
        print(chat.choices[0].message.content)


if __name__ == "__main__":
    main()
