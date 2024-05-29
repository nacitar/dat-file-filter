import subprocess
from pathlib import Path


def main() -> int:
    script_dir = Path(__file__).parent
    try:
        commands = [
            ["black", "."],
            ["isort", "."],
            ["mypy", "."],
            ["flake8", "."],
            ["pytest", "."],
        ]
        for command in commands:
            print(f"Running {command[0]}...")
            subprocess.run(command, check=True, cwd=script_dir)
            print()
    except subprocess.CalledProcessError as e:
        return e.returncode
    print("All checks completed successfully!")
    return 0
