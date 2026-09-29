class SkillError(Exception):
    """Base exception for all skill-related errors."""


class ParseError(SkillError):
    """Raised when SKILL.md parsing fails."""


class ValidationError(SkillError):
    """Raised when skill property is invalid.

    Attributes:
        errors: List of validation error messages (may contain just one)

    """

    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors if errors is not None else [message]
