# graphics-project-3

This code is the full scene for Project 3: Interactive 3D Scene, done by Matthew Merritt, Michael Merritt, and Harsh Gandhi. 

## Running the Scene

Ensure that you have the following python packages installed:

```
pillow==11.0.0
pygame==2.6.0
PyOpenGL==3.1.7
```

Once the packages are installed, run the following:

```bash
python interactive_scene_pygame.py
```

An additional window should open with the interactive 3D scene.

## Files

The code is divided into four files, with the following breakdown:

- `interactive_scene_pygame.py` - Contains the interactive 3D scene with tables, lights, objects, and player controls. This is the file that should be run.
- `utils.py` - Supporting module based on class examples. Includes classes for points and vectors, with some additional operations added (namely dot products and scalar multiplication for vectors).
- `camera.py` - Supporting module based on class examples. Includes camera movement and rotation, but also includes boundary and collision detection.
- `light.py` - Supporting module for representing a single light in the scene. Does NOT place the lights.

All textures are available in the `resources` directory.

## Features

The features are the following:

### Camera

Can move in all directions, spin around a full 360 degrees, and tilt up or down up to 90 degrees. Movement is bounded to the room, limiting the player from entering the walls, tables, or painting.

### Lights

There are 6 lights, and 4 start enabled at the beginning of the program. Lights 1, 2, and 3 are red, blue, and green overhead point lights, respectively. These start enabled to make it easy to see the room. Light 4 is the overhead yellow spotlight, and it will flicker whenever it is on. Light 5 is the white desk lamp, which acts as a downward spot light. Light 0 is the flashlight, which is a directional spotlight.

### Dice

There are dice in the corner of the room which will roll randomly if the player presses a button. These dice are textured and have 6 different faces.

### Hanging Lamp

The hanging yellow spotlight can swing with the press of a button, and it can be slowed to a stop by pressing the button again. It follows a pendulum motion. To prevent unexpected velocity and position jumps from the angle functions, the swinging can only start when it is at rest.

### Painting 

Disable all the lights except the flashlight to have the painting in the back revealed. When it is hidden, the concrete ceiling texture is displayed instead.

### Controls

Camera Controls:
  W/S - Move forward/backward
  A/D - Strafe left/right
  Q/E - Turn camera left/right
  Z/X - Tilt camera up/down
  R   - Reset camera to home position
  T   - Reset camera to original angle

Light Controls:
  0 - Toggle flashlight
  1 - Toggle red overhead light
  2 - Toggle green overhead light
  3 - Toggle blue overhead light
  4 - Toggle hanging spotlight (yellow)
  5 - Toggle desk lamp

Interaction Controls:
  G - Roll the dice
  F - Toggle hanging light swing

System Controls:
  H - Show this help message
  ESC - Exit program

### Bonus Features

Still in progress
