"""Nanocryotron `[1] <https://doi.org/10.1021/nl502629x>`_ variants."""

import gdsfactory as gf

from typing import Tuple, Optional


@gf.cell
def smooth(
    choke_w: float = 0.03,
    gate_w: float = 0.2,
    channel_w: float = 0.1,
    source_w: float = 0.3,
    drain_w: float = 0.3,
    choke_shift: float = -0.3,
    layer: int = 1,
) -> gf.Component:
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

    D = gf.Component()

    choke = gf.components.superconductors.optimal_step(
        gate_w, choke_w, symmetric=True, num_pts=100, layer=layer
    )
    k = D << choke

    channel = gf.components.compass(
        size=(channel_w, choke_w), layer=layer, port_type="optical"
    )
    c = D << channel
    c.connect(port=c.ports["o1"], other=k.ports["e2"], allow_width_mismatch=True)

    drain = gf.components.superconductors.optimal_step(
        drain_w, channel_w, symmetric=False, num_pts=100, layer=layer
    )
    d = D << drain
    d.connect(port=d.ports["e2"], other=c.ports["o2"])

    source = gf.components.superconductors.optimal_step(
        channel_w, source_w, symmetric=False, num_pts=100, layer=layer
    )
    s = D << source
    s.connect(port=s.ports["e1"], other=c.ports["o4"])

    k.movey(choke_shift)

    D.add_port(name="g", port=k.ports["e1"], port_type="electrical")
    D.add_port(name="s", port=s.ports["e2"], port_type="electrical")
    D.add_port(name="d", port=d.ports["e1"], port_type="electrical")

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
) -> gf.Component:
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

    D = gf.Component()

    choke = gf.components.tapers.taper(choke_l, gate_w, choke_w, layer=layer)
    k = D << choke

    channel = gf.components.compass(
        size=(channel_w, channel_l), layer=layer, port_type="optical"
    )
    c = D << channel
    c.connect(port=c.ports["o1"], other=k.ports["o2"], allow_width_mismatch=True)

    drain = gf.components.tapers.taper(drain_l, channel_w, drain_w, layer=layer)
    d = D << drain
    d.connect(port=d.ports["o1"], other=c.ports["o2"])

    source = gf.components.tapers.taper(source_l, channel_w, source_w, layer=layer)
    s = D << source
    s.connect(port=s.ports["o1"], other=c.ports["o4"])

    D.add_port(name="g", port=k.ports["o1"], port_type="electrical")
    D.add_port(name="s", port=s.ports["o2"], port_type="electrical")
    D.add_port(name="d", port=d.ports["o2"], port_type="electrical")
    return D
