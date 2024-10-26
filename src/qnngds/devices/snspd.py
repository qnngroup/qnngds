"""Superconducting nanowire single photon detector geometries."""

from phidl import Device

import phidl.geometry as pg
from typing import Tuple, Optional, Union


def basic(
    wire_width: float = 0.2,
    wire_pitch: float = 0.6,
    size: Tuple[Optional[Union[int, float]], Optional[Union[int, float]]] = (6, 10),
    num_squares: Optional[int] = None,
    turn_ratio: Union[int, float] = 4,
    terminals_same_side: bool = False,
    layer: int = 1,
) -> Device:
    """Creates an optimally-rounded SNSPD.

    Takes Phidl's snspd, perform a union and rename it.

    Parameters:
        wire_width (float): Width of the nanowire.
        wire_pitch (float): Pitch of the nanowire.
        size (tuple of Optional[int or float]): Size of the detector in squares (width, height).
        num_squares (Optional[int]): Number of squares in the detector.
        turn_ratio (int or float): Specifies how much of the SNSPD width is
            dedicated to the 180 degree turn. A turn_ratio of 10 will result in 20%
            of the width being comprised of the turn.
        terminals_same_side (bool): If True, both ports will be located on the
            same side of the SNSPD.
        layer (int): Layer for the device to be created on.

    Returns:
        Device: A Device containing an optimally-rounded SNSPD, as provided by
        Phidl but renamed and unified.
    """
    # check parameters constrains
    if wire_pitch <= wire_width:
        print(
            "Warning, wire_pitch cannot be smaller than wire_pitch. "
            "Choosing wire_pitch = 2*wire_width."
        )
        wire_pitch = 2 * wire_width

    SNSPD = pg.snspd(
        wire_width=wire_width,
        wire_pitch=wire_pitch,
        size=size,
        num_squares=num_squares,
        turn_ratio=turn_ratio,
        terminals_same_side=terminals_same_side,
        layer=layer,
    )
    ports = SNSPD.ports
    SNSPD = pg.union(SNSPD, layer=layer)
    SNSPD.ports = ports
    SNSPD.name = f"SNSPD.BASIC(w={wire_width}, pitch={wire_pitch})"
    return SNSPD


def vertical(
    wire_width: float = 0.2,
    wire_pitch: float = 0.6,
    size: Tuple[Union[int, float], Union[int, float]] = (6, 10),
    num_squares: Optional[int] = None,
    extend: Optional[float] = None,
    layer: int = 1,
) -> Device:
    """Creates an optimally-rounded SNSPD, with terminals in its center instead
    of the side.

    Parameters:
        wire_width (float): Width of the nanowire.
        wire_pitch (float): Pitch of the nanowire.
        size (tuple of int or float): Size of the detector in squares (width, height).
        num_squares (Optional[int]): Number of squares in the detector.
        extend (Optional[bool]): Whether or not to extend the ports.
        layer (int): Layer for the device to be created on.

    Returns:
        Device: The vertical SNSPD device.
    """
    # check parameters constrains
    if wire_pitch <= wire_width:
        print(
            "Warning, wire_pitch cannot be smaller than wire_pitch. "
            "Choosing wire_pitch = 2*wire_width."
        )
        wire_pitch = 2 * wire_width

    D = Device("SNSPD VERTICAL")

    S = pg.snspd(
        wire_width=wire_width,
        wire_pitch=wire_pitch,
        size=size,
        num_squares=num_squares,
        terminals_same_side=False,
        layer=layer,
    )
    s1 = D << S

    HP = pg.optimal_hairpin(
        width=wire_width, pitch=wire_pitch, length=S.xsize / 2, layer=layer
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
    D.name = f"SNSPD.VERTICAL(w={wire_width}, pitch={wire_pitch})"
    return D
