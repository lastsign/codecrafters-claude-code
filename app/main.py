import argparse
import html
import os
import re
import shlex

from dotenv import load_dotenv
from openai import OpenAI

from app.prompts import system_prompt
from app.skills.parser import get_available_skills
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
    skills_desc = ["<available_skills>"]
    for frontmatter, body, path in skills.values():
        skills_desc.append("<skill>")
        skills_desc.append("<name>")
        skills_desc.append(html.escape(frontmatter["name"]))
        skills_desc.append("</name>")
        skills_desc.append("<description>")
        skills_desc.append(html.escape(frontmatter["description"]))
        skills_desc.append("</description>")
        skills_desc.append("<location>")
        skills_desc.append(path)
        skills_desc.append("</location>")
        skills_desc.append("</skill>")
    skills_desc.append("</available_skills>")
    return skills_desc


def pass_arguments_to_skill(arguments, skill_body):
    pattern = r"\$ARGUMENTS\[(\d+)\]|\$ARGUMENTS|\$(\d+)"

    def callback(m: re.Match) -> str:
        if m.group(0):
            return " ".join(arguments)
        i = int(m.group(1)) or int(m.group(2))
        if i and i < len(arguments):
            return arguments[i]
        return ""

    result, count = re.subn(pattern, callback, skill_body)
    if count == 0 and arguments:
        result = f"{skill_body}\n\nARGUMENTS: {' '.join(arguments)}"

    return result


def load_skill(prompt, skills):
    try:
        parts = shlex.split(prompt)
    except Exception:
        parts = prompt.split()
    skill_names = []
    for part in parts:
        if part.startswith("/") and part[1:] in skills:
            skill_names.append(part[1:])

    loaded_skills = []
    arguments = parts[len(skill_names) :]
    for skill_name in skill_names:
        if skill_name in skills:
            _, skill_body, _ = skills[skill_name]
            content = pass_arguments_to_skill(arguments, skill_body)
            loaded_skills.append({"role": "user", "content": content})
    return loaded_skills


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
