"""Geometries contains useful shapes/tools that are not available in phidl's
geometry library."""

from phidl import Device
import numpy as np
import phidl.path as pp
from typing import Tuple, List, Union, Optional

def hyper_taper(length=10, wide_section=50, narrow_section=5, layer=1):
    """Hyperbolic taper (solid). Designed by colang.

    Args:
        length (float): Length of taper.
        wide_section (float): Wide width dimension.
        narrow_section (float): Narrow width dimension.
        layer (int): Layer for device to be created on.

    Returns:
        Device: The hyper taper.
    """

    taper_length = length
    wide = wide_section
    zero = 0
    narrow = narrow_section
    x_list = np.arange(0, taper_length + 0.1, 0.1)
    x_list2 = np.arange(taper_length, -0.1, -0.1)
    pts = []

    a = np.arccosh(wide / narrow) / taper_length

    for x in x_list:
        pts.append((x, np.cosh(a * x) * narrow / 2))
    for y in x_list2:
        pts.append((y, -np.cosh(a * y) * narrow / 2))
        HT = Device("hyper_taper")
        hyper_taper = HT.add_polygon(pts)
        HT.add_port(name=1, midpoint=[0, 0], width=narrow, orientation=180)
        HT.add_port(name=2, midpoint=[taper_length, 0], width=wide, orientation=0)
        HT.flatten(single_layer=layer)
    return HT

def angled_taper(wire_width: Union[int, float] = 0.2,
                 constr_width: Union[int, float] = 0.1,
                 angle: Union[int, float] = 60,
                 layer: int = 1):
    """Create an angled taper with euler curves

    Parameters
    -----------------
    wire_width : int or float
        Width of wide end of taper
    constr_width: int or float
        Width of narrow end of taper
    angle: int or float
        Angle between taper ends in degrees

    Returns
    -------------
    D : Device
        A Device containing a single taper

    """

    D = Device('taper')

    # heuristic for length between narrow end and bend
    l_constr = constr_width*2 + wire_width*2
    # heuristic for length between wide end and bend
    l_wire = constr_width*2 + wire_width*2
    sin = np.sin(angle*np.pi/180)
    cos = np.cos(angle*np.pi/180)
    # path along the center of the taper
    p_center = np.array([[0,0], [l_constr, 0], [l_constr+l_wire*cos,l_wire*sin]])
    # upper (shorter) path along the inside edge of the taper
    p_upper = np.array([[0,constr_width/2], [0, constr_width/2], p_center[2] + [-wire_width/2*sin, wire_width/2*cos]])
    p_upper[1,0] = (constr_width/2-p_upper[2,1])*cos/sin + p_upper[2,0]
    # lower (longer) path along the outside edge of the taper
    p_lower = np.array([[0,-constr_width/2], [0, -constr_width/2], p_center[2] + [wire_width/2*sin, -wire_width/2*cos]])
    p_lower[1,0] = (-constr_width/2-p_lower[2,1])*cos/sin + p_lower[2,0]
    # interpolate euler curve between points
    P_upper = pp.smooth(points=p_upper, radius=wire_width, corner_fun=pp.euler, use_eff=False)
    P_lower = pp.smooth(points=p_lower, radius=wire_width, corner_fun=pp.euler, use_eff=False)
    
    # create a polygon
    points = np.concatenate((P_upper.points, P_lower.points[::-1]))
    D.add_polygon(points, layer=layer)

    # port 1: narrow/constr_width end, port 2: wide/wire_width end
    D.add_port(name=1, midpoint=(P_upper.points[0] + P_lower.points[0])/2, width=constr_width, orientation=180)
    D.add_port(name=2, midpoint=(P_upper.points[-1] + P_lower.points[-1])/2, width=wire_width, orientation=angle)

    return D
