import shlex

from app.agent import agent, Agent
from app.skills.load import pass_arguments_to_skill
from app.skills.parser import get_available_skills
from app.tools import get_tools


def skill(name: str, args: str | None = None) -> str | None:
    arguments = []
    if args:
        try:
            arguments = shlex.split(args)
        except Exception:
            arguments = args.split()
    skills = get_available_skills()
    frontmatter, skill_body, path = skills[name]
    body = pass_arguments_to_skill(arguments, skill_body)

    content = (
        f"Skill: {name} (located at {path})\n"
        "Paths in the instructions below are relative to that folder.\n\n"
        f"{body}"
    )

    if "context" in frontmatter and frontmatter["context"] == "fork":
        content, name
        messages = [{"role": "user", "content": content}]
        result = Agent(get_tools()).agent_loop(messages)
        return f"Skill {name} ran in a separate context and returned: {result}"

    return content
