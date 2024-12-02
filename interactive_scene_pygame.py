#==============================
# Matthew Merritt, Michael Merritt, Harsh Gandhi
# CSC345/CSC645: Computer Graphics
#   Fall 2024
# Description:
#   Displays a interactive 3D scene with tables, lights, objects, and player controls.
#   Boilerplate code is reused from examples in class.
#==============================

import sys
import pygame
import math
import copy
from OpenGL.GLU import *
from OpenGL.GL import *
from utils import *
from camera import *
from light import *
from PIL import Image
import random

#=======================================
# Initial data configuration + Global module variables
#=======================================

# These parameters define the camera's lens shape
CAM_NEAR = 0.01
CAM_FAR = 1000.0
CAM_ANGLE = 60.0

# camera position at start
start_camera_position = Point(0, 15, 40)

# quadrics used for curved shapes
tube = None
ball = None
disk = None

# textures
floor_texture = None
wall_texture = None
ceiling_texture = None
table_top_texture = None 
table_support_texture = None
lamp_support_texture = None
lamp_head_texture = None
aluminum_light_texture = None
aluminum_dark_texture = None
felt_texture = None
dice_texture_1 = None
dice_texture_2 = None
dice_texture_3 = None
dice_texture_4 = None
dice_texture_5 = None
dice_texture_6 = None

# Dice state information
dice_animating = False
dice_rotation = [0, 0, 0] 
dice_rotation2 = [0, 0, 0]

# Hanging light state information
hanging_light_switched_on = False
flickering = False
flicker_duration = 0
flicker_elapsed_frames = 0
reflickering = False
reflicker_duration = 0
reflicker_elapsed_frames = 0

light_swinging = False
light_swing_speed = 0
light_swing_angle = 0

# These parameters define simple animation properties
FPS = 60.0
DELAY = int(1000.0 / FPS + 0.5)

# all lights in the scene
# order is flashlight (100% white), overhead red, overhead green, overhead blue, hanging light (50% yellow) + flicker, desk lamp (75% white)
lights = [ 
    # TODO: update flashlight position and direction with camera
    Light(
        GL_LIGHT0, 
        enabled=True,
        position=copy.deepcopy(start_camera_position), # flashlight starts where player is
        ambient=[1.0, 1.0, 1.0, 1.0],  
        diffuse=[1.0, 1.0, 1.0, 1.0],
        specular=[1.0, 1.0, 1.0, 1.0],
        direction=[0.0, 0.0, -1.0, 0.0],
        display_ball=False,
        is_spot_light=True,
        constant_attenuation=1,
        linear_attenuation=0.01,
        quadratic_attenuation=0,
        spot_cutoff=30,
        spot_exponent=15
    ),
    # Red light in far-left quarter of room
    Light(
        GL_LIGHT1, 
        enabled=False,
        position=Point(20, 40, -20),
        ambient=[0.3, 0.0, 0.0, 1.0],  
        diffuse=[0.3, 0.0, 0.0, 1.0],
        specular=[0.3, 0.0, 0.0, 1.0],
        display_ball=True,
        is_point_light=True, # TODO: determine if this is the correct type
        constant_attenuation=1,
        linear_attenuation=0.01,
        quadratic_attenuation=0
    ),
    # Green light in left-center area of room
    Light(
        GL_LIGHT2, 
        enabled=False,
        position=Point(-20, 40, 0),
        ambient=[0.0, 0.3, 0.0, 1.0],  
        diffuse=[0.0, 0.3, 0.0, 1.0],
        specular=[0.0, 0.3, 0.0, 1.0],
        display_ball=True,
        is_point_light=True, # TODO: determine if this is the correct type
        constant_attenuation=1,
        linear_attenuation=0.01,
        quadratic_attenuation=0
    ),
    # Blue light in close-right quarter of room
    Light(
        GL_LIGHT3, 
        enabled=False,
        position=Point(20, 40, 20),
        ambient=[0.0, 0.0, 0.3, 1.0],  
        diffuse=[0.0, 0.0, 0.3, 1.0],
        specular=[0.0, 0.0, 0.3, 1.0],
        display_ball=True,
        is_point_light=True, # TODO: determine if this is the correct type
        constant_attenuation=1,
        linear_attenuation=0.01,
        quadratic_attenuation=0
    ),
    # Hanging light in center of the room
    Light(
        GL_LIGHT4, 
        enabled=False,
        position=Point(0, 35, 0), # hanging light y-value is 40 - 5 (room height - pole height)
        ambient=[0.5, 0.5, 0.0, 1.0],  
        diffuse=[0.5, 0.5, 0.0, 1.0],
        specular=[0.5, 0.5, 0.0, 1.0],
        direction=[0.0, -1.0, 0.0, 0.0],
        display_ball=True,
        is_spot_light=True,
        spot_cutoff=10.0,
        spot_exponent=10
    ),
    # Lamp in far right-corner of room
    Light(
        GL_LIGHT5, 
        enabled=False,
        position=Point(-32, 11.2, -36), # lamp y-value is 8 + 4 - 1/2 (1.6) (table height + pole height + 1/2 shade height)
        ambient=[0.75, 0.75, 0.75, 1.0],  
        diffuse=[0.75, 0.75, 0.75, 1.0],
        specular=[0.75, 0.75, 0.75, 1.0],
        direction=[0.0, -1.0, 0.0, 0.0],
        display_ball=True,
        is_spot_light=True,
        spot_cutoff=90.0,
        spot_exponent=10
    ),
]

# Bounding box for room (xz-plane only)
room_bounds = ((-40, -40), (40, 40))

# Bounding boxes for obstacles (xz-plane only)
obstacles = [
    ((-39, -37), (-31, -31)),   # Side table boundaries
    ((-9, -5), (9, 5)),         # Pool table boundaries
]

# Window data
window_dimensions = (1000, 800)
name = b'Project 2'

#==============================
# OpenGL and Scene Setup
#==============================

def main():
    init()
    global camera
    camera = Camera(CAM_ANGLE, window_dimensions[0]/window_dimensions[1], CAM_NEAR, CAM_FAR)
    camera.eye = Point(0, 15, 40)  # Position the camera
    camera.look = Point(0, 0, 0)  # Look at the center of the scene
    camera.up = Vector(Point(0, 1, 0))  # Set up vector
    camera.add_room_boundaries(room_bounds) # Add bounding box for room
    camera.add_obstacle_bounding_boxes(obstacles) # Add bounding boxes for objects

    # Enters the main loop.   
    # Displays the window and starts listening for events.
    main_loop()
    return

# Any initialization material to do...
def init():
    # state information
    global clock, running
    # quadrics
    global tube, ball, disk
    # textures
    global dice_texture_1, dice_texture_2, dice_texture_3, dice_texture_4, dice_texture_5, dice_texture_6, floor_texture, wall_texture, ceiling_texture, table_support_texture, table_top_texture, lamp_support_texture, lamp_head_texture, aluminum_light_texture, aluminum_dark_texture, felt_texture

    # pygame setup
    pygame.init()
    pygame.key.set_repeat(300, 50)
    pygame.display.set_mode(window_dimensions, pygame.DOUBLEBUF|pygame.OPENGL)
    clock = pygame.time.Clock()
    running = True

    # loading / generating textures
    wall_texture = load_texture("wall.jpg", 512)
    ceiling_texture = load_texture("Concrete_texture.jpg", 1024) 
    table_top_texture = load_texture("table_top.jpg", 512)
    table_support_texture = load_texture("table_support.jpg", 512)
    lamp_support_texture = load_texture("lamp_support.jpg", 512)
    lamp_head_texture = load_texture("lamp_head.jpg", 512)
    aluminum_dark_texture = load_texture("HangingLamp_Dark.jpg", 1024)
    aluminum_light_texture = load_texture("HangingLamp_Light.jpg", 1024)
    felt_texture = load_texture("felt-temp.jpg", 512)
    dice_texture_1 = load_texture("dice_1.jpg", 512)
    dice_texture_2 = load_texture("dice_2.jpg", 512)
    dice_texture_3 = load_texture("dice_3.jpg", 512)
    dice_texture_4 = load_texture("dice_4.jpg", 512)
    dice_texture_5 = load_texture("dice_5.jpg", 512)
    dice_texture_6 = load_texture("dice_6.jpg", 512)
    floor_texture = generate_checkerboard_texture(4, 4, 1, [[139, 69, 19, 255], [205, 133, 63, 255]]) 

    # loading / creating quadrics
    tube = gluNewQuadric()
    gluQuadricDrawStyle(tube, GLU_FILL)
    gluQuadricTexture(tube, GL_TRUE)
    gluQuadricNormals(tube, GLU_SMOOTH) 

    ball = gluNewQuadric()
    gluQuadricDrawStyle(ball, GLU_FILL)
    gluQuadricTexture(ball, GL_TRUE)
    gluQuadricNormals(ball, GLU_SMOOTH) 

    disk = gluNewQuadric()
    gluQuadricDrawStyle(disk, GLU_FILL)
    gluQuadricTexture(disk, GL_TRUE)
    gluQuadricNormals(disk, GLU_SMOOTH) 

    # OpenGL setup
    glEnable(GL_LIGHTING)
    glEnable(GL_NORMALIZE)    # Inefficient...
    glEnable(GL_DEPTH_TEST)   # For z-buffering!

# helper function to load in textures with a given file and image size
#   in order to preserve repeating patterns, the image is resized instead of cropped
def load_texture(file_name, dim):
    im = Image.open(file_name)
    size = (dim, dim)
    texture = im.resize(size).tobytes("raw")

    texture_name = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_name)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, dim, dim, 0, GL_RGB,
                 GL_UNSIGNED_BYTE, texture)
    return texture_name

# helper function to create a checkerboard texture, used for the floor
def generate_checkerboard_texture(nrows, ncols, block_size, block_colors):
    color_size = len(block_colors[0])
    if color_size != 4:
        print("Error: Currently only RGBA supported here. Texture not generated.")
        return None

    texture = [0]*(nrows*ncols*block_size*block_size*color_size)
    idx = 0
    for i in range(nrows):
        for ib in range(block_size):
            for j in range(ncols):
                color = block_colors[(i+j)%len(block_colors)]
                for jb in range(block_size):
                    for c in color:
                        texture[idx] = c
                        idx += 1

    texture_name = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_name)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                 ncols*block_size, 
                 nrows*block_size, 
                 0, GL_RGBA, 
                 GL_UNSIGNED_BYTE, texture)
    return texture_name

def main_loop():
    global running, clock
    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                keyboard(event)


        # Always advance to the next frame
        #   Necessary for calculating rolling dice positions or swinging light location
        advance()

        # (Re)draw the scene (should only do this when necessary!)
        display()

        # Flipping causes the current image to be seen. (Double-Buffering)
        pygame.display.flip()

        clock.tick(FPS)  # delays to keep it at FPS frame rate

# Callback function used to display the scene
# Currently it just draws a simple polyline (LINE_STRIP)
def display():
    # Set the viewport to the full screen
    win_width = window_dimensions[0]
    win_height = window_dimensions[1]
    glViewport(0, 0, win_width, win_height)

    camera.setProjection()

    # Clear the Screen
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # And draw the "Scene"
    glColor3f(1.0, 1.0, 1.0)
    draw_scene()

    # And show the scene
    glFlush()

# Advance the scene one frame
def advance():
    # Dice animations
    global dice_animating, dice_rotation, dice_rotation2
    if dice_animating:
        dice_rotation[0] += 5  
        dice_rotation[1] += 8  
        dice_rotation[2] += 3  
        
        dice_rotation2[0] += 8  
        dice_rotation2[1] += 5
        dice_rotation2[2] += 6
    
        if dice_rotation[0] >= 540: 
            dice_animating = False
            dice_rotation = [random.randint(0,3) * 90, random.randint(0,3) * 90, random.randint(0,3) * 90]
            dice_rotation2 = [random.randint(0,3) * 90, random.randint(0,3) * 90, random.randint(0,3) * 90]

    # Hanging light animations
    global hanging_light_switched_on, flickering, flicker_duration, flicker_elapsed_frames, reflickering, reflicker_duration, reflicker_elapsed_frames

    # FLICKERING PROCESS:
    #   If the light has been activated by the player, it can flicker off randomly
    #       When it flickers off, the light is immediately disabled and the duration of this flicker is set
    #       The light will be in the flicker state until the full flicker duration has passed
    #       When in the flicker state, it is possible for the light to turn on again, called a reflicker
    #       This will cause the light to immediately be re-enabled and a new duration for reflicker is set
    #       When in a reflicker state, the light is enabled, until the reflicker is over

    # only start a flicker if the light is on
    if hanging_light_switched_on:
        # if not flickering, try to start one
        if not flickering:
            # check if a flicker should happen (has a 10% chance every frame)
            should_flicker = random.random() < 0.1
            # begin the flicker
            if should_flicker:
                flickering = True
                flicker_duration = random.random() * 1.5 * FPS # flicker of up to 3 seconds
                flicker_elapsed_frames = 0
                lights[4].enabled = False
        # if the light is flickering, count up the flicker time or reflicker time
        else:
            # check if flicker is ongoing or ended
            if flicker_duration > flicker_elapsed_frames:
                flicker_elapsed_frames += 1
            else:
                flickering = False
                flicker_duration = 0
                flicker_elapsed_frames = 0
                
                reflickering = False
                reflicker_duration = 0
                reflicker_elapsed_frames = 0

                # restore original light properties
                lights[4].enabled = True
                lights[4].ambient = [0.5, 0.5, 0.0, 1.0]
                lights[4].diffuse = [0.5, 0.5, 0.0, 1.0]
                lights[4].specular = [0.5, 0.5, 0.0, 1.0]

            # if not reflickering, try to start one
            if not reflickering:
                # check if a reflicker should happen (has a 30% chance every frame)
                should_reflicker = random.random() < 0.3
                # begin the reflicker
                if should_reflicker:
                    reflickering = True
                    reflicker_duration = random.random() * 0.5 * FPS # reflicker of up to 1 seconds
                    reflicker_elapsed_frames = 0
                    # reflicker with lower light level
                    lights[4].enabled = True
                    lights[4].ambient = [0.1, 0.1, 0.0, 1.0]
                    lights[4].diffuse = [0.1, 0.1, 0.0, 1.0]
                    lights[4].specular = [0.1, 0.1, 0.0, 1.0]
            else:
                # check if reflicker is ongoing or ended
                if reflicker_duration > reflicker_elapsed_frames:
                    reflicker_elapsed_frames += 1
                else:                 
                    reflickering = False
                    reflicker_duration = 0
                    reflicker_elapsed_frames = 0
                    # restore original light level
                    lights[4].enabled = True
                    lights[4].ambient = [0.5, 0.5, 0.0, 1.0]
                    lights[4].diffuse = [0.5, 0.5, 0.0, 1.0]
                    lights[4].specular = [0.5, 0.5, 0.0, 1.0]

    # print(f'Flicker: \t{flickering}, Reflicker: \t{reflickering}')
                    
    global light_swinging, light_slowing, light_swing_speed, light_swing_angle
    # if the light is actively swinging, keep adjusting the angle
    if light_swinging:
        light_swing_angle += light_swing_speed
        if abs(light_swing_angle) >= 45:
            light_swing_speed *= -1
        # need to multiply by 5 to account for the radius of the lights arc
        # otherwise the angle is drawn from straight down, so x is sine and y is cosine
        light_x = 5 * math.sin(math.radians(light_swing_angle))
        light_y = 5 * math.cos(math.radians(light_swing_angle))
        lights[4].position.x = light_x
        lights[4].position.y = 40 - light_y # need to account for coming from the ceiling
        lights[4].direction[0] = math.sin(math.radians(light_swing_angle)) # normalized
        lights[4].direction[1] = -math.cos(math.radians(light_swing_angle)) # normalized

    # print(f'Swinging: \t{light_swinging}, Angle: {light_swing_angle}')
    # print(f'Light Pos: {lights[4].position}, Light Direction: {lights[4].direction}')

    # Flashlight updating

    # calculate the direction using vector between camera location and look at point 
    camera_direction = Vector(camera.eye, camera.get_look_at_point())

    lights[0].position = copy.deepcopy(camera.eye)
    lights[0].direction = [camera_direction.dx, camera_direction.dy, camera_direction.dz, 0.0]

# Function used to handle any key events
# event: The keyboard event that happened
def keyboard(event):
    global running, dice_animating, hanging_light_switched_on, light_swinging, light_swing_speed
    key = event.key # "ASCII" value of the key pressed
    if key == 27:  # ASCII code 27 = ESC-key
        running = False
    elif key == ord('w'):
        # Go forward
        camera.slide(0,0,-1)
    elif key == ord('s'):
        # Go backward
        camera.slide(0,0,1)
    elif key == ord('a'):
        # Go left (relative to camera)
        camera.slide(1,0,0)
    elif key == ord('d'):
        # Go right (relative to camera)
        camera.slide(-1,0,0)
    elif key == ord('q'):
        # Turn camera left (counter-clockwise)
        camera.turn(1)
    elif key == ord('e'):
        # Turn camera right (clockwise)
        camera.turn(-1)
    elif key == ord('z'):
        # Rotate camera up
        camera.tilt(1)
    elif key == ord('x'):
        # Rotate camera down
        camera.tilt(-1)
    elif key == ord('h'):
        # Output help message to the console
        print_help_message()
    elif key == ord('0'):
        # Toggle activation of light 0
        lights[0].enabled = not lights[0].enabled
    elif key == ord('1'):
        # Toggle activation of light 1
        lights[1].enabled = not lights[1].enabled
    elif key == ord('2'):
        # Toggle activation of light 2
        lights[2].enabled = not lights[2].enabled
    elif key == ord('3'):
        # Toggle activation of light 3
        lights[3].enabled = not lights[3].enabled
    elif key == ord('4'):
        # Toggle activation of light 4
        hanging_light_switched_on = not hanging_light_switched_on
        lights[4].enabled = hanging_light_switched_on
        # stop flickering if the light gets turned off
        if not hanging_light_switched_on:
            light_flickering = False
    elif key == ord('5'):
        # Toggle activation of light 5
        lights[5].enabled = not lights[5].enabled
    elif key == ord('g'):
        # Play dice roll animation
        if not dice_animating:
            dice_animating = True
    elif key == ord('t'):
        # Play hanging light swing
        light_swinging = not light_swinging
        light_swing_speed = 0.5

# function to set up the camera, lights, and world
def draw_scene():
    """
    * draw_scene:
    *    Draws a simple scene with a few shapes
    """
    # Place the camera
    glMatrixMode(GL_MODELVIEW);
    camera.placeCamera()
    
    # Now transform the world
    glColor3f(1, 1, 1)
    place_lights()
    draw_objects() 

# function to set up the main lights in the room
def place_lights():
    """Set up the main lights."""
    global lights

    amb = [0.3, 0.3, 0.3, 1.0]   # No ambient light initially
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, amb)

    for index, light in enumerate(lights):
        # skip disabled lights
        if not light.enabled:
            glDisable(light.gl_light_name)
            continue
        # display enabled lights
        else:
            glMatrixMode(GL_MODELVIEW)

            # For each light, set position, ambient, diffuse, and specular values using class
            #   note: light.position is not valid for GL_POSITION, as it is a point and not a list
            glLightfv(light.gl_light_name, GL_POSITION, light.get_position_list())
            glLightfv(light.gl_light_name, GL_AMBIENT, light.ambient)
            glLightfv(light.gl_light_name, GL_DIFFUSE, light.diffuse)
            glLightfv(light.gl_light_name, GL_SPECULAR, light.specular)

            # Constant attenuation (for distance, etc.)
            # Only works for fixed light locations!  Otherwise disabled
            glLightf(light.gl_light_name, GL_CONSTANT_ATTENUATION, light.constant_attenuation)
            glLightf(light.gl_light_name, GL_LINEAR_ATTENUATION, light.linear_attenuation)
            glLightf(light.gl_light_name, GL_QUADRATIC_ATTENUATION, light.quadratic_attenuation)

            # Create a spotlight effect (none at the moment)
            #   note: if not a spot light, these values should be 180.0 and 0.0, meaning they have no effect
            glLightf(light.gl_light_name, GL_SPOT_CUTOFF, light.spot_cutoff) 
            glLightf(light.gl_light_name, GL_SPOT_EXPONENT, light.spot_exponent)
            # Attach direction to spot lights only
            if light.is_spot_light:
                glLightfv(light.gl_light_name, GL_SPOT_DIRECTION, light.direction)

            glEnable(light.gl_light_name)

            # This part draws a SELF-COLORED sphere (in spot where light is!)
            if (light.display_ball):
                glPushMatrix()
                glTranslatef(light.position.x, light.position.y, light.position.z)
                glDisable(GL_LIGHTING)
                glColor3f(light.ambient[0], light.ambient[1], light.ambient[2]) # Colored sphere
                gluSphere(ball, 0.2, 100, 100)
                glEnable(GL_LIGHTING)
                glPopMatrix()

    glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE) # draw specular reflections relative to camera direction
    glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE) # light both sides of a shape

# function to draw the actual elements and objects in the room
def draw_objects():
    glPushMatrix()
    # TODO: add function calls here
    draw_floor(0, 0, 0, 80, 80, 10, 10)
    draw_walls(0, 0, 0, 80, 40, 10, 5)
    draw_ceiling(0, 40, 0, 80, 80, 10, 10)
    draw_side_table(-35, 0, -34)
    draw_desk_lamp(-32, 8, -36)
    draw_dice(-37, 8.22, -34)
    draw_hanging_spotlight(0, 40, 0)
    draw_pool_table(0, 4, 0)
    # ball bounds are x: [-7.25, 7.25] z: [-2.75, 2.75]
    draw_cue_ball(0, 9.25, 0) 
    glPopMatrix()
    
#=======================================
# Scene-drawing functions
#=======================================

# draws the floor using a textured plane
def draw_floor(center_x, y, center_z, x_dim, z_dim, x_slices, z_slices):
    set_floor_material(GL_FRONT)
    
    glPushMatrix()
    glTranslatef(center_x - x_dim / 2, y, center_z + z_dim / 2)
    glRotatef(-90, 1, 0, 0)
    draw_textured_plane(x_dim, z_dim, x_slices, z_slices, floor_texture)
    # glTranslatef(0, 0, 1); gluSphere(ball, 0.25, 16, 16) # Normal check
    glPopMatrix()

# draws a square room using textured planes
def draw_walls(center_x, y, center_z, length, height, l_slices, h_slices):
    set_wall_material(GL_FRONT)  

    # Draw side 1 backward-facing wall on xy-plane (opposite player)
    glPushMatrix()
    glTranslatef(center_x - length / 2, y, center_z - length / 2)    
    draw_textured_plane(length, height, l_slices, h_slices, wall_texture)
    # glTranslatef(0, 0, 1); gluSphere(ball, 0.25, 16, 16) # Normal check
    glPopMatrix()

    # Draw side 2 forward-facing wall on xy-plane (behind player)
    glPushMatrix()
    glRotate(180, 0, 1, 0)
    glTranslatef(center_x - length / 2, y, center_z - length / 2)
    draw_textured_plane(length, height, l_slices, h_slices, wall_texture)
    # glTranslatef(0, 0, 1); gluSphere(ball, 0.25, 16, 16) # Normal check   
    glPopMatrix()

    # Draw side 3 right-facing wall on yz-plane (left of player)
    glPushMatrix()
    glRotate(90, 0, 1, 0)
    glTranslatef(center_z - length / 2, y, center_x - length / 2)
    draw_textured_plane(length, height, l_slices, h_slices, wall_texture) 
    # glTranslatef(0, 0, 1); gluSphere(ball, 0.25, 16, 16) # Normal check  
    glPopMatrix()

    # Draw side 4 left-facing wall on yz-plane (right of player)
    glPushMatrix()
    glRotate(270, 0, 1, 0)
    glTranslatef(center_z - length / 2, y, center_x - length / 2)
    draw_textured_plane(length, height, l_slices, h_slices, wall_texture)  
    # glTranslatef(0, 0, 1); gluSphere(ball, 0.25, 16, 16) # Normal check
    glPopMatrix()

# draws the ceiling using a textured plane facing down
def draw_ceiling(center_x, y, center_z, x_dim, z_dim, x_slices, z_slices):
    set_ceiling_material(GL_FRONT)
    
    glPushMatrix()
    glTranslatef(center_x - x_dim / 2, y, center_z - z_dim / 2)
    glRotatef(90, 1, 0, 0)
    draw_textured_plane(x_dim, z_dim, x_slices, z_slices, ceiling_texture)
    # glTranslatef(0, 0, 1); gluSphere(ball, 0.25, 16, 16) # Normal check
    glPopMatrix()

def draw_table_top(width, length):
    thickness = 0.8 

    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 10.0)

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, table_top_texture)
    
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glTexCoord2f(0, 0)
    glVertex3f(-width/2, 0, -length/2)
    glTexCoord2f(1, 0)
    glVertex3f(width/2, 0, -length/2)
    glTexCoord2f(1, 1)
    glVertex3f(width/2, 0, length/2)
    glTexCoord2f(0, 1)
    glVertex3f(-width/2, 0, length/2)
    
    glNormal3f(0, -1, 0)
    glTexCoord2f(0, 0)
    glVertex3f(-width/2, -thickness, -length/2)
    glTexCoord2f(1, 0)
    glVertex3f(width/2, -thickness, -length/2)
    glTexCoord2f(1, 1)
    glVertex3f(width/2, -thickness, length/2)
    glTexCoord2f(0, 1)
    glVertex3f(-width/2, -thickness, length/2)
    
    glNormal3f(0, 0, 1)
    glTexCoord2f(0, 0)
    glVertex3f(-width/2, -thickness, length/2)
    glTexCoord2f(1, 0)
    glVertex3f(width/2, -thickness, length/2)
    glTexCoord2f(1, thickness/2)
    glVertex3f(width/2, 0, length/2)
    glTexCoord2f(0, thickness/2)
    glVertex3f(-width/2, 0, length/2)
    
    glNormal3f(0, 0, -1)
    glTexCoord2f(0, 0)
    glVertex3f(-width/2, -thickness, -length/2)
    glTexCoord2f(1, 0)
    glVertex3f(width/2, -thickness, -length/2)
    glTexCoord2f(1, thickness/2)
    glVertex3f(width/2, 0, -length/2)
    glTexCoord2f(0, thickness/2)
    glVertex3f(-width/2, 0, -length/2)
    
    glNormal3f(-1, 0, 0)
    glTexCoord2f(0, 0)
    glVertex3f(-width/2, -thickness, -length/2)
    glTexCoord2f(1, 0)
    glVertex3f(-width/2, -thickness, length/2)
    glTexCoord2f(1, thickness/2)
    glVertex3f(-width/2, 0, length/2)
    glTexCoord2f(0, thickness/2)
    glVertex3f(-width/2, 0, -length/2)
    
    glNormal3f(1, 0, 0)
    glTexCoord2f(0, 0)
    glVertex3f(width/2, -thickness, -length/2)
    glTexCoord2f(1, 0)
    glVertex3f(width/2, -thickness, length/2)
    glTexCoord2f(1, thickness/2)
    glVertex3f(width/2, 0, length/2)
    glTexCoord2f(0, thickness/2)
    glVertex3f(width/2, 0, -length/2)
    glEnd()
    
    glDisable(GL_TEXTURE_2D)

def draw_table_leg(height):
    glPushMatrix()
    
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 10.0)

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, table_support_texture)
    
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    
    glRotatef(-90, 1, 0, 0)
    radius = 0.4
    gluCylinder(tube, radius, radius, height, 32, 4)  
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()
    
def draw_side_table(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)    
    height = 8
    width = 8 
    length = 6
    
    glPushMatrix()
    glTranslatef(-width/2 + 1, 0, -length/2 + 1)
    draw_table_leg(height)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(width/2 - 1, 0, -length/2 + 1)
    draw_table_leg(height)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-width/2 + 1, 0, length/2 - 1)
    draw_table_leg(height)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(width/2 - 1, 0, length/2 - 1)
    draw_table_leg(height)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, height, 0)
    draw_table_top(width, length)
    glPopMatrix()
    
    glPopMatrix()

def draw_lamp_base(radius):
    glPushMatrix()
    
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 10.0)
    
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, lamp_support_texture)
    
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    
    glRotatef(-90, 1, 0, 0)
    base_height = 0.1 
    gluQuadricTexture(tube, GL_TRUE)
    gluCylinder(tube, radius, radius, base_height, 32, 1)
    gluDisk(disk, 0, radius, 32, 1)  
    glTranslatef(0, 0, base_height)
    gluDisk(disk, 0, radius, 32, 1)
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def draw_lamp_pole(height, radius):
    glPushMatrix()
    
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 10.0)

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, lamp_support_texture)
    
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    
    glRotatef(-90, 1, 0, 0)
    gluQuadricTexture(tube, GL_TRUE)
    gluCylinder(tube, radius, radius, height, 16, 1)
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def draw_lamp_head(radius, height):
    glPushMatrix()
    
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 10.0)

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, lamp_head_texture)
    
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    
    glRotatef(90, 1, 0, 0)
    gluQuadricTexture(tube, GL_TRUE)
    gluCylinder(tube, radius, radius, height, 32, 1)
    gluDisk(disk, 0, radius, 32, 1)
    glTranslatef(0, 0, height)
    gluDisk(disk, 0, radius, 32, 1)
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def draw_desk_lamp(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    base_radius = 0.8
    draw_lamp_base(base_radius)

    pole_height = 4.0
    pole_radius = 0.1
    draw_lamp_pole(pole_height, pole_radius)
    
    
    glTranslatef(0, pole_height, 0)
    head_radius = 1.2
    head_height = 1.6
    draw_lamp_head(head_radius, head_height)
    
    glPopMatrix()

def draw_single_dice(x, y, z, size, rotations=[0,0,0]):
    glPushMatrix()
    glTranslatef(x, y, z)   
    glRotatef(rotations[0], 1, 0, 0)
    glRotatef(rotations[1], 0, 1, 0)
    glRotatef(rotations[2], 0, 0, 1) 
    
    glMaterialfv(GL_FRONT, GL_AMBIENT, [1.0, 1.0, 1.0, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 0.0)
    
    glEnable(GL_TEXTURE_2D)
    
    def set_texture_params():
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    
    glBindTexture(GL_TEXTURE_2D, dice_texture_1)
    set_texture_params()
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glTexCoord2f(0.0, 0.0); glVertex3f(-size, -size, size)
    glTexCoord2f(1.0, 0.0); glVertex3f(size, -size, size)
    glTexCoord2f(1.0, 1.0); glVertex3f(size, size, size)
    glTexCoord2f(0.0, 1.0); glVertex3f(-size, size, size)
    glEnd()
    
    glBindTexture(GL_TEXTURE_2D, dice_texture_6)
    set_texture_params()
    glBegin(GL_QUADS)
    glNormal3f(0, 0, -1)
    glTexCoord2f(0.0, 0.0); glVertex3f(-size, -size, -size)
    glTexCoord2f(1.0, 0.0); glVertex3f(-size, size, -size)
    glTexCoord2f(1.0, 1.0); glVertex3f(size, size, -size)
    glTexCoord2f(0.0, 1.0); glVertex3f(size, -size, -size)
    glEnd()
    
    glBindTexture(GL_TEXTURE_2D, dice_texture_2)
    set_texture_params()
    glBegin(GL_QUADS)
    glNormal3f(1, 0, 0)
    glTexCoord2f(0.0, 0.0); glVertex3f(size, -size, -size)
    glTexCoord2f(1.0, 0.0); glVertex3f(size, size, -size)
    glTexCoord2f(1.0, 1.0); glVertex3f(size, size, size)
    glTexCoord2f(0.0, 1.0); glVertex3f(size, -size, size)
    glEnd()
    
    glBindTexture(GL_TEXTURE_2D, dice_texture_5)
    set_texture_params()
    glBegin(GL_QUADS)
    glNormal3f(-1, 0, 0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-size, -size, -size)
    glTexCoord2f(1.0, 0.0); glVertex3f(-size, -size, size)
    glTexCoord2f(1.0, 1.0); glVertex3f(-size, size, size)
    glTexCoord2f(0.0, 1.0); glVertex3f(-size, size, -size)
    glEnd()
    
    glBindTexture(GL_TEXTURE_2D, dice_texture_3)
    set_texture_params()
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-size, size, -size)
    glTexCoord2f(1.0, 0.0); glVertex3f(-size, size, size)
    glTexCoord2f(1.0, 1.0); glVertex3f(size, size, size)
    glTexCoord2f(0.0, 1.0); glVertex3f(size, size, -size)
    glEnd()
    
    glBindTexture(GL_TEXTURE_2D, dice_texture_4)
    set_texture_params()
    glBegin(GL_QUADS)
    glNormal3f(0, -1, 0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-size, -size, -size)
    glTexCoord2f(1.0, 0.0); glVertex3f(size, -size, -size)
    glTexCoord2f(1.0, 1.0); glVertex3f(size, -size, size)
    glTexCoord2f(0.0, 1.0); glVertex3f(-size, -size, size)
    glEnd()
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def draw_dice(x, y, z):
    draw_single_dice(x, y, z, 0.2, dice_rotation)
    draw_single_dice(x + 1.2, y, z + 0.2, 0.2, dice_rotation2)

# TODO: implement
def draw_pool_table(x, y, z):
    # corners (3 x 2 x 3) # floor should be at midpoint level, hole extends down

    glPushMatrix()
    glTranslatef(x, y, z)

    # top left
    glPushMatrix()
    glRotatef(-90, 0, 1, 0)
    draw_corner(-3.5, 4.75, 8)
    glPopMatrix()
    
    # top right
    glPushMatrix()
    glRotatef(180, 0, 1, 0)
    draw_corner(-8, 4.75, 3.5)
    glPopMatrix()

    # bottom left
    glPushMatrix()
    draw_corner(-8, 4.75, 3.5)
    glPopMatrix()

    # bottom right
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    draw_corner(-3.5, 4.75, 8)
    glPopMatrix()

    # middles (3 x 2 x 3) # floor should be at midpoint level, hole extends down

    glPushMatrix()
    draw_middle_hole(0, 4.75, 3.5)
    glRotatef(180, 0, 1, 0)
    draw_middle_hole(0, 4.75, 3.5)
    glPopMatrix()

    glPopMatrix()

    # x-aligned wood segments (5 x 1.5 x 1.5)
    set_wood_support_material(GL_FRONT)
    draw_rect(x - 4, y + 4.75, z - 4.25, 5, 1.5, 1.5, 10, 4, 3, table_support_texture, False)
    draw_rect(x + 4, y + 4.75, z - 4.25, 5, 1.5, 1.5, 10, 4, 3, table_support_texture, False)
    draw_rect(x - 4, y + 4.75, z + 4.25, 5, 1.5, 1.5, 10, 4, 3, table_support_texture, False)
    draw_rect(x + 4, y + 4.75, z + 4.25, 5, 1.5, 1.5, 10, 4, 3, table_support_texture, False)

    # x-aligned felt segments (5 x 1.5 x 0.5)
    set_felt_material(GL_FRONT)
    draw_rect(x - 4, y + 4.75, z - 3.25, 5, 1.5, 0.5, 10, 4, 1, felt_texture, False)
    draw_rect(x + 4, y + 4.75, z - 3.25, 5, 1.5, 0.5, 10, 4, 1, felt_texture, False)
    draw_rect(x - 4, y + 4.75, z + 3.25, 5, 1.5, 0.5, 10, 4, 1, felt_texture, False)
    draw_rect(x + 4, y + 4.75, z + 3.25, 5, 1.5, 0.5, 10, 4, 1, felt_texture, False)

    # z-aligned wood segments (1.5 x 1.5 x 4)
    set_wood_support_material(GL_FRONT)
    draw_rect(x - 8.75, y + 4.75, z, 1.5, 1.5, 4, 3, 4, 8, table_support_texture, False)
    draw_rect(x + 8.75, y + 4.75, z, 1.5, 1.5, 4, 3, 4, 8, table_support_texture, False)

    # z-aligned felt segments (0.5 x 1.5 x 4)
    set_felt_material(GL_FRONT)
    draw_rect(x - 7.75, y + 4.75, z, 0.5, 1.5, 4, 3, 4, 8, felt_texture, False)
    draw_rect(x + 7.75, y + 4.75, z, 0.5, 1.5, 4, 3, 4, 8, felt_texture, False)

    # felt play area (15 x 1 x 6) minus corners
    set_felt_material(GL_FRONT)
    draw_rect(x, y + 4.5, z, 13, 1, 4, 26, 2, 8, felt_texture, False) # big center

    draw_rect(x - 4, y + 4.5, z - 2.5, 5, 1, 1, 10, 1, 2, felt_texture, False)
    draw_rect(x + 4, y + 4.5, z - 2.5, 5, 1, 1, 10, 1, 2, felt_texture, False)
    draw_rect(x - 4, y + 4.5, z + 2.5, 5, 1, 1, 10, 1, 2, felt_texture, False)
    draw_rect(x + 4, y + 4.5, z + 2.5, 5, 1, 1, 10, 1, 2, felt_texture, False)

    draw_rect(x - 7, y + 4.5, z, 1, 1, 4, 1, 1, 4, felt_texture, False)
    draw_rect(x + 7, y + 4.5, z, 1, 1, 4, 1, 1, 4, felt_texture, False)

    # wood bottom middle (19 x 1 x 10)
    set_wood_support_material(GL_FRONT)
    draw_rect(x, y + 3.5, z, 19, 1, 10, 19, 1, 10, table_support_texture, False)

    # wood legs (3 x 7 x 3)
    set_wood_support_material(GL_FRONT)
    draw_rect(x - 6, y - 0.5, z - 2.5, 3, 7, 3, 3, 7, 3, table_support_texture, False)
    draw_rect(x + 6, y - 0.5, z - 2.5, 3, 7, 3, 3, 7, 3, table_support_texture, False)
    draw_rect(x - 6, y - 0.5, z + 2.5, 3, 7, 3, 3, 7, 3, table_support_texture, False)
    draw_rect(x + 6, y - 0.5, z + 2.5, 3, 7, 3, 3, 7, 3, table_support_texture, False)

def draw_textured_plane(x_size, y_size, x_slices, y_slices, texture, stretch=True):
    """ Draw a textured plane of the specified dimensions on the xy-plane.
        The plane is a unit square with lower left corner at origin.
    """
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE) # try GL_DECAL/GL_REPLACE/GL_MODULATE
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)           # try GL_NICEST/GL_FASTEST
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)  # try GL_CLAMP/GL_REPEAT/GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST) # try GL_NEAREST/GL_LINEAR
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)

    # Center the plane on the origin in x-direction
    # Lower corner = (sx, sy) and upper corner = (ex, ey)
    dx = x_size/x_slices # Change in x direction
    dy = y_size/y_slices  # Change in y direction

    glNormal3f(0, 0, 1)
    y = 0
    for j in range(y_slices):
        glBegin(GL_TRIANGLE_STRIP)
        cx = 0
        for i in range(x_slices):
            if stretch:
                glTexCoord2f(cx/x_size, (y+dy)/y_size)
            else:
                glTexCoord2f(cx, (y+dy))
            glVertex3f(cx, y+dy, 0)
            if stretch:
                glTexCoord2f(cx/x_size, y/y_size)
            else:
                glTexCoord2f(cx, y)
            glVertex3f(cx, y, 0)
            cx += dx
        if stretch:
            glTexCoord2f(1, (y+dy)/y_size)
        else:
            glTexCoord2f(x_size, (y+dy))
        glVertex3f(x_size, y+dy, 0)
        if stretch:
            glTexCoord2f(1, y/y_size)
        else:
            glTexCoord2f(x_size, y)
        glVertex3f(x_size, y, 0)
        glEnd()
        y += dy
   
    glDisable(GL_TEXTURE_2D)

def draw_rect(x, y, z, x_size, y_size, z_size, x_slices, y_slices, z_slices, texture_name, stretch=True):
    """ Draw a rectangle centered around (x, y, z) with size (x_size, y_size, z_size)."""  
    # move to cube location
    glPushMatrix()
    glTranslate(x, y, z)  

    # Draw side 1 (+z)
    glPushMatrix()
    glTranslate(-x_size/2, -y_size/2, z_size/2)
    draw_textured_plane(x_size, y_size, x_slices, y_slices, texture_name, stretch)
    glPopMatrix()

    # Draw side 2 (-z)
    glPushMatrix()
    glTranslate(x_size/2, -y_size/2, -z_size/2)
    glRotated(180, 0, 1, 0)
    draw_textured_plane(x_size, y_size, x_slices, y_slices, texture_name, stretch)
    glPopMatrix()

    # Draw side 3 (-x)
    glPushMatrix()
    glTranslate(-x_size/2, -y_size/2, -z_size/2)
    glRotatef(-90, 0, 1, 0)
    draw_textured_plane(z_size, y_size, z_slices, y_slices, texture_name, stretch)
    glPopMatrix()

    # Draw side 4 (+x)
    glPushMatrix()
    glTranslatef(x_size/2, -y_size/2, z_size/2)
    glRotatef(90, 0, 1, 0)
    draw_textured_plane(z_size, y_size, z_slices, y_slices, texture_name, stretch)
    glPopMatrix()

    # Draw side 5 (-y)
    glPushMatrix()
    glTranslatef(-x_size/2, -y_size/2, -z_size/2)
    glRotatef(90, 1, 0, 0)
    draw_textured_plane(x_size, z_size, x_slices, z_slices, texture_name, stretch)
    glPopMatrix()

    # Draw side 6 (+y)
    glPushMatrix()
    glTranslatef(-x_size/2, y_size/2, z_size/2)
    glRotatef(-90, 1, 0, 0)
    draw_textured_plane(x_size, z_size, x_slices, z_slices, texture_name, stretch)
    glPopMatrix()

    # return
    glPopMatrix()

def draw_hole_insides(start_angle, end_angle, turn_amount, height):
    glPushMatrix()

    # TODO: texture configuration, for if a different one is used

    dtheta = turn_amount
    theta = start_angle

    prev = (math.sin(theta), math.cos(theta)) # first/start point for panel

    while theta < end_angle:
        theta += dtheta # go to second point in panel

        vx = math.sin(theta)
        vz = math.cos(theta)

        curr = (vx, vz)

        # draw the panel
        size = math.sqrt((curr[0] - prev[0])**2 + (curr[1] - prev[1])**2)

        glPushMatrix()
        glTranslate(prev[0], -0.75, prev[1])
        glRotatef(-90, 0, 1, 0)
        glRotatef(math.degrees(((math.pi / 2) - (turn_amount / 2) + theta)), 0, 1, 0)
        draw_textured_plane(size, height, 3, 3, felt_texture) # TODO: change texture
        glPopMatrix()

        prev = (vx, vz)

    glPopMatrix()

# for drawing L-shaped rounded planes with upwards-facing normals
# only use on quadrantal angles
def draw_quarter_rim(start_angle, end_angle, turn_amount, corner_x, corner_z, entry_x, entry_z, exit_x, exit_z):
    glPushMatrix() 

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)

    glNormal3f(0, -1, 0)

    glBegin(GL_TRIANGLE_FAN)
    glTexCoord2f(corner_x, corner_z)
    glVertex3f(corner_x, 0, corner_z)
    glTexCoord2f(entry_x, entry_z)
    glVertex3f(entry_x, 0, entry_z)

    dtheta = turn_amount
    theta = start_angle

    while theta < end_angle:
        vx = math.sin(theta)
        vz = math.cos(theta)

        glTexCoord2f(vx, vz)
        glVertex3f(vx, 0, vz) # point on circle

        theta += dtheta

    theta = end_angle # end goal
    vx = math.sin(theta)
    vz = math.cos(theta)

    glTexCoord2f(vx, vz)
    glVertex3f(vx, 0, vz) # last point on circle

    glTexCoord2f(exit_x, exit_z)
    glVertex3f(exit_x, 0, exit_z)

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

def draw_corner(x, y, z):
    # note: faces that would be otherwise fully included in the structure are not drawn
    # this includes stuff like the seam between the felt and wood, and so on

    glPushMatrix()
    glTranslate(x, y, z) 

    # wood section
    set_wood_support_material(GL_FRONT)
    glBindTexture(GL_TEXTURE_2D, table_support_texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE) # try GL_DECAL/GL_REPLACE/GL_MODULATE
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_FASTEST)           # try GL_NICEST/GL_FASTEST
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)  # try GL_CLAMP/GL_REPEAT/GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST) # try GL_NEAREST/GL_LINEAR
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    # wood corner walls

    # back
    glPushMatrix()
    glTranslate(-1.5, -0.75, 1.5)
    draw_textured_plane(3, 1.5, 6, 4, table_support_texture, False)
    glPopMatrix()

    # side
    glPushMatrix()
    glTranslate(-1.5, -0.75, -1.5)
    glRotatef(-90, 0, 1, 0)
    draw_textured_plane(3, 1.5, 6, 4, table_support_texture, False)
    glPopMatrix()

    # wood corner top
    glPushMatrix()

    glTranslatef(0, 0.75, 0)

    draw_quarter_rim(math.pi, 3 * math.pi / 2, math.pi / 16, -1.5, -1.5, 0, -1.5, -1.5, 0) # top left
    draw_quarter_rim(3 * math.pi / 2, 2 * math.pi, math.pi / 16, -1.5, 1.5, -1.5, 0, 0, 1.5) # bottom left
    draw_quarter_rim(0, math.pi / 2, math.pi / 16, 1.5, 1.5, 0, 1.5, 1.5, 0) # bottom right

    glPopMatrix()

    # felt section
    set_felt_material(GL_FRONT_AND_BACK) # TODO: fix normals and revert to front if possible
    glBindTexture(GL_TEXTURE_2D, felt_texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE) # try GL_DECAL/GL_REPLACE/GL_MODULATE
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_FASTEST)           # try GL_NICEST/GL_FASTEST
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)  # try GL_CLAMP/GL_REPEAT/GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST) # try GL_NEAREST/GL_LINEAR
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    # slope in on top
    glPushMatrix()

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)

    glNormal3f(0.5, 0, 0.5)

    glBegin(GL_TRIANGLE_FAN)

    glTexCoord2f(0, 0)
    glVertex3f(0, 0, -1)

    glTexCoord2f(0, 1)
    glVertex3f(0, 0.75, -1)

    glTexCoord2f(1, 1)
    glVertex3f(0.5, 0.75, -1.5)

    glTexCoord2f(1, 0)
    glVertex3f(0.5, 0, -1.5)

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

    # top of top
    glPushMatrix()

    glNormal3f(0, 1, 0)

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)
    
    glBegin(GL_TRIANGLE_FAN)

    glTexCoord2f(0, -1)
    glVertex3f(0, 0.75, -1)

    glTexCoord2f(0, -1.5)
    glVertex3f(0, 0.75, -1.5)

    glTexCoord2f(0.5, -1.5)
    glVertex3f(0.5, 0.75, -1.5)

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

    # right
    glPushMatrix()

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)
    
    glNormal3f(0.5, 0, -0.5)

    glBegin(GL_TRIANGLE_FAN)

    glTexCoord2f(0, 0)
    glVertex3f(1, 0, 0)

    glTexCoord2f(0, 1)
    glVertex3f(1, 0.75, 0)

    glTexCoord2f(1, 1)
    glVertex3f(1.5, 0.75, -0.5)

    glTexCoord2f(1, 0)
    glVertex3f(1.5, 0, -0.5)

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

    # top right

    glPushMatrix()

    glNormal3f(0, 1, 0)

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)
    
    glBegin(GL_TRIANGLE_FAN)

    glTexCoord2f(-1, 0)
    glVertex3f(1, 0.75, 0)

    glTexCoord2f(-1.5, 0)
    glVertex3f(1.5, 0.75, 0)

    glTexCoord2f(-1.5, -0.5)
    glVertex3f(1.5, 0.75, -0.5)

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

    # felt entryway
    glPushMatrix()

    glTranslatef(0, 0.25, 0)

    draw_quarter_rim(math.pi / 2, math.pi, math.pi / 16, 1.5, -1.5, 1.5, 0, 0, -1.5) # top right

    glPopMatrix()

    # black section
    # TODO: texture parameter?

    # black cylinder liner
    draw_hole_insides(math.pi, 5 * math.pi / 2, math.pi / 16, 1.5) # outer
    draw_hole_insides(math.pi / 2, math.pi, math.pi / 16, 1) # inner

    glPopMatrix()

def draw_middle_hole(x, y, z):
    glPushMatrix()

    glTranslatef(x, y, z)

    # wood section
    set_wood_support_material(GL_FRONT)
    glBindTexture(GL_TEXTURE_2D, table_support_texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE) # try GL_DECAL/GL_REPLACE/GL_MODULATE
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_FASTEST)           # try GL_NICEST/GL_FASTEST
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)  # try GL_CLAMP/GL_REPEAT/GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST) # try GL_NEAREST/GL_LINEAR
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    # back wooden part entryway
    glPushMatrix()

    glTranslate(0, 0.75, 0) # offset center

    draw_quarter_rim(3 * math.pi / 2, 2 * math.pi, math.pi / 16, -1.5, 1.5, -1.5, 0, 0, 1.5) # left
    draw_quarter_rim(0, math.pi / 2, math.pi / 16, 1.5, 1.5, 0, 1.5, 1.5, 0) # right

    glPopMatrix()

    # wooden back panel
    glPushMatrix()
    glTranslate(-1.5, -0.75, 1.5)
    draw_textured_plane(3, 1.5, 6, 4, table_support_texture, False)
    glPopMatrix()

    # felt section
    set_felt_material(GL_FRONT_AND_BACK)
    glBindTexture(GL_TEXTURE_2D, felt_texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE) # try GL_DECAL/GL_REPLACE/GL_MODULATE
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_FASTEST)           # try GL_NICEST/GL_FASTEST
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)  # try GL_CLAMP/GL_REPEAT/GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST) # try GL_NEAREST/GL_LINEAR
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    # slope in on left
    glPushMatrix()

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)
    
    glNormal3f(0.5, 0, -0.5)

    glBegin(GL_TRIANGLE_FAN)

    glTexCoord2f(0, 0)
    glVertex3f(-1, 0, 0)

    glTexCoord2f(0, 1)
    glVertex3f(-1, 0.75, 0)

    glTexCoord2f(1, 1)
    glVertex3f(-1.5, 0.75, -0.5)

    glTexCoord2f(1, 0)
    glVertex3f(-1.5, 0, -0.5)

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

    # top left

    glPushMatrix()

    glNormal3f(0, 1, 0)

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)
    
    glBegin(GL_TRIANGLE_FAN)

    glTexCoord2f(1, 0)
    glVertex3f(-1, 0.75, 0)

    glTexCoord2f(1.5, 0)
    glVertex3f(-1.5, 0.75, 0)

    glTexCoord2f(1.5, -0.5)
    glVertex3f(-1.5, 0.75, -0.5)

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

    # felt entryway
    glPushMatrix()

    glTranslate(0, 0.25, 0) # offset center

    draw_quarter_rim(math.pi, 3 * math.pi / 2, math.pi / 16, -1.5, -1.5, 0, -1.5, -1.5, 0) # left
    draw_quarter_rim(math.pi / 2, math.pi, math.pi / 16, 1.5, -1.5, 1.5, 0, 0, -1.5) # right

    glPopMatrix()

    # slope on right

    glPushMatrix()

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)
    
    glNormal3f(0.5, 0, -0.5)

    glBegin(GL_TRIANGLE_FAN)

    glTexCoord2f(0, 0)
    glVertex3f(1, 0, 0)

    glTexCoord2f(0, 1)
    glVertex3f(1, 0.75, 0)

    glTexCoord2f(1, 1)
    glVertex3f(1.5, 0.75, -0.5)

    glTexCoord2f(1, 0)
    glVertex3f(1.5, 0, -0.5)

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

    # top right

    glPushMatrix()

    glNormal3f(0, 1, 0)

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)
    
    glBegin(GL_TRIANGLE_FAN)

    glTexCoord2f(-1, 0)
    glVertex3f(1, 0.75, 0)

    glTexCoord2f(-1.5, 0)
    glVertex3f(1.5, 0.75, 0)

    glTexCoord2f(-1.5, -0.5)
    glVertex3f(1.5, 0.75, -0.5)

    glEnd()

    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

    # black section
    # TODO: texture parameter?

    # black cylinder liner
    draw_hole_insides(math.pi / 2, 3 * math.pi / 2, math.pi / 16, 1) # inner
    draw_hole_insides(3 * math.pi / 2, 5 * math.pi / 2, math.pi / 16, 1.5) # outer

    glPopMatrix()

# TODO: implement
def draw_billiard_ball(x, y, z, texture, x_rotation=0, z_rotation=0):
    pass

# TODO: implement
def draw_cue_ball(x, y, z, x_rotation=0, z_rotation=0):
    glPushMatrix()
    glTranslatef(x, y, z)
    gluSphere(ball, 0.25, 16, 16)
    glPopMatrix()

# TODO: implement swinging
def draw_hanging_spotlight(x, y, z):
    # may need additional parameters for swinging
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(light_swing_angle, 0, 0, 1)

    pole_radius = 0.25
    pole_height = 5

    upper_lamp_radius = 2
    lower_lamp_radius = 5
    lamp_height = 5

    # prepare the texture for the hanging lamp pole
    glBindTexture(GL_TEXTURE_2D, aluminum_light_texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE) # try GL_DECAL/GL_REPLACE/GL_MODULATE
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)           # try GL_NICEST/GL_FASTEST
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)  # try GL_CLAMP/GL_REPEAT/GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST) # try GL_LINEAR/GL_NEAREST
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)

    # drawing the hanging light pole
    glTranslatef(0, -pole_height, 0)
    glRotatef(-90, 1, 0, 0)
    set_aluminum_material(GL_FRONT_AND_BACK)
    # parameters are: quadric, base radius, height radius, height, slices, stacks
    gluCylinder(tube, pole_radius, pole_radius, pole_height, 30, 10)
    glRotatef(90, 1, 0, 0)

    # Disabling texturing mode to switch texture
    glDisable(GL_TEXTURE_2D)

    # prepare the texture for the hanging lamp shade
    glBindTexture(GL_TEXTURE_2D, aluminum_dark_texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE) # try GL_DECAL/GL_REPLACE/GL_MODULATE
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)           # try GL_NICEST/GL_FASTEST
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)  # try GL_CLAMP/GL_REPEAT/GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST) # try GL_LINEAR/GL_NEAREST
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    # Enable/Disable each time or OpenGL ALWAYS expects texturing!
    glEnable(GL_TEXTURE_2D)

    # draw a circle for the top of the lamp shade
    # parameters are: quadric, inner radius (imagine a donut), outer radius, slices, and rings
    # TODO: determine if this should be done manually
    glRotatef(-90, 1, 0, 0)
    set_aluminum_material(GL_FRONT_AND_BACK)
    gluDisk(disk, 0, upper_lamp_radius, 30, 10)
    glRotate(90, 1, 0, 0)

    # drawing the hanging light shade
    glTranslatef(0, -lamp_height, 0)
    glRotatef(-90, 1, 0, 0)
    set_aluminum_material(GL_FRONT_AND_BACK)
    gluCylinder(tube, lower_lamp_radius, upper_lamp_radius, lamp_height, 30, 10)
    glRotatef(90, 1, 0, 0)

    # Disabling texturing mode
    glDisable(GL_TEXTURE_2D)

    glPopMatrix()

# TODO: implement
def draw_wall_picture(x, y, z):
    pass

# TODO: implement
def print_help_message():
    print("\nCamera Controls:")
    print("  W/S - Move forward/backward")
    print("  A/D - Strafe left/right")
    print("  Q/E - Turn camera left/right")
    print("  Z/X - Tilt camera up/down")
    print("  Current Camera:", camera)
    
    print("\nLight Controls:")
    print("  0 - Toggle flashlight")
    print("  1 - Toggle red overhead light")
    print("  2 - Toggle green overhead light")
    print("  3 - Toggle blue overhead light")
    print("  4 - Toggle hanging spotlight (yellow)")
    print("  5 - Toggle desk lamp")
    
    print("\nInteraction Controls:")
    print("  G - Roll the dice")
    print("  T - Toggle hanging light swing")
    
    print("\nSystem Controls:")
    print("  H - Show this help message")
    print("  ESC - Exit program")

#=======================================
# Material Property Functions
#=======================================

# helper method to set the material properties for a given face to match an aluminum surface
#   properties derived from: https://people.eecs.ku.edu/~jrmiller/Courses/672/InClass/3DLighting/MaterialProperties.html
#   specifically the one for silver
# face will be either GL_FRONT, GL_BACK, or GL_FRONT_AND_BACK
def set_aluminum_material(face):
    glMaterialfv(face, GL_AMBIENT, [ 0.19225, 0.19225, 0.19225, 1.0 ])
    glMaterialfv(face, GL_DIFFUSE, [ 0.50754, 0.50754, 0.50754, 1.0 ])
    glMaterialfv(face, GL_SPECULAR, [ 0.508273, 0.508273, 0.508273, 1.0 ])
    glMaterialf(face, GL_SHININESS, 51.2)

# helper method to set the material properties for the checkerboard floor
def set_floor_material(face):
    glMaterialfv(face, GL_AMBIENT, [0.4, 0.4, 0.4, 1.0])
    glMaterialfv(face, GL_DIFFUSE, [0.6, 0.6, 0.6, 1.0])
    glMaterialfv(face, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])
    glMaterialf(face, GL_SHININESS, 0.0)

# helper method to set the material properties for the walls
def set_wall_material(face):
    glMaterialfv(face, GL_AMBIENT, [0.4, 0.4, 0.4, 1.0])
    glMaterialfv(face, GL_DIFFUSE, [0.6, 0.6, 0.6, 1.0])
    glMaterialfv(face, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])
    glMaterialf(face, GL_SHININESS, 0.0)

# helper method to set the material properties for the walls
def set_ceiling_material(face):
    glMaterialfv(face, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glMaterialfv(face, GL_DIFFUSE, [0.6, 0.6, 0.6, 1.0])
    glMaterialfv(face, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialf(face, GL_SHININESS, 10.0)

# helper method to set the material properties for the felt
# TODO: double check values
def set_felt_material(face):
    glMaterialfv(face, GL_AMBIENT, [0.5, 0.5, 0.5, 1.0])
    glMaterialfv(face, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    glMaterialfv(face, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialf(face, GL_SHININESS, 10.0)

# helper method to set the material properties for the table supports
def set_wood_support_material(face):
    pass # TODO: find and implement

#=======================================
# Direct OpenGL Matrix Operation Examples
#=======================================
def printMatrix():
    """
    Prints out the Current ModelView Matrix
    The problem is in how it is stored in the system
    The matrix is in COL-major versus ROW-major so
    indexing is a bit odd.
    """
    m = glGetFloatv(GL_MODELVIEW_MATRIX)
   
    for row in range(4):
        for col in range(4):
            sys.stdout.write('{0:6.3f} '.format(m[col][row]))
        sys.stdout.write('\n')
    

if __name__ == '__main__': main()
