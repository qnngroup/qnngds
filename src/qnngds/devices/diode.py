"""Layout for superconducting diode `[1] <https://doi.org/10.1038/s41928-025-01376-4>`_."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import gdsfactory as gf
from gdsfactory.typings import LayerSpec, ComponentSpec
import qnngds as qg

import numpy as np

from functools import partial


@gf.cell
def basic(
    width: float = 2,
    notch_depth: float = 1,
    notch_angle: float = 90,
    length: float = 5,
    mirror: bool = False,
    layer: LayerSpec = "EBEAM_FINE",
    port_type: str = "electrical",
) -> gf.Component:
    """Create notched vortex diode on single layer

    Args:
        width (float): wire width in microns
        notch_depth (float): amount notch protrudes into wire
        notch_angle (float): angle of notch opening in degrees
        length (float): length of device
        mirror (bool): if True, place notch on left side
        layer (LayerSpec): GDS layer
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: the diode
    """
    DIODE = gf.Component()
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
        name="e1",
        center=(DIODE.x, length / 2),
        width=width,
        orientation=90,
        layer=layer,
        port_type=port_type,
    )

    DIODE.add_port(
        name="e2",
        center=(DIODE.x, -length / 2),
        width=width,
        orientation=270,
        layer=layer,
        port_type=port_type,
    )

    return DIODE


@gf.cell
def gated(
    channel_spec: ComponentSpec = basic,
    gate_spec: ComponentSpec = partial(
        qg.geometries.optimal_hairpin, width=2, pitch=4, turn_ratio=2, layer="PHOTO1"
    ),
) -> gf.Component:
    """Create notched vortex diode on single layer

    Args:
        channel_spec (ComponentSpec): what to use for diode channel (e.g. diode.basic)
        gate_spec (ComponentSpec): what to use for top gate (e.g. geometries.optimal_hairpin)

    Returns:
        gf.Component: the gated diode
    """
    DIODE = gf.Component()

    channel = DIODE << gf.get_component(channel_spec)
    gate = DIODE << gf.get_component(gate_spec)
    gate.movex(channel.ports["e1"].width / 2)
    for n, port in enumerate(channel.ports):
        DIODE.add_port(name=f"c{n + 1}", port=port)
    for n, port in enumerate(gate.ports):
        DIODE.add_port(name=f"g{n + 1}", port=port)

    return DIODE
