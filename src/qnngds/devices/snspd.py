"""Superconducting nanowire single photon detector geometries."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import qnngds as qg
import phidl.geometry as pg

import numpy as np

from qnngds.typing import LayerSpec
from qnngds import Device

from typing import Tuple


@qg.device
def basic(
    wire_width: float = 0.2,
    wire_pitch: float = 0.6,
    size: Tuple[int | float | None, int | float | None] = (5, 5),
    num_squares: int | None = None,
    turn_ratio: int | float = 4,
    num_pts: int = 50,
    extend_terminals: bool = True,
    terminals_same_side: bool = False,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Creates an optimally-rounded SNSPD.

    Modification of gdsfactory's and phidl's implementations

    Args:
        wire_width (float): Width of the nanowire.
        wire_pitch (float): Pitch of the nanowire.
        size (tuple of Optional[int or float]): Size of the detector.
        num_squares (int | None): Number of squares in the detector.
        turn_ratio (int or float): Specifies how much of the SNSPD width is
            dedicated to the 180 degree turn. A turn_ratio of 10 will result in 20%
            of the width being comprised of the turn.
        num_pts (int): number of polygon points to use for turn
        extend_terminals (bool): If True, bring ports flush to edges of device
        terminals_same_side (bool): If True, both ports will be located on the
            same side of the SNSPD.
        layer (LayerSpec): GDS layer

    Returns:
        Device: optimally-rounded SNSPD, as provided by
        Phidl but renamed and unified.
    """
    # check parameters constrains
    if wire_pitch <= wire_width:
        print(
            "Warning, wire_pitch cannot be smaller than wire_pitch. "
            "Choosing wire_pitch = 2*wire_width."
        )
        wire_pitch = 2 * wire_width

    if num_squares is not None and (
        (size is None) or ((size[0] is None) and (size[1]) is None)
    ):
        xy = np.sqrt(num_squares * wire_pitch * wire_width)
        size = [xy, xy]
        num_squares = None
    if [size[0], size[1], num_squares].count(None) != 1:
        raise ValueError(
            "SNSPD requires that exactly ONE value of "
            "the arguments ``num_squares`` and ``size`` be None "
            "to prevent overconstraining, for example:\n"
            ">>> snspd(size = (3, None), num_squares = 2000)"
        )
    if size[0] is None:
        ysize = size[1]
        xsize = num_squares * wire_pitch * wire_width / ysize
    elif size[1] is None:
        xsize = size[0]
        ysize = num_squares * wire_pitch * wire_width / xsize
    else:
        xsize = size[0]
        ysize = size[1]

    num_meanders = int(np.ceil(ysize / wire_pitch))

    half_size = xsize / 2

    SNSPD = Device()
    hairpin = qg.geometries.optimal_hairpin(
        width=wire_width,
        pitch=wire_pitch,
        turn_ratio=turn_ratio,
        length=half_size,
        num_pts=num_pts,
        layer=layer,
    )

    if not terminals_same_side and (num_meanders % 2) == 0:
        num_meanders += 1
    elif terminals_same_side and (num_meanders % 2) == 1:
        num_meanders += 1

    if extend_terminals:
        start_nw = SNSPD.add_ref(
            pg.straight(size=(wire_width, half_size), layer=qg.get_layer(layer))
        )
        hp_prev = SNSPD.add_ref(hairpin)
        hp_prev.connect(1, start_nw.ports[2])
    else:
        start_nw = SNSPD.add_ref(hairpin)
        hp_prev = start_nw
    alternate = True
    last_port = None
    for _n in range(2, num_meanders):
        hp = SNSPD.add_ref(hairpin)
        if alternate:
            hp.connect(2, hp_prev.ports[2])
        else:
            hp.connect(1, hp_prev.ports[1])
        last_port = hp.ports[2] if terminals_same_side else hp.ports[1]
        hp_prev = hp
        alternate = not alternate

    if extend_terminals:
        finish_se = SNSPD.add_ref(
            pg.straight(size=(wire_width, half_size), layer=qg.get_layer(layer))
        )
        if last_port is not None:
            finish_se.connect(2, last_port)
        SNSPD.add_port(port=finish_se.ports[1], name=2, layer=layer)
    else:
        SNSPD.add_port(port=last_port, name=2, layer=layer)

    SNSPD.add_port(port=start_nw.ports[1], name=1, layer=layer)

    SNSPD.info["num_squares"] = num_meanders * (xsize / wire_width)
    SNSPD.info["area"] = xsize * ysize
    SNSPD.info["xsize"] = xsize
    SNSPD.info["ysize"] = ysize
    SNSPD.flatten()
    SNSPDu = Device("snspd_basic")
    SNSPDu << pg.union(SNSPD, layer=qg.get_layer(layer))
    SNSPDu.add_ports(SNSPD.ports)
    SNSPDu.move(SNSPDu.center, (0, 0))
    return SNSPDu


@qg.device
def vertical(
    wire_width: float = 0.2,
    wire_pitch: float = 0.6,
    size: Tuple[int | float, int | float] = (5, 5),
    num_squares: int | None = None,
    extend: float | None = 1,
    num_pts: int = 50,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Creates an optimally-rounded SNSPD, with terminals in its center instead
    of the side.

    Args:
        wire_width (float): Width of the nanowire.
        wire_pitch (float): Pitch of the nanowire.
        size (tuple of int or float): Size of the detector.
        num_squares (int | None): Number of squares in the detector.
        extend (bool | None): Whether or not to extend the ports.
        num_pts (int): number of points to use for optimal hairpin.
        layer (LayerSpec): GDS layer

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

    D = Device()

    S = basic(
        wire_width=wire_width,
        wire_pitch=wire_pitch,
        size=size,
        num_squares=num_squares,
        extend_terminals=False,
        terminals_same_side=False,
        layer=layer,
        num_pts=num_pts,
    )
    D << S

    T = pg.optimal_90deg(width=wire_width, layer=qg.get_layer(layer))
    t1 = D << T
    t1.move(np.subtract(S.ports[1].center, t1.ports[2].center))
    t1.movex(T.xsize - wire_width / 2)

    t2 = D << T
    t2.rotate(180)
    t2.move(np.subtract(S.ports[2].center, t2.ports[2].center))
    t2.movex(-T.xsize + wire_width / 2)

    ports = []
    if extend is not None:
        E = pg.straight(size=(wire_width, extend), layer=qg.get_layer(layer))
        e1 = D << E
        e1.connect(port=e1.ports[1], destination=t1.ports[1])
        e2 = D << E
        e2.connect(port=e2.ports[1], destination=t2.ports[1])
        ports.append(e1.ports[2])
        ports.append(e2.ports[2])
    else:
        ports.append(t1.ports[1])
        ports.append(t2.ports[1])
    Du = Device("snspd_vert")
    Du << pg.union(D, layer=qg.get_layer(layer))
    Du.flatten()
    for p, port in enumerate(ports):
        Du.add_port(
            name=p + 1,
            port=port,
            layer=layer,
        )
    return Du
