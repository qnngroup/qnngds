"""Layouts for resistors and resistors with superconducting contacts."""

import numpy as np

from phidl import Device

import phidl.geometry as pg
from typing import Tuple, Optional


def meander(
    width: float = 2,
    pitch: float = 4,
    squares: float = 100,
    max_length: Optional[float] = 20,
    layer: int = 1,
) -> Device:
    """Create resistor meander with specified number of squares.

    If squares*width > max_length or max_length is None, meander the resistor,
    otherwise just return a straight line.

    Args:
        width (float): wire width in microns
        pitch (float): desired pitch of meander in microns
        squares (float or None): desired number of squares
        max_length (float): desired length of device
        layer (int): GDS layer

    Returns:
        D (Device): the resistor meander
    """
    D = Device("resistor_meander")

    meander_spacing = (pitch - width) / width

    if max_length is None or width * squares < max_length:
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

    # solve system for hairpin length (hp_length), number of (double) turns (n_turn),
    # meander width (width_m) given:
    #   - meander height (height),
    #   - number of squares (squares),
    #   - meander pitch (pitch),
    #   - wire width (width)
    n_turn = int(np.ceil((max_length - 3 * width) / pitch))
    # calculate the hairpin length
    # correction of 1.09 is the total number of squares contributed by the two
    # corners of the hairpin
    # ================+
    #                 |
    # ================+
    # = : squares / n_turn squares
    # | : (pitch - width) / width squares
    # + : 1.09 squares
    # squares - 3.09 for corners connecting meander to contacts
    # these contributions lead to the following equation for the toal number of squares
    # n_turn * (2*hp_length/width + 1.09 + (pitch - width) / width) = squares - 3.09
    hp_length = (
        (squares - 3.09) / n_turn - 1.09 - (pitch - width) / width
    ) * width / 2 + width
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
    max_length: Optional[float] = 10,
    meander_pitch: Optional[float] = 2,
    contact_size: Tuple[float, float] = (8, 3),
    outline_sc: float = 1,
    layer_res: int = 3,
    layer_sc: int = 1,
) -> Device:
    """Create resistor meander with superconducting contacts.

    If squares*width > max_length or if max_length is None, meander the resistor.

    Args:
        width (float): width of resistor
        squares (float): desired number of squares
        max_length (float or None): maximum desired length of device
        meander_pitch (float or None): desired pitch of meander in microns
        contact_size (tuple[float, float]): (width, height) of resistor<->superconductor contact
        outline_sc (float): superconductor extra width on each side of contact
        layer_res (int): GDS layer for resistor
        layer_sc (int): GDS layer for superconductor

    Returns:
        D (Device): the resistor meander
    """
    MEAN_SC_CONT = Device(
        f"RESISTOR.MEANDER_SC_CONTACTS (w={width}, pitch={meander_pitch})"
    )
    CONTACTS = Device("CONTACTS")

    if meander_pitch is None:
        meander_pitch = np.inf

    res = MEAN_SC_CONT << meander(
        layer=layer_res,
        width=width,
        pitch=max(meander_pitch, width + 1),
        squares=squares,
        max_length=max_length,
    )
    stub = pg.straight(size=(width, outline_sc), layer=layer_res)
    contact = pg.straight(size=contact_size, layer=layer_res)
    contact_sc = pg.straight(
        size=(contact_size[0] + 2 * outline_sc, contact_size[1] + 2 * outline_sc),
        layer=layer_sc,
    )
    ports = []
    for p, port in res.ports.items():
        s = CONTACTS << stub
        s.connect(s.ports[1], port)
        c = CONTACTS << contact
        c.connect(c.ports[1], s.ports[2])
        c_sc = CONTACTS << contact_sc
        c_sc.center = c.center
        ports.append(c_sc.ports[2 - (p % 2)])

    CONTACTS = pg.union(CONTACTS, by_layer=True)
    CONTACTS.name = "CONTACTS"
    MEAN_SC_CONT << CONTACTS

    MEAN_SC_CONT.add_port(port=ports[0], name=1)
    MEAN_SC_CONT.add_port(port=ports[1], name=2)
    MEAN_SC_CONT.info = locals()
    return MEAN_SC_CONT
