"""Nanocryotron `[1] <https://doi.org/10.1021/nl502629x>`_ variants."""

from phidl import Device
from phidl import Port

import phidl.geometry as pg
from typing import Tuple, Optional


def smooth(
    choke_w: float = 0.03,
    gate_w: float = 0.2,
    channel_w: float = 0.1,
    source_w: float = 0.3,
    drain_w: float = 0.3,
    choke_shift: float = -0.3,
    layer: int = 1,
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

    precision = 1e-6
    D = pg.union(D, precision=precision)
    D.flatten(single_layer=layer)
    # move ports towards device center by 2*precision
    names = ("g", "d", "s")
    for i, p in enumerate((k.ports[1], d.ports[1], s.ports[2])):
        dn = p.normal[1] - p.normal[0]
        D.add_port(
            name=names[i],
            port=Port(
                midpoint=p.center - 2 * dn * precision,
                width=p.width,
                orientation=p.orientation,
            ),
        )
    D.name = f"NTRON.SMOOTH(choke_w={choke_w}, channel_w={channel_w})"
    D.info = locals()

    return D


def sharp(
    choke_w: float = 0.03,
    choke_l: float = 0.5,
    gate_w: float = 0.2,
    channel_w: float = 0.1,
    channel_l: float = 0.1,
    source_w: float = 0.3,
    source_l: float = 1.5,
    drain_w: float = 0.3,
    drain_l: float = 1.5,
    layer: int = 1,
) -> Device:
    """Creates a sharp ntron device.

    Args:
        choke_w (float): Width of the choke region.
        choke_l (float): Length of the choke region.
        gate_w (float): Width of the gate region.
        channel_w (float): Width of the channel region.
        channel_l (float): Length of channel region.
        source_w (float): Width of the source region.
        source_l (float): Length of the source region.
        drain_w (float): Width of the drain region.
        drain_l (float): Length of the drain region.
        layer (int): Layer for the device to be created on.

    Returns:
        Device: The sharp ntron device.
    """

    D = Device()

    choke = pg.taper(choke_l, gate_w, choke_w)
    k = D << choke

    channel = pg.compass(size=(channel_w, channel_l))
    c = D << channel
    c.connect(channel.ports["W"], choke.ports[2])

    drain = pg.taper(drain_l, drain_w, channel_w)
    d = D << drain
    d.connect(drain.ports[2], c.ports["N"])

    source = pg.taper(source_l, channel_w, source_w)
    s = D << source
    s.connect(source.ports[1], c.ports["S"])

    precision = 1e-6
    D = pg.union(D, precision=precision)
    D.flatten(single_layer=layer)
    # move ports towards device center by 2*precision
    names = ("g", "d", "s")
    for i, p in enumerate((k.ports[1], d.ports[1], s.ports[2])):
        dn = p.normal[1] - p.normal[0]
        D.add_port(
            name=names[i],
            port=Port(
                midpoint=p.center - dn * precision,
                width=p.width,
                orientation=p.orientation,
            ),
        )
    D.name = f"NTRON.SHARP(choke_w={choke_w}, channel_w={channel_w})"
    D.info = locals()
    return D
