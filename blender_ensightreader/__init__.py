try:
    from .importer import ImportEnsightGold
    import bpy
except ImportError:
    ImportSomeData = None
    bpy = None


bl_info = {
    "name": "Import EnSight Gold format (*.case)",
    "author": "Tomas Karabela",
    "description": "Imports surface geometry from EnSight Gold case.",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "File > Import > EnSight Gold",
    "url": "https://github.com/tkarabela/ensight-reader",
    "wiki_url": "https://github.com/tkarabela/ensight-reader",
    "tracker_url": "https://github.com/tkarabela/ensight-reader/issues",
    "category": "Import-Export"
}

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportEnsightGold.bl_idname, text="EnSight Gold (*.case)")


# Register and add to the "file selector" menu (required to use F3 search "Text Import Operator" for quick access)
def register():
    bpy.utils.register_class(ImportEnsightGold)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportEnsightGold)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_test.some_data('INVOKE_DEFAULT')
