"""Heater cryotron devices `[1] <https://doi.org/10.1038/s41928-019-0300-8>`_, `[2] <https://doi.org/10.1103/PhysRevApplied.14.054011>`_."""

from phidl import Device

import phidl.geometry as pg
from typing import Tuple, Optional

# -*- coding: utf-8 -*-
"""
Created on Wed Mar 04 14:33:29 2024

@author: reedf

"""

import gdsfactory as gf
import numpy as np

from qnngds.geometries import angled_taper
from typing import Tuple, List, Union, Optional


@gf.cell
def planar_hTron(
    wire_width: Union[int, float] = 0.3,
    gate_width: Union[int, float] = 0.1,
    channel_width: Union[int, float] = 0.2,
    gap: Union[int, float] = 0.02,
    gate_length: Union[int, float] = 0.01,
    channel_length: Union[int, float] = 0.01,
    layer: int = 1,
) -> gf.Component:
    """Create a planar hTron.

    Parameters
    -----------------
    wire_width : int or float
        Width of routing wires in microns
    gate_width : int or float
        Width of superconducting gate in microns
    channel_width : int or float
        Width of superconducting channel in microns
    gap : int or float
        Spacing between gate and channel in microns
    gate_length : int or float
        Length of superconducting gate in microns
    channel_length : int or float
        Length of superconducting channel in microns
    layer: int
        Layer to draw device on

    Returns
    -------------
    HTRON : gf.Component
        A gdsfactory Component containing a single hTron
    """

    HTRON = gf.Component()

    ports = []
    for direction, width, length in (
        (1, channel_width, channel_length),
        (-1, gate_width, gate_length),
    ):
        compass_size = (width, np.max((length - 4 * width, 0.1)))
        constr = HTRON << gf.components.compass(
            size=compass_size, layer=layer, port_type="electrical"
        )
        constr.center = [0, 0]
        constr.move([direction * (gap / 2 + width / 2), 0])
        taper = angled_taper(wire_width, width, 45, layer=layer)
        taper_lower = HTRON << taper
        taper_upper = HTRON << taper
        if direction < 0:
            taper_upper.mirror()
        else:
            taper_lower.mirror()
        taper_lower.connect(port=taper_lower.ports["e1"], other=constr.ports["e2"])
        taper_upper.connect(port=taper_upper.ports["e1"], other=constr.ports["e4"])
        ports.append(taper_lower.ports["e2"])
        ports.append(taper_upper.ports["e2"])
    for p, port in enumerate(ports):
        HTRON.add_port(name=f"e{p}", port=port)
    return HTRON
