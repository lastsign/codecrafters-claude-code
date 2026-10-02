from app.tools.bash import bash


def test_read_command():
    assert (
        bash("ls")
        == "README.md\napp\ncodecrafters.yml\npyproject.toml\ntests\nuv.lock\nyour_program.sh\n"
    )
