try:  # let nuke_utilities.py work in any context, not only inside nuke
    import nuke
except ImportError:
    pass

import os
import re
import platform
import tempfile

from MatchMoveExporter.lib.utilities.cmd_utilities import run_terminal_command, correct_path_to_console_path
from MatchMoveExporter.lib.utilities.os_utilities import get_version_with_postfix
from MatchMoveExporter.userconfig import UserConfig


MOV_EXTENSIONS = [".mov", ".mp4"]
SEQUENCE_EXNTENSIONS = [".exr", ".dpx", ".png", ".tiff", ".psd", ".jpeg", ".jpg"]


def get_export_pyscript() -> str:
    """
    Return Python Script for Nuke which export all tracking data. This script
    works only with json data (JsonForNuke) that must be exported from 3DE4 or
    SynthEyes project. As system arguments script expects to receive json data.

    This function read Python Script from nuke_export_script.py file which
    located in current directory. And write it to .../TEMP/MMEXPORTER_NUKE_PYTHON_SCRIPT.py
    path.

    :return: path to Python Script in temp directory.
    """
    this_path = os.path.dirname(os.path.abspath(__file__))
    pyscript_path = os.path.join(this_path, "nuke_export_script.py")
    with open(pyscript_path, "r") as file:
        script = file.read()

    filepath = os.path.join(os.path.join(tempfile.gettempdir(), "MMEXPORTER_NUKE_PYTHON_SCRIPT.py"))
    with open(filepath, "w") as file:
        file.write(script)

    return filepath


def add_paths_to_command(command: str, paths_to_add: list, env_name: str):
    """
    Adds paths to the PYTHONPATH environment variable based on the operating system.

    Args:
        command (str): The command to which the environment variables will be added.
        kwargs (dict): A dictionary of parameters where the key 'PATHS_TO_ADD_TO_PYTHONPATH' contains a list of paths.

    Returns:
        str: The updated command with the environment variables added.
    """
    if platform.system() == "Windows":
        # For Windows, use `set` to add environment variables
        command += f"set {env_name}=" + os.pathsep.join(paths_to_add) + " & "
    else:
        # For Unix-like systems, use `export`
        command += f"export {env_name}=" + ":".join(paths_to_add) + " && "

    return command


def execute_nuke_script(nuke_exec_path: str,
                        py_script_path: str,
                        *args, **kwargs) -> None:
    """
    Execute Python Script through Nuke terminal mode (opens new terminal).

    :param nuke_exec_path: path to nuke executable.
    :param py_script_path: path to Python file to execute in Nuke.
    :param args: any args to use in py_script. Example: nuke script path, etc.
    :param kwargs:
        PATHS_TO_ADD_TO_PYTHONPATH: list of additional paths which will be added to
        environment. For example, so that Nuke can import certain user libraries.
        PATHS_TO_ADD_TO_NUKE_PATH: list of additional paths which will be added to
        NUKE_PATH environment. For example, if you need to add some nuke plugins.
    :return: None
    """
    command = ""

    # Add paths to environment variables depending on the OS
    if "PATHS_TO_ADD_TO_PYTHONPATH" in kwargs:
        paths_to_add = kwargs["PATHS_TO_ADD_TO_PYTHONPATH"]
        if isinstance(paths_to_add, list) and paths_to_add:
            command = add_paths_to_command(command, paths_to_add, "PYTHONPATH")
    if "PATHS_TO_ADD_TO_NUKE_PATH" in kwargs:
        paths_to_add = kwargs["PATHS_TO_ADD_TO_NUKE_PATH"]
        if isinstance(paths_to_add, list) and paths_to_add:
            command = add_paths_to_command(command, paths_to_add, "NUKE_PATH")

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


def get_nuke_script_path(path: str, script_name: str) -> str:
    """
    Generate Nuke script path according to parameters. Create folders if they don't exist.

    :param path: path to folder where will be structure (like: "/folder/script_name.nk") created.
    :param script_name: name of Nuke script.
    :param dir_folder_is_version: if True, folder will be version with postfix (detects automatically
    with regexp from script_name).
    :return: path to Nuke script.
    """
    folder = UserConfig.get_export_folder_name(script_name)

    nuke_script_path = os.path.join(
        path,
        folder,
        script_name + ".nk"
    )

    os.makedirs(os.path.dirname(nuke_script_path), exist_ok=True)

    return nuke_script_path


def check_path_exists(file_path: str) -> bool:
    """Check if file path exists."""
    if not file_path.strip():
        return False

    if get_extension(file_path) in MOV_EXTENSIONS and not os.path.exists(file_path):
        return False

    if get_extension(file_path) in SEQUENCE_EXNTENSIONS and not os.path.exists(os.path.dirname(file_path)):
        return False

    return True


def check_file_is_sequence(file_path: str) -> bool:
    """
    Check if file path is sequence or not. Works even file doesn't exist.

    :param file_path: path to file which check.
    :return: True, if file is sequence.
    """
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
    """Return file extension with dot."""
    try:
        return os.path.splitext(file_path)[1]
    except IndexError:
        return ""


def get_file_name(file_full_name: str, ignore_version_and_postfix: bool = True) -> str:
    """
    Removes extension and counter/padding from file name.

    :param file_full_name: file name with version and extension.
    :param ignore_version_and_postfix: if True, also remove version and postfix.
    :return: file name without extension and version.
    """

    # remove extension
    file_name = os.path.splitext(file_full_name)[0]

    # remove: %d, %00d, .##, _##
    file_name = re.sub("%(\d+|)d", "", file_name)
    file_name = re.sub("\.#+", "", file_name)
    file_name = re.sub("_#+", "", file_name)

    # remove version
    if ignore_version_and_postfix:
        file_name = re.sub("_v\d+(_.+|)", "", file_name)

    # remove dots in the end if still exists
    file_name = re.sub("\.+$", "", file_name)
    return re.sub("_+$", "", file_name)


def import_file_as_read_node(file_path: str):
    """
    Get file path and import like Read node.

    :param file_path: path to file to import as Read node.
    :return: nuke.Node (Read)
    """
    if not check_path_exists(file_path):
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

    read_node["auto_alpha"].setValue(1)

    return read_node


def import_nodes_from_script(script_path: str) -> list:
    """
    Import nodes from Nuke script to current Nuke script.

    :param script_path: path to Nuke script from which to import nodes.
    :return: list of Nuke nodes.
    """
    previous_all_nodes = nuke.allNodes()
    nuke.scriptReadFile(script_path)
    return list(set(nuke.allNodes()) - set(previous_all_nodes))

def animate_xyz_knob_values(knob,  # nuke.XYZ_Knob
                            values: [[], [], []],  # [[x], [y], [z]]
                            first_frame: int) -> None:
    """
    Animates nuke knob from certain frame according to x, y and z values.

    Warning: quantity of values in all of 3 lists must be the same,
    otherwise iteration will be for the smallest one.

    :param knob: Nuke knob which holds a 3D coordinate.
    :param values: list of lists with 3D coordinates in format [[x], [y], [z]].
    :param first_frame: frame to start animation with.
    :return: None
    """
    knob.setAnimated()
    for i, (x, y, z) in enumerate(zip(*values)):
        frame = first_frame + i
        knob.setValueAt(x, frame, 0)  # x
        knob.setValueAt(y, frame, 1)  # y
        knob.setValueAt(z, frame, 2)  # z


def animate_array_knob_values(knob,  # nuke.Array_Knob
                              values: [int],
                              first_frame: int) -> None:
    """
    Animates nuke knob from certain frame according values.

    :param knob: Nuke slider knob.
    :param values: list of integers.
    :param first_frame: frame to start animation with.
    :return: None
    """
    knob.setAnimated()
    for i, value in enumerate(values):
        frame = first_frame + i
        knob.setValueAt(value, frame)


def declone_node(node):
    """
    Copy from nukescripts.misc file

    :param node: nuke.Node
    :return: nuke.Node
    """
    if node.clones() == 0:
        return node
    args = node.writeKnobs(nuke.WRITE_ALL | nuke.WRITE_USER_KNOB_DEFS | nuke.WRITE_NON_DEFAULT_ONLY | nuke.TO_SCRIPT)
    with node.parent():
        newnode = nuke.createNode(node.Class(), knobs = args)
    nuke.inputs(newnode, nuke.inputs(node))
    num_inputs = nuke.inputs(node)
    for i in range(num_inputs):
     newnode.setInput(i, node.input(i))
    node.setInput(0, newnode)
    nuke.delete(node)
    return newnode


def copy_paste_node(node):
    """

    :param node: nuke.Node
    :return: nuke.Node
    """
    # new_node = nuke.clone(node)
    # new_node = declone_node(new_node)
    # new_node.setName(node.name())
    # return new_node
    return nuke.clone(node)