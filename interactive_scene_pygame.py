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
floor_texture = None
ball = None
wall_texture = None
table_top_texture = None 
table_support_texture = None
lamp_support_texture = None
lamp_head_texture = None
dice_animating = False
dice_rotation = [0, 0, 0] 
dice_rotation2 = [0, 0, 0]
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

# first light is white, second is green, third is blue
lights = [ 
    Light(
        GL_LIGHT0, 
        position=Point(0, 20, 0),
        ambient=[1.0, 1.0, 1.0, 1.0],  
        diffuse=[1.0, 1.0, 1.0, 1.0],
        specular=[1.0, 1.0, 1.0, 1.0] 
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
    camera.eye = Point(0, 15, 40)  # Position the camera
    camera.look = Point(0, 0, 0)  # Look at the center of the scene
    camera.up = Vector(Point(0, 1, 0))  # Set up vector

    # Enters the main loop.   
    # Displays the window and starts listening for events.
    main_loop()
    return

# Any initialization material to do...
def init():
    global tube, clock, running, floor_texture, wall_texture, table_support_texture, table_top_texture, lamp_support_texture, lamp_head_texture, ball

    # pygame setup
    pygame.init()
    pygame.key.set_repeat(300, 50)
    pygame.display.set_mode(window_dimensions, pygame.DOUBLEBUF|pygame.OPENGL)
    clock = pygame.time.Clock()
    running = True
    ball = gluNewQuadric()
    lights[0].enabled = True
    wall_texture = load_texture("wall.jpg") 
    table_top_texture = load_texture("table_top.jpg")
    table_support_texture = load_texture("table_support.jpg")
    lamp_support_texture = load_texture("lamp_support.jpg")
    lamp_head_texture = load_texture("lamp_head.jpg")
    tube = gluNewQuadric()
    gluQuadricDrawStyle(tube, GLU_FILL)
    gluQuadricTexture(tube, GL_TRUE)
    gluQuadricNormals(tube, GLU_SMOOTH) 
    floor_texture = generate_checkerboard_texture(4, 4, 1, [[139, 69, 19, 255], [205, 133, 63, 255]]) 
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
    global running, animate, viewAngle, spinAngle, active_light, dice_animating
    key = event.key # "ASCII" value of the key pressed
    if key == 27:  # ASCII code 27 = ESC-key
        running = False
    elif key == ord(' '):
        if active_light != -1:
            lights[active_light].enabled = not lights[active_light].enabled
        else:
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
    elif key == ord('6'):
        if not dice_animating:
            dice_animating = True
            animate = True

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
    draw_floor()
    draw_walls()
    draw_ceiling()
    draw_side_table(-35, 0, -34)
    draw_desk_lamp(-32, 8, -36)
    draw_dice(-37, 8.22, -34)
    glPopMatrix()
    
def load_texture(file_name):
    im = Image.open(file_name)
    dim = 512  
    size = (0,0,dim,dim)
    texture = im.crop(size).tobytes("raw")

    texture_name = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_name)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, dim, dim, 0, GL_RGB,
                 GL_UNSIGNED_BYTE, texture)
    return texture_name

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
    gluDisk(tube, 0, radius, 32, 1)  
    glTranslatef(0, 0, base_height)
    gluDisk(tube, 0, radius, 32, 1)
    
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
    gluDisk(tube, 0, radius, 32, 1)
    glTranslatef(0, 0, height)
    gluDisk(tube, 0, radius, 32, 1)
    
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

def draw_dice_face_dots(face_number):
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0, 0, 0, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0, 0, 0, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 32.0)
    
    dot_radius = 0.02 
    offset = 0.1     

    if face_number == 1:
        glPushMatrix()
        glTranslatef(0, 0, 0)
        gluSphere(ball, dot_radius, 16, 16)
        glPopMatrix()
        
    elif face_number == 2:
        glPushMatrix()
        glTranslatef(offset, offset, 0)
        gluSphere(ball, dot_radius, 16, 16)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(-offset, -offset, 0)
        gluSphere(ball, dot_radius, 16, 16)
        glPopMatrix()
        
    elif face_number == 3:
        glPushMatrix()
        glTranslatef(0, 0, 0)
        gluSphere(ball, dot_radius, 16, 16)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(offset, offset, 0)
        gluSphere(ball, dot_radius, 16, 16)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(-offset, -offset, 0)
        gluSphere(ball, dot_radius, 16, 16)
        glPopMatrix()
        
    elif face_number == 4:
        for x in [offset, -offset]:
            for y in [offset, -offset]:
                glPushMatrix()
                glTranslatef(x, y, 0)
                gluSphere(ball, dot_radius, 16, 16)
                glPopMatrix()
                
    elif face_number == 5:
        glPushMatrix()
        glTranslatef(0, 0, 0)
        gluSphere(ball, dot_radius, 16, 16)
        glPopMatrix()
        
        for x in [offset, -offset]:
            for y in [offset, -offset]:
                glPushMatrix()
                glTranslatef(x, y, 0)
                gluSphere(ball, dot_radius, 16, 16)
                glPopMatrix()
                
    elif face_number == 6:
        for x in [offset, -offset]:
            for y in [offset, 0, -offset]:
                glPushMatrix()
                glTranslatef(x, y, 0)
                gluSphere(ball, dot_radius, 16, 16)
                glPopMatrix()

def draw_single_dice(x, y, z, size, rotations=[0,0,0]):
    glPushMatrix()
    glTranslatef(x, y, z)   
    glRotatef(rotations[0], 1, 0, 0)
    glRotatef(rotations[1], 0, 1, 0)
    glRotatef(rotations[2], 0, 0, 1) 
    
    glMaterialfv(GL_FRONT, GL_AMBIENT, [0.2, 0, 0, 1.0])
    glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.8, 0, 0, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [0.3, 0.3, 0.3, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 32.0)
    
    glBegin(GL_QUADS)
    
    glNormal3f(0, 0, 1)
    glVertex3f(-size, -size, size)
    glVertex3f(size, -size, size)
    glVertex3f(size, size, size)
    glVertex3f(-size, size, size)
    
    glNormal3f(0, 0, -1)
    glVertex3f(-size, -size, -size)
    glVertex3f(-size, size, -size)
    glVertex3f(size, size, -size)
    glVertex3f(size, -size, -size)
    
    glNormal3f(1, 0, 0)
    glVertex3f(size, -size, -size)
    glVertex3f(size, size, -size)
    glVertex3f(size, size, size)
    glVertex3f(size, -size, size)
    
    glNormal3f(-1, 0, 0)
    glVertex3f(-size, -size, -size)
    glVertex3f(-size, -size, size)
    glVertex3f(-size, size, size)
    glVertex3f(-size, size, -size)
    
    glNormal3f(0, 1, 0)
    glVertex3f(-size, size, -size)
    glVertex3f(-size, size, size)
    glVertex3f(size, size, size)
    glVertex3f(size, size, -size)
    
    glNormal3f(0, -1, 0)
    glVertex3f(-size, -size, -size)
    glVertex3f(size, -size, -size)
    glVertex3f(size, -size, size)
    glVertex3f(-size, -size, size)
    
    glEnd()    
    glPushMatrix()
    glTranslatef(0, 0, size + 0.001)  
    draw_dice_face_dots(1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, 0, -(size + 0.001))  
    draw_dice_face_dots(6)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(size + 0.001, 0, 0)  
    glRotatef(90, 0, 1, 0)
    draw_dice_face_dots(2)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-(size + 0.001), 0, 0)  
    glRotatef(-90, 0, 1, 0)
    draw_dice_face_dots(5)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, size + 0.001, 0)  
    glRotatef(-90, 1, 0, 0)
    draw_dice_face_dots(3)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, -(size + 0.001), 0)  
    glRotatef(90, 1, 0, 0)
    draw_dice_face_dots(4)
    glPopMatrix()
    
    glPopMatrix()

def draw_dice(x, y, z):
    draw_single_dice(x, y, z, 0.2, dice_rotation)
    draw_single_dice(x + 1.2, y, z + 0.3, 0.2, dice_rotation2)

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
