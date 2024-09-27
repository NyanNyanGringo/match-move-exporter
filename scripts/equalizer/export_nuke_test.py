#
# 3DE4.script.name:	Nuke...
#
# 3DE4.script.version:	v2.0
#
# 3DE4.script.gui:	Main Window::3DE4::Export Project
#
# 3DE4.script.comment:	Creates an NK file that contains all cameras and point groups, which can be imported into Nuke.
#

import sys
from vl_sdv import rot3d, mat3d, VL_APPLY_ZXY
import tde4
import math

# Helper functions
def convert_to_angles(r3d):
    """Converts a rotation matrix to angles in degrees."""
    rot = rot3d(mat3d(r3d)).angles(VL_APPLY_ZXY)
    rx = math.degrees(rot[0])
    ry = math.degrees(rot[1])
    rz = math.degrees(rot[2])
    return (rx, ry, rz)

def convert_z_up(p3d, y_up):
    """Converts coordinate system from Y-up to Z-up or vice versa."""
    if y_up == 1:
        return p3d
    else:
        return [p3d[0], -p3d[2], p3d[1]]

def angle_mod_360(d0, d):
    """Adjusts angle to be within 360 degrees range."""
    dd = d - d0
    if dd > 180.0:
        d = angle_mod_360(d0, d - 360.0)
    elif dd < -180.0:
        d = angle_mod_360(d0, d + 360.0)
    return d

def valid_name(name):
    """Validates a name by replacing invalid characters."""
    return name.replace(" ", "_").replace("#", "_")

def write_root(first_frame, last_frame, frame, width, height, aspect=1, fps=25):
    """Generates the Root node for the Nuke script."""
    return f"""Root {{
 inputs 0
 name MatchMoveExporter
 frame {frame}
 first_frame {first_frame}
 last_frame {last_frame}
 format "{width} {height} 0 0 {width} {height} {aspect} {width}x{height}"
 fps {fps}
}}"""

def write_nuke_script(f, campg, frame0, yup=1):
    """Writes the entire Nuke script to the file."""
    # Get camera and image properties
    cam = tde4.getCurrentCamera()
    no_frames = tde4.getCameraNoFrames(cam)
    width = tde4.getCameraImageWidth(cam)
    height = tde4.getCameraImageHeight(cam)
    last_frame = frame0 + no_frames
    fps = tde4.getCameraFPS(cam)

    # Write Root node
    root_node = write_root(frame0, last_frame, frame0, width, height, aspect=1, fps=fps)
    f.write("#! nuke\n")
    f.write("version 4.8200\n")
    f.write(root_node + "\n")

    # Write locators
    write_locators(f, campg, yup)

    # Write object point groups
    pgl = tde4.getPGroupList()
    write_object_point_groups(f, pgl, cam, frame0, yup)

    # Write scene transforms
    write_scene_transforms(f)

    # Write cameras
    write_cameras(f, campg, frame0, yup)

def write_locators(f, campg, y_up):
    """Writes locator nodes to the Nuke script."""
    # Create Locator Group
    f.write("Group {\n")
    f.write(" inputs 0\n")
    f.write(" name Locators\n")
    f.write(" xpos 0\n")
    f.write(" ypos 0\n")
    f.write("}\n")

    # Write Constant node
    f.write("Constant {\n")
    f.write(" inputs 0\n")
    f.write(" color {1 0 0 1}\n")
    f.write(" name Constant1\n")
    f.write(" xpos 0\n")
    f.write(" ypos -442\n")
    f.write("}\n")

    # Write Sphere node (reference geometry)
    f.write("Sphere {\n")
    f.write(" rows 9\n")
    f.write(" columns 9\n")
    f.write(" radius 2\n")
    f.write(" name Sphere1\n")
    f.write(" xpos 0\n")
    f.write(" ypos -346\n")
    f.write("}\n")
    f.write("set LOCATORREFNODE [stack 0]\n")

    # Write TransformGeo nodes for each point
    point_list = tde4.getPointList(campg)
    pos = 0
    for p in point_list:
        if tde4.isPointCalculated3D(campg, p):
            # TransformGeo Node has 3 inputs
            f.write("push 0\n")
            f.write("push 0\n")
            f.write("push $LOCATORREFNODE\n")
            name = tde4.getPointName(campg, p)
            name = f"p{valid_name(name)}"
            p3d = tde4.getPointCalcPosition3D(campg, p)
            p3d = convert_z_up(p3d, y_up)
            f.write("TransformGeo {\n")
            f.write(" inputs 3\n")
            f.write(" translate {%.15f %.15f %.15f}\n" % (p3d[0], p3d[1], p3d[2]))
            f.write(" name %s\n" % name)
            f.write(" xpos %d\n" % pos)
            pos += 100
            f.write(" ypos -250\n")
            f.write("}\n")
    # Merge all the geometry to one geo node
    num_points = tde4.getNoPoints(campg)
    f.write("MergeGeo {\n")
    f.write(" inputs %d\n" % num_points)
    f.write(" xpos 0\n")
    f.write(" ypos -154\n")
    f.write("}\n")
    f.write("Output {\n")
    f.write(" xpos 0\n")
    f.write(" ypos -60\n")
    f.write("}\n")
    f.write("end_group\n")
    f.write("set LOCATOR [stack 0]\n")

def write_axis_curves(f, pg, cam, frame0, y_up):
    """Writes the translate and rotate curves for an Axis node."""
    no_frames = tde4.getCameraNoFrames(cam)
    x_trans = "{curve i"
    y_trans = "{curve i"
    z_trans = "{curve i"
    x_rot = "{curve i"
    y_rot = "{curve i"
    z_rot = "{curve i"

    rot0 = [0, 0, 0]
    for frame in range(1, no_frames + 1):
        p3d = tde4.getPGroupPosition3D(pg, cam, frame)
        p3d = convert_z_up(p3d, y_up)
        r3d = tde4.getPGroupRotation3D(pg, cam, frame)
        rot = convert_to_angles(r3d)
        if frame > 1:
            rot = [angle_mod_360(rot0[0], rot[0]),
                   angle_mod_360(rot0[1], rot[1]),
                   angle_mod_360(rot0[2], rot[2])]
        rot0 = rot
        frame_idx = frame + frame0
        x_trans += f" x{frame_idx} {p3d[0]}"
        y_trans += f" x{frame_idx} {p3d[1]}"
        z_trans += f" x{frame_idx} {p3d[2]}"
        x_rot += f" x{frame_idx} {rot[0]}"
        y_rot += f" x{frame_idx} {rot[1]}"
        z_rot += f" x{frame_idx} {rot[2]}"

    x_trans += " }"
    y_trans += " }"
    z_trans += " }"
    x_rot += " }"
    y_rot += " }"
    z_rot += " }"

    f.write(f" translate {x_trans} {y_trans} {z_trans}\n")
    f.write(f" rotate {x_rot} {y_rot} {z_rot}\n")

def write_object_point_groups(f, pgl, cam, frame0, y_up):
    """Writes object point groups to the Nuke script."""
    group_xpos = 180
    for pg in pgl:
        pg_name = valid_name(tde4.getPGroupName(pg))
        if tde4.getPGroupType(pg) == "OBJECT" and cam is not None:
            f.write("Group {\n")
            f.write(" inputs 0\n")
            f.write(" name %s\n" % pg_name)
            f.write(" xpos %d\n" % group_xpos)
            group_xpos += 130
            f.write(" ypos -154\n")
            f.write("}\n")

            # Write Constant node
            f.write("Constant {\n")
            f.write(" inputs 0\n")
            f.write(" color {0 1 0 1}\n")
            f.write(" name Constant_%s\n" % pg_name)
            f.write(" xpos 0\n")
            f.write(" ypos -442\n")
            f.write("}\n")

            # Write Sphere node
            f.write("Sphere {\n")
            f.write(" rows 9\n")
            f.write(" columns 9\n")
            f.write(" radius 2\n")
            f.write(" name Sphere_%s\n" % pg_name)
            f.write(" xpos 0\n")
            f.write(" ypos -346\n")
            f.write("}\n")
            f.write("set OBJECTREF_%s [stack 0]\n" % pg_name)

            # Write Axis node
            f.write("push 0\n")
            f.write("push 0\n")
            f.write("Axis {\n")
            f.write(" rot_order ZXY\n")

            # Create curves for translate and rotate
            write_axis_curves(f, pg, cam, frame0, y_up)

            scl = tde4.getPGroupScale3D(pg)
            f.write(" scaling {%.15f %.15f %.15f}\n" % (scl, scl, scl))
            f.write(" name Axis_%s\n" % pg_name)
            f.write(" xpos 110\n")
            f.write(" ypos -366\n")
            f.write("}\n")
            f.write("set Axis_%s [stack 0]\n" % pg_name)

            # Write TransformGeo nodes for points
            xpos = 0
            point_list = tde4.getPointList(pg)
            pc = 0
            for p in point_list:
                if tde4.isPointCalculated3D(pg, p):
                    pname = tde4.getPointName(pg, p)
                    pname = f"p{valid_name(pname)}"
                    p3d = tde4.getPointCalcPosition3D(pg, p)
                    p3d = convert_z_up(p3d, y_up)
                    f.write("push 0\n")
                    f.write("push $Axis_%s\n" % pg_name)
                    f.write("push $OBJECTREF_%s\n" % pg_name)
                    f.write("TransformGeo {\n")
                    f.write(" inputs 3\n")
                    f.write(" translate {%.15f %.15f %.15f}\n" % (p3d[0], p3d[1], p3d[2]))
                    f.write(" name %s\n" % pname)
                    f.write(" xpos %d\n" % xpos)
                    xpos += 100
                    f.write(" ypos -250\n")
                    f.write("}\n")
                    pc += 1
            # Merge geometry
            f.write("MergeGeo {\n")
            f.write(" inputs %d\n" % pc)
            f.write(" xpos 0\n")
            f.write(" ypos -154\n")
            f.write("}\n")
            f.write("Output {\n")
            f.write(" xpos 0\n")
            f.write(" ypos -60\n")
            f.write("}\n")
            f.write("end_group\n")
            f.write("set GROUP_%s [stack 0]\n" % pg_name)

def write_scene_transforms(f):
    """Writes the scene transforms to the Nuke script."""
    # Get scene transforms
    scene_trs = tde4.getScenePosition3D()
    scene_rot_matrix = tde4.getSceneRotation3D()
    scene_rot = convert_to_angles(scene_rot_matrix)
    scl = tde4.getSceneScale3D()

    # Write TransformGeo node
    f.write("TransformGeo {\n")
    f.write(" rot_order ZXY\n")
    f.write(" translate {%.15f %.15f %.15f}\n" % (scene_trs[0], scene_trs[1], scene_trs[2]))
    f.write(" rotate {%.15f %.15f %.15f}\n" % (scene_rot[0], scene_rot[1], scene_rot[2]))
    f.write(" scaling {%.15f %.15f %.15f}\n" % (scl, scl, scl))
    f.write(" name SceneNodeTrans\n")
    f.write(" xpos 0\n")
    f.write(" ypos 250\n")
    f.write("}\n")
    f.write("set SCENE3D [stack 0]\n")

def write_camera_node(f, cam, campg, frame0, posx, y_up):
    """Writes a Camera node to the Nuke script."""
    no_frames = tde4.getCameraNoFrames(cam)
    lens = tde4.getCameraLens(cam)
    img_width = tde4.getCameraImageWidth(cam)
    img_height = tde4.getCameraImageHeight(cam)
    cam_name = tde4.getCameraName(cam)
    fback_w = tde4.getLensFBackWidth(lens)
    fback_h = tde4.getLensFBackHeight(lens)
    lco_x = -tde4.getLensLensCenterX(lens) * 2 / fback_w
    lco_y = -tde4.getLensLensCenterY(lens) * 2 / fback_h

    # Get field of view
    xa, xb, ya, yb = tde4.getCameraFOV(cam)
    width = (xb - xa) * img_width
    height = (yb - ya) * img_height

    # Write Camera node
    f.write("Camera {\n")
    f.write(" rot_order ZXY\n")

    # Write translate curves
    x_trans = "{curve i"
    y_trans = "{curve i"
    z_trans = "{curve i"
    rot0 = [0, 0, 0]
    for frame in range(1, no_frames + 1):
        p3d = tde4.getPGroupPosition3D(campg, cam, frame)
        p3d = convert_z_up(p3d, y_up)
        frame_idx = frame + frame0
        x_trans += f" x{frame_idx} {p3d[0]}"
        y_trans += f" x{frame_idx} {p3d[1]}"
        z_trans += f" x{frame_idx} {p3d[2]}"
    x_trans += " }"
    y_trans += " }"
    z_trans += " }"
    f.write(f" translate {x_trans} {y_trans} {z_trans}\n")

    # Write rotate curves
    x_rot = "{curve i"
    y_rot = "{curve i"
    z_rot = "{curve i"
    for frame in range(1, no_frames + 1):
        r3d = tde4.getPGroupRotation3D(campg, cam, frame)
        rot = convert_to_angles(r3d)
        if frame > 1:
            rot = [angle_mod_360(rot0[0], rot[0]),
                   angle_mod_360(rot0[1], rot[1]),
                   angle_mod_360(rot0[2], rot[2])]
        rot0 = rot
        frame_idx = frame + frame0
        x_rot += f" x{frame_idx} {rot[0]}"
        y_rot += f" x{frame_idx} {rot[1]}"
        z_rot += f" x{frame_idx} {rot[2]}"
    x_rot += " }"
    y_rot += " }"
    z_rot += " }"
    f.write(f" rotate {x_rot} {y_rot} {z_rot}\n")

    # Write focal length
    focal_str = "{ i"
    for frame in range(1, no_frames + 1):
        focal = tde4.getCameraFocalLength(cam, frame) * 10
        frame_idx = frame + frame0
        focal_str += f" x{frame_idx} {focal}"
    focal_str += "}"
    f.write(f" focal {focal_str}\n")

    f.write(f" haperture {fback_w * 10}\n")
    f.write(f" vaperture {fback_h * 10}\n")
    f.write(f" win_translate {{{lco_x} {lco_y}}}\n")
    f.write(" win_scale {1 1}\n")
    f.write(f" name {cam_name}\n")
    f.write(f" xpos {posx}\n")
    f.write(" ypos 200\n")
    f.write("}\n")

    # Write ScanlineRender node
    f.write("push $SCENE3D\n")
    f.write("push 0\n")  # Handle Crop node if necessary
    f.write("ScanlineRender {\n")
    f.write(" inputs 3\n")
    f.write(f" name render3DE({cam_name})\n")
    f.write(f" xpos {posx}\n")
    f.write(" ypos 300\n")
    f.write("}\n")

def write_cameras(f, campg, frame0, y_up):
    """Writes the cameras to the Nuke script."""
    cl = tde4.getCameraList()
    posx = 200
    for cam in cl:
        # Push void onto the stack
        f.write("push 0\n")

        # Write Axis node for scene transforms
        scene_trs = tde4.getScenePosition3D()
        scene_rot_matrix = tde4.getSceneRotation3D()
        scene_rot = convert_to_angles(scene_rot_matrix)
        scl = tde4.getSceneScale3D()
        f.write("Axis {\n")
        f.write(" inputs 0\n")
        f.write(" rot_order ZXY\n")
        f.write(" translate {%.15f %.15f %.15f}\n" % (scene_trs[0], scene_trs[1], scene_trs[2]))
        f.write(" rotate {%.15f %.15f %.15f}\n" % (scene_rot[0], scene_rot[1], scene_rot[2]))
        f.write(" scaling {%.15f %.15f %.15f}\n" % (scl, scl, scl))
        f.write(" name Axis_Scene\n")
        f.write(" xpos %i\n" % posx)
        f.write(" ypos 100\n")
        f.write("}\n")

        # Write Camera node
        write_camera_node(f, cam, campg, frame0, posx, y_up)
        posx += 175

def main():
    # Search for camera point group
    campg = None
    pgl = tde4.getPGroupList()
    for pg in pgl:
        if tde4.getPGroupType(pg) == "CAMERA":
            campg = pg
            break
    if campg is None:
        tde4.postQuestionRequester("Export Nuke...", "Error, there is no camera point group.", "Ok")
        return

    # Open requester
    req = tde4.createCustomRequester()
    tde4.addFileWidget(req, "file_browser", "Export file...", "*.nk")
    tde4.addTextFieldWidget(req, "startframe_field", "Start frame", "1")

    cam = tde4.getCurrentCamera()
    offset = tde4.getCameraFrameOffset(cam)
    tde4.setWidgetValue(req, "startframe_field", str(offset))

    ret = tde4.postCustomRequester(req, "Export Nuke (NK File)...", 540, 0, "Ok", "Cancel")

    if ret != 1:
        tde4.deleteCustomRequester(req)
        return

    path = tde4.getWidgetValue(req, "file_browser")
    frame0 = int(tde4.getWidgetValue(req, "startframe_field")) - 1

    if not path:
        tde4.postQuestionRequester("Export Nuke...", "Error, no file path specified.", "Ok")
        tde4.deleteCustomRequester(req)
        return

    # Open output file
    try:
        with open(path, "w") as f:
            write_nuke_script(f, campg, frame0)
        tde4.postQuestionRequester("Export Nuke...", "Project successfully exported.", "Ok")
    except IOError:
        tde4.postQuestionRequester("Export Nuke...", "Error, couldn't open file.", "Ok")

    tde4.deleteCustomRequester(req)

# Run the script
if __name__ == "__main__":
    main()
