try:  # let work nuke_utilities.py work in any context, not only inside nuke
    import nuke
except ImportError:
    pass

import os
import re
import platform
import tempfile

from lib.utilities.cmd_utilities import run_terminal_command, correct_path_to_console_path
from lib.utilities.os_utilities import get_version_with_postfix


MOV_EXTENSIONS = [".mov", ".mp4"]
SEQUENCE_EXNTENSIONS = [".exr", ".dpx", ".png", ".tiff", ".psd", ".jpeg", ".jpg"]


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


def _check_path_exists(file_path: str) -> bool:
    if not file_path.replace(" ", ""):
        return False

    if get_extension(file_path) in MOV_EXTENSIONS and not os.path.exists(file_path):
        return False

    if get_extension(file_path) in SEQUENCE_EXNTENSIONS and not os.path.exists(os.path.dirname(file_path)):
        return False

    return True


# START


def check_file_is_sequence(file_path: str) -> bool:
    no_extension = len(os.path.splitext(file_path)) == 1
    if no_extension:
        raise ValueError(f"Looks like {file_path} is folder, not file.")

    if os.path.splitext(file_path)[-1] in MOV_EXTENSIONS:
        return False

    file_name = get_file_name(os.path.basename(file_path), ignore_version_and_postfix=False)

    if os.path.exists(file_path):
        files_in_dir = os.listdir(os.path.dirname(file_path))
        matching_files_count = sum(1 for f in files_in_dir if file_name in f)
    else:
        matching_files_count = 42  # some random (or not random...) value

    assert matching_files_count != 0, \
        f"No files with name {file_name} found in: {os.path.dirname(file_path)}"

    return matching_files_count > 1


def get_extension(file_path: str) -> str:
    """Return file extension with dot"""
    try:
        return os.path.splitext(file_path)[1]
    except IndexError:
        return ""


def get_file_name(file_full_name: str, ignore_version_and_postfix: bool = True) -> str:
    """Return file name without extension and version"""

    # remove extension
    file_name = os.path.splitext(file_full_name)[0]

    # remove: %d, %00d, .##, _##
    file_name = re.sub("%(\d+|)d", "", file_name)
    file_name = re.sub("\.#+", "", file_name)
    file_name = re.sub("_#+", "", file_name)

    # remove version
    if ignore_version_and_postfix:
        file_name = re.sub("_v\d+(_.+|)", "", file_name)

    # remove dots in the end if exists
    file_name = re.sub("\.+$", "", file_name)
    return re.sub("_+$", "", file_name)


def import_file_as_read_node(file_path):
    """

    :param file_path:
    :return: nuke.Node (Read)
    """
    if not _check_path_exists(file_path):
        raise FileNotFoundError(f"File doesn't exists:\n\n{file_path}")

    if get_extension(file_path) not in MOV_EXTENSIONS + SEQUENCE_EXNTENSIONS:
        raise ValueError(f"File doesn't supported. Supported types: {MOV_EXTENSIONS + SEQUENCE_EXNTENSIONS}")

    if check_file_is_sequence(file_path):

        file_dir = os.path.dirname(file_path)
        file_full_name = os.path.basename(file_path)
        file_name = get_file_name(file_full_name, ignore_version_and_postfix=False)
        file_extension = get_extension(file_full_name)

        nuke_file_name = str()
        for f in nuke.getFileNameList(file_dir):

            if file_extension not in f:
                continue
            if file_name not in f:
                continue
            if "3de_bcompress" in f:
                continue

            nuke_file_name = f

        assert nuke_file_name, f"Unsuspected Error!"
        nuke_file_path = os.path.join(file_dir, nuke_file_name).replace("\\", "/")

        regexp_pattern = r" \d+-\d+$"
        more_than_one_file_in_sequence = re.findall(regexp_pattern, nuke_file_name)
        if more_than_one_file_in_sequence:
            frame_range = re.findall(regexp_pattern, nuke_file_name)[0]
            read_node = nuke.nodes.Read(file=re.split(regexp_pattern, nuke_file_path)[0],
                                        first=frame_range.split("-")[0],
                                        last=frame_range.split("-")[1])
        else:
            read_node = nuke.createNode('Read', "file {" + nuke_file_path + "}", inpanel=False)

    else:
        read_node = nuke.createNode('Read', "file {" + file_path + "}", inpanel=False)

    return read_node
