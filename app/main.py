import argparse
import html
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.prompts import system_prompt
from app.skills.load import load_skill
from app.skills.parser import get_available_skills
from app.tools import bash, get_tools, human_in_the_loop, read, skill, write

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def call_tool(tool):
    local_tools = {
        "read": read,
        "write": write,
        "bash": bash,
        "human_in_the_loop": human_in_the_loop,
        "skill": skill,
    }

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

            if not response.choices or len(response.choices) == 0:
                raise RuntimeError("no choices in response")

            message = response.choices[0].message

            messages.append(
                {"role": "assistant", "content": None, "tool_calls": message.tool_calls}
            )

            if not message.tool_calls:
                print(message.content)
                break

            for tool in message.tool_calls:
                result = call_tool(tool)
                messages.append(
                    {"role": "tool", "tool_call_id": tool.id, "content": result}
                )


def prepare_skills_description(skills):
    skills_desc = []
    for frontmatter, body, path in skills.values():
        skills_desc.append(
            f"- {html.escape(frontmatter['name'])}: {html.escape(frontmatter['description'])}"
        )
    return skills_desc


# def prepare_skills_description(skills):
#     skills_desc = ["<available_skills>"]
#     for frontmatter, body, path in skills.values():
#         skills_desc.append("<skill>")
#         skills_desc.append("<name>")
#         skills_desc.append(html.escape(frontmatter["name"]))
#         skills_desc.append("</name>")
#         skills_desc.append("<description>")
#         skills_desc.append(html.escape(frontmatter["description"]))
#         skills_desc.append("</description>")
#         skills_desc.append("<location>")
#         skills_desc.append(path)
#         skills_desc.append("</location>")
#         skills_desc.append("</skill>")
#     skills_desc.append("</available_skills>")
#     return skills_desc


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    prompt = args.p
    skills = get_available_skills()
    skills_desc = prepare_skills_description(skills)

    messages = [
        {
            "role": "system",
            "content": system_prompt.format(skills="\n".join(skills_desc)),
        },
    ]

    if prompt.startswith("/"):
        prompt = load_skill(prompt, skills)
    else:
        prompt = {"role": "user", "content": prompt}
    if isinstance(prompt, dict):
        messages.append(prompt)
    if isinstance(prompt, list):
        messages.extend(prompt)

    tools = get_tools()
    agent = Agent(tools)
    agent.agent_loop(messages)


if __name__ == "__main__":
    main()
