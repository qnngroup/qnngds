"""Layouts for resistors and resistors with superconducting contacts."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import qnngds as qg
import phidl.geometry as pg

import numpy as np

from qnngds.typing import LayerSpec, LayerSpecs
from qnngds import Device


@qg.device
def meander(
    width: float = 2,
    pitch: float = 4,
    squares: float = 100,
    max_length: float | None = 20,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Create resistor meander with specified number of squares.

    If squares*width > max_length or max_length is None, meander the resistor,
    destinationwise just return a straight line.

    Args:
        width (float): wire width in microns
        pitch (float): desired pitch of meander in microns
        squares (float or None): desired number of squares
        max_length (float): desired length of device
        layer (LayerSpec): GDS layer

    Returns:
        Device: the resistor meander
    """
    D = Device()

    meander_spacing = (pitch - width) / width

    if max_length is None or width * squares < max_length:
        # just make a straight
        straight = D << pg.straight(
            size=(width, width * squares), layer=qg.get_layer(layer)
        )
        D.add_port(name=1, port=straight.ports[1], layer=layer)
        D.add_port(name=2, port=straight.ports[2], layer=layer)
        return D

    # make meander
    def hairpin(hp_length):
        """Create hairpin used in meander."""
        H = Device()
        straight = pg.rectangle(
            size=(hp_length - width, width), layer=qg.get_layer(layer)
        )
        conn = pg.rectangle(
            size=(width, (2 + meander_spacing) * width), layer=qg.get_layer(layer)
        )
        for i in range(2):
            s = H << straight
            s.move((-s.xmax, -s.ymin + (1 + meander_spacing) * width * i))
        c = H << conn
        c.move((-c.xmin, -c.ymin))
        H.add_port(
            name=1,
            midpoint=(-hp_length + width, width / 2),
            width=width,
            orientation=180,
            layer=layer,
        )
        H.add_port(
            name=2,
            midpoint=(-hp_length + width, (1 + meander_spacing) * width + width / 2),
            width=width,
            orientation=180,
            layer=layer,
        )
        return H

    def stub(orientation):
        """Create stub to connect to meander ends."""
        S = Device()
        straight = pg.rectangle(size=(width, 2 * width), layer=qg.get_layer(layer))
        s = S << straight
        s.move((-s.x, -s.ymin))
        S.add_port(
            name=1,
            midpoint=(0, width / 2),
            width=width,
            orientation=orientation,
            layer=layer,
        )
        S.add_port(
            name=2,
            midpoint=(0, 2 * width),
            width=width,
            orientation=90,
            layer=layer,
        )
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
    # round to nearest 2nm, since gdsfactory rounds to nearest 1nm which can cause gaps between each hairpin
    hp_length = max(hp_length, width)
    hp = hairpin(hp_length)
    hp_prev = None
    for i in range(n_turn):
        hp_i = D << hp
        if hp_prev is not None:
            hp_i.connect(
                port=hp_i.ports[2 - (i % 2)],
                destination=hp_prev.ports[2 - (i % 2)],
            )
        else:
            stub_top = D << stub(0)
            stub_top.connect(
                port=stub_top.ports[1],
                destination=hp_i.ports[2],
            )
        hp_prev = hp_i
    stub_bot = D << stub(180 * (n_turn % 2))
    stub_bot.connect(
        port=stub_bot.ports[1], destination=hp_prev.ports[2 - (n_turn % 2)]
    )
    Du = Device("resistor")
    Du << pg.union(D, layer=qg.get_layer(layer))
    Du.flatten()
    for name, port in zip((1, 2), (stub_top.ports[2], stub_bot.ports[2])):
        Du.add_port(name=name, port=port)
    return Du


@qg.device
def meander_sc_contacts(
    width: float = 1,
    squares: float = 60,
    max_length: float | None = 10,
    meander_pitch: float | None = 2,
    contact_size: tuple[float, float] = (8, 3),
    outline_contacts: float = 1,
    layer_res: LayerSpec = "PHOTO1",
    layer_contacts: LayerSpecs = ["EBEAM_FINE", "PHOTO2"],
    layer_keepout: LayerSpecs = ["EBEAM_KEEPOUT"],
) -> Device:
    """Create resistor meander with superconducting contacts.

    If squares*width > max_length or if max_length is None, meander the resistor.

    Args:
        width (float): width of resistor
        squares (float): desired number of squares
        max_length (float or None): maximum desired length of device
        meander_pitch (float or None): desired pitch of meander in microns
        contact_size (tuple[float, float]): (width, height) of resistor<->superconductor contact
        outline_contacts (float): superconductor extra width on each side of contact
        layer_res (LayerSpec): resistor GDS layer
        layer_contacts (LayerSpecs): layer(s) for contact to superconductor (first will define port layer)
        layer_keepout (LayerSpecs): layer(s) to do keepout on

    Returns:
        Device: the resistor meander
    """
    D = Device()

    if meander_pitch is None:
        meander_pitch = np.inf

    if len(layer_contacts) < 1:
        raise ValueError(f"must have at least one contact layer, got {layer_contacts}")

    res = D << meander(
        layer=layer_res,
        width=width,
        pitch=max(meander_pitch, width + 1),
        squares=squares,
        max_length=max_length,
    )
    for layer in layer_keepout:
        res_ko = D << pg.rectangle(
            size=(res.xsize + 2 * width, res.ysize),
            layer=qg.get_layer(layer),
        )
        res_ko.move(res_ko.center, res.center)
    stub = pg.compass(
        size=(width, outline_contacts),
        layer=qg.get_layer(layer_res),
    )
    contact = pg.compass(
        size=contact_size,
        layer=qg.get_layer(layer_res),
    )
    contacts = []
    for layer in layer_contacts:
        contacts.append(
            pg.compass(
                size=(
                    contact_size[0] + 2 * outline_contacts,
                    contact_size[1] + 2 * outline_contacts,
                ),
                layer=qg.get_layer(layer),
            )
        )
    ports = []
    dir_lut = {1: "W", 2: "N", 3: "E", 4: "S"}
    for p, port in enumerate(res.ports):
        s = D << stub
        s.connect(port=s.ports["S"], destination=res.ports[port])
        c = D << contact
        c.connect(port=c.ports["S"], destination=s.ports["N"])
        for i, con_sc in enumerate(contacts):
            c_sc = D << con_sc
            c_sc.center = c.center
            if i == 0:
                ports.append(c_sc.ports[dir_lut[2 + 2 * (p % 2)]])

    Du = Device("resistor_contacts")
    Du << pg.union(D, by_layer=True)
    Du.flatten()
    for name, port in zip((1, 2), ports):
        Du.add_port(name=name, port=port)
    return Du
