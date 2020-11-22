# Mustard Tools

This is an addon with some tools for riggers and animators. It's still in early developement, so expect more features in the future.

![](https://ams0.files.sfmlab.com/content/content/image/script5_EgfcjNX.png)

## Features of the addon

- IK constraint generation for bone chains (with possible automatic creation of controller and pole bones)
- IK Spline rig generation for bone chains
- possibility to add bendy bones for both functions above
- mouth controller (for quicker mouth poses) generator
- Keyframes Slide function, to scale a specific set of bones and move the other keyframes preserving their distance (BETA)
- additional tools (OptiX Compatibility)
- full and only compatibility with Blender 2.83/2.90

## Instructions

- This is an early version! Be sure to make a backup of your work before using this model on it!
- Install the addon as any other Blender addon (if you don't know how to do it, google it!)
- Press N in Viewport, and find the "Mustard Tools" tab
- You can find a very brief video tutorial here:
https://streamable.com/10u6sd

## Troubleshooting

- When I use the IK Spline, the controllers are generated far from the actual curve.
When this happens, also a warning message should appear, remembering you to Apply the location to your armature. To do so, go in Object moe, select the Armature and press Ctrl+A. Then choose Location (even if, in general, applying the full LocRotSca is a good practice).

