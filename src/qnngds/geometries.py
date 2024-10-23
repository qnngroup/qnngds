"""Geometries contains useful shapes/tools that are not available in phidl's
geometry library."""

from phidl import Device
import numpy as np


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
