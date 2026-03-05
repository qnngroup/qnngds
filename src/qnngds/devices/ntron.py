"""Nanocryotron `[1] <https://doi.org/10.1021/nl502629x>`_ variants."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import qnngds as qg
import phidl.geometry as pg


from qnngds.typing import LayerSpec, DeviceSpec
from qnngds import Device


@qg.device
def smooth(
    choke_w: float = 0.03,
    gate_w: float = 0.2,
    channel_w: float = 0.2,
    source_w: float = 0.3,
    drain_w: float = 0.3,
    choke_shift: float = -0.3,
    num_pts: int = 100,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Creates a ntron device.

    Args:
        choke_w (float): Width of the choke region.
        gate_w (float): Width of the gate region.
        channel_w (float): Width of the channel region.
        source_w (float): Width of the source region.
        drain_w (float): Width of the drain region.
        choke_shift (float): Shift of the choke region.
        num_pts (int): number of points to use for optimal steps
        layer (LayerSpec): GDS layer specification

    Returns:
        (Device): The ntron device.
    """

    D = Device("ntron_smooth")

    choke = pg.optimal_step(
        start_width=gate_w,
        end_width=choke_w,
        symmetric=True,
        num_pts=num_pts,
        layer=qg.get_layer(layer),
    )
    k = D << choke

    channel = pg.compass(size=(channel_w, choke_w), layer=layer)
    c = D << channel
    c.connect(port=c.ports["W"], destination=k.ports[2])
    c.move(c.center, (0, 0))

    drain = pg.optimal_step(
        start_width=drain_w,
        end_width=channel_w,
        symmetric=False,
        num_pts=num_pts,
        layer=qg.get_layer(layer),
    )
    d = D << drain
    d.connect(port=d.ports[2], destination=c.ports["N"])

    source = pg.optimal_step(
        start_width=channel_w,
        end_width=source_w,
        symmetric=False,
        num_pts=num_pts,
        layer=qg.get_layer(layer),
    )
    s = D << source
    s.connect(port=s.ports[1], destination=c.ports["S"])

    k.move((c.xmin - k.xmax, choke_shift))

    Du = Device("ntron_smooth")
    Du << pg.union(D, layer=qg.get_layer(layer))
    Du.flatten()

    for name, port in zip(("g", "s", "d"), (k.ports[1], s.ports[2], d.ports[1])):
        Du.add_port(name=name, port=port)

    return Du


@qg.device
def sharp(
    choke_w: float = 0.03,
    gate_w: float = 0.2,
    channel_w: float = 0.1,
    source_w: float = 0.3,
    drain_w: float = 0.3,
    gate_sq: float = 2,
    channel_sq: float = 1,
    source_sq: float = 5,
    drain_sq: float = 5,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Creates a sharp ntron device.

    Args:
        choke_w (float): Width of the choke region.
        gate_w (float): Width of the gate region.
        gate_sq (float): Length of the gate region in squares.
        channel_w (float): Width of the channel region.
        channel_sq (float): Length of channel region in squares.
        source_w (float): Width of the source region.
        source_sq (float): Length of the source region in squares.
        drain_w (float): Width of the drain region.
        drain_sq (float): Length of the drain region in squares.
        layer (LayerSpec): GDS layer specification

    Returns:
        (Device): The sharp ntron device.
    """

    D = Device("ntron_sharp")

    gate_l = gate_sq * gate_w
    channel_l = channel_sq * channel_w
    drain_l = drain_sq * drain_w
    source_l = source_sq * source_w

    choke = qg.geometries.taper(
        length=gate_l,
        start_width=gate_w,
        end_width=choke_w,
        layer=layer,
    )
    k = D << choke

    channel = pg.compass(size=(channel_w, channel_l), layer=qg.get_layer(layer))
    c = D << channel
    c.connect(port=c.ports["W"], destination=k.ports[2])
    D.move(c.center, (0, 0))

    drain = qg.geometries.taper(
        length=drain_l,
        start_width=channel_w,
        end_width=drain_w,
        layer=layer,
    )
    d = D << drain
    d.connect(port=d.ports[1], destination=c.ports["N"])

    source = qg.geometries.taper(
        length=source_l,
        start_width=channel_w,
        end_width=source_w,
        layer=layer,
    )
    s = D << source
    s.connect(port=s.ports[1], destination=c.ports["S"])

    Du = Device("ntron_sharp")
    Du << pg.union(D, layer=qg.get_layer(layer))
    Du.flatten()

    for name, port in zip(("g", "s", "d"), (k.ports[1], s.ports[2], d.ports[2])):
        Du.add_port(name=name, port=port)

    return Du


@qg.device
def slotted(
    base_spec: DeviceSpec = smooth,
    slot_width: int | float = 0.04,
    slot_length: int | float = 1.5,
    slot_pitch: int | float = 0.08,
    n_slot: int = 2,
    num_pts: int = 100,
) -> Device:
    """Parallel-channel nanocryotron

    See `[1] <https://doi.org/10.1063/5.0180709>`_

    Args:
        base_spec (DeviceSpec): callable function that generates a Device for the base nTron
        slot_width (int or float): width of each slot
        slot_length (int or float): length of each slot
        slot_pitch (int or float): pitch of slots
        n_slot (int): number of slots
        num_pts (int): number of points to use for hairpin

    Returns:
        (Device): nTron with slots

    """
    D = Device("ntron_slotted")
    base = qg.get_device(base_spec)
    if n_slot == 0:
        return base

    base_layer = base.layers.copy().pop()

    # use optimal hairpin as template for slot
    hairpin = qg.geometries.optimal_hairpin(
        width=slot_pitch - slot_width,
        pitch=slot_pitch,
        length=slot_length / 2,
        turn_ratio=2,
        num_pts=num_pts,
        layer=(1, 0),
    )
    slot_inv = Device()
    hp1 = slot_inv.add_ref(hairpin)
    hp2 = slot_inv.add_ref(hairpin)
    hp2.mirror()
    hp2.connect(port=hp2.ports[1], destination=hp1.ports[1])
    slot_inv.rotate(90)
    slot_inv.move(slot_inv.center, (0, 0))
    box = pg.bbox(slot_inv.bbox, layer=(1, 0))
    slot = Device()
    slot.add_ref(pg.kl_boolean(A=box, B=slot_inv, operation="A-B", layer=(1, 0)))

    # array slots
    slots = Device()
    slots.add_array(slot, columns=n_slot, rows=1, spacing=(slot_pitch, 0))
    slots.move(slots.center, (0, 0))
    D.add_ref(
        pg.kl_boolean(
            A=base,
            B=slots,
            operation="A-B",
            layer=qg.get_layer(base_layer),
        )
    )

    D.add_ports(base.ports)

    return D
