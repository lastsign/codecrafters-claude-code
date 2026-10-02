import argparse
import html
import os

from dotenv import load_dotenv

from app.agent.agent import agent
from app.prompts import system_prompt
from app.skills.load import load_skill
from app.skills.parser import get_available_skills

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")


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

    agent.agent_loop(messages)


if __name__ == "__main__":
    main()
