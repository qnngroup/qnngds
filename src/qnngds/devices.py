"""Devices module contain the basic devices that QNN uses in its circuits (e.g.
ntron, htron etc)."""

from phidl import Device

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


def resistor_meander(
    width: float = 2,
    pitch: float = 4,
    squares: float = 100,
    max_length: float = 20,
    aspect_ratio: float = 1,
    layer: int = 1,
) -> Device:
    """Create resistor meander with specified number of squares.

    If squares*width > max_length, meander the resistor, otherwise just return a straight line

    Args:
        width (float): width in microns
        pitch (float): desired pitch of meander in microns
        squares (float): desired number of squares
        max_length (float): desired length of device
        aspect_ratio (float): desired w/h ratio of meander
        layer (int): GDS layer

    Returns:
        D (Device): the resistor meander
    """
    D = Device("resistor_meander")

    meander_spacing = (pitch - width) / width

    if width * squares < max_length:
        # just make a straight
        return pg.straight(size=(width, width * squares), layer=layer)

    # make meander
    def hairpin(hp_length):
        """Create hairpin used in meander."""
        H = Device("hairpin")
        straight = pg.rectangle(size=(hp_length - width, width), layer=layer)
        conn = pg.rectangle(size=(width, (2 + meander_spacing) * width), layer=layer)
        for i in range(2):
            s = H << straight
            s.move((-s.xmax, -s.ymin + (1 + meander_spacing) * width * i))
        c = H << conn
        c.move((-c.xmin, -c.ymin))
        H = pg.union(H, by_layer=True)
        H.add_port(
            name=1,
            midpoint=(-hp_length + width, width / 2),
            width=width,
            orientation=180,
        )
        H.add_port(
            name=2,
            midpoint=(-hp_length + width, (1 + meander_spacing) * width + width / 2),
            width=width,
            orientation=180,
        )
        return H

    def stub(orientation):
        """Create stub to connect to meander ends."""
        S = Device("stub")
        straight = pg.rectangle(size=(width, 2 * width), layer=layer)
        s = S << straight
        s.move((-s.x, -s.ymin))
        S.add_port(
            name=1, midpoint=(0, width / 2), width=width, orientation=orientation
        )
        S.add_port(name=2, midpoint=(0, 2 * width), width=width, orientation=90)
        return S

    # solve system for hp_length, n_turn given squares, pitch, aspect_ratio, width:
    # squares = 2 * (2 * hp_length/width + 0.5) * n_turn
    # width_meander = 2 * hp_length
    # height_meander = 2 * pitch * n_turn
    # width_meander/height_meander = aspect_ratio
    #
    # double number of hairpins
    squares -= 2  # account for extra squares from stubs
    n_turn = int(
        2
        * ((16 * aspect_ratio * squares * pitch * width + width**2) ** 0.5 - width)
        / (8 * aspect_ratio * pitch)
    )
    hp_length = (squares / n_turn - 0.5) * width / 2
    hp = hairpin(hp_length)
    hp_prev = None
    for i in range(n_turn):
        hp_i = D << hp
        if hp_prev is not None:
            hp_i.connect(hp_i.ports[2 - (i % 2)], hp_prev.ports[2 - (i % 2)])
        else:
            stub_top = D << stub(0)
            stub_top.connect(stub_top.ports[1], hp_i.ports[2])
        hp_prev = hp_i
    stub_bot = D << stub(180 * (n_turn % 2))
    stub_bot.connect(stub_bot.ports[1], hp_prev.ports[2 - (n_turn % 2)])
    D = pg.union(D, by_layer=True, precision=0.01)
    D.add_port(name=1, port=stub_top.ports[2])
    D.add_port(name=2, port=stub_bot.ports[2])
    D.info = locals()
    return D


def resistor_sc_contacts(
    width: float = 1,
    squares: float = 60,
    max_length: float = 10,
    meander_pitch: float = 2,
    contact_width: float = 8,
    contact_height: float = 2,
    outline_sc: float = 1,
    width_routing: float = 1,
    layer_res: int = 2,
    layer_sc: int = 1,
) -> Device:
    """Create resistor meander with superconducting contacts.

    If squares*width > max_length, meander the resistor.

    Args:
        width (float): width of resistor
        squares (float): desired number of squares
        max_length (float): desired length of device
        meander_pitch (float): desired pitch of meander in microns
        contact_width (float): width of resistor<->superconductor contact
        contact_height (float): height of resistor<->superconductor contact
        outline_sc (float): superconductor extra width on each side of contact
        width_routing (float): width of routing connections on superconducting layer
        layer_res (int): GDS layer for resistor
        layer_sc (int): GDS layer for superconductor

    Returns:
        D (Device): the resistor meander
    """
    D = Device("resistor_negtone")
    aspect_ratio = (contact_width + 2 * outline_sc) / max_length * 1.5
    res = D << resistor_meander(
        layer=layer_res,
        width=width,
        pitch=max(meander_pitch, width + 1),
        squares=squares,
        max_length=max_length,
        aspect_ratio=aspect_ratio,
    )
    stub = pg.straight(size=(width, outline_sc), layer=layer_res)
    contact = pg.straight(size=(contact_width, contact_height), layer=layer_res)
    contact_sc = pg.straight(
        size=(contact_width + 2 * outline_sc, contact_height + 2 * outline_sc),
        layer=layer_sc,
    )
    rout = pg.straight(size=(width_routing, 2 * width_routing), layer=layer_sc)
    ports = []
    for p, port in res.ports.items():
        s = D << stub
        s.connect(s.ports[1], port)
        c = D << contact
        c.connect(c.ports[1], s.ports[2])
        c_sc = D << contact_sc
        c_sc.center = c.center
        r = D << rout
        r.connect(r.ports[1], c_sc.ports[2 - (p % 2)])
        ports.append(r.ports[2])
    D = pg.union(D, by_layer=True)
    D.add_port(port=ports[0], name=1)
    D.add_port(port=ports[1], name=2)
    D.info = locals()
    return D
