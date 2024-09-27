#
# 3DE4.script.name:	MatchMove Exporter
#
# 3DE4.script.version:	v1.0
#
# 3DE4.script.gui:	Main Window::MMExporter
#
# 3DE4.script.comment:	Easy and Fast Export for work.
#


import os
import re

import tde4
from vl_sdv import rot3d, mat3d, VL_APPLY_ZXY

from lib.utilities.os_utilities import get_root_path
from lib.utilities.cmd_utilities import run_terminal_command, correct_path_to_console_path, execute_nuke_script
from lib.utilities.nuke_utilities import get_export_py_script
from lib.utilities.log_utilities import setup_or_get_logger


LOGGER = setup_or_get_logger(force_setup=True, use_console_handler=False)

NUKE_EXPORT_SCRIPT = r"C:\Users\user\github\MatchMoveExporter\test_files\sh020\v001\sh020_track_v001.nk"
NUKE_EXECUTABLE = os.getenv("NUKE_EXECUTABLE_PATH")


# FUNCTIONS


def check_nuke_executable_path() -> bool:
    if not os.path.exists(NUKE_EXECUTABLE):
        message = f"Nuke path doesn't exists: {NUKE_EXECUTABLE}"
        tde4.postQuestionRequester("Message", message, "OK")
        return False

    if not re.fullmatch(r"^Nuke[0-9]+.[0-9]\.exe$", os.path.basename(NUKE_EXECUTABLE)):
        message = f"Incorrect Nuke executable path: {NUKE_EXECUTABLE}"
        message += f"\nExample of correct path: C:\\Program Files\\Nuke14.0v7\\Nuke14.0.exe"
        tde4.postQuestionRequester("Message", message, "OK")
        return False

    return True


# CALLBACKS


def button_clicked_callback(requester, widget, action) -> None:
    print ("New callback from widget ",widget," received, action: ", action)
    print ("Put your code here...")

    if not check_nuke_executable_path():
        return

    execute_nuke_script(NUKE_EXECUTABLE,  # nuke_exec_path
                        get_export_py_script(),  # py_script_path
                        NUKE_EXPORT_SCRIPT,  # args: add nuke export-script path
                        PATHS_TO_ADD_TO_PYTHONPATH=[get_root_path()]  # kwargs: add access to lib folder for nuke
                        )

    LOGGER.info("EQUALIZER STILL HAS LOGGING!")

def label_changed_callback(requester, widget, action) -> None:
    print ("New callback from widget ",widget," received, action: ",action)
    print ("Put your code here...")
    return


def _MatchMoveExporterUpdate(requester) -> None:
    print ("New update callback received, put your code here...")
    # LOGGER.info("EQUALIZER STILL HAS LOGGING!")
    return


# GENERATE NUKE FILE


def convertToAngles(r3d):
    """
    Converts a given 3x3 rotation matrix to Euler angles using the ZXY convention.

    Args:
        r3d (list[list[float]]): A 3x3 rotation matrix.

    Returns:
        tuple: Euler angles (rx, ry, rz) in degrees corresponding to the rotation matrix.

    Note:
        The conversion is performed by first calculating the ZXY Euler angles from
        the rotation matrix and then converting these angles from radians to degrees.
    """
    rot = rot3d(mat3d(r3d)).angles(VL_APPLY_ZXY)
    rx = (rot[0] * 180.0) / 3.141592654
    ry = (rot[1] * 180.0) / 3.141592654
    rz = (rot[2] * 180.0) / 3.141592654
    return rx, ry, rz


def convertZup(p3d, yup):
    """
    Converts a 3D point's Y-up coordinates to Z-up coordinates if needed.

    Args:
        p3d (list[float]): A 3D point [x, y, z] in Y-up coordinates.
        yup (int): Indicates whether the coordinates are Y-up (1) or Z-up (0).

    Returns:
        list: A 3D point in Z-up coordinates [x, z, -y] if yup is 0, otherwise returns the input coordinates.
    """
    if yup == 1:
        return p3d
    else:
        return [p3d[0], -p3d[2], p3d[1]]


def angleMod360(d0, d):
    """
    Adjusts an angle to stay within the range of -180 to 180 degrees relative to a reference angle.

    Args:
        d0 (float): The reference angle.
        d (float): The angle to be adjusted.

    Returns:
        float: The adjusted angle within the -180 to 180 degree range.
    """
    dd = d - d0
    if dd > 180.0:
        d = angleMod360(d0, d - 360.0)
    elif dd < -180.0:
        d = angleMod360(d0, d + 360.0)
    return d


def validName(name):
    """
    Cleans a given name string by replacing spaces and '#' symbols with underscores.

    Args:
        name (str): The name string to be cleaned.

    Returns:
        str: The cleaned name with spaces and '#' replaced by underscores.
    """
    name = name.replace(" ", "_")
    name = name.replace("#", "_")
    return name


class ParentNode:
    def __init__(self, name: str, xpos: int = None, ypos: int = None,
                 additional_strings: [str] = None):

        self.class_ = getattr(self, 'class_', None)  # Берём class_ из дочернего класса, если он определён
        if self.class_ is None:
            raise ValueError("class_ не может быть пустым. Убедитесь, что он определён в дочернем классе.")

        self.inputs = getattr(self, 'inputs', None)
        if self.inputs is None:
            raise ValueError("inputs не может быть пустым. Убедитесь, что он определён в дочернем классе.")

        self.name = name

        if xpos is not None: self.xpos = xpos
        if ypos is not None: self.ypos = ypos
        if additional_strings is not None: self.additional_strings = additional_strings

    def _get_all_attrs(self) -> dict:
        """
        Возвращает все атрибуты класса и экземпляра в виде словаря.
        """
        attrs = {}
        # Получаем атрибуты экземпляра
        attrs.update(self.__dict__)
        # Получаем атрибуты класса (без магических методов)
        attrs.update({key: value for key, value in self.__class__.__dict__.items() if not key.startswith("__")})
        return attrs

    def get_code(self) -> str:
        code = f"{self.class_} {{\n"

        for knob_name, knob_value in self._get_all_attrs().items():
            if knob_name == "class_":
                continue
            elif knob_name == "additional_strings":
                code += f"{self.convert_additional_strings_to_text(knob_value)}\n"
            else:
                code += f" {knob_name} {knob_value}\n"

        code += "}"

        return code

    @staticmethod
    def convert_additional_strings_to_text(additional_strings: []) -> str:
        return chr(10).join([" " + string for string in additional_strings])


class RootNode(ParentNode):
    class_: str = "Root"
    inputs: int = 0

    frame: int = 1001
    first_frame: int = 1001
    last_frame: int = 0
    # format: bbox.x bbox.y 0 0 width height aspect name
    format: str = "1920 1080 0 0 1920 1080 1 1920x1080"
    fps: int = 25


class GroupNode(ParentNode):
    class_: str = "Group"
    inputs: int = 0


class ConstantNode(ParentNode):
    class_: str = "Constant"
    inputs: int = 0

    color: str = "{1.0 1.0 1.0}"


def generate_nuke_script():
    code = f"""
{RootNode(name="").get_code()}
{GroupNode(name="").get_code()}
{ConstantNode(name="").get_code()}
"""
    # TODO: stopped there :D

    return code.strip()

#
# DO NOT ADD ANY CUSTOM CODE BEYOND THIS POINT!
#

try:
    requester	= _MatchMoveExporter_requester
except (ValueError,NameError,TypeError):
    requester = tde4.createCustomRequester()
    tde4.addButtonWidget(requester,"button_export","EXPORT")
    tde4.setWidgetOffsets(requester,"button_export",60,60,30,0)
    tde4.setWidgetAttachModes(requester,"button_export","ATTACH_WINDOW","ATTACH_WINDOW","ATTACH_WIDGET","ATTACH_NONE")
    tde4.setWidgetSize(requester,"button_export",80,30)
    tde4.setWidgetCallbackFunction(requester,"button_export","button_clicked_callback")
    tde4.addTextFieldWidget(requester,"textfield_name","NAME:","sh000_00_track_v001")
    tde4.setWidgetOffsets(requester,"textfield_name",60,60,30,0)
    tde4.setWidgetAttachModes(requester,"textfield_name","ATTACH_WINDOW","ATTACH_WINDOW","ATTACH_WINDOW","ATTACH_NONE")
    tde4.setWidgetSize(requester,"textfield_name",200,20)
    tde4.setWidgetCallbackFunction(requester,"textfield_name","label_changed_callback")
    tde4.addLabelWidget(requester,"label_pattern","[seq_name]_sh<shot_number>_<task_number>_track_v000_[definition]","ALIGN_LABEL_LEFT")
    tde4.setWidgetOffsets(requester,"label_pattern",60,60,15,0)
    tde4.setWidgetAttachModes(requester,"label_pattern","ATTACH_WINDOW","ATTACH_WINDOW","ATTACH_WIDGET","ATTACH_NONE")
    tde4.setWidgetSize(requester,"label_pattern",200,20)
    tde4.setWidgetLinks(requester,"button_export","","","label_pattern","")
    tde4.setWidgetLinks(requester,"textfield_name","","","","")
    tde4.setWidgetLinks(requester,"label_pattern","","","textfield_name","")
    _MatchMoveExporter_requester = requester

#
# DO NOT ADD ANY CUSTOM CODE UP TO THIS POINT!
#

if tde4.isCustomRequesterPosted(_MatchMoveExporter_requester)=="REQUESTER_UNPOSTED":
    if tde4.getCurrentScriptCallHint()=="CALL_GUI_CONFIG_MENU":
        tde4.postCustomRequesterAndContinue(_MatchMoveExporter_requester,"MatchMove Exporter",0,0,"_MatchMoveExporterUpdate")
    else:
        tde4.postCustomRequesterAndContinue(_MatchMoveExporter_requester,"MatchMove Exporter v1.0",800,600,"_MatchMoveExporterUpdate")
else:	tde4.postQuestionRequester("MatchMove Exporter","Window/Pane is already posted, close manually first!","Ok")
