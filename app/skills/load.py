import re
import shlex


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
            _, skill_body, path = skills[skill_name]
            body = pass_arguments_to_skill(arguments, skill_body)

            content = (
                f"Skill: {skill_name} (located at {path})\n"
                "Paths in the instructions below are relative to that folder.\n\n"
                f"{body}"
            )

            loaded_skills.append({"role": "user", "content": content})
    return loaded_skills
