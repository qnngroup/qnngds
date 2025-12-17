"""Heater cryotron devices `[1] <https://doi.org/10.1038/s41928-019-0300-8>`_, `[2] <https://doi.org/10.1103/PhysRevApplied.14.054011>`_."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import qnngds as qg
import phidl.geometry as pg

import numpy as np

from functools import partial

from qnngds.typing import LayerSpec, DeviceSpec
from qnngds import Device

from . import nanowire as nanowire


@qg.device
def planar(
    wire_width: int | float = 0.3,
    gate_width: int | float = 0.1,
    channel_width: int | float = 0.2,
    gap: int | float = 0.02,
    gate_length: int | float = 0.01,
    channel_length: int | float = 0.01,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Create a planar hTron.

    Args:
        wire_width (int or float): Width of routing wires in microns
        gate_width (int or float): Width of superconducting gate in microns
        channel_width (int or float): Width of superconducting channel in microns
        gap (int or float): Spacing between gate and channel in microns
        gate_length (int or float): Length of superconducting gate in microns
        channel_length (int or float): Length of superconducting channel in microns
        layer (LayerSpec): GDS layer specification

    Returns:
        Device: a single planar hTron
    """

    HTRON = Device("htron_planar")

    ports = []
    for direction, width, length in (
        (1, channel_width, channel_length),
        (-1, gate_width, gate_length),
    ):
        compass_size = (width, np.max((length - 4 * width, 0.1)))
        constr = HTRON << pg.compass(size=compass_size, layer=qg.get_layer(layer))
        constr.center = [0, 0]
        constr.move([direction * (gap / 2 + width / 2), 0])
        taper = qg.geometries.angled_taper(wire_width, width, 45, layer=layer)
        taper_lower = HTRON << taper
        taper_upper = HTRON << taper
        if direction < 0:
            taper_upper.mirror()
        else:
            taper_lower.mirror()
        taper_lower.connect(port=taper_lower.ports[1], destination=constr.ports["N"])
        taper_upper.connect(port=taper_upper.ports[1], destination=constr.ports["S"])
        ports.append(taper_lower.ports[2])
        ports.append(taper_upper.ports[2])
    for p, port in enumerate(ports):
        HTRON.add_port(name=p + 1, port=port)
    return HTRON


@qg.device
def heater(
    pad_size: tuple[float, float] = (2, 2),
    constr_length: float = 2,
    constr_width: float = 0.5,
    pad_outline: float = 0.5,
    heater_layer: LayerSpec = (10, 0),
    pad_layer: LayerSpec = (20, 0),
) -> Device:
    """Create a heater for use with hTrons.

    Args:
        pad_size (tuple[float, float]): (width, height) of pad
        constr_length (float): length of heater constriction
        constr_width (float): width at narrowest point
        pad_outline (float): amount by which to oversize top pad on each side
        heater_layer (LayerSpec): layer specification for heater
        pad_layer (LayerSpec): layer specification for top pads

    Returns:
        Device: a heater
    """
    if pad_size[1] - 2 * pad_outline < constr_width:
        raise ValueError(
            f"{pad_size=} and {pad_outline=} do not give enough space to "
            f"make a constriction of width {constr_width=}. "
            "Increase pad_size and/or decrease pad_outline"
        )
    h_pad = pg.compass(
        size=(pad_size[0] - pad_outline, pad_size[1] - 2 * pad_outline),
        layer=qg.get_layer(heater_layer),
    )
    t_pad = pg.compass(size=pad_size, layer=qg.get_layer(pad_layer))
    HEATER = Device("heater")
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
        h_pads[i].connect(h_pads[i].ports["W"], heater.ports[i + 1])
        t_pads[i].connect(
            t_pads[i].ports["W"],
            heater.ports[i + 1],
        )
    HEATERu = Device("heater")
    HEATERu << pg.union(HEATER, by_layer=True)
    dir_lut = {1: "W", 2: "N", 3: "E", 4: "S"}
    for n, t_pad in enumerate(t_pads):
        for i in range(3):
            HEATERu.add_port(
                name=3 * n + i + 1, port=t_pad.ports[dir_lut[i + 2]], layer=pad_layer
            )
    return HEATERu


@qg.device
def multilayer(
    rotation: float = 0,
    channel_spec: DeviceSpec = partial(
        nanowire.variable_length, constr_width=1, wire_width=2, length=4, layer=(1, 0)
    ),
    gate_spec: DeviceSpec = heater,
) -> Device:
    """Create a multilayer hTron.

    Args:
        rotation (float): amount to rotate gate relative to channel.
        channel_spec (DeviceSpec): callable function that generates a Device for the channel nanowire
        gate_spec (DeviceSpec): callable function that generates a Device for the gate nanowire

    Returns:
        Device: a multilayer hTron
    """

    HTRON = Device("htron_multilayer")

    c = qg.get_device(channel_spec)
    g = qg.get_device(gate_spec)

    channel = HTRON << c
    gate = HTRON << g
    gate.rotate(rotation)
    gate.move(gate.center, channel.center)
    for p, port_name in enumerate(gate.ports):
        HTRON.add_port(name=f"g{p + 1}", port=gate.ports[port_name])
    for p, port_name in enumerate(channel.ports):
        HTRON.add_port(name=f"c{p + 1}", port=channel.ports[port_name])
    return HTRON
