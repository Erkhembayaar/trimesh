import os
import platform

from .. import resources, util
from ..constants import log
from .generic import MeshScript

_search_path = os.environ.get("PATH", "")
if platform.system() == "Windows":
    # try to find Blender install on Windows
    # split existing path by delimiter
    _search_path = [i for i in _search_path.split(";") if len(i) > 0]
    for pf in [r"C:\Program Files", r"C:\Program Files (x86)"]:
        pf = os.path.join(pf, "Blender Foundation")
        if os.path.exists(pf):
            for p in os.listdir(pf):
                if "Blender" in p:
                    _search_path.append(os.path.join(pf, p))
    _search_path = ";".join(_search_path)
    log.debug("searching for blender in: %s", _search_path)

if platform.system() == "Darwin":
    # try to find Blender on Mac OSX
    _search_path = [i for i in _search_path.split(":") if len(i) > 0]
    _search_path.append("/Applications/blender.app/Contents/MacOS")
    _search_path.append("/Applications/Blender.app/Contents/MacOS")
    _search_path.append("/Applications/Blender/blender.app/Contents/MacOS")
    _search_path = ":".join(_search_path)
    log.debug("searching for blender in: %s", _search_path)

_blender_executable = util.which("blender", path=_search_path)
exists = _blender_executable is not None


def boolean(meshes, operation="difference", solver_options=False, use_self=False, debug=False):
    """
    Run a boolean operation with multiple meshes using Blenderoy.
    Parameters:
    - meshes: List of mesh file paths to be processed.
    - operation: Type of boolean operation ("difference", "union", "intersect").
    - solver_options: Solver option for the boolean operation, True == 'Exact'
    - use_self: Boolean indicating whether to consider self-intersections.
    - debug: If True, run in debug mode to provide additional output for troubleshooting.
    Returns:
    - The result of the boolean operation on the provided meshes.
    """
    if not exists:
        raise ValueError("No blender available!")
    operation = str.upper(operation)
    if operation == "INTERSECTION":
        operation = "INTERSECT"

    if solver_options is True:
        solver_options = 'EXACT'
    else:
        solver_options = 'FAST'
    # get the template from our resources folder
    template = resources.get("templates/blender_boolean.py.tmpl")
    script = template.replace("$OPERATION", operation)
    script = script.replace("$SOLVER_OPTIONS", solver_options)
    script = script.replace("$USE_SELF", f'{use_self}')

    with MeshScript(meshes=meshes, script=script, debug=debug) as blend:
        result = blend.run(_blender_executable + " --background --python $SCRIPT")

    for m in util.make_sequence(result):
        # blender returns actively incorrect face normals
        m.face_normals = None

    return result


def unwrap(mesh, angle_limit=66, island_margin=0.0, debug=False):
    """
    Run an unwrap operation using blender.
    """
    if not exists:
        raise ValueError("No blender available!")

    # get the template from our resources folder
    template = resources.get("templates/blender_unwrap.py")
    script = template.replace("$ANGLE_LIMIT", "%.6f" % angle_limit).replace(
        "$ISLAND_MARGIN", "%.6f" % island_margin
    )

    with MeshScript(meshes=[mesh], script=script, exchange="obj", debug=debug) as blend:
        result = blend.run(_blender_executable + " --background --python $SCRIPT")

    for m in util.make_sequence(result):
        # blender returns actively incorrect face normals
        m.face_normals = None

    return result
