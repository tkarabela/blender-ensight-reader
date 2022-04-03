# EnSight Gold reader for Blender

This add-on lets you import geometry and scalar/vector
variable data from EnSight Gold case into Blender,
for scientific or engineering visualization.

### Features

- It's minimal - works with Blender 2.93+ (no extra dependencies
  or special builds needed)
- It's fast - import only parts/variables you need
- It's native - parts are loaded as objects, variables are loaded
  as float vertex attributes (for use with shaders or geometry nodes)

![EnSight Gold case loaded in Blender 3.1](images/blender-ensight-reader.png)

*Above: example case exported from Paraview 5.10 in EnSight Gold format
and imported into Blender 3.1.*

### Installation

1. Download the plug-in ZIP from [GitHub releases page](https://github.com/tkarabela/blender-ensight-reader/releases/)
2. In Blender, go to menu `Edit > Preferences > Add-ons > Install`
   and point it to the ZIP file you downloaded (eg. `blender-ensight-reader-1.0.0.zip`)
3. Enable the add-on by clicking the checkbox next to it.

### Usage

You can load EnSight Gold case from the menu `File > Import > EnSight Gold (*.case)`.
The dialog has several options to specify the data you want to load:

<dl>
  <dt>Time step [integer]</dt>
  <dd>Index of time step to load (0, 1, 2, ...); for non-transient cases, leave this at 0.
      Note that this is <i>not</i> a time value in seconds.</dd>
  <dt>Variables to load [comma-delimited list of names]</dt>
  <dd>Here you can select which variables should be loaded - separate them
      with commas, without spaces (eg. <code>p,U</code>). To load all variables, use <code>*</code>. If you don't
      want to load any variables, leave the field empty.</dd>
  <dt>Parts to include [regular expression]</dt>
  <dd>Only parts containing given expression will be loaded - you can use Python regular expressions.
      To load all parts, leave the field empty. Note that parts containing only
      3D elements will not be loaded in any case, as the add-on creates regular Blender meshes
      which can only contain surface elements.</dd>
  <dt>Parts to exclude [regular expression]</dt>
  <dd>Parts containing given expression will <i>not</i> be loaded - this option takes precedence
      over "Parts to include". To load all parts, leave the field empty.</dd>
</dl>

### Current limitations

- only "scalar per node" and "vector per node" variables are supported
- only "C Binary" EnSight Gold files with unstructured grids are supported
- only 2D elements are imported (Blender has no concept of unstructured grid
  with 3D elements; points and lines are untested)
- there is no concept of time beyond importing data for a particular time step
  (once the objects are created, you cannot animate the variable data or geometry
  based on other time steps in the original case)
- for more technical details, see [documentation of `ensight-reader`](https://ensight-reader.readthedocs.io/en/latest/api-reference.html#ensightreader.EnsightCaseFile),
  the library used by this add-on
