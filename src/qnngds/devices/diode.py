"""Layout for superconducting diode `[1] <https://doi.org/10.1038/s41928-025-01376-4>`_."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import qnngds as qg


import numpy as np

from functools import partial

from qnngds.typing import LayerSpec, DeviceSpec
from qnngds import Device


def basic(
    width: float = 2,
    notch_depth: float = 1,
    notch_angle: float = 90,
    length: float = 5,
    mirror: bool = False,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Create notched vortex diode on single layer

    Args:
        width (float): wire width in microns
        notch_depth (float): amount notch protrudes into wire
        notch_angle (float): angle of notch opening in degrees
        length (float): length of device
        mirror (bool): if True, place notch on left side
        layer (LayerSpec): GDS layer

    Returns:
        Device: the diode
    """
    DIODE = Device("diode_basic")
    points = [
        (-width, -length / 2),
        (0, -length / 2),
        (0, -notch_depth * np.sin(notch_angle / 2)),
        (-notch_depth, 0),
        (0, notch_depth * np.sin(notch_angle / 2)),
        (0, length / 2),
        (-width, length / 2),
    ]

    DIODE.add_polygon(points, layer=layer)
    DIODE.move((DIODE.x + width / 2 - notch_depth, DIODE.y), (0, 0))

    DIODE.add_port(
        name=1,
        midpoint=(DIODE.x, length / 2),
        width=width,
        orientation=90,
        layer=layer,
    )

    DIODE.add_port(
        name=2,
        midpoint=(DIODE.x, -length / 2),
        width=width,
        orientation=270,
        layer=layer,
    )

    return DIODE


def gated(
    channel_spec: DeviceSpec = basic,
    gate_spec: DeviceSpec = partial(
        qg.geometries.optimal_hairpin,
        width=2,
        pitch=4,
        turn_ratio=2,
        layer=(10, 0),
    ),
) -> Device:
    """Create notched vortex diode with a gate.

    Lateral offset of the gate can be done by first offsetting the gate before
    passing it as an argument to this function.

    Args:
        channel_spec (DeviceSpec): what to use for diode channel (e.g. diode.basic)
        gate_spec (DeviceSpec): what to use for top gate (e.g. geometries.optimal_hairpin)

    Returns:
        Device: the gated diode
    """
    DIODE = Device("diode_gated")

    channel = DIODE << qg.get_device(channel_spec)
    gate = DIODE << qg.get_device(gate_spec)
    gate.movex(channel.ports[1].width / 2)
    for n, port_name in enumerate(channel.ports):
        DIODE.add_port(name=f"c{n + 1}", port=channel.ports[port_name])
    for n, port_name in enumerate(gate.ports):
        DIODE.add_port(name=f"g{n + 1}", port=gate.ports[port_name])

    return DIODE
