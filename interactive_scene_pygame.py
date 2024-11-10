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

# These parameters define the camera's lens shape
CAM_NEAR = 0.01
CAM_FAR = 1000.0
CAM_ANGLE = 60.0

# These parameters define simple animation properties
FPS = 60.0
DELAY = int(1000.0 / FPS + 0.5)

# Light state machine
class Light:
    # constructor
    def __init__(self, gl_light_name, position=Point(0, 10, 0), enabled=False, ambient=[1.0, 1.0, 1.0, 1.0], diffuse=[1.0, 1.0, 1.0, 1.0], specular=[1.0, 1.0, 1.0, 1.0], is_point=True):
        self.enabled = enabled
        self.is_point = is_point
        self.gl_light_name = gl_light_name

        # copy arrays / objects to prevent aliasing
        self.position = copy.deepcopy(position)
        self.ambient = copy.deepcopy(ambient)
        self.diffuse = copy.deepcopy(diffuse)
        self.specular = copy.deepcopy(specular)
        
    # used to get the position as 4 value list for glLightfv function
    # constructs the list using the position Point and the is_point value to determine if point light or directional light
    def get_position_list(self):
        return [ self.position.x, self.position.y, self.position.z, 1.0 if self.is_point else 0.0 ]

# first light is red, second is green, third is blue
lights = [ 
    Light(
        GL_LIGHT0, 
        ambient=[1.0, 0.0, 0.0, 1.0],
        diffuse=[1.0, 0.0, 0.0, 1.0],
        specular=[1.0, 0.0, 0.0, 1.0]
    ), 
    Light(
        GL_LIGHT1,
        ambient=[0.0, 1.0, 0.0, 1.0],
        diffuse=[0.0, 1.0, 0.0, 1.0],
        specular=[0.0, 1.0, 0.0, 1.0]
    ), 
    Light(
        GL_LIGHT2,
        ambient=[0.0, 0.0, 1.0, 1.0],
        diffuse=[0.0, 0.0, 1.0, 1.0],
        specular=[0.0, 0.0, 1.0, 1.0]
    ) 
]
active_light = -1

# Global (Module) Variables

# Window data
window_dimensions = (1000, 800)
name = b'Project 2'
animate = False
viewAngle = 0

def main():
    init()
    global camera
    camera = Camera(CAM_ANGLE, window_dimensions[0]/window_dimensions[1], CAM_NEAR, CAM_FAR)
    camera.eye = Point(0, 5, 30)  # Position the camera
    camera.look = Point(0, 0, 0)  # Look at the center of the scene
    camera.up = Vector(Point(0, 1, 0))  # Set up vector

    # Enters the main loop.   
    # Displays the window and starts listening for events.
    main_loop()
    return

# Any initialization material to do...
def init():
    global tube, clock, running

    # pygame setup
    pygame.init()
    pygame.key.set_repeat(300, 50)
    pygame.display.set_mode(window_dimensions, pygame.DOUBLEBUF|pygame.OPENGL)
    clock = pygame.time.Clock()
    running = True

    tube = gluNewQuadric()
    gluQuadricDrawStyle(tube, GLU_LINE)

    # Set up lighting and depth-test
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
    glClear(GL_COLOR_BUFFER_BIT)


    # And draw the "Scene"
    glColor3f(1.0, 1.0, 1.0)
    draw_scene()

    # And show the scene
    glFlush()

# Advance the scene one frame
def advance():
    # put any animation stuff in here
    pass

# Function used to handle any key events
# event: The keyboard event that happened
def keyboard(event):
    global running, animate, viewAngle, spinAngle, active_light
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
    elif key == ord('z'):
        # Turn camera left (counter-clockwise)
        camera.turn(1)
    elif key == ord('x'):
        # Turn camera right (clockwise)
        camera.turn(-1)
    elif key == ord('q'):
        # Go up
        camera.slide(0,1,0)
    elif key == ord('e'):
        # Go down
        camera.slide(0,-1,0)
    elif key == pygame.K_LEFT:
        # turn world left
        viewAngle += 1
    elif key == pygame.K_RIGHT:
        # turn world right
        viewAngle -= 1
    elif key == ord('j'):
        # Move light left (global coordinates)
        if active_light != -1:
            lights[active_light].position.x -= 0.1
    elif key == ord('l'):
        # Move light right (global coordinates)
        if active_light != -1:
            lights[active_light].position.x += 0.1
    elif key == ord('i'):
        # Move light forward (global coordinates)
        if active_light != -1:
            lights[active_light].position.z -= 0.1
    elif key == ord('k'):
        # Move light backward (global coordinates)
        if active_light != -1:
            lights[active_light].position.z += 0.1
    elif key == ord('u'):
        # Move light up (global coordinates)
        if active_light != -1:
            lights[active_light].position.y += 0.1
    elif key == ord('o'):
        # Move light down (global coordinates)
        if active_light != -1:
            lights[active_light].position.y -= 0.1
    elif key == ord('p'):
        # Print values of light
        print('Light location: {0}'.format(
            lights[active_light].position if (active_light != -1) else 'N/A'
        ))
    elif key == ord('0'):
        # Select light 0
        if active_light == 0:
            active_light = -1
            print("No light selected.")
        else:
            active_light = 0
            print("Select light 0.")
    elif key == ord('1'):
        # Select light 1
        if active_light == 1:
            active_light = -1
            print("No light selected.")
        else:
            active_light = 1
            print("Select light 1.")
    elif key == ord('2'):
        # Select light 2
        if active_light == 2:
            active_light = -1
            print("No light selected.")
        else:
            active_light = 2
            print("Select light 2.")
    elif key == ord(' '):
        # Enable selected light
        if active_light != -1:
            lights[active_light].enabled = not lights[active_light].enabled


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
    glRotate(viewAngle, 0, 1, 0)
    place_lights()
    draw() 

def place_lights():
    """Set up the main lights."""
    global lights

    amb = [ 0, 0, 0, 1.0 ]  # No ambient light initially
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
            # Note that light.position is not valid for GL_POSITION, as it is a point and not a list
            glLightfv(light.gl_light_name, GL_POSITION, light.get_position_list())
            glLightfv(light.gl_light_name, GL_AMBIENT, light.ambient)
            glLightfv(light.gl_light_name, GL_DIFFUSE, light.diffuse)
            glLightfv(light.gl_light_name, GL_SPECULAR, light.specular)

            glEnable(light.gl_light_name)

            # This part draws a SELF-COLORED sphere (in spot where light is!)
            glPushMatrix()
            glTranslatef(light.position.x, light.position.y, light.position.z)
            glDisable(GL_LIGHTING)
            glColor3f(
                1 if index == 0 else 0,
                1 if index == 1 else 0,
                1 if index == 2 else 0
            ) # Colored sphere
            gluSphere(ball, 0.2, 100, 100)
            glEnable(GL_LIGHTING)
            glPopMatrix()

def draw():
    glPushMatrix()

    # TODO: add function calls here

    glPopMatrix()

#=======================================
# Scene-drawing functions
#=======================================

def draw_floor():
    pass

def draw_walls():
    pass

def draw_ceiling():
    pass

def draw_side_table(x, y, z):
    pass

def draw_desk_lamp(x, y, z):
    pass

def draw_die(x, y, z):
    # will likely need to call more than once
    # may need additional parameters to connect multiple dice
    pass

def draw_pool_table(x, y, z):
    pass

def draw_billiard_ball(x, y, z, num):
    pass

def draw_cue_ball(x, y, z):
    pass

# TODO: uncertain if lights should have functions or be included in place_lights instead
def draw_hanging_spotlight(x, y, z):
    # may need additional parameters for swinging
    pass

def draw_wall_picture(x, y, z):
    pass

def print_help_message():
    pass

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
