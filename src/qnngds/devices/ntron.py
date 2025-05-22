"""Nanocryotron `[1] <https://doi.org/10.1021/nl502629x>`_ variants."""

import gdsfactory as gf
from gdsfactory.typings import ComponentSpec, LayerSpec

import qnngds as qg


@gf.cell
def smooth(
    choke_w: float = 0.03,
    gate_w: float = 0.2,
    channel_w: float = 0.2,
    source_w: float = 0.3,
    drain_w: float = 0.3,
    choke_shift: float = -0.3,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Creates a ntron device.

    Args:
        choke_w (float): Width of the choke region.
        gate_w (float): Width of the gate region.
        channel_w (float): Width of the channel region.
        source_w (float): Width of the source region.
        drain_w (float): Width of the drain region.
        choke_shift (float): Shift of the choke region.
        layer (LayerSpec): GDS layer
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: The ntron device.
    """

    D = gf.Component()

    choke = gf.components.superconductors.optimal_step(
        gate_w, choke_w, symmetric=True, num_pts=500, layer=layer
    )
    k = D << choke

    channel = gf.components.compass(
        size=(channel_w, choke_w), layer=layer, port_type="optical"
    )
    c = D << channel
    c.connect(port=c.ports["o1"], other=k.ports["e2"], allow_width_mismatch=True)
    c.move(c.center, (0, 0))

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

    k.move((c.xmin - k.xmax, choke_shift))

    Du = gf.Component()
    Du << qg.utilities.union(D)
    Du.flatten()

    for name, port in zip(
        ("g", "s", "d"), (k.ports["e1"], s.ports["e2"], d.ports["e1"])
    ):
        Du.add_port(name=name, port=port)
    for port in Du.ports:
        port.port_type = port_type

    return Du


@gf.cell
def sharp(
    choke_w: float = 0.03,
    gate_w: float = 0.2,
    channel_w: float = 0.1,
    source_w: float = 0.3,
    drain_w: float = 0.3,
    gate_sq: float = 10,
    channel_sq: float = 1,
    source_sq: float = 5,
    drain_sq: float = 5,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
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
        layer (LayerSpec): GDS layer
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        Device: The sharp ntron device.
    """

    D = gf.Component()

    gate_l = gate_sq * gate_w
    channel_l = channel_sq * channel_w
    drain_l = drain_sq * drain_w
    source_l = source_sq * source_w

    choke = qg.geometries.taper(
        gate_l, gate_w, choke_w, layer=layer, port_type="electrical"
    )
    k = D << choke

    channel = gf.components.compass(
        size=(channel_w, channel_l), layer=layer, port_type="electrical"
    )
    c = D << channel
    c.connect(port=c.ports["e1"], other=k.ports["e2"], allow_width_mismatch=True)
    D.move(c.center, (0, 0))

    drain = qg.geometries.taper(
        drain_l, channel_w, drain_w, layer=layer, port_type="electrical"
    )
    d = D << drain
    d.connect(port=d.ports["e1"], other=c.ports["e2"])

    source = qg.geometries.taper(
        source_l, channel_w, source_w, layer=layer, port_type="electrical"
    )
    s = D << source
    s.connect(port=s.ports["e1"], other=c.ports["e4"])

    Du = gf.Component()
    Du << qg.utilities.union(D)
    Du.flatten()

    for name, port in zip(
        ("g", "s", "d"), (k.ports["e1"], s.ports["e2"], d.ports["e2"])
    ):
        Du.add_port(name=name, port=port)
    for port in Du.ports:
        port.port_type = port_type

    return Du


@gf.cell
def slotted(
    base_spec: ComponentSpec = smooth,
    slot_width: int | float = 0.04,
    slot_length: int | float = 1.5,
    slot_pitch: int | float = 0.08,
    n_slot: int = 2,
) -> gf.Component:
    """Parallel-channel nanocryotron

    See `[1] <https://doi.org/10.1063/5.0180709>`_

    Args:
        base_spec (ComponentSpec): callable function that generates a gf.Component for the base nTron
        slot_width (int or float): width of each slot
        slot_length (int or float): length of each slot
        slot_pitch (int or float): pitch of slots
        n_slot (int): number of slots

    Returns:
        (gf.Component): nTron with slots

    """
    D = gf.Component()
    base = gf.get_component(base_spec)
    if n_slot == 0:
        return base

    # use optimal hairpin as template for slot
    hairpin = gf.components.optimal_hairpin(
        width=slot_pitch - slot_width,
        pitch=slot_pitch,
        length=slot_length / 2,
        turn_ratio=2,
        num_pts=300,
        layer=(1, 0),
    )
    slot_inv = gf.Component()
    hp1 = slot_inv.add_ref(hairpin)
    hp2 = slot_inv.add_ref(hairpin)
    hp2.mirror()
    hp2.connect(port=hp2.ports["e1"], other=hp1.ports["e1"])
    slot_inv.rotate(90)
    slot_inv.move(slot_inv.center, (0, 0))
    box = gf.components.shapes.bbox(slot_inv, layer=(1, 0))
    slot = gf.Component()
    slot.add_ref(gf.boolean(box, slot_inv, "-", layer=(1, 0)))

    # array slots
    slots = gf.Component()
    slots.add_ref(slot, columns=n_slot, rows=1, column_pitch=slot_pitch, row_pitch=0)
    slots.move(slots.center, (0, 0))
    D.add_ref(gf.boolean(base, slots, "-", layer=base.layers[0]))

    D.add_ports(base.ports)

    return D
