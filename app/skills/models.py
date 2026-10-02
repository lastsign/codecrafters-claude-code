from dataclasses import dataclass

@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body: str
