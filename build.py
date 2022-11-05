#!/usr/bin/env python

import blender_ensightreader
import os
import os.path as op
import zipfile
import shutil
import glob

version_str = ".".join(map(str, blender_ensightreader.bl_info["version"]))
release_name = f"blender-ensight-reader-{version_str}"

build_dir = "./build"
release_dir = op.join(build_dir, release_name)
release_module_dir = op.join(release_dir, "blender_ensightreader")
zip_path = op.join(build_dir, release_name + ".zip")

print("building into", release_dir)

if op.exists(release_dir):
    print("removing old release dir")
    shutil.rmtree(release_dir)
os.makedirs(release_dir)

shutil.copytree("./blender_ensightreader", release_module_dir)

# replace the dummy ensightreader module with actual code
shutil.copy("./ensight-reader/ensightreader.py", release_module_dir)

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as fp_zip:
    for path in glob.glob(op.join(release_module_dir, "*")):
        fp_zip.write(path, arcname=op.relpath(path, release_dir))

print("wrote", zip_path)
