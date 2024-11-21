#==============================
# Christian Duncan
# CSC345/645: Computer Graphics
#   Fall 2024
#
# camera.py module
# Description:
#   Defines a simple camera class for navigation
#==============================
import math
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
from utils import *

class Camera:
    """A simple 3D Camera System"""

    def __init__(self, camAngle=45, aspRatio=1, near=0.1, far=1000, eye=Point(0,0,0), lookAngle=0, pitchAngle=0):
        """A constructor for Camera class using initial default values.
           eye is a Point
           lookAngle is the angle that camera is looking in measured in degrees
        """
        self.camAngle = camAngle
        self.aspRatio = aspRatio
        self.near = near
        self.far = far
        self.eye = eye
        self.lookAngle = lookAngle
        self.pitchAngle = pitchAngle

    def __str__(self):
        """Basic string representation of this Camera"""
        return "Camera Eye at %s with angle (%f) and pitch (%f)"%(self.eye, self.lookAngle, self.pitchAngle)

    def setProjection(self):
        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        # Set view to Perspective Proj. (angle, aspect ratio, near/far planes)
        gluPerspective(self.camAngle, self.aspRatio, self.near, self.far)

    def placeCamera(self):
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();

        # Compute the look at point based on the turn angle
        rad = math.radians(self.lookAngle)
        pitch_rad = math.radians(self.pitchAngle)
        lookX = self.eye.x - math.sin(rad) * math.cos(pitch_rad)
        lookY = self.eye.y - math.sin(pitch_rad)
        lookZ = self.eye.z - math.cos(rad) * math.cos(pitch_rad)

        # Place the camera
        # TODO: To fix the 90 degree pitch issues, need to update the up vector as we go
        gluLookAt(self.eye.x, self.eye.y, self.eye.z,  # Camera's origin
                  lookX, lookY, lookZ,                 # Camera's look at point
                  0, 1, 0)                             # Camera is always oriented vertically
        
    def slide(self, du, dv, dn):
        # note: sliding does not support vertical angle adjustments
        #   the perspective is always assumed to be level with the ground
        #   (essentially up is always Vector(Point(0, 1, 0)) for the math)

        # calculating the forward vector n
        rad = math.radians(self.lookAngle)
        lookDX = math.sin(rad)
        lookDZ = math.cos(rad)

        # find the u vector (rotated x-axis) using cross product of
        #   new n vector (rotated z-axis) and v vector (up vector / y-axis)
        n = Vector(Point(lookDX, 0, lookDZ))
        v = Vector(Point(0, 1, 0))
        u = n.cross(v)
        u.normalize()
        
        new_x = self.eye.x + du * u.dx + dn * n.dx
        new_y = self.eye.y + dv
        new_z = self.eye.z + du * u.dz + dn * n.dz

        # TODO: find a more efficient way to do bounds checking
        # forcing the camera in the room boundaries
        new_x = min(new_x, self.max_room_bound_x - 1)
        new_x = max(new_x, self.min_room_bound_x + 1)
        new_z = min(new_z, self.max_room_bound_z - 1)
        new_z = max(new_z, self.min_room_bound_z + 1)

        # TODO: find a more efficient way to do bounds checking
        # force the camera off of the walls of objects
        # TODO: fix issue causing camera to get stuck in objects
        for ((min_obj_bound_x, min_obj_bound_z), (max_obj_bound_x, max_obj_bound_z)) in self.obstacle_bounding_boxes:
            if new_x <= max_obj_bound_x + 1 and new_x >= min_obj_bound_x - 1 and new_z <= max_obj_bound_z + 1 and new_z >= min_obj_bound_z - 1:
                move_direction_x = new_x - self.eye.x
                move_direction_z = new_z - self.eye.y

                # drawing the line between old position and new position
                # TODO: see textbook and phone for calculations

        self.eye.x = new_x
        self.eye.y = new_y
        self.eye.z = new_z
    
    def turn(self, angle):
        """ Turn the camera by the given angle"""
        self.lookAngle += angle
        if self.lookAngle < 0: self.lookAngle += 360  # Just to wrap around
        elif self.lookAngle >= 360: self.lookAngle -= 360  # Just to wrap around

    def tilt(self, angle):
        """ Tilt the camera by the given angle. Modifies the pitch (up/down rotation). """
        resultant_angle = self.pitchAngle + angle
        
        # TODO: if updating up axis, can support 90 degree angles
        # clamping the angle between -90 and 90
        resultant_angle = min(89, resultant_angle)
        resultant_angle = max(-89, resultant_angle)

        self.pitchAngle = resultant_angle
        
    def add_obstacle_bounding_boxes(self, boxes):
        """ Load all object bounding boxes for collision detection. """
        self.obstacle_bounding_boxes = boxes

    def add_room_boundaries(self, bounds):
        """ Load room bounding bounds for collision detection. """
        ((self.min_room_bound_x, self.min_room_bound_z), (self.max_room_bound_x, self.max_room_bound_z)) = bounds