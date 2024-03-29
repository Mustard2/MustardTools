# Mustard Tools

This is an addon with some tools for riggers and animators. It's still in early developement, so expect more features in the future.

![](https://ams0.files.sfmlab.com/content/content/image/script5_EgfcjNX.png)

## Features of the addon

- IK constraint generator for bone chains (with possible automatic creation of controller and pole bones)
- IK Spline rig generator for bone chains
- Mouth controller (for quicker mouth poses) generator
- Tool to merge 3 images into a single RGB image (to decrease memory allocation by a factor of 3)

## Instructions

- This is an early version! Be sure to make a backup of your work before using this model on it!
- Install the addon as any other Blender addon (if you don't know how to do it, google it!)
- Press N in Viewport, and find the "Mustard Tools" tab
- **IK and IK Spline generators**: Tutorial available at https://streamable.com/10u6sd
- **Merge Images To Grayscale**: Select 3 images on the shader editor, and press the Merge button in the Mustard Tools tab

## Troubleshooting

- When I use the IK Spline, the controllers are generated far from the actual curve.
When this happens, also a warning message should appear, remembering you to Apply the location to your armature. To do so, go in Object moe, select the Armature and press Ctrl+A. Then choose Location (even if, in general, applying the full LocRotSca is a good practice).

