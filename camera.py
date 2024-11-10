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

    def __init__(self, camAngle=45, aspRatio=1, near=0.1, far=1000, eye=Point(0,0,0), lookAngle=0):
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

    def __str__(self):
        """Basic string representation of this Camera"""
        return "Camera Eye at %s with angle (%f)"%(self.eye, self.lookAngle)

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
        lookX = self.eye.x - math.sin(rad)
        lookY = self.eye.y
        lookZ = self.eye.z - math.cos(rad)

        # Place the camera
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
        
        self.eye.x += du * u.dx + dn * n.dx
        self.eye.y += dv
        self.eye.z += du * u.dz + dn * n.dz
    
    def turn(self, angle):
        """ Turn the camera by the given angle"""
        self.lookAngle += angle
        if self.lookAngle < 0: self.lookAngle += 360  # Just to wrap around
        elif self.lookAngle >= 360: self.lookAngle -= 360  # Just to wrap around
        
