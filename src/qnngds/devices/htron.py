"""Heater cryotron devices `[1] <https://doi.org/10.1038/s41928-019-0300-8>`_, `[2] <https://doi.org/10.1103/PhysRevApplied.14.054011>`_."""

from phidl import Device

import phidl.geometry as pg
from typing import Tuple, Optional

# -*- coding: utf-8 -*-
"""
Created on Wed Mar 04 14:33:29 2024

@author: reedf

"""

import numpy as np
from phidl import Device
import phidl.geometry as pg
from qnngds.utilities import PadPlacement, QnnDevice
from qnngds.geometries import angled_taper
from typing import Tuple, List, Union, Optional

def planar_hTron(wire_width: Union[int, float]= 0.3,
                 gate_width: Union[int, float] = 0.1,
                 channel_width: Union[int, float] = 0.2,
                 gap: Union[int, float] = 0.02,
                 gate_length : Union[int, float]= 0.01,
                 channel_length: Union[int, float] = 0.01,
                 layer: int = 1
                 ) -> QnnDevice:
    """Create a planar hTron

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
    HTRON : QnnDevice
        A QnnDevice containing a single hTron

    """

    HTRON = Device('hTron')

    ports = []
    for direction,width,length in ((1,channel_width, channel_length), (-1,gate_width, gate_length)):
        W = Device('wire')
        constr = W << pg.straight(size=(width, np.max(length - 4*width,0)), layer=layer)
        constr.center = [0,0]
        constr.move([direction*(gap/2+width/2),0])
        taper = angled_taper(wire_width, width, 45, layer=layer)
        if direction < 0:
            taper.mirror()
        taper_lower = W << taper
        taper_lower.connect(taper_lower.ports[1], constr.ports[2])
        taper_upper = W << taper
        taper_upper.mirror()
        taper_upper.connect(taper_upper.ports[1], constr.ports[1])
        ports.append(taper_lower.ports[2])
        ports.append(taper_upper.ports[2])
        HTRON << W

    HTRON = pg.union(HTRON, layer=layer)

    final_HTRON = QnnDevice('hTron')
    final_HTRON.set_pads(PadPlacement(
        cell_scaling_factor_x= 1,
        num_pads_n=2,
        num_pads_s=2,
        port_map_x={
            0:("S", 2),
            1:("N", 2),
            2:("S", 1),
            3:("N", 1)
        }
    ))
    final_HTRON << HTRON
    for p, port in enumerate(ports):
        final_HTRON.add_port(name=p, port=port)

    final_HTRON.center = [0,0]
    final_HTRON.name = f"HTRON.planar(w={wire_width:.2f})"
    final_HTRON.simplify(1e-3)
    return final_HTRON