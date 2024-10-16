import os
import platform
import tempfile

from lib.utilities.cmd_utilities import run_terminal_command, correct_path_to_console_path
from lib.utilities.os_utilities import get_version_with_postfix

# private


def _create_script_file(script: str) -> str:
    dir_path = os.path.join(tempfile.gettempdir(), "match_move_exporter")

    os.makedirs(dir_path, exist_ok=True)

    filepath = os.path.join(dir_path, "NUKE_PYTHON_SCRIPT.py")

    with open(filepath, "w") as file:
        file.write(script)

    return filepath


# public


def get_export_pyscript(return_file: bool = True) -> str:
    """
    Скрипт для Nuke, который экспортирует трекинг-дату:
    - Дэйлиз .mov
    - STMap дисторсию .exr
    - Камеру и геометрию в формате .abc и .fbx
    - Undistort в формате .exr
    - Папку geo, где будет вся геометрия

    На входе скрипту требуются аргументы:
    - argv[1]: Подготовленный под экспорт скрипт .nk

    Важно: для корректной работы скрипта необходим подготовленный '.nk' файл, который
    создается на этапе экспорта из 3DEqualizer или SynthEyes. Также, должен быть
    доступ к импорту файлов из папки lib.
    """
    this_path = os.path.dirname(os.path.abspath(__file__))
    pyscript_path = os.path.join(this_path, "nuke_export_script.py")
    with open(pyscript_path, "r") as file:
        script = file.read()

    if return_file:
        return _create_script_file(script)
    return script


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


def get_nuke_script_path(folder_path: str, script_name: str, dir_folder_is_version: bool = True) -> str:
    if dir_folder_is_version:  # TODO: add env arg
        dir_folder = get_version_with_postfix(script_name)
    else:
        dir_folder = script_name

    nuke_script_path = os.path.join(
        folder_path,
        dir_folder,
        script_name + ".nk"
    )

    os.makedirs(os.path.dirname(nuke_script_path), exist_ok=True)

    return nuke_script_path
