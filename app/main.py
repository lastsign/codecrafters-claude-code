import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.tools.read import read

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


local_tools = {"read": read}


def call_tool(tool):
    func = tool.function
    name = func.name
    arguments = eval(func.arguments)
    callable = local_tools.get(name)
    if callable:
        return callable(**arguments)


def call_tools(tools):
    results = []
    for tool in tools:
        res = call_tool(tool)
        print(res)
        results.append(res)
    return results


class Agent:
    def __init__(self, tools, model="anthropic/claude-haiku-4.5"):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.tools = tools
        self.model = model

    def call_api(self, messages):
        chat = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
        )
        return chat

    def agent_loop(self, messages):
        while True:
            response = self.call_api(messages)
            messages.append(response.choices[0].message)

            if not response.choices[0].message.tool_calls:
                print(response.choices[0].message.content)
                break

            for tool in response.choices[0].message.tool_calls:
                result = call_tool(tool)
                messages.append(
                    {"role": "tool", "tool_call_id": tool.id, "content": result}
                )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

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

    messages = [{"role": "user", "content": args.p}]

    agent = Agent(tools)
    agent.agent_loop(messages)


if __name__ == "__main__":
    main()
