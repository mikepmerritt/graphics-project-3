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
from PIL import Image
import random

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

# scene-specific state information
dice_animating = False
dice_rotation = [0, 0, 0] 
dice_rotation2 = [0, 0, 0]

# These parameters define simple animation properties
FPS = 60.0
DELAY = int(1000.0 / FPS + 0.5)

# Light state machine
class Light:
    # constructor
    def __init__(
        self, 
        gl_light_name,                      # the light to be enabled (ex: GL_LIGHT0)
        enabled=False,                      # boolean for if the light is on
        position=Point(0, 10, 0),           # position of the light as a Point
        ambient=[1.0, 1.0, 1.0, 1.0],       # ambient lighting values
        diffuse=[1.0, 1.0, 1.0, 1.0],       # diffuse lighting values
        specular=[1.0, 1.0, 1.0, 1.0],      # specular lighting values
        direction=[0.0, -1.0, 0.0, 0.0],    # direction vector for spot lights
        display_ball=True,                  # flag to draw a colored sphere at the point
        is_point_light=False,               # flag to set light type as point
        is_spot_light=False,                # flag to set light type as spot
        is_directional_light=False,         # flag to set light type as directional
        constant_attenuation=1,             # constant attenuation for distance
        linear_attenuation=0,               # linear attenuation for distance
        quadratic_attenuation=0,            # quadratic attenuation for distance
        spot_cutoff=180.0,                  # how wide the spot light will be
        spot_exponent=0.0                   # how focused the spot light will be
    ):
        # light display properties
        self.gl_light_name = gl_light_name
        self.enabled = enabled
        self.display_ball = display_ball

        # types of lights
        self.is_point_light = is_point_light,
        self.is_spot_light = is_spot_light,
        self.is_directional_light = is_directional_light

        # special light properties
        self.constant_attenuation = constant_attenuation
        self.linear_attenuation = linear_attenuation
        self.quadratic_attenuation = quadratic_attenuation
        self.spot_cutoff = spot_cutoff
        self.spot_exponent = spot_exponent

        # copy arrays / objects to prevent aliasing
        self.position = copy.deepcopy(position)
        self.ambient = copy.deepcopy(ambient)
        self.diffuse = copy.deepcopy(diffuse)
        self.specular = copy.deepcopy(specular)
        self.direction = copy.deepcopy(direction)

        # print an warning if the light was not configured with type
        if not is_point_light and not is_spot_light and not is_directional_light:
            print(f'Warning: Light {gl_light_name} was loaded without a type specified.')
        
    # used to get the position as 4 value list for glLightfv function
    # constructs the list using the position Point and the is_point_light and is_directional_light value to determine if point light or directional light
    def get_position_list(self):
        return [ self.position.x, self.position.y, self.position.z, 1.0 if self.is_point_light and not self.is_directional_light else 0.0 ]

# TODO: order is flashlight, overhead red, overhead green, overhead blue, hanging light (50% yellow) + flicker, desk lamp (75% white)
lights = [ 
    # Debug light in the center of the room with pure white, used to test textures and whatnot
    # TODO: replace with flashlight position
    Light(
        GL_LIGHT0, 
        enabled=True,
        position=copy.deepcopy(start_camera_position), # flashlight starts where player is
        ambient=[1.0, 1.0, 1.0, 1.0],  
        diffuse=[1.0, 1.0, 1.0, 1.0],
        specular=[1.0, 1.0, 1.0, 1.0],
        direction=[0.0, 0.0, -1.0, 0.0],
        display_ball=True,
        is_spot_light=True,
        constant_attenuation=100,
        linear_attenuation=0.1,
        quadratic_attenuation=0,
        spot_cutoff=30,
        spot_exponent=15
    ),
    # Red light in far-left quarter of room
    Light(
        GL_LIGHT1, 
        enabled=False,
        position=Point(20, 40, -20),
        ambient=[1.0, 0.0, 0.0, 1.0],  
        diffuse=[1.0, 0.0, 0.0, 1.0],
        specular=[1.0, 0.0, 0.0, 1.0],
        display_ball=True,
        is_point_light=True # TODO: determine if this is the correct type
    ),
    # Green light in left-center area of room
    Light(
        GL_LIGHT2, 
        enabled=False,
        position=Point(-20, 40, 0),
        ambient=[0.0, 1.0, 0.0, 1.0],  
        diffuse=[0.0, 1.0, 0.0, 1.0],
        specular=[0.0, 1.0, 0.0, 1.0],
        display_ball=True,
        is_point_light=True # TODO: determine if this is the correct type
    ),
    # Blue light in close-right quarter of room
    Light(
        GL_LIGHT3, 
        enabled=False,
        position=Point(20, 40, 20),
        ambient=[0.0, 0.0, 1.0, 1.0],  
        diffuse=[0.0, 0.0, 1.0, 1.0],
        specular=[0.0, 0.0, 1.0, 1.0],
        display_ball=True,
        is_point_light=True # TODO: determine if this is the correct type
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
        spot_cutoff=90.0,
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

# Global (Module) Variables

# Window data
window_dimensions = (1000, 800)
name = b'Project 2'
animate = False

def main():
    init()
    global camera
    camera = Camera(CAM_ANGLE, window_dimensions[0]/window_dimensions[1], CAM_NEAR, CAM_FAR)
    camera.eye = Point(0, 15, 40)  # Position the camera
    camera.look = Point(0, 0, 0)  # Look at the center of the scene
    camera.up = Vector(Point(0, 1, 0))  # Set up vector

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
    global dice_texture_1, dice_texture_2, dice_texture_3, dice_texture_4, dice_texture_5, dice_texture_6, floor_texture, wall_texture, table_support_texture, table_top_texture, lamp_support_texture, lamp_head_texture, aluminum_light_texture, aluminum_dark_texture, felt_texture

    # pygame setup
    pygame.init()
    pygame.key.set_repeat(300, 50)
    pygame.display.set_mode(window_dimensions, pygame.DOUBLEBUF|pygame.OPENGL)
    clock = pygame.time.Clock()
    running = True

    # loading / generating textures
    wall_texture = load_texture("wall.jpg", 512) 
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

def main_loop():
    global running, clock, animate
    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                keyboard(event)

        if animate:
            # Advance to the next frame
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
    # put any animation stuff in here
     global dice_animating, dice_rotation, dice_rotation2, animate
     if dice_animating:
        dice_rotation[0] += 5  
        dice_rotation[1] += 8  
        dice_rotation[2] += 3  
        
        dice_rotation2[0] += 8  
        dice_rotation2[1] += 5
        dice_rotation2[2] += 6
        
        if dice_rotation[0] >= 540: 
            dice_animating = False
            animate = False
            dice_rotation = [random.randint(0,3) * 90, random.randint(0,3) * 90, random.randint(0,3) * 90]
            dice_rotation2 = [random.randint(0,3) * 90, random.randint(0,3) * 90, random.randint(0,3) * 90]

# Function used to handle any key events
# event: The keyboard event that happened
def keyboard(event):
    global running, animate, dice_animating
    key = event.key # "ASCII" value of the key pressed
    if key == 27:  # ASCII code 27 = ESC-key
        running = False
    elif key == ord(' '):
        animate = not animate
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
        lights[4].enabled = not lights[4].enabled
    elif key == ord('5'):
        # Toggle activation of light 5
        lights[5].enabled = not lights[5].enabled
    elif key == ord('6'):
        if not dice_animating:
            dice_animating = True
            animate = True

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
    draw_floor()
    draw_walls()
    draw_ceiling()
    draw_side_table(-35, 0, -34)
    draw_desk_lamp(-32, 8, -36)
    draw_dice(-37, 8.22, -34)
    draw_hanging_spotlight(0, 40, 0)
    draw_pool_table(0, 5, 0)
    # ball bounds are x: [-7.25, 7.25] z: [-2.75, 2.75]
    draw_cue_ball(0, 10.25, 0) 
    glPopMatrix()
    
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

#=======================================
# Scene-drawing functions
#=======================================

def draw_floor():
    glPushMatrix()
    
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.4, 0.4, 0.4, 1.0])  
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.6, 0.6, 0.6, 1.0])   
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])  
    glMaterialf(GL_FRONT, GL_SHININESS, 0.0)     
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, floor_texture)
    
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)  
    glTexCoord2f(0, 0)
    glVertex3f(-40, 0, -40)  
    glTexCoord2f(8, 0)      
    glVertex3f(40, 0, -40)   
    glTexCoord2f(8, 8)      
    glVertex3f(40, 0, 40)    
    glTexCoord2f(0, 8)     
    glVertex3f(-40, 0, 40)   
    glEnd()
    
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()
    
def draw_wall(start_x, start_z, end_x, end_z, height, normal):
    glBegin(GL_QUADS)
    glNormal3f(*normal)  
    glTexCoord2f(0, 0)
    glVertex3f(start_x, 0, start_z)      
    glTexCoord2f(4, 0)
    glVertex3f(end_x, 0, end_z)          
    glTexCoord2f(4, 2)
    glVertex3f(end_x, height, end_z)      
    glTexCoord2f(0, 2)
    glVertex3f(start_x, height, start_z)  
    glEnd()

def apply_wall_material_and_texture():
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.4, 0.4, 0.4, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.6, 0.6, 0.6, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 0.0)

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, wall_texture)
    
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

def draw_walls():
    glPushMatrix()
    apply_wall_material_and_texture()
    
    height = 40
    draw_wall(-40, -40, 40, -40, height, (0, 0, 1))    
    draw_wall(40, -40, 40, 40, height, (-1, 0, 0))     
    draw_wall(-40, 40, -40, -40, height, (1, 0, 0))   
    draw_wall(40, 40, -40, 40, height, (0, 0, -1))   

    glDisable(GL_TEXTURE_2D)
    glPopMatrix()

def draw_ceiling():
    glPushMatrix()
    
    apply_wall_material_and_texture()
    glBegin(GL_QUADS)
    glNormal3f(0, -1, 0)
    glTexCoord2f(0, 0)
    glVertex3f(-40, 40, -40)
    glTexCoord2f(4, 0)
    glVertex3f(40, 40, -40)
    glTexCoord2f(4, 4)
    glVertex3f(40, 40, 40)
    glTexCoord2f(0, 4)
    glVertex3f(-40, 40, 40)
    glEnd()

    glDisable(GL_TEXTURE_2D)
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

    # middles (3 x 2 x 3) # floor should be at midpoint level, hole extends down

    # x-aligned wood segments (5 x 2 x 1)
    draw_rect(x - 4, y + 4.75, z - 4.5, 5, 1.5, 1, 10, 4, 2, table_support_texture)
    draw_rect(x + 4, y + 4.75, z - 4.5, 5, 1.5, 1, 10, 4, 2, table_support_texture)
    draw_rect(x - 4, y + 4.75, z + 4.5, 5, 1.5, 1, 10, 4, 2, table_support_texture)
    draw_rect(x + 4, y + 4.75, z + 4.5, 5, 1.5, 1, 10, 4, 2, table_support_texture)

    # x-aligned felt segments (5 x 2 x 1)
    draw_rect(x - 4, y + 4.75, z - 3.5, 5, 1.5, 1, 10, 4, 2, felt_texture)
    draw_rect(x + 4, y + 4.75, z - 3.5, 5, 1.5, 1, 10, 4, 2, felt_texture)
    draw_rect(x - 4, y + 4.75, z + 3.5, 5, 1.5, 1, 10, 4, 2, felt_texture)
    draw_rect(x + 4, y + 4.75, z + 3.5, 5, 1.5, 1, 10, 4, 2, felt_texture)

    # z-aligned wood segments (1 x 2 x 4)
    draw_rect(x - 9, y + 4.75, z, 1, 1.5, 4, 2, 4, 8, table_support_texture)
    draw_rect(x + 9, y + 4.75, z, 1, 1.5, 4, 2, 4, 8, table_support_texture)

    # z-aligned felt segments (1 x 2 x 4)
    draw_rect(x - 8, y + 4.75, z, 1, 1.5, 4, 2, 4, 8, felt_texture)
    draw_rect(x + 8, y + 4.75, z, 1, 1.5, 4, 2, 4, 8, felt_texture)

    # felt play area (15 x 1 x 6)
    draw_rect(x, y + 4.5, z, 15, 1, 6, 15, 1, 6, felt_texture)

    # wood bottom middle (19 x 1 x 6)
    draw_rect(x, y + 3.5, z, 19, 1, 10, 19, 1, 10, table_support_texture)

    # wood legs (3 x 8 x 3)
    draw_rect(x - 6, y, z - 2.5, 3, 8, 3, 3, 8, 3, table_support_texture)
    draw_rect(x + 6, y, z - 2.5, 3, 8, 3, 3, 8, 3, table_support_texture)
    draw_rect(x - 6, y, z + 2.5, 3, 8, 3, 3, 8, 3, table_support_texture)
    draw_rect(x + 6, y, z + 2.5, 3, 8, 3, 3, 8, 3, table_support_texture)

def draw_plane(x_size, y_size, x_slices, y_slices, texture):
    """ Draw a textured plane of the specified dimension.
        The plane is a unit square with lower left corner at origin.
    """
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE) # try GL_DECAL/GL_REPLACE/GL_MODULATE
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_FASTEST)           # try GL_NICEST/GL_FASTEST
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)  # try GL_CLAMP/GL_REPEAT/GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST) # try GL_NEAREST/GL_LINEAR
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    # set up felt to be brighter
    if texture == felt_texture:
        glMaterialfv(GL_FRONT, GL_AMBIENT, [0.5, 0.5, 0.5, 1.0])
        glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 10.0)

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
            glTexCoord2f(cx, y+dy)
            glVertex3f(cx, y+dy, 0)
            glTexCoord2f(cx, y)
            glVertex3f(cx, y, 0)
            cx += dx
        glTexCoord2f(x_size, y+dy)
        glVertex3f(x_size, y+dy, 0)
        glTexCoord2f(x_size, y)
        glVertex3f(x_size, y, 0)
        glEnd()
        y += dy
   
    glDisable(GL_TEXTURE_2D)

def draw_rect(x, y, z, x_size, y_size, z_size, x_slices, y_slices, z_slices, texture_name):
    """ Draw a rectangle centered around (x, y, z) with size (x_size, y_size, z_size)."""  
    # move to cube location
    glPushMatrix()
    glTranslate(x, y, z)  

    # Draw side 1 (+z)
    glPushMatrix()
    glTranslate(-x_size/2, -y_size/2, z_size/2)
    draw_plane(x_size, y_size, x_slices, y_slices, texture_name)
    glPopMatrix()

    # Draw side 2 (-z)
    glPushMatrix()
    glTranslate(x_size/2, -y_size/2, -z_size/2)
    glRotated(180, 0, 1, 0)
    draw_plane(x_size, y_size, x_slices, y_slices, texture_name)
    glPopMatrix()

    # Draw side 3 (-x)
    glPushMatrix()
    glTranslate(-x_size/2, -y_size/2, -z_size/2)
    glRotatef(-90, 0, 1, 0)
    draw_plane(z_size, y_size, z_slices, y_slices, texture_name)
    glPopMatrix()

    # Draw side 4 (+x)
    glPushMatrix()
    glTranslatef(x_size/2, -y_size/2, z_size/2)
    glRotatef(90, 0, 1, 0)
    draw_plane(z_size, y_size, z_slices, y_slices, texture_name)
    glPopMatrix()

    # Draw side 5 (-y)
    glPushMatrix()
    glTranslatef(-x_size/2, -y_size/2, -z_size/2)
    glRotatef(90, 1, 0, 0)
    draw_plane(x_size, z_size, x_slices, z_slices, texture_name)
    glPopMatrix()

    # Draw side 6 (+y)
    glPushMatrix()
    glTranslatef(-x_size/2, y_size/2, z_size/2)
    glRotatef(-90, 1, 0, 0)
    draw_plane(x_size, z_size, x_slices, z_slices, texture_name)
    glPopMatrix()

    # return
    glPopMatrix()


# TODO: implement
def draw_billiard_ball(x, y, z, texture):
    pass

# TODO: implement
def draw_cue_ball(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    gluSphere(ball, 0.25, 16, 16)
    glPopMatrix()

# TODO: implement swinging
def draw_hanging_spotlight(x, y, z):
    # may need additional parameters for swinging
    glPushMatrix()
    glTranslatef(x, y, z)

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
    set_aluminum(GL_FRONT_AND_BACK)
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
    set_aluminum(GL_FRONT_AND_BACK)
    gluDisk(disk, 0, upper_lamp_radius, 30, 10)
    glRotate(90, 1, 0, 0)

    # drawing the hanging light shade
    glTranslatef(0, -lamp_height, 0)
    glRotatef(-90, 1, 0, 0)
    set_aluminum(GL_FRONT_AND_BACK)
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
    print(camera)
    pass

#=======================================
# Material Property Functions
#=======================================

# helper method to set the material properties for a given face to match an aluminum surface
#   properties derived from: https://people.eecs.ku.edu/~jrmiller/Courses/672/InClass/3DLighting/MaterialProperties.html
#   specifically the one for silver
# face will be either GL_FRONT, GL_BACK, or GL_FRONT_AND_BACK
def set_aluminum(face):
    ambient = [ 0.19225, 0.19225, 0.19225, 1.0 ]
    diffuse = [ 0.50754, 0.50754, 0.50754, 1.0 ]
    specular = [ 0.508273, 0.508273, 0.508273, 1.0 ]
    shininess = 51.2
    glMaterialfv(face, GL_AMBIENT, ambient)
    glMaterialfv(face, GL_DIFFUSE, diffuse)
    glMaterialfv(face, GL_SPECULAR, specular)
    glMaterialf(face, GL_SHININESS, shininess)

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
