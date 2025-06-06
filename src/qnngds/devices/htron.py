"""Heater cryotron devices `[1] <https://doi.org/10.1038/s41928-019-0300-8>`_, `[2] <https://doi.org/10.1103/PhysRevApplied.14.054011>`_."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import gdsfactory as gf
import numpy as np

import qnngds as qg

import qnngds.devices.nanowire as nanowire

from functools import partial

from gdsfactory.typings import LayerSpec, ComponentSpec
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
    port_type: str = "electrical",
) -> gf.Component:
    """Create a planar hTron.

    Args:
        wire_width (int or float): Width of routing wires in microns
        gate_width (int or float): Width of superconducting gate in microns
        channel_width (int or float): Width of superconducting channel in microns
        gap (int or float): Spacing between gate and channel in microns
        gate_length (int or float): Length of superconducting gate in microns
        channel_length (int or float): Length of superconducting channel in microns
        layer (LayerSpec): GDS layer
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
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
        HTRON.add_port(name=f"e{p + 1}", port=port)
    for port in HTRON.ports:
        port.port_type = port_type
    return HTRON


@gf.cell
def heater(
    pad_size: tuple[float, float] = (2, 2),
    constr_length: float = 2,
    constr_width: float = 0.5,
    pad_outline: float = 0.5,
    heater_layer: LayerSpec = (2, 0),
    pad_layer: LayerSpec = (3, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Create a heater for use with hTrons.

    Args:
        pad_size (tuple[float, float]): (width, height) of pad
        constr_length (float): length of heater constriction
        constr_width (float): width at narrowest point
        pad_outline (float): amount by which to oversize top pad on each side
        heater_layer (LayerSpec): layer for heater
        pad_layer (LayerSpec): layer for top pads
        port_type (str): type of port, default "electrical"

    Returns:
        gf.Component: a heater
    """
    if pad_size[1] - 2 * pad_outline < constr_width:
        error_msg = (
            f"{pad_size=} and {pad_outline=} do not give enough space to make a "
        )
        error_msg += f"constriction of width {constr_width=}. Increase pad_size and/or decrease pad_outline"
        raise ValueError(error_msg)
    h_pad = gf.components.shapes.compass(
        size=(pad_size[0] - pad_outline, pad_size[1] - 2 * pad_outline),
        layer=heater_layer,
    )
    t_pad = gf.components.shapes.compass(size=pad_size, layer=pad_layer)
    HEATER = gf.Component()
    h_pads = []
    t_pads = []
    heater = HEATER << nanowire.sharp(
        constr_width=constr_width,
        wire_width=pad_size[1] - 2 * pad_outline,
        length=constr_length,
        layer=heater_layer,
    )
    for i in range(2):
        h_pads.append(HEATER << h_pad)
        t_pads.append(HEATER << t_pad)
    for i in range(2):
        h_pads[i].connect(h_pads[i].ports["e1"], heater.ports[f"e{i + 1}"])
        t_pads[i].connect(
            t_pads[i].ports["e1"],
            heater.ports[f"e{i + 1}"],
            allow_width_mismatch=True,
            allow_layer_mismatch=True,
        )
    HEATERu = gf.Component()
    HEATERu << qg.utilities.union(HEATER)
    for n, t_pad in enumerate(t_pads):
        for i in range(3):
            HEATERu.add_port(name=f"e{3 * n + i + 1}", port=t_pad.ports[f"e{i + 2}"])
    for port in HEATERu.ports:
        port.port_type = port_type
    return HEATERu


@gf.cell
def multilayer(
    rotation: float = 0,
    channel_spec: ComponentSpec = partial(
        nanowire.variable_length, constr_width=1, wire_width=2, length=4, layer=(1, 0)
    ),
    gate_spec: ComponentSpec = heater,
) -> gf.Component:
    """Create a multilayer hTron.

    Args:
        rotation (float): amount to rotate gate relative to channel.
        channel_spec (ComponentSpec): callable function that generates a gf.Component for the channel nanowire
        gate_spec (ComponentSpec): callable function that generates a gf.Component for the gate nanowire

    Returns:
        gf.Component: a multilayer hTron
    """

    HTRON = gf.Component()

    c = gf.get_component(channel_spec)
    g = gf.get_component(gate_spec)

    channel = HTRON << c
    gate = HTRON << g
    gate.rotate(rotation)
    gate.move(gate.center, channel.center)
    for p, port in enumerate(gate.ports):
        HTRON.add_port(name=f"g{p + 1}", port=port)
    for p, port in enumerate(channel.ports):
        HTRON.add_port(name=f"c{p + 1}", port=port)
    return HTRON
