"""Superconducting nanowire single photon detector geometries."""

from phidl import Device

import phidl.geometry as pg
from typing import Tuple, Optional, Union


def vertical(
    wire_width: float = 0.2,
    wire_pitch: float = 0.6,
    size: Tuple[Union[int, float], Union[int, float]] = (6, 10),
    num_squares: Optional[int] = None,
    terminals_same_side: bool = False,
    extend: Optional[float] = None,
    layer: int = 0,
) -> Device:
    """Creates a vertical superconducting nanowire single-photon detector
    (SNSPD).

    Args:
        wire_width (float): Width of the nanowire.
        wire_pitch (float): Pitch of the nanowire.
        size (tuple of int or float): Size of the detector in squares (width, height).
        num_squares (Optional[int]): Number of squares in the detector.
        terminals_same_side (bool): Whether the terminals are on the same side of the detector.
        extend (Optional[bool]): Whether or not to extend the ports.
        layer (int): Layer for the device to be created on.

    Returns:
        Device: The vertical SNSPD device.
    """
    D = Device("SNSPD VERTICAL")

    S = pg.snspd(
        wire_width=wire_width,
        wire_pitch=wire_pitch,
        size=size,
        num_squares=num_squares,
        terminals_same_side=terminals_same_side,
        layer=layer,
    )
    s1 = D << S

    HP = pg.optimal_hairpin(
        width=wire_width, pitch=wire_pitch, length=size[0] / 2, layer=layer
    )
    h1 = D << HP
    h1.connect(h1.ports[1], S.references[0].ports["E"])
    h1.rotate(180, h1.ports[1])

    h2 = D << HP
    h2.connect(h2.ports[1], S.references[-1].ports["E"])
    h2.rotate(180, h2.ports[1])

    T = pg.optimal_90deg(width=wire_width, layer=layer)
    t1 = D << T
    T_width = t1.ports[2].midpoint[0]
    t1.connect(t1.ports[1], h1.ports[2])
    t1.movex(-T_width + wire_width / 2)

    t2 = D << T
    t2.connect(t2.ports[1], h2.ports[2])
    t2.movex(T_width - wire_width / 2)

    D = pg.union(D, layer=layer)
    D.flatten()
    if extend:
        E = pg.straight(size=(wire_width, extend), layer=layer)
        e1 = D << E
        e1.connect(e1.ports[1], t1.ports[2])
        e2 = D << E
        e2.connect(e2.ports[1], t2.ports[2])
        D = pg.union(D, layer=layer)
        D.add_port(name=1, port=e1.ports[2])
        D.add_port(name=2, port=e2.ports[2])
    else:
        D.add_port(name=1, port=t1.ports[2])
        D.add_port(name=2, port=t2.ports[2])

    D.info = S.info
    D.move(D.center, (0, 0))
    D.name = "SNSPD VERTICAL"
    return D
