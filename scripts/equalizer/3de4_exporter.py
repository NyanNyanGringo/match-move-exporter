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
from lib.utilities.cmd_utilities import run_terminal_command, correct_path_to_console_path
from lib.utilities.nuke_utilities import get_export_pyscript, execute_nuke_script
from lib.utilities.log_utilities import setup_or_get_logger


LOGGER = setup_or_get_logger(force_setup=True, use_console_handler=False)

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

    # checks

    if not check_nuke_executable_path():
        return

    nuke_script_name: str = tde4.getWidgetValue(requester, "textfield_name")

    if not nuke_script_name.strip():
        message = "Parameter name can't be empty."
        tde4.postQuestionRequester("Message", message, "OK")
        return

    camera_point_group = None
    for point_group in tde4.getPGroupList():
        if tde4.getPGroupType(point_group) == "CAMERA":
            camera_point_group = point_group
    if camera_point_group is None:
        message = "Error, there is no camera point group."
        tde4.postQuestionRequester("Message", message, "Ok")

    # nuke_export_script

    versions = re.findall("_v\d+(?:_.+)?", nuke_script_name)  # search versions with postfix
    if versions:  # TODO: добавить аргумент из командной строки ONLY_VERSION_IN_DIR_NAME
        dir_name = versions[-1]
    else:
        dir_name = nuke_script_name

    nuke_export_script = os.path.join(
        os.path.dirname(tde4.getProjectPath()),
        dir_name,
        nuke_script_name + ".nk"
    )
    os.makedirs(os.path.dirname(nuke_export_script), exist_ok=True)









    # cam = tde4.getCurrentCamera()
    # noframes = tde4.getCameraNoFrames(cam)
    # lens = tde4.getCameraLens(cam)
    # cattr = tde4.getCameraSequenceAttr(cam)
    # filename = tde4.getCameraPath(cam)
    # width = tde4.getCameraImageWidth(cam)
    # height = tde4.getCameraImageHeight(cam)
    # camname = tde4.getCameraName(cam)
    # focal = tde4.getCameraFocalLength(cam, 1)
    # fback_w = tde4.getLensFBackWidth(lens)
    # fback_h = tde4.getLensFBackHeight(lens)




    # create json file to read in nuke

    camera_point_group = [pg for pg in tde4.getPGroupList() if tde4.getPGroupType(pg) == "CAMERA"][0]
    scene_translate = tde4.getScenePosition3D()
    scene_rotation = convertToAngles(tde4.getSceneRotation3D())
    scene_scale = tde4.getSceneScale3D()

    # points = tde4.getPointList(camera_point_group)

    JSON = {}

    cameras = []
    for camera in tde4.getCameraList():
        camera_translate_x, camera_translate_y, camera_translate_z = [], [], []
        camera_rotate_x, camera_rotate_y, camera_rotate_z = [], [], []
        focal = []
        previous_rotation = None
        for frame in range(1, tde4.getCameraNoFrames(camera) + 1):
            x_pos, y_pos, z_pos = tde4.getPGroupPosition3D(camera_point_group, camera, frame)
            camera_translate_x.append(x_pos), camera_translate_y.append(y_pos), camera_translate_z.append(z_pos)

            current_rotation = convertToAngles(tde4.getPGroupRotation3D(camera_point_group, camera, frame))
            if previous_rotation:
                current_rotation = [
                    angleMod360(previous_rotation[0], current_rotation[0]),
                    angleMod360(previous_rotation[1], current_rotation[1]),
                    angleMod360(previous_rotation[2], current_rotation[2])
                ]
            previous_rotation = current_rotation
            x_rot, y_rot, z_rot = current_rotation
            camera_rotate_x.append(x_rot), camera_rotate_y.append(y_rot), camera_rotate_z.append(z_rot)

            f = tde4.getCameraFocalLength(camera, frame) * 10
            focal.append(f)

        camera_dict = {
            "first_frame": tde4.getCameraFrameOffset(camera),
            "axis": {
                "translate": {
                    "x": scene_translate[0],
                    "y": scene_translate[1],
                    "z": scene_translate[2]
                },
                "rotate": {
                    "x": scene_rotation[0],
                    "y": scene_rotation[1],
                    "z": scene_rotation[2]
                },
                "scale": scene_scale
            },
            "camera": {
                "translate": {
                    "x": camera_translate_x,
                    "y": camera_translate_y,
                    "z": camera_translate_z
                },
                "rotate": {
                    "x": camera_rotate_x,
                    "y": camera_rotate_y,
                    "z": camera_rotate_z
                },
                "focal": focal,
                "haperture": tde4.getLensFBackWidth(tde4.getCameraLens(camera)) * 10,
                "vaperture": tde4.getLensFBackHeight(tde4.getCameraLens(camera)) * 10
            }
        }

        cameras.append(camera_dict)

    JSON["cameras"] = cameras




    print("GOOD")

    # axis
    #

    # camera
    #

    return

    # export

    execute_nuke_script(NUKE_EXECUTABLE,  # nuke_exec_path
                        get_export_pyscript(),  # py_script_path
                        nuke_export_script,  # args: add nuke export-script path
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


def angleMod360(prev_angle, current_angle):
    """
    Adjusts an angle to stay within the range of -180 to 180 degrees relative to a reference angle.

    Args:
        prev_angle (float): The reference angle.
        current_angle (float): The angle to be adjusted.

    Returns:
        float: The adjusted angle within the -180 to 180 degree range.
    """
    delta = current_angle - prev_angle
    if delta > 180.0:
        current_angle -= 360.0
    elif delta < -180.0:
        current_angle += 360.0
    return current_angle


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
