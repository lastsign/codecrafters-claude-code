from pathlib import Path

import strictyaml

from app.skills.errors.errors import ParseError, ValidationError


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---"):
        raise ParseError("Skill doesn't contain frontmatter")

    parts = content.split("---", 2)

    frontmatter = parts[1]
    body = parts[2].strip()

    try:
        metadata = strictyaml.load(frontmatter).data
    except strictyaml.YAMLError as e:
        raise ParseError(f"Invalid YAML in frontmatter{e}")

    if not isinstance(metadata, dict):
        raise ParseError("SKILL.md should be valid yaml mapping")

    if "metadata" in metadata and isinstance(metadata["metadata"], dict):
        metadata["metadata"] = {str(k): str(v) for k, v in metadata["metadata"].items()}

    return metadata, body


def parse_skill(skill_folder: Path) -> tuple[dict[str, str], str, str]:
    skill = Path(skill_folder / "SKILL.md").read_text()
    frontmatter, body = parse_frontmatter(skill)

    if "name" not in frontmatter:
        raise ValidationError("name is required field of frontmatter")
    if "description" not in frontmatter:
        raise ValidationError("description is required field of frontmatter")

    if frontmatter["name"] != skill_folder.name.lower():
        raise ValidationError(
            f"Skill name is invalid it should be equal to folder name {skill_folder}."
        )

    return frontmatter, body, f"{skill_folder.name.lower()}/SKILL.md"


def get_available_skills():
    skills_prefix = ".claude/skills/"
    skills_dir = Path(Path.cwd() / skills_prefix)

    if not skills_dir.exists():
        return [f"Path does not exist: {skills_dir}"]

    if not skills_dir.is_dir():
        return [f"Not a directory: {skills_dir}"]

    skills = {}
    for skill_folder in skills_dir.iterdir():
        if skill_folder.is_dir() and Path(skill_folder / "SKILL.md").exists():
            skills[skill_folder.name.lower()] = parse_skill(skill_folder)

    return skills
