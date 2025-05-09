"""Heater cryotron devices `[1] <https://doi.org/10.1038/s41928-019-0300-8>`_, `[2] <https://doi.org/10.1103/PhysRevApplied.14.054011>`_."""

import gdsfactory as gf
import numpy as np

import qnngds as qg

from gdsfactory.typings import LayerSpec
from typing import Union


@gf.cell
def planar(
    wire_width: Union[int, float] = 0.3,
    gate_width: Union[int, float] = 0.1,
    channel_width: Union[int, float] = 0.2,
    gap: Union[int, float] = 0.02,
    gate_length: Union[int, float] = 0.01,
    channel_length: Union[int, float] = 0.01,
    layer: LayerSpec = (1, 0),
) -> gf.Component:
    """Create a planar hTron.

    Parameters
        wire_width (int or float): Width of routing wires in microns
        gate_width (int or float): Width of superconducting gate in microns
        channel_width (int or float): Width of superconducting channel in microns
        gap (int or float): Spacing between gate and channel in microns
        gate_length (int or float): Length of superconducting gate in microns
        channel_length (int or float): Length of superconducting channel in microns
        layer (LayerSpec): GDS layer tuple (layer, type)

    Returns
        gf.Component: a single planar hTron
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
        taper = qg.geometries.angled_taper(wire_width, width, 45, layer=layer)
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


@gf.cell
def multilayer(
    wire_width: Union[int, float] = 0.3,
    gate_width: Union[int, float] = 0.1,
    channel_width: Union[int, float] = 0.2,
    gate_length: Union[int, float] = 0.01,
    channel_length: Union[int, float] = 0.01,
    gate_layer: LayerSpec = (1, 0),
    channel_layer: LayerSpec = (2, 0),
) -> gf.Component:
    """Create a multilayer hTron.

    Parameters
        wire_width (int or float): Width of routing wires in microns
        gate_width (int or float): Width of superconducting gate in microns
        channel_width (int or float): Width of superconducting channel in microns
        gate_length (int or float): Length of superconducting gate in microns
        channel_length (int or float): Length of superconducting channel in microns
        gate_layer (LayerSpec): GDS layer tuple for the gate (layer, type)
        channel_layer (LayerSpec): GDS layer tuple for the channel (layer, type)

    Returns
        gf.Component: a single planar hTron
    """

    HTRON = gf.Component()

    channel = HTRON << qg.devices.nanowire.variable_length(
        constr_width=channel_width,
        wire_width=wire_width,
        length=channel_length,
        layer=channel_layer,
    )
    gate = HTRON << qg.devices.nanowire.variable_length(
        constr_width=gate_width,
        wire_width=wire_width,
        length=gate_length,
        layer=gate_layer,
    )
    gate.rotate(90)
    gate.move(gate.center, channel.center)
    for p, port in enumerate(gate.ports):
        HTRON.add_port(name=f"g{p}", port=port)
    for p, port in enumerate(channel.ports):
        HTRON.add_port(name=f"c{p}", port=port)
    return HTRON
