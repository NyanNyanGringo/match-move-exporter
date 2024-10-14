import tde4
from vl_sdv import rot3d, mat3d, VL_APPLY_ZXY


class JsonForNuke:
    def __init__(self):
        self.camera_point_group = [pg for pg in tde4.getPGroupList() if tde4.getPGroupType(pg) == "CAMERA"][0]
        self.scene_translate = tde4.getScenePosition3D()
        self.scene_rotation = convertToAngles(tde4.getSceneRotation3D())
        self.scene_scale = tde4.getSceneScale3D()

    def get_json(self):
        JSON = {
            "cameras": self.get_cameras_list()
        }
        return JSON

    def get_camera_dict(self, camera):
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
            "first_frame": tde4.getCameraFrameOffset(camera),
            "axis": {
                "translate": {
                    "x": self.scene_translate[0],
                    "y": self.scene_translate[1],
                    "z": self.scene_translate[2]
                },
                "rotate": {
                    "x": self.scene_rotation[0],
                    "y": self.scene_rotation[1],
                    "z": self.scene_rotation[2]
                },
                "scale": self.scene_scale
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

        return camera_dict

    def get_cameras_list(self):
        cameras = []
        for camera in tde4.getCameraList():
            cameras.append(self.get_camera_dict(camera))
        return cameras


def write_json_for_nuke_data(json_data: JsonForNuke) -> str:
    return str()


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
