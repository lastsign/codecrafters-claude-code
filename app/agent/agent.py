import os

from dotenv import load_dotenv
from openai import OpenAI

from app.tools import bash, get_tools, human_in_the_loop, read, write

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def call_tool(tool):
    local_tools = {
        "read": read,
        "write": write,
        "bash": bash,
        "human_in_the_loop": human_in_the_loop,
        # "skill": skill,
    }

    func = tool.function
    name = func.name
    arguments = eval(func.arguments)
    if name == "skill":
        from app.tools import skill

        skill(**arguments)
    callable = local_tools.get(name)
    if callable:
        return callable(**arguments)


def call_tools(tools):
    results = []
    for tool in tools:
        res = call_tool(tool)
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

    def agent_loop(self, messages) -> str | None:
        while True:
            response = self.call_api(messages)

            if not response.choices or len(response.choices) == 0:
                raise RuntimeError("no choices in response")

            message = response.choices[0].message

            messages.append(
                {"role": "assistant", "content": None, "tool_calls": message.tool_calls}
            )

            if not message.tool_calls:
                print(message.content)
                return message.content

            for tool in message.tool_calls:
                result = call_tool(tool)
                messages.append(
                    {"role": "tool", "tool_call_id": tool.id, "content": result}
                )


agent = Agent(get_tools())
