"""Layouts for resistors and resistors with superconducting contacts."""

from phidl import Device

import phidl.geometry as pg
from typing import Tuple, Optional


def meander(
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

    D.name = f"RESISTOR.MEANDER (w={width}, pitch={pitch})"
    D.info = locals()
    return D


def meander_sc_contacts(
    width: float = 1,
    squares: float = 60,
    max_length: float = 10,
    meander_pitch: float = 2,
    contact_width: float = 8,
    contact_height: float = 2,
    outline_sc: float = 1,
    width_routing: float = 1,
    layer_res: int = 3,
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
    MEAN_SC_CONT = Device(
        f"RESISTOR.MEANDER_SC_CONTACTS (w={width}, pitch={meander_pitch})"
    )
    CONTACTS = Device("CONTACTS")

    aspect_ratio = (contact_width + 2 * outline_sc) / max_length * 1.5
    res = MEAN_SC_CONT << meander(
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
        s = CONTACTS << stub
        s.connect(s.ports[1], port)
        c = CONTACTS << contact
        c.connect(c.ports[1], s.ports[2])
        c_sc = CONTACTS << contact_sc
        c_sc.center = c.center
        r = CONTACTS << rout
        r.connect(r.ports[1], c_sc.ports[2 - (p % 2)])
        ports.append(r.ports[2])

    CONTACTS = pg.union(CONTACTS, by_layer=True)
    CONTACTS.name = "CONTACTS"
    MEAN_SC_CONT << CONTACTS

    MEAN_SC_CONT.add_port(port=ports[0], name=1)
    MEAN_SC_CONT.add_port(port=ports[1], name=2)
    MEAN_SC_CONT.info = locals()
    return MEAN_SC_CONT
