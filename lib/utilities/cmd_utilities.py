import os
import subprocess
import platform


def run_terminal_command(command: str, cwd: str = None) -> None:
    OS = platform.system()

    if OS == "Windows":
        script = ['start', 'cmd', '/k', command]
        use_shell = True

    elif OS == "Darwin":
        script = f'osascript -e \'tell application "Terminal" to do script "{command}"\''
        use_shell = True

    else:
        script = ['x-terminal-emulator', '-e', command]
        use_shell = False

    if cwd:
        subprocess.Popen(script, shell=use_shell, cwd=cwd)
    else:
        subprocess.Popen(script, shell=use_shell)


def correct_path_to_console_path(input_path: str) -> str:
    path_corrected = str()
    for path_part in input_path.replace("\\", r'/').split("/"):
        if " " in path_part:
            path_corrected += f'"{path_part}"/'
            continue
        path_corrected += f'{path_part}/'

    if path_corrected[-1] == "/":
        path_corrected = path_corrected[:-1]

    return path_corrected
