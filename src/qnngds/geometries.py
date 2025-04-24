"""Geometries contains useful shapes/tools that are not available in phidl's
geometry library."""

import gdsfactory as gf
import numpy as np
from typing import Tuple, List, Union, Optional


@gf.cell
def hyper_taper(length=10, wide_section=50, narrow_section=5, layer=1) -> gf.Component:
    """Hyperbolic taper (solid). Designed by colang.

    Parameters
        length (int or float): Length of taper
        wide_section (int or float): Width of wide end of taper
        narrow_section (int or float): Width of narrow end of taper
        layer (int or tuple): GDS layer, either as tuple (layer, type) or int layer (assumed type is 0)

    Returns
        gf.Component: a single taper
    """
    HT = gf.Component()

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
    hyper_taper = HT.add_polygon(pts, layer=layer)
    HT.add_port(name="e1", center=[0, 0], width=narrow, orientation=180, layer=layer)
    HT.add_port(
        name="e2", center=[taper_length, 0], width=wide, orientation=0, layer=layer
    )
    return HT


@gf.cell
def angled_taper(
    wire_width: Union[int, float] = 0.2,
    constr_width: Union[int, float] = 0.1,
    angle: Union[int, float] = 60,
    layer: Union[int, tuple] = 1,
) -> gf.Component:
    """Create an angled taper with euler curves.

    Parameters
        wire_width (int or float): Width of wide end of taper
        constr_width (int or float): Width of narrow end of taper
        angle (int or float): Angle between taper ends in degrees
        layer (int or tuple): GDS layer, either as tuple (layer, type) or int layer (assumed type is 0)

    Returns
    -------------
    gf.Component: a single taper
    """

    D = gf.Component()
    # heuristic for length between narrow end and bend
    l_constr = constr_width * 2 + wire_width * 2
    # heuristic for length between wide end and bend
    l_wire = constr_width * 2 + wire_width * 2
    sin = np.sin(angle * np.pi / 180)
    cos = np.cos(angle * np.pi / 180)
    # path along the center of the taper
    p_center = np.array(
        [[0, 0], [l_constr, 0], [l_constr + l_wire * cos, l_wire * sin]]
    )
    # upper (shorter) path along the inside edge of the taper
    p_upper = np.array(
        [
            [0, constr_width / 2],
            [0, constr_width / 2],
            p_center[2] + [-wire_width / 2 * sin, wire_width / 2 * cos],
        ]
    )
    p_upper[1, 0] = (constr_width / 2 - p_upper[2, 1]) * cos / sin + p_upper[2, 0]
    # lower (longer) path along the outside edge of the taper
    p_lower = np.array(
        [
            [0, -constr_width / 2],
            [0, -constr_width / 2],
            p_center[2] + [wire_width / 2 * sin, -wire_width / 2 * cos],
        ]
    )
    p_lower[1, 0] = (-constr_width / 2 - p_lower[2, 1]) * cos / sin + p_lower[2, 0]
    # interpolate euler curve between points
    P_upper = gf.path.smooth(
        points=p_upper, radius=wire_width, bend=gf.path.euler, use_eff=False
    )
    P_lower = gf.path.smooth(
        points=p_lower, radius=wire_width, bend=gf.path.euler, use_eff=False
    )

    # create a polygon
    points = np.concatenate((P_upper.points, P_lower.points[::-1]))
    D.add_polygon(points, layer=layer)

    # port 1: narrow/constr_width end, port 2: wide/wire_width end
    D.add_port(
        name="e1",
        center=(P_upper.points[0] + P_lower.points[0]) / 2,
        width=constr_width,
        orientation=180,
        layer=layer,
        port_type="electrical",
    )
    D.add_port(
        name="e2",
        center=(P_upper.points[-1] + P_lower.points[-1]) / 2,
        width=wire_width,
        orientation=angle,
        layer=layer,
        port_type="electrical",
    )

    return D
