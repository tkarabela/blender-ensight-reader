# Copyright (c) 2022 Tomas Karabela
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import mmap
import re
from typing import List, Set, Dict
import numpy as np
from .ensightreader import read_case, GeometryPart, EnsightVariableFile, VariableLocation, VariableType

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, IntProperty
from bpy.types import Operator, Object
import bpy


class ImportEnsightGold(Operator, ImportHelper):
    """Import surface geometry from EnSight Gold file"""
    bl_idname = "blender_ensightreader.import_ensight_gold"
    bl_label = "Import EnSight Gold file"

    # ImportHelper mixin class uses this
    filename_ext = ".case"

    filter_glob: StringProperty(
        default="*.case",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    timestep: IntProperty(
        name="Time step",
        description="Index of time step to load (for non-transient case, use 0)",
        default=0,
        min=0)

    variables: StringProperty(
        name="Variables to load",
        description="Comma-separated list of per-node variables to load (eg. 'pMean,UMean');"
                    " use '*' to load all and '' to load none",
        default="*")

    parts_include_regex: StringProperty(
        name="Parts to include",
        description="Regular expression for part names that should be loaded; use '.*' to load all",
        default=".*")

    parts_exclude_regex: StringProperty(
        name="Parts to exclude",
        description="Regular expression for part names that should *not* be loaded;"
                    " takes priority over parts_include_regex; use '' to not exclude any",
        default="internalMesh")

    def execute(self, context) -> Set[str]:
        timestep = self.timestep
        path_to_case = self.filepath
        parts_include_regex = re.compile(self.parts_include_regex or ".*")
        parts_exclude_regex = re.compile(self.parts_exclude_regex or "$^")
        requested_variables = self.variables.split(",")

        # ---------------------------------------------------------------------------------

        self.report({"INFO"}, f"Reading case {path_to_case}")
        case = read_case(path_to_case)
        geofile = case.get_geometry_model(timestep)

        parts_to_read: List[GeometryPart] = []
        for part_id, part in geofile.parts.items():
            part_name = part.part_name
            if parts_exclude_regex.search(part_name):
                self.report({"INFO"}, f"Not reading part {part_name} (parts_exclude_regex matches)")
            elif not parts_include_regex.search(part_name):
                self.report({"INFO"}, f"Not reading part {part_name} (parts_include_regex does not match)")
            else:
                if not part.is_surface():
                    self.report({"WARNING"}, f"Not reading part {part_name} (no surface elements)")
                else:
                    self.report({"INFO"}, f"Reading part {part_name}")
                    parts_to_read.append(part)

        variables_to_read: List[EnsightVariableFile] = []
        for variable_name in case.get_variables():
            variable = case.get_variable(variable_name, timestep)
            if variable.variable_location != VariableLocation.PER_NODE:
                self.report({"WARNING"}, f"Not reading variable {variable_name} (per-element variables are not supported)")
            elif not (variable_name in requested_variables or "*" in requested_variables):
                self.report({"INFO"}, f"Not reading variable {variable_name} (not in requested variables)")
            else:
                variables_to_read.append(variable)

        variables_file_dict = {}
        variables_mmap_dict = {}
        created_objects: List[Object] = []

        with open(geofile.file_path, "rb") as fp_geo, mmap.mmap(fp_geo.fileno(), 0, access=mmap.ACCESS_READ) as mm_geo:
            try:
                for variable in variables_to_read:
                    variables_file_dict[variable.variable_name] = fp = open(variable.file_path, "rb")
                    variables_mmap_dict[variable.variable_name] = mmap.mmap(fp.fileno(), 0, access=mmap.ACCESS_READ)

                for part in parts_to_read:
                    self.report({"INFO"}, f"Reading data for part {part.part_name}")

                    obj = self.convert_ensight_part_to_blender_object(part, variables_to_read, mm_geo,
                                                                      variables_mmap_dict)
                    created_objects.append(obj)
            finally:
                for mm in variables_mmap_dict.values():
                    mm.close()
                for fp in variables_file_dict.values():
                    fp.close()

        # ---------------------------------------------------------------------------------

        self.report({"INFO"}, f"Adding {len(created_objects)} objects to scene")
        scene = context.scene

        bpy.ops.object.select_all(action='DESELECT')
        for obj in created_objects:
            self.report({"DEBUG"}, f"linking object {obj}")
            scene.collection.objects.link(obj)
            obj.select_set(True)
        context.view_layer.objects.active = created_objects[0]

        self.report({"INFO"}, f"Finished importing EnSight Gold case")

        return {'FINISHED'}

    def convert_ensight_part_to_blender_object(self, part: GeometryPart, variables_to_read: List[EnsightVariableFile],
                                               mm_geo: mmap.mmap, variables_mmap_dict: Dict[str, mmap.mmap]) -> Object:
        # -------------------------------------------------------------------------
        # Read geometry
        # - create Blender mesh object and import geometry data using NumPy arrays
        # - adapted from code example by Paul Melis on devtalk.blender.org:
        #   https://devtalk.blender.org/t/alternative-in-2-80-to-create-meshes-from-python-using-the-tessfaces-api/7445
        # -------------------------------------------------------------------------

        vertices = part.read_nodes(mm_geo).flatten()

        vertex_index_ = []
        loop_start_ = []
        loop_total_ = []

        block_loop_start = 0

        for block in part.element_blocks:
            self.report({"DEBUG"}, f"Element block with {block.number_of_elements} {block.element_type} elements")
            if block.element_type.dimension != 2:
                self.report({"DEBUG"}, f"Skipping non-surface element block")
                continue

            if block.element_type == block.element_type.NSIDED:
                polygon_node_counts, polygon_connectivity = block.read_connectivity_nsided(mm_geo)
            else:
                connectivity = block.read_connectivity(mm_geo)
                polygon_node_counts = np.full((connectivity.shape[0],), connectivity.shape[1])
                polygon_connectivity = connectivity.flatten()

            vertex_index_.append(polygon_connectivity)
            tmp = np.cumsum(polygon_node_counts, dtype=np.int32)
            tmp -= polygon_node_counts
            tmp += block_loop_start
            loop_start_.append(tmp)
            loop_total_.append(polygon_node_counts)
            block_loop_start += len(polygon_connectivity)

        vertex_index = np.concatenate(vertex_index_).astype(np.int32)
        vertex_index -= 1  # Blender numbers vertices from 0
        loop_start = np.concatenate(loop_start_).astype(np.int32)
        loop_total = np.concatenate(loop_total_).astype(np.int32)
        num_vertices = vertices.shape[0] // 3
        num_vertex_indices = vertex_index.shape[0]
        num_loops = loop_start.shape[0]

        mesh = bpy.data.meshes.new(name=part.part_name)

        mesh.vertices.add(num_vertices)
        mesh.vertices.foreach_set("co", vertices)

        mesh.loops.add(num_vertex_indices)
        mesh.loops.foreach_set("vertex_index", vertex_index)

        mesh.polygons.add(num_loops)
        mesh.polygons.foreach_set("loop_start", loop_start)
        mesh.polygons.foreach_set("loop_total", loop_total)

        mesh.update()
        mesh.validate()

        obj = bpy.data.objects.new(part.part_name, mesh)

        # -------------------------------------------------------------------------
        # Read variable data
        # - attach per-node variables from EnSight case as scalar/vector attributes
        # -------------------------------------------------------------------------

        for variable in variables_to_read:
            variable_name = variable.variable_name
            if not variable.is_defined_for_part_id(part.part_id):
                self.report({"INFO"}, f"Skipping variable {variable_name} (not defined for this part)")
                continue

            if variable.variable_type == VariableType.SCALAR:
                blender_type = "FLOAT"
                blender_attribute_set = "value"
            elif variable.variable_type == VariableType.VECTOR:
                blender_type = "FLOAT_VECTOR"
                blender_attribute_set = "vector"
            else:
                # TODO We could support tensor or complex variables, perhaps by creating multiple scalar
                #      attributes from them?
                self.report({"WARNING"}, f"Skipping variable {variable_name} (unsupported variable type)")
                continue

            if variable.variable_location != VariableLocation.PER_NODE:
                # TODO It would be nice to support per-element variables as well, but I've encountered problems
                #      when implementing this - Blender seems to do some processing of faces when calling
                #      mesh.update() and mesh.validate(), such that number of faces does not match input.
                self.report({"WARNING"}, f"Skipping variable {variable_name} (per-element variables are not supported)")
                continue

            self.report({"DEBUG"}, f"Reading variable {variable_name}")
            mm = variables_mmap_dict[variable_name]
            variable_data = variable.read_node_data(mm, part.part_id).flatten()
            blender_domain = "POINT"

            attr = obj.data.attributes.new(variable_name, blender_type, blender_domain)
            attr.data.foreach_set(blender_attribute_set, variable_data)

        obj.data.update()  # finishes reading attribute data

        return obj
