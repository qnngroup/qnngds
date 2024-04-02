"""Devices module contain the basic devices that QNN uses in its circuits (e.g.
ntron, htron etc)."""

from phidl import Device

# from phidl import quickplot as qp
# from phidl import set_quickplot_options
import phidl.geometry as pg
from typing import Tuple, Optional


def ntron(
    choke_w: float = 0.03,
    gate_w: float = 0.2,
    channel_w: float = 0.1,
    source_w: float = 0.3,
    drain_w: float = 0.3,
    choke_shift: float = -0.3,
    layer: int = 0,
) -> Device:
    """Creates a ntron device.

    Args:
        choke_w (float): Width of the choke region.
        gate_w (float): Width of the gate region.
        channel_w (float): Width of the channel region.
        source_w (float): Width of the source region.
        drain_w (float): Width of the drain region.
        choke_shift (float): Shift of the choke region.
        layer (int): Layer for the device to be created on.

    Returns:
        Device: The ntron device.
    """

    D = Device()

    choke = pg.optimal_step(gate_w, choke_w, symmetric=True, num_pts=100)
    k = D << choke

    channel = pg.compass(size=(channel_w, choke_w))
    c = D << channel
    c.connect(channel.ports["W"], choke.ports[2])

    drain = pg.optimal_step(drain_w, channel_w)
    d = D << drain
    d.connect(drain.ports[2], c.ports["N"])

    source = pg.optimal_step(channel_w, source_w)
    s = D << source
    s.connect(source.ports[1], c.ports["S"])

    k.movey(choke_shift)

    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(name=3, port=k.ports[1])
    D.add_port(name=1, port=d.ports[1])
    D.add_port(name=2, port=s.ports[2])
    D.name = f"NTRON {choke_w} {channel_w} "
    D.info = locals()

    return D


def ntron_compassPorts(
    choke_w: float = 0.03,
    gate_w: float = 0.2,
    channel_w: float = 0.1,
    source_w: float = 0.3,
    drain_w: float = 0.3,
    choke_shift: float = -0.3,
    layer: int = 0,
) -> Device:
    """Creates a ntron device with compass ports (i.e. N1, W1, S1 for drain,
    gate, source respectively).

    Args:
        choke_w (float): Width of the choke region.
        gate_w (float): Width of the gate region.
        channel_w (float): Width of the channel region.
        source_w (float): Width of the source region.
        drain_w (float): Width of the drain region.
        choke_shift (float): Shift of the choke region.
        layer (int): Layer for the device to be created on.

    Returns:
        Device: The ntron device.
    """

    D = Device()

    choke = pg.optimal_step(gate_w, choke_w, symmetric=True, num_pts=100)
    k = D << choke

    channel = pg.compass(size=(channel_w, choke_w))
    c = D << channel
    c.connect(channel.ports["W"], choke.ports[2])

    drain = pg.optimal_step(drain_w, channel_w)
    d = D << drain
    d.connect(drain.ports[2], c.ports["N"])

    source = pg.optimal_step(channel_w, source_w)
    s = D << source
    s.connect(source.ports[1], c.ports["S"])

    k.movey(choke_shift)

    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(name="N1", port=d.ports[1])
    D.add_port(name="S1", port=s.ports[2])
    D.add_port(name="W1", port=k.ports[1])
    D.name = f"NTRON {choke_w} {channel_w} "
    D.info = locals()

    return D


def ntron_sharp(
    choke_w: float = 0.03,
    choke_l: float = 0.5,
    gate_w: float = 0.2,
    channel_w: float = 0.1,
    source_w: float = 0.3,
    drain_w: float = 0.3,
    layer: int = 0,
) -> Device:
    """Creates a sharp ntron device.

    Args:
        choke_w (float): Width of the choke region.
        choke_l (float): Length of the choke region.
        gate_w (float): Width of the gate region.
        channel_w (float): Width of the channel region.
        source_w (float): Width of the source region.
        drain_w (float): Width of the drain region.
        layer (int): Layer for the device to be created on.

    Returns:
        Device: The sharp ntron device.
    """

    D = Device("nTron")

    choke = pg.taper(choke_l, gate_w, choke_w)
    k = D << choke

    channel = pg.compass(size=(channel_w, choke_w / 10))
    c = D << channel
    c.connect(channel.ports["W"], choke.ports[2])

    drain = pg.taper(channel_w * 6, drain_w, channel_w)
    d = D << drain
    d.connect(drain.ports[2], c.ports["N"])

    source = pg.taper(channel_w * 6, channel_w, source_w)
    s = D << source
    s.connect(source.ports[1], c.ports["S"])

    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(name="g", port=k.ports[1])
    D.add_port(name="d", port=d.ports[1])
    D.add_port(name="s", port=s.ports[2])
    D.name = "nTron"
    D.info = locals()
    return D


def nanowire(
    channel_w: float = 0.1, source_w: float = 0.3, layer: int = 0, num_pts: int = 100
) -> Device:
    """Creates a single wire, with the same appearance as an NTRON but without
    the gate.

    Args:
        channel_w (int or float): The width of the channel (at the hot-spot location).
        source_w (int or float): The width of the nanowire's "source".
        layer (int): The layer where to put the device.
        num_pts (int): The number of points comprising the optimal_steps geometries.

    Returns:
        Device: A device containing 2 optimal steps joined at their channel_w end.
    """

    NANOWIRE = Device(f"NANOWIRE {channel_w} ")
    wire = pg.optimal_step(channel_w, source_w, symmetric=True, num_pts=num_pts)
    source = NANOWIRE << wire
    gnd = NANOWIRE << wire
    source.connect(source.ports[1], gnd.ports[1])

    NANOWIRE.flatten(single_layer=layer)
    NANOWIRE.add_port(name=1, port=source.ports[2])
    NANOWIRE.add_port(name=2, port=gnd.ports[2])
    NANOWIRE.rotate(-90)
    NANOWIRE.move(NANOWIRE.center, (0, 0))

    return NANOWIRE


def snspd_vert(
    wire_width: float = 0.2,
    wire_pitch: float = 0.6,
    size: Tuple[int, int] = (6, 10),
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
        size (Tuple[int, int]): Size of the detector in squares (width, height).
        num_squares (Optional[int]): Number of squares in the detector.
        terminals_same_side (bool): Whether the terminals are on the same side of the detector.
        extend (Optional[bool]): Whether or not to extend the ports.
        layer (int): Layer for the device to be created on.

    Returns:
        Device: The vertical SNSPD device.
    """
    D = Device("snspd_vert")
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
    return D
