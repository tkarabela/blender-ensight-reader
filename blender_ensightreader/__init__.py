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
    "blender": (2, 93, 0),
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
    bpy.ops.blender_ensightreader.import_ensight_gold('INVOKE_DEFAULT')
