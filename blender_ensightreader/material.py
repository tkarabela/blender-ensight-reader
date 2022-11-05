import bpy


def create_new_material(prefix: str):
    name = prefix
    mat = bpy.data.materials.get(name)
    if mat is not None:
        for i in range(1, 100):
            name = f"{prefix}{i}"
            mat = bpy.data.materials.get(name)
            if mat is None:
                break
        else:
            raise RuntimeError("Giving up on creating new material")

    assert mat is None
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True

    return mat


def setup_ensight_material_node_tree(mat,
                                     default_attribute_name: str = "",
                                     default_attribute_is_vector: bool = False):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    links.clear()
    nodes.clear()

    attr_node = nodes.new("ShaderNodeAttribute")
    attr_node.label = "Variable"
    attr_node.attribute_name = default_attribute_name

    attr_scalar_node = nodes.new("NodeReroute")
    attr_scalar_node.label = "Scalar"
    attr_scalar_node.location = 340, -20
    links.new(attr_node.outputs[2], attr_scalar_node.inputs[0])

    attr_vector_mag_node = nodes.new("ShaderNodeVectorMath")
    attr_vector_mag_node.operation = "LENGTH"
    attr_vector_mag_node.hide = True
    attr_vector_mag_node.label = "Vector mag."
    attr_vector_mag_node.location = 200, -60
    links.new(attr_node.outputs[1], attr_vector_mag_node.inputs[0])

    attr_vector_xyz_node = nodes.new("ShaderNodeSeparateXYZ")
    attr_vector_xyz_node.hide = True
    attr_vector_xyz_node.label = "Vector XYZ"
    attr_vector_xyz_node.location = 200, -110
    links.new(attr_node.outputs[1], attr_vector_xyz_node.inputs[0])

    attr_map_range_node = nodes.new("ShaderNodeMapRange")
    attr_map_range_node.label = "Palette range"
    attr_map_range_node.location = 400, 0
    if default_attribute_name and default_attribute_is_vector:
        links.new(attr_vector_mag_node.outputs[0], attr_map_range_node.inputs[0])
    elif default_attribute_name:
        links.new(attr_scalar_node.outputs[0], attr_map_range_node.inputs[0])

    attr_color_ramp_node = nodes.new("ShaderNodeValToRGB")
    attr_color_ramp_node.label = "Palette"
    attr_color_ramp_node.location = 600, 0
    cr = attr_color_ramp_node.color_ramp  # set "jet" palette
    cr.elements.new(position=0.5)
    cr.elements[0].color = (0, 0, 1, 1)
    cr.elements[1].color = (0, 1, 0, 1)
    cr.elements[2].color = (1, 0, 0, 1)
    links.new(attr_map_range_node.outputs[0], attr_color_ramp_node.inputs[0])

    principled_bsdf_node = nodes.new("ShaderNodeBsdfPrincipled")
    principled_bsdf_node.location = 1000, 0
    if default_attribute_name:
        links.new(attr_color_ramp_node.outputs[0], principled_bsdf_node.inputs[0])

    output_node = nodes.new("ShaderNodeOutputMaterial")
    output_node.location = 1300, 0
    links.new(principled_bsdf_node.outputs[0], output_node.inputs[0])

    # LIC AOV ----------------------------------------------------------------

    lic_frame_node = nodes.new("NodeFrame")
    lic_frame_node.label = "Line integral convolution"
    lic_frame_node.location = -50, -350
    lic_frame_node.width = 630
    lic_frame_node.height = 320

    attr_node = nodes.new("ShaderNodeAttribute")
    attr_node.label = "Variable for LIC"
    attr_node.attribute_name = "U"
    attr_node.location = 0, -400

    point_node = nodes.new("ShaderNodePointInfo")
    point_node.hide = True
    point_node.location = 0, -600

    vector_transform_A_node = nodes.new("ShaderNodeVectorTransform")
    vector_transform_A_node.vector_type = "POINT"
    vector_transform_A_node.convert_from = "WORLD"
    vector_transform_A_node.convert_to = "CAMERA"
    vector_transform_A_node.location = 200, -400
    vector_transform_A_node.hide = True
    links.new(point_node.outputs[0], vector_transform_A_node.inputs[0])

    vector_math_B_node = nodes.new("ShaderNodeVectorMath")
    vector_math_B_node.operation = "ADD"
    vector_math_B_node.location = 200, -450
    vector_math_B_node.hide = True
    links.new(point_node.outputs[0], vector_math_B_node.inputs[0])
    links.new(attr_node.outputs[1], vector_math_B_node.inputs[1])

    vector_transform_B_node = nodes.new("ShaderNodeVectorTransform")
    vector_transform_B_node.vector_type = "POINT"
    vector_transform_B_node.convert_from = "WORLD"
    vector_transform_B_node.convert_to = "CAMERA"
    vector_transform_B_node.location = 200, -500
    vector_transform_B_node.hide = True
    links.new(vector_math_B_node.outputs[0], vector_transform_B_node.inputs[0])

    vector_math_AB_node = nodes.new("ShaderNodeVectorMath")
    vector_math_AB_node.operation = "SUBTRACT"
    vector_math_AB_node.location = 200, -550
    vector_math_AB_node.hide = True
    links.new(vector_transform_A_node.outputs[0], vector_math_AB_node.inputs[0])
    links.new(vector_transform_B_node.outputs[0], vector_math_AB_node.inputs[1])

    separate_AB_node = nodes.new("ShaderNodeSeparateXYZ")
    separate_AB_node.hide = True
    separate_AB_node.location = 200, -600
    separate_AB_node.hide = True
    links.new(vector_math_AB_node.outputs[0], separate_AB_node.inputs[0])

    aov_x_node = nodes.new("ShaderNodeOutputAOV")
    aov_x_node.name = "LIC_x"
    aov_x_node.location = 400, -400
    links.new(separate_AB_node.outputs[0], aov_x_node.inputs[1])

    aov_y_node = nodes.new("ShaderNodeOutputAOV")
    aov_y_node.name = "LIC_y"
    aov_y_node.location = 400, -520
    links.new(separate_AB_node.outputs[1], aov_y_node.inputs[1])

    return mat
