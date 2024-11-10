#==============================
# Christian Duncan
# CSC345: Computer Graphics
#   Fall 2016
#
# utils.py module
# Description:
#   Defines a few classes used for the sample programs.
#   These classes are NOT COMPLETE but are shortened to 
#   include mostly relevant material.
#   For example, Vector class ideally would have ways to do
#   dot product, cross product, normalization, etc.
#   But those aren't needed here so they are left off.
#==============================
import math

class Point:
    """A simple 3D Point Class"""
    
    def __init__(self, x=0, y=0, z=0):
        """A constructor for Point class using initial x,y values"""
        self.x = x; self.y = y; self.z = z

    def __str__(self):
        """Basic string representation of this point"""
        return "(%s,%s,%s)"%(self.x,self.y,self.z)

    def lerp(self, q, t):
        """Linear interpolation between two points"""
        return Point(self.x + t*(q.x - self.x),
                     self.y + t*(q.y - self.y),
                     self.z + t*(q.z - self.z))

    def lerpV(self, v, t):
        """Linear interpolation between a point and a vector"""
        return Point(self.x + t*v.dx,
                     self.y + t*v.dy,
                     self.z + t*v.dz)

class Vector:
    """A simple 3D Vector Class"""
    def __init__(self, p=None, q=None, a_list=None):
        """A constructor for Vector class between two Points p and q"""
        if q is None:
            if p is None:
                if a_list is None:
                    self.dx = 0; self.dy = 0; self.dz = 0   # No direction at all
                else:
                    self.dx = a_list[0]; self.dy = a_list[1]; self.dz = a_list[2]
            else:
                self.dx = p.x; self.dy = p.y; self.dz = p.z  # Origin to p
        else:
            self.dx = q.x - p.x; self.dy = q.y - p.y; self.dz = q.z - p.z

    def __str__(self):
        """Basic string representation of this point"""
        return "<%s,%s,%s>"%(self.dx,self.dy,self.dz)

    def cross(self, other):
        res = Vector()
        res.dx = self.dy*other.dz - self.dz*other.dy
        res.dy = self.dz*other.dx - self.dx*other.dz
        res.dz = self.dx*other.dy - self.dy*other.dx
        return  res

    def magnitude(self):
        """Computes the magnitude (length) of this vector"""
        return math.sqrt(self.dx*self.dx + self.dy*self.dy + self.dz*self.dz)
    
    def normalize(self):
        """Normalizes this Vector"""
        mag = self.magnitude()
        if mag != 0:
            self.dx /= mag
            self.dy /= mag
            self.dz /= mag
    
