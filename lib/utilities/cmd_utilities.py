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

def execute_nuke_script(nuke_exec_path: str,
                        py_script_path: str,
                        *args, **kwargs):
    """
    Opens NukeX or NukeStudio in new terminal

    :param nuke_exec_path: path to nuke executable
    :param py_script_path: path to .py file to execute in nuke
    :param args: any args to use in py_script. Example: nuke script path, etc.
    :param kwargs:
        PATHS_TO_ADD_TO_PYTHONPATH: list, дополнительные пути, которые нужно добавить в окружение.
        Например, чтобы Nuke мог импортировать определенные пользовательские библиотеки.
    :return: None
    """
    command = ""

    # Add paths to environment variables depending on the OS
    if "PATHS_TO_ADD_TO_PYTHONPATH" in kwargs:
        paths_to_add = kwargs["PATHS_TO_ADD_TO_PYTHONPATH"]
        if isinstance(paths_to_add, list) and paths_to_add:
            if platform.system() == "Windows":
                # Для Windows используем `set` для добавления переменных окружения
                command += "set PYTHONPATH=" + os.pathsep.join(paths_to_add) + " & "
            else:
                # Для Unix-подобных систем используем `export`
                command += "export PYTHONPATH=" + ":".join(paths_to_add) + " && "

    # change disk where py_script located (for Windows only)
    if platform.system() == "Windows":
        command += py_script_path.replace("\\", "/").split("/")[0] + " & "

    # change dir to py_script dir
    command += "cd " + correct_path_to_console_path(os.path.dirname(py_script_path)) + " &"

    # set nuke executable
    command += " " + correct_path_to_console_path(nuke_exec_path)

    # set terminal mode
    command += " -t"

    # set py_script
    command += " " + os.path.basename(py_script_path)

    # args
    for arg in args:
        command += " " + arg

    # exit terminal after execute nuke
    if not os.getenv("DEV"):
        command += " && exit"

    # get script directory
    cwd = os.path.dirname(py_script_path)

    return run_terminal_command(command, cwd=cwd)
