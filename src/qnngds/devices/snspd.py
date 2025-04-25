"""Superconducting nanowire single photon detector geometries."""

import gdsfactory as gf
import numpy as np

import qnngds.utilities as qu

from typing import Tuple, Optional, Union


@gf.cell
def basic(
    wire_width: float = 0.2,
    wire_pitch: float = 0.6,
    size: Tuple[Optional[Union[int, float]], Optional[Union[int, float]]] = (10, 20),
    num_squares: Optional[int] = None,
    turn_ratio: Union[int, float] = 4,
    terminals_same_side: bool = False,
    layer: tuple = (1, 0),
) -> gf.Component:
    """Creates an optimally-rounded SNSPD.

    Takes gdsfactory's SNSPD and perform union.

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
        layer (tuple): GDS layer tuple (layer, type)

    Returns:
        gf.Component: optimally-rounded SNSPD, as provided by
        Phidl but renamed and unified.
    """
    # check parameters constrains
    if wire_pitch <= wire_width:
        print(
            "Warning, wire_pitch cannot be smaller than wire_pitch. "
            "Choosing wire_pitch = 2*wire_width."
        )
        wire_pitch = 2 * wire_width

    SNSPD = gf.Component()
    SNSPD << gf.components.superconductors.snspd(
        wire_width=wire_width,
        wire_pitch=wire_pitch,
        size=size,
        num_squares=num_squares,
        turn_ratio=turn_ratio,
        terminals_same_side=terminals_same_side,
        layer=layer,
        port_type="electrical",
    )
    ports = SNSPD.ports
    SNSPDu = gf.Component()
    SNSPDu << qu.union(SNSPD)
    SNSPDu.flatten()
    SNSPDu.add_ports(ports)
    return SNSPDu


@gf.cell
def vertical(
    wire_width: float = 0.2,
    wire_pitch: float = 0.6,
    size: Tuple[Union[int, float], Union[int, float]] = (10, 20),
    num_squares: Optional[int] = None,
    extend: Optional[float] = 1,
    layer: tuple = (1, 0),
) -> gf.Component:
    """Creates an optimally-rounded SNSPD, with terminals in its center instead
    of the side.

    Parameters:
        wire_width (float): Width of the nanowire.
        wire_pitch (float): Pitch of the nanowire.
        size (tuple of int or float): Size of the detector in squares (width, height).
        num_squares (Optional[int]): Number of squares in the detector.
        extend (Optional[bool]): Whether or not to extend the ports.
        layer (tuple): GDS layer tuple (layer, type)

    Returns:
        gf.Component: The vertical SNSPD device.
    """
    # check parameters constrains
    if wire_pitch <= wire_width:
        print(
            "Warning, wire_pitch cannot be smaller than wire_pitch. "
            "Choosing wire_pitch = 2*wire_width."
        )
        wire_pitch = 2 * wire_width

    D = gf.Component()

    S = gf.components.superconductors.snspd(
        wire_width=wire_width,
        wire_pitch=wire_pitch,
        size=size,
        num_squares=num_squares,
        terminals_same_side=False,
        layer=layer,
        port_type="optical",
    )
    D << S

    HP = gf.components.superconductors.optimal_hairpin(
        width=wire_width, pitch=wire_pitch, length=S.xsize / 2, layer=layer
    )
    h1 = D << HP
    h1.mirror()
    h1.move(np.subtract(S.ports["e1"].center, h1.ports["e2"].center))
    h1.movex(size[0] / 2)

    h2 = D << HP
    h2.move(np.subtract(S.ports["e2"].center, h2.ports["e1"].center))
    h2.movex(-size[0] / 2)

    T = gf.components.superconductors.optimal_90deg(width=wire_width, layer=layer)
    t1 = D << T
    t1.rotate(90)
    t1.move(np.subtract(h1.ports["e1"].center, t1.ports["e1"].center))
    t1.movex(-T.xsize)

    t2 = D << T
    t2.rotate(270)
    t2.move(np.subtract(h2.ports["e2"].center, t2.ports["e1"].center))
    t2.movex(T.xsize)

    ports = []
    if extend:
        E = gf.components.compass(size=(extend, wire_width), layer=layer)
        e1 = D << E
        e1.connect(e1.ports["e1"], t1.ports["e2"], allow_type_mismatch=True)
        e2 = D << E
        e2.connect(e2.ports["e1"], t2.ports["e2"], allow_type_mismatch=True)
        ports.append(e1.ports["e2"])
        ports.append(e2.ports["e2"])
    else:
        ports.append(t1.ports["e2"])
        ports.append(t2.ports["e2"])
    Du = gf.Component()
    Du << qu.union(D)
    Du.flatten()
    for p, port in enumerate(ports):
        Du.add_port(name=f"e{p}", port=port, port_type="electrical")
    return Du
