import os
import tempfile


def generate_nuke_python_file_path(script: str) -> str:
    dir_path = os.path.join(tempfile.gettempdir(), "match_move_exporter")

    os.makedirs(dir_path, exist_ok=True)

    filepath = os.path.join(dir_path, "NUKE_PYTHON_SCRIPT.py")

    with open(filepath, "w") as file:
        file.write(script)

    return filepath


def generate_and_get_nuke_python_script_path() -> str:
    script = """
import nuke

nuke.createNode("Blur")
"""
    # C:\Users\user\AppData\Local\Temp\match_move_exporter\NUKE_PYTHON_SCRIPT.py
    return generate_nuke_python_file_path(script)
