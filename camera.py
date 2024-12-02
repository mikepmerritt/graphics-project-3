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

# constants, the meaning of each bit in a region code for clipping
left_bit_code = 0b0001      # farther in the negative x direction
right_bit_code = 0b0010     # farther in the positive x direction
behind_bit_code = 0b0100    # farther in the negative z direction
ahead_bit_code = 0b1000     # farther in the positive z direction

# helper function to take a point and boundary, and return the 4 bit 
#   region code for where that point is relative to the boundary
#   if a code is 0000, that means the point is in the boundary
#   otherwise, the point is somewhere outside based on the constants above
# the inside flag is used to determine if being on the edge is allowed
#   for inside, being on the edge counts as inside center region
#   for outside, being on the edge counts as outside the center region
#   this is necessary to keep the player outside of obstacles but in bounds
def generate_region_code(x, z, boundary, inside):
    code = 0b0000
    # if inside bounds, being on the edge counts as being in the center
    #   this makes it so that if the target point is inside the room and the
    #   start location is on the edge, you are not crossing the shape
    if inside:
        if x < boundary[0][0]:
            code |= left_bit_code
        if x > boundary[1][0]:
            code |= right_bit_code
        if z < boundary[0][1]:
            code |= behind_bit_code
        if z > boundary[1][1]:
            code |= ahead_bit_code
    # if outside bounds, being on the edge counts as not being in the center
    #   this makes it so that if the target point is inside an object and the
    #   start location is on the edge, you are seen as crossing into the shape
    else:
        if x <= boundary[0][0]:
            code |= left_bit_code
        if x >= boundary[1][0]:
            code |= right_bit_code
        if z <= boundary[0][1]:
            code |= behind_bit_code
        if z >= boundary[1][1]:
            code |= ahead_bit_code
    return code

# helper function to perform the Cohen-Sutherland clipping
#   if intersection is found, returns (True, x, z) where (x, z) is the intersection 
#   otherwise returns (False, end_x, end_z)
def line_clip(start_x, start_z, end_x, end_z, boundary, inside):
    start_code = generate_region_code(start_x, start_z, boundary, inside)
    end_code = generate_region_code(end_x, end_z, boundary, inside)

    # check if both points are inside the boundary
    if not (start_code | end_code):
        return (False, end_x, end_z) # return the endpoint, move is valid
    else:
        # check if both points are outside the boundary
        if start_code & end_code:
            return (False, end_x, end_z) # return the endpoint, move is valid
        # otherwise, one point is outside and the other is inside
        # this makes the move invalid, so the endpoint will be the intersection
        else:
            # NOTE: point 1 is outside and point 2 is inside
            # check to see if the start point is the one inside the boundary
            if not start_code:
                p1_x = end_x; p1_z = end_z; p2_x = start_x; p2_z = start_z
                c1 = end_code; c2 = start_code
            else:
                p1_x = start_x; p1_z = start_z; p2_x = end_x; p2_z = end_z
                c1 = start_code; c2 = end_code

            # use slope (when defined) to find the intersection
            if p1_x != p2_x:
                m = (p2_z - p1_z) / (p2_x - p1_x)
            # if the outside point falls to the left, 
            #   use the distance between min x bound and x value 
            #   of point with the slope to find the intersection
            if (c1 & left_bit_code):
                p1_z += (boundary[0][0] - p1_x) * m
                p1_x = boundary[0][0]
            # if the outside point falls to the right, 
            #   use the distance between max x bound and x value 
            #   of point with the slope to find the intersection
            elif (c1 & right_bit_code):
                p1_z += (boundary[1][0] - p1_x) * m
                p1_x = boundary[1][0]
            # if the outside point falls behind the obstacle, 
            #   use the distance between min z bound and z value 
            #   of point with the slope to find the intersection
            elif (c1 & behind_bit_code):
                # only update x value for nonvertical lines in xz-plane
                if p1_x != p2_x:
                    p1_x += (boundary[0][1] - p1_z) / m
                p1_z = boundary[0][1]
            # if the outside point falls ahead of the obstacle, 
            #   use the distance between max z bound and z value 
            #   of point with the slope to find the intersection
            elif (c1 & ahead_bit_code):
                # only update x value for nonvertical lines in xz-plane
                if p1_x != p2_x:
                    p1_x += (boundary[1][1] - p1_z) / m
                p1_z = boundary[1][1]
            # return the updated intersection point
            return (True, p1_x, p1_z)

class Camera:
    """A simple 3D Camera System"""

    # wall tolerance added or subtracted to all boundaries
    tolerance = 1

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
        
        target_x = self.eye.x + du * u.dx + dn * n.dx
        target_y = self.eye.y + dv
        target_z = self.eye.z + du * u.dz + dn * n.dz

        # forcing the camera in the room boundaries
        (moved_outside, inside_x, inside_z) = line_clip(self.eye.x, self.eye.z, target_x, target_z, self.room_bounds, True)
        # if moved_outside:
        #     print("Attempted to move out of room bounds!")

        # values for other obstacles to compare to and update
        new_x = inside_x
        new_y = target_y
        new_z = inside_z

        # forcing the camera out of obstacles
        for obstacle_box in self.obstacle_bounding_boxes:
            (moved_inside, new_x, new_z) = line_clip(self.eye.x, self.eye.z, new_x, new_z, obstacle_box, False)
            # if moved_inside:
            #     print("Attempted to walk inside an object!")

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

    def get_look_at_point(self):
        # Compute the look at point based on the turn angle
        rad = math.radians(self.lookAngle)
        pitch_rad = math.radians(self.pitchAngle)
        lookX = self.eye.x - math.sin(rad) * math.cos(pitch_rad)
        lookY = self.eye.y - math.sin(pitch_rad)
        lookZ = self.eye.z - math.cos(rad) * math.cos(pitch_rad)

        return Point(lookX, lookY, lookZ)
        
    # function to load in obstacle bounding boxes
    #   intended for the table and objects in the room
    #   assumes that boxes is an array of boundaries
    def add_obstacle_bounding_boxes(self, boxes):
        """ Load all object bounding boxes for collision detection. Tolerances are factored in. """
        self.obstacle_bounding_boxes = []
        # apply tolerances
        for box in boxes:
            self.obstacle_bounding_boxes.append(self.recalculate_bounds_with_tolerance(box, False))

    # function to load in the room boundaries
    #   intended for the walls of the room
    #   assumes that boundaries is a single set of square boundaries
    def add_room_bounds(self, bounds):
        """ Load room bounds for collision detection. Tolerances are factored in. """
        self.room_bounds = self.recalculate_bounds_with_tolerance(bounds, True)

    # helper method to get bounds with tolerance automatically factored in
    def recalculate_bounds_with_tolerance(self, bounds, inside):
        # if inside, the lower bounds should have the tolerance added 
        #   and the upper bounds should have the tolerance removed
        if inside:
            return ((bounds[0][0] + self.tolerance, bounds[0][1] + self.tolerance), (bounds[1][0] - self.tolerance, bounds[1][1] - self.tolerance))
        # else, opposite tolerances
        else:
            return ((bounds[0][0] - self.tolerance, bounds[0][1] - self.tolerance), (bounds[1][0] + self.tolerance, bounds[1][1] + self.tolerance))