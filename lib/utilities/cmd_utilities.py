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
        # command += f"""&& osascript -e 'tell application "Terminal" to close first window'""" close macOS terminal
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

def execute_nuke_script(nuke_exec_path: str,
                        nuke_script_path: str,
                        py_script_path: str):
    """
    Opens NukeX or NukeStudio in new terminal

    # <путь_к_NukeX> --nukex <путь_к_nk_файлу> -t <путь_к_python_скрипту>

    :param py_script_path:
    :param nuke_script_path: string, path to script for open
    :param nuke_exec_path: string, path to nuke executable
    :return: None
    """
    command = ""

    # change disk if Windows
    if py_script_path and platform.system() == "Windows":
        command += py_script_path.replace("\\", "/").split("/")[0] + " & "

    # change dir to script dir
    if py_script_path:
        command += "cd " + correct_path_to_console_path(os.path.dirname(py_script_path)) + " & "

    # set nuke executable path
    command += correct_path_to_console_path(nuke_exec_path)

    # # set sys args that nuke has
    # for arg in nuke.rawArgs:
    #     if arg == nuke.rawArgs[0]:  # first arg is nuke executable we already have it
    #         continue
    #     command += " " + arg

    command += " --nukex"

    command += " " + nuke_script_path

    command += " -t"

    # set script file name to open
    if py_script_path:
        command += " " + os.path.basename(py_script_path)

    # exit terminal after execute nuke
    command += " && exit"

    # get script directory
    if nuke_script_path:
        cwd = os.path.dirname(py_script_path)
    else:
        cwd = None

    return run_terminal_command(command, cwd=cwd)
