"""Superconducting nanowire single photon detector geometries."""

import gdsfactory as gf
import numpy as np

import qnngds.utilities as qu

from typing import Tuple, Optional, Union


@gf.cell
def basic(
    wire_width: float = 0.2,
    wire_pitch: float = 0.6,
    size: Tuple[Optional[Union[int, float]], Optional[Union[int, float]]] = (10, 10),
    num_squares: Optional[int] = None,
    turn_ratio: Union[int, float] = 4,
    extend_terminals: bool = True,
    terminals_same_side: bool = False,
    layer: tuple = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Creates an optimally-rounded SNSPD.

    Modification of gdsfactory's and phidl's implementations

    Args:
        wire_width (float): Width of the nanowire.
        wire_pitch (float): Pitch of the nanowire.
        size (tuple of Optional[int or float]): Size of the detector in squares (width, height).
        num_squares (Optional[int]): Number of squares in the detector.
        turn_ratio (int or float): Specifies how much of the SNSPD width is
            dedicated to the 180 degree turn. A turn_ratio of 10 will result in 20%
            of the width being comprised of the turn.
        extend_terminals (bool): If True, bring ports flush to edges of device
        terminals_same_side (bool): If True, both ports will be located on the
            same side of the SNSPD.
        layer (tuple): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

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

    if num_squares is not None and (
        (size is None) or ((size[0] is None) and (size[1]) is None)
    ):
        xy = np.sqrt(num_squares * wire_pitch * wire_width)
        size = [xy, xy]
        num_squares = None
    if [size[0], size[1], num_squares].count(None) != 1:
        raise ValueError(
            "[qnngds] snspd() requires that exactly ONE value of "
            "the arguments ``num_squares`` and ``size`` be None "
            "to prevent overconstraining, for example:\n"
            ">>> snspd(size = (3, None), num_squares = 2000)"
        )
    if size[0] is None:
        ysize = size[1] * wire_width
        xsize = num_squares * wire_pitch * wire_width / ysize
    elif size[1] is None:
        xsize = size[0] * wire_width
        ysize = num_squares * wire_pitch * wire_width / xsize
    else:
        xsize = size[0] * wire_width
        ysize = size[1] * wire_width

    num_meanders = int(np.ceil(ysize / wire_pitch))

    half_size = xsize / 2 + turn_ratio * wire_width

    SNSPD = gf.Component()
    hairpin = gf.components.superconductors.optimal_hairpin(
        width=wire_width,
        pitch=wire_pitch,
        turn_ratio=turn_ratio,
        length=half_size,
        num_pts=20,
        layer=layer,
    )

    if not terminals_same_side and (num_meanders % 2) == 0:
        num_meanders += 1
    elif terminals_same_side and (num_meanders % 2) == 1:
        num_meanders += 1

    if extend_terminals:
        start_nw = SNSPD.add_ref(
            gf.c.compass(
                size=(half_size, wire_width), layer=layer, port_type="electrical"
            )
        )
        hp_prev = SNSPD.add_ref(hairpin)
        hp_prev.connect("e1", start_nw.ports["e3"])
    else:
        start_nw = SNSPD.add_ref(hairpin)
        hp_prev = start_nw
    alternate = True
    last_port = None
    for _n in range(2, num_meanders):
        hp = SNSPD.add_ref(hairpin)
        if alternate:
            hp.connect("e2", hp_prev.ports["e2"])
        else:
            hp.connect("e1", hp_prev.ports["e1"])
        last_port = hp.ports["e2"] if terminals_same_side else hp.ports["e1"]
        hp_prev = hp
        alternate = not alternate

    if extend_terminals:
        finish_se = SNSPD.add_ref(
            gf.c.compass(
                size=(half_size, wire_width), layer=layer, port_type="electrical"
            )
        )
        if last_port is not None:
            finish_se.connect("e3", last_port)
        SNSPD.add_port(port=finish_se.ports["e1"], name="e2")
    else:
        SNSPD.add_port(port=last_port, name="e2")

    SNSPD.add_port(port=start_nw.ports["e1"], name="e1")

    SNSPD.info["num_squares"] = num_meanders * (xsize / wire_width)
    SNSPD.info["area"] = xsize * ysize
    SNSPD.info["xsize"] = xsize
    SNSPD.info["ysize"] = ysize
    SNSPD.flatten()
    SNSPDu = gf.Component()
    SNSPDu << qu.union(SNSPD)
    SNSPDu.add_ports(SNSPD.ports)
    SNSPDu.move(SNSPDu.center, (0, 0))
    for port in SNSPDu.ports:
        port.port_type = port_type
    return SNSPDu


@gf.cell
def vertical(
    wire_width: float = 0.2,
    wire_pitch: float = 0.6,
    size: Tuple[Union[int, float], Union[int, float]] = (5, 5),
    num_squares: Optional[int] = None,
    extend: Optional[float] = 1,
    layer: tuple = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Creates an optimally-rounded SNSPD, with terminals in its center instead
    of the side.

    Args:
        wire_width (float): Width of the nanowire.
        wire_pitch (float): Pitch of the nanowire.
        size (tuple of int or float): Size of the detector in squares (width, height).
        num_squares (Optional[int]): Number of squares in the detector.
        extend (Optional[bool]): Whether or not to extend the ports.
        layer (tuple): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

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
    if extend is not None:
        E = gf.components.compass(size=(extend, wire_width), layer=layer)
        e1 = D << E
        e1.connect(e1.ports["e1"], t1.ports["e2"], allow_type_mismatch=True)
        e2 = D << E
        e2.connect(e2.ports["e1"], t2.ports["e2"], allow_type_mismatch=True)
        ports.append(e1.ports["e3"])
        ports.append(e2.ports["e3"])
    else:
        ports.append(t1.ports["e2"])
        ports.append(t2.ports["e2"])
    Du = gf.Component()
    Du << qu.union(D)
    Du.flatten()
    for p, port in enumerate(ports):
        Du.add_port(
            name=f"e{p + 1}",
            port=port,
        )
    for port in Du.ports:
        port.port_type = port_type
    return Du
