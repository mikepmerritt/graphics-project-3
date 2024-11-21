#==============================
# Matthew Merritt, Michael Merritt, Harsh Gandhi
# CSC345: Computer Graphics
#   Fall 2024
#
# light.py module
# Description:
#   Defines a light class used for the sample programs.
#   Supports point, spot, and directional lights.
#   Default values are for a fully bright light at the origin,
#   facing downward of unspecified type, with no attenuation.
#   Choosing the type of light is required, and a warning
#   will be displayed if not specified.
#==============================
from utils import *
import copy

class Light:
    # constructor
    def __init__(
        self, 
        gl_light_name,                      # the light to be enabled (ex: GL_LIGHT0)
        enabled=False,                      # boolean for if the light is on
        position=Point(0, 0, 0),           # position of the light as a Point
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