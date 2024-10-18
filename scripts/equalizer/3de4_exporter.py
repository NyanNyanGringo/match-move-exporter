#
# 3DE4.script.name:	MatchMove Exporter
#
# 3DE4.script.version:	v1.0
#
# 3DE4.script.gui:	Main Window::MMExporter
#
# 3DE4.script.comment:	Easy and Fast Export for work.
#
import json
import os
import re
import shutil
import tempfile

import tde4
from vl_sdv import rot3d, mat3d, VL_APPLY_ZXY, vec3d

from lib.utilities.os_utilities import get_root_path, open_in_explorer
from lib.utilities.nuke_utilities import get_export_pyscript, execute_nuke_script, get_nuke_script_path
from lib.utilities.log_utilities import setup_or_get_logger
from lib.utilities.export_nuke_LD_3DE4_Lens_Distortion_Node import exportNukeDewarpNode


LOGGER = setup_or_get_logger(force_setup=True, use_console_handler=False)
NUKE_EXECUTABLE = os.getenv("NUKE_EXECUTABLE_PATH")


# CHECK FUNCTIONS


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

def check_camera_point_group() -> bool:
    for point_group in tde4.getPGroupList():
        if tde4.getPGroupType(point_group) == "CAMERA":
            return True

    message = "Error, there is no camera point group."
    tde4.postQuestionRequester("Message", message, "Ok")
    return False

def check_nuke_script_name() -> bool:
    nuke_script_name: str = tde4.getWidgetValue(requester, "textfield_name")

    if nuke_script_name.strip():
        return True

    message = "Parameter name can't be empty."
    tde4.postQuestionRequester("Message", message, "OK")

    return False

def check_project_exists() -> bool:
    if tde4.getProjectPath():
        return True

    message = "Project doesn't exists."
    tde4.postQuestionRequester("Message", message, "OK")

    return False

def check_and_remove_files_in_existed_path(path) -> bool:
    folder_path = os.path.dirname(path)
    if os.path.exists(folder_path):
        request = tde4.postQuestionRequester("Question", f"Path already exists: {folder_path}\n\n"
                                                  f"Important: all the files inside this folder will be deleted.\n\n"
                                                  f"Continue?", "Yes", "No")
        if request == 1:  # 1 is True, 2 is False
            shutil.rmtree(folder_path)
            os.mkdir(folder_path)
            return True
        else:
            return False

    return True


# CALLBACKS


def button_clicked_callback(requester, widget, action) -> None:
    LOGGER.info(f"New callback from widget {widget} received, action: {action}")

    if not check_project_exists():
        return

    if not check_nuke_executable_path():
        return

    if not check_nuke_script_name():
        return

    if not check_camera_point_group():
        return

    # TODO: проверять, что во всех камерах source существует

    nuke_pyscript = get_export_pyscript()
    LOGGER.info(f"nuke_pyscript: {nuke_pyscript}")

    nuke_script_path = get_nuke_script_path(folder_path=os.path.dirname(tde4.getProjectPath()),
                                            script_name=tde4.getWidgetValue(requester, "textfield_name"),
                                            dir_folder_is_version=True)
    LOGGER.info(f"nuke_script_path: {nuke_script_path}")

    if not check_and_remove_files_in_existed_path(nuke_script_path):
        return

    json_for_nuke_path = JsonForNuke().get_json_path()
    LOGGER.info(f"json_for_nuke_path: {json_for_nuke_path}")

    execute_nuke_script(NUKE_EXECUTABLE,  # nuke_exec_path
                        nuke_pyscript,  # py_script_path
                        nuke_script_path,  # args: add nuke script path
                        json_for_nuke_path,  # args: add json data path
                        PATHS_TO_ADD_TO_PYTHONPATH=[get_root_path()]  # kwargs: add access to lib folder for nuke
                        )

def label_changed_callback(requester, widget, action) -> None:
    LOGGER.info(f"New callback from widget {widget} received, action: {action}")
    pass

def _MatchMoveExporterUpdate(requester) -> None:
    LOGGER.info("New update callback received, put your code here...")
    pass


# 3DE4 FUNCTIONS


def get_obj_filepath(pg, model):
    """
    Generates an `.obj` file for a 3D model and returns its file path.

    If the model already has an associated `.obj` file, the function returns that path.
    Otherwise, it creates a new `.obj` file in the system's temporary directory, writes
    the model's vertices, faces, and UV coordinates (if available), and returns the path to the new file.

    Args:
        pg (int): The point group ID that contains the model.
        model (int): The ID of the 3D model in 3DEqualizer.

    Returns:
        str: The path to the `.obj` file.

    Raises:
        Exception: If no current camera is found.
    """
    # Check if the model already has a filepath
    filepath = tde4.get3DModelFilepath(pg, model)
    if filepath:
        return filepath

    # Get the model name
    model_name = validName(tde4.get3DModelName(pg, model))

    # Create the path in the temporary directory
    obj_path = os.path.join(tempfile.gettempdir(), f"{model_name}.obj")

    # Get the current camera and frame
    camera = tde4.getCurrentCamera()
    if camera is None:
        raise Exception("No current camera.")
    frame = tde4.getCurrentFrame(camera)

    # Get model position and rotation
    p3d = vec3d(tde4.get3DModelPosition3D(pg, model, camera, frame))
    r3d = mat3d(tde4.get3DModelRotationScale3D(pg, model))

    # Check if the point group is not the camera group
    if tde4.getPGroupType(pg) != "CAMERA":
        p3do = vec3d(tde4.getPGroupPosition3D(pg, camera, frame))
        r3do = mat3d(tde4.getPGroupRotation3D(pg, camera, frame))

    # Open the .obj file for writing
    with open(obj_path, "w") as f:
        # Write vertices
        n_vertices = tde4.get3DModelNoVertices(pg, model)
        for i in range(n_vertices):
            v = vec3d(tde4.get3DModelVertex(pg, model, i, camera, frame))
            v = (r3d * v) + p3d
            if tde4.getPGroupType(pg) != "CAMERA":
                v = (r3do * v) + p3do
            f.write("v %f %f %f\n" % (v[0], v[1], v[2]))

        # Write UV coordinates if they exist
        uv_coords_exist = False
        n_faces = tde4.get3DModelNoFaces(pg, model)
        # uv_coords = []
        for i in range(n_faces):
            fl = tde4.get3DModelFaceVertexIndices(pg, model, i)
            for j in range(len(fl)):
                u, v = tde4.get3DModelFaceUVCoord(pg, model, i, j)
                uv_coords_exist = True
                f.write("vt %f %f\n" % (u, v))

        # Write faces
        uv_index = 1
        for i in range(n_faces):
            fl = tde4.get3DModelFaceVertexIndices(pg, model, i)
            f.write("f ")
            for pi in fl:
                if uv_coords_exist:
                    f.write("%d/%d " % (pi + 1, uv_index))
                    uv_index += 1
                else:
                    f.write("%d " % (pi + 1))
            f.write("\n")

    # Return the path to the .obj file
    return obj_path

class JsonForNuke:
    def __init__(self):
        self.camera_point_group = [pg for pg in tde4.getPGroupList() if tde4.getPGroupType(pg) == "CAMERA"][0]
        self.scene_translate = tde4.getScenePosition3D()
        self.scene_rotation = convertToAngles(tde4.getSceneRotation3D())
        self.scene_scale = tde4.getSceneScale3D()

    def get_json_path(self):

        json_path = os.path.join(tempfile.gettempdir(), "json_for_nuke.json")

        with open(json_path, "w") as json_file:
            json.dump(self.get_json(), json_file, indent=4)

        return json_path

    def get_json(self) -> dict:
        """
        {
        "program": "3DE4" or "SynthEyes"
        "first_frame": 0,
        "fps": 0,
        "width": 0),
        "height": 0,
        "range": [0, 0],
        "cameras": [
            {
                "first_frame": 0,
                "axis": {
                    "translate": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "rotation": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": 0.0
                    },
                    "scale": 0.0
                },
                "translate": {
                    "xs": [0.0, ...],
                    "ys": [0.0, ...],
                    "zs": [0.0, ...]
                },
                "rotate": {
                    "xs": [0.0, ...],
                    "ys": [0.0, ...],
                    "zs": [0.0, ...]
                },
                "focal": [0.0, ...],
                "haperture": 0.0,
                "vaperture": 0.0,
                "    if intermediate_name:
        filepath += f"undistort_{intermediate_name}/"
    else:
        filepath += "undistort/"": "",
                "undistort_script_path": ".../Temp/undistort_for_CameraName.nk",
                "source": {
                    "path": ".../source/source.####.exr"
                    "black_point": 0.0,
                    "white_point": 0.0,
                    "gamma": 0.0,
                    "softclip": 0.0
                }
            },
        ],
        "point_groups": [
            {
                "type": "CAMERA" or "OBJECT",
                "name": "pgroup_0",
                "axis": {
                    "translate": {
                        "xs": [0.0, ...], "ys": [0.0, ...], "zs": [0.0, ...],
                    },
                    "rotate": {
                        "xs": [0.0, ...], "ys": [0.0, ...], "zs": [0.0, ...],
                    }
                },
                "points": [
                    {
                        "name": "00",
                        "x_pos": 0.0,
                        "y_pos": 0.0,
                        "z_pos": 0.0
                    },
                "geo": [".../Temp/SomeGeo.obj", ...]
                ],
        "3de4_project_path": ".../path/to/equalizer_project.3de"
    }
        """
        first_camera = tde4.getFirstCamera()
        JSON = {
            "program": "3DE4",

            "first_frame": tde4.getCameraFrameOffset(first_camera),
            "fps": tde4.getCameraFPS(first_camera),
            "width": tde4.getCameraImageWidth(first_camera),
            "height": tde4.getCameraImageHeight(first_camera),
            "range": tde4.getCameraCalculationRange(first_camera),

            "cameras": self.get_cameras_list(),
            "point_groups": self.get_point_group_list(),
            "3de4_project_path": tde4.getProjectPath()
        }

        return JSON

    def get_camera_dict(self, camera) -> dict:
        offset = tde4.getCameraFrameOffset(camera)
        camera_name = validName(tde4.getCameraName(camera))

        nk_undistort_path = os.path.join(  # STOP THERE: TEST CODE!
            tempfile.gettempdir(),
            f"undistort_for_{camera_name}.nk"
        )
        os.makedirs(os.path.dirname(nk_undistort_path), exist_ok=True)
        exportNukeDewarpNode(camera, offset, nk_undistort_path)

        camera_translate_x, camera_translate_y, camera_translate_z = [], [], []
        camera_rotate_x, camera_rotate_y, camera_rotate_z = [], [], []
        focal = []
        previous_rotation = None
        for frame in range(1, tde4.getCameraNoFrames(camera) + 1):
            x_pos, y_pos, z_pos = tde4.getPGroupPosition3D(self.camera_point_group, camera, frame)
            camera_translate_x.append(x_pos), camera_translate_y.append(y_pos), camera_translate_z.append(z_pos)

            current_rotation = convertToAngles(tde4.getPGroupRotation3D(self.camera_point_group, camera, frame))
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
            "axis": {
                "translate": {
                    "x": self.scene_translate[0],
                    "y": self.scene_translate[1],
                    "z": self.scene_translate[2],
                },
                "rotation": {
                    "x": self.scene_rotation[0],
                    "y": self.scene_rotation[1],
                    "z": self.scene_rotation[2]
                },
                "scale": self.scene_scale
            },
            "translate": {
                "xs": camera_translate_x,
                "ys": camera_translate_y,
                "zs": camera_translate_z
            },
            "rotate": {
                "xs": camera_rotate_x,
                "ys": camera_rotate_y,
                "zs": camera_rotate_z
            },
            "focal": focal,
            "haperture": tde4.getLensFBackWidth(tde4.getCameraLens(camera)) * 10,
            "vaperture": tde4.getLensFBackHeight(tde4.getCameraLens(camera)) * 10,
            "name": camera_name,
            "undistort_script_path": nk_undistort_path,
            "source": {
                "path": tde4.getCameraPath(camera),
                "black_white": tde4.getCamera8BitColorBlackWhite(camera),
                "gamma": tde4.getCamera8BitColorGamma(camera),
                "softclip": tde4.getCamera8BitColorSoftclip(camera)
            }
        }

        return camera_dict

    def get_cameras_list(self) -> list:
        cameras = []
        for camera in tde4.getCameraList():
            if tde4.getCameraType(camera) == "SEQUENCE":
                cameras.append(self.get_camera_dict(camera))
                # cameras.append(self.get_camera_dict(camera))  # for test
        return cameras

    def get_point_group_dict(self, pg, camera) -> dict:
        # collect translate and rotate of point group for Axis
        axis_translate_x, axis_translate_y, axis_translate_z = [], [], []
        axis_rotate_x, axis_rotate_y, axis_rotate_z = [], [], []
        previous_rotation = None
        for frame in range(1, tde4.getCameraNoFrames(camera) + 1):
            x_pos, y_pos, z_pos = tde4.getPGroupPosition3D(pg, camera, frame)
            axis_translate_x.append(x_pos), axis_translate_y.append(y_pos), axis_translate_z.append(z_pos)

            current_rotation = convertToAngles(tde4.getPGroupRotation3D(pg, camera, frame))
            if previous_rotation:
                current_rotation = [
                    angleMod360(previous_rotation[0], current_rotation[0]),
                    angleMod360(previous_rotation[1], current_rotation[1]),
                    angleMod360(previous_rotation[2], current_rotation[2])
                ]
            previous_rotation = current_rotation
            x_rot, y_rot, z_rot = current_rotation
            axis_rotate_x.append(x_rot), axis_rotate_y.append(y_rot), axis_rotate_z.append(z_rot)

        # collect points of point group
        points = []
        for point in [p for p in tde4.getPointList(pg) if tde4.isPointCalculated3D(pg, p)]:
            point_3d_pos = tde4.getPointCalcPosition3D(pg, point)
            point_dict = {
                "name": validName(tde4.getPointName(pg, point)),
                "x_pos": point_3d_pos[0],
                "y_pos": point_3d_pos[1],
                "z_pos": point_3d_pos[2]
            }
            points.append(point_dict)

        # collect geo of point group
        geo = []
        for model in tde4.get3DModelList(pg, 0):  # 0 means selected only False

            if not tde4.get3DModelVisibleFlag(pg, model):
                continue

            filepath = get_obj_filepath(pg, model)
            geo.append(filepath)

        point_group_dict = {
            "type": tde4.getPGroupType(pg),
            "name": validName(tde4.getPGroupName(pg)),
            "axis": {
                "translate": {
                    "xs": axis_translate_x,
                    "ys": axis_translate_y,
                    "zs": axis_translate_z
                },
                "rotate": {
                    "xs": axis_rotate_x,
                    "ys": axis_rotate_y,
                    "zs": axis_rotate_z
                }
            },
            "points": points,
            "geo": geo
        }
        return point_group_dict

    def get_point_group_list(self) -> list:
        point_groups = []

        camera = tde4.getCurrentCamera()  # get any camera
        for point_group in tde4.getPGroupList():
            if camera is not None:
                point_groups.append(self.get_point_group_dict(point_group, camera))

        return point_groups

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
    for bad_symbol in [" ", "-", "#"]:
        name = name.replace(bad_symbol, "_")
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
