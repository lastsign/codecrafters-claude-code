import shlex

from app.skills.load import pass_arguments_to_skill
from app.skills.parser import get_available_skills


def skill(name: str, args: str | None) -> str:
    if args:
        try:
            arguments = shlex.split(args)
        except Exception:
            arguments = args.split()
    skills = get_available_skills()
    _, skill_body, path = skills[name]
    body = pass_arguments_to_skill(arguments, skill_body)

    content = (
        f"Skill: {name} (located at {path})\n"
        "Paths in the instructions below are relative to that folder.\n\n"
        f"{body}"
    )
    return content
