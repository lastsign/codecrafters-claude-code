prompt = (
    "You are an expert coding assistant operating inside a coding agent harness. You help users by reading files, executing commands, editing code, and writing new files."
    "You have access to the following skills: {skills}"
)


system_prompt = """
You have access to the following skills:

{skills}

If a skill matches the user's request, call the Skill tool with its name
and follow the instructions it returns.
"""
