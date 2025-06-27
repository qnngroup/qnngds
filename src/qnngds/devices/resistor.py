"""Layouts for resistors and resistors with superconducting contacts."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import gdsfactory as gf
import numpy as np

import qnngds as qg

from gdsfactory.typings import LayerSpec


@gf.cell
def meander(
    width: float = 2,
    pitch: float = 4,
    squares: float = 100,
    max_length: float | None = 20,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Create resistor meander with specified number of squares.

    If squares*width > max_length or max_length is None, meander the resistor,
    otherwise just return a straight line.

    Args:
        width (float): wire width in microns
        pitch (float): desired pitch of meander in microns
        squares (float or None): desired number of squares
        max_length (float): desired length of device
        layer (LayerSpec): GDS layer
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: the resistor meander
    """
    D = gf.Component()

    meander_spacing = (pitch - width) / width

    if max_length is None or width * squares < max_length:
        # just make a straight
        straight = D << qg.geometries.compass(
            size=(width, width * squares), layer=layer, port_type="electrical"
        )
        D.add_port(name="e1", port=straight.ports["e2"])
        D.add_port(name="e2", port=straight.ports["e4"])
        return D

    # make meander
    def hairpin(hp_length):
        """Create hairpin used in meander."""
        H = gf.Component()
        straight = qg.geometries.compass(size=(hp_length - width, width), layer=layer)
        conn = qg.geometries.compass(
            size=(width, (2 + meander_spacing) * width), layer=layer
        )
        for i in range(2):
            s = H << straight
            s.move((-s.xmax, -s.ymin + (1 + meander_spacing) * width * i))
        c = H << conn
        c.move((-c.xmin, -c.ymin))
        H.add_port(
            name="e1",
            center=(-hp_length + width, width / 2),
            width=width,
            orientation=180,
            port_type="electrical",
            layer=layer,
        )
        H.add_port(
            name="e2",
            center=(-hp_length + width, (1 + meander_spacing) * width + width / 2),
            width=width,
            orientation=180,
            port_type="electrical",
            layer=layer,
        )
        return H

    def stub(orientation):
        """Create stub to connect to meander ends."""
        S = gf.Component()
        straight = qg.geometries.compass(size=(width, 2 * width), layer=layer)
        s = S << straight
        s.move((-s.x, -s.ymin))
        S.add_port(
            name="e1",
            center=(0, width / 2),
            width=width,
            orientation=orientation,
            port_type="electrical",
            layer=layer,
        )
        S.add_port(
            name="e2",
            center=(0, 2 * width),
            width=width,
            orientation=90,
            port_type="electrical",
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
    hp_length = np.round(hp_length / (2 * gf.kcl.dbu)) * (gf.kcl.dbu * 2)
    hp_length = max(hp_length, width + 2 * gf.kcl.dbu)
    hp = hairpin(hp_length)
    hp_prev = None
    for i in range(n_turn):
        hp_i = D << hp
        if hp_prev is not None:
            hp_i.connect(
                port=hp_i.ports[f"e{2 - (i % 2)}"],
                other=hp_prev.ports[f"e{2 - (i % 2)}"],
            )
        else:
            stub_top = D << stub(0)
            stub_top.connect(
                port=stub_top.ports["e1"],
                other=hp_i.ports["e2"],
                allow_width_mismatch=True,
            )
        hp_prev = hp_i
    stub_bot = D << stub(180 * (n_turn % 2))
    stub_bot.connect(
        port=stub_bot.ports["e1"], other=hp_prev.ports[f"e{2 - (n_turn % 2)}"]
    )
    Du = gf.Component()
    Du << qg.utilities.union(D)
    Du.flatten()
    for name, port in zip(("e1", "e2"), (stub_top.ports["e2"], stub_bot.ports["e2"])):
        Du.add_port(
            name=name,
            port=port,
        )
    for port in Du.ports:
        port.port_type = port_type
    return Du


@gf.cell
def meander_sc_contacts(
    width: float = 1,
    squares: float = 60,
    max_length: float | None = 10,
    meander_pitch: float | None = 2,
    contact_size: tuple[float, float] = (8, 3),
    outline_sc: float = 1,
    layer_res: LayerSpec = (4, 0),
    layer_sc: LayerSpec = (1, 0),
    layer_keepout: LayerSpec | None = (3, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Create resistor meander with superconducting contacts.

    If squares*width > max_length or if max_length is None, meander the resistor.

    Args:
        width (float): width of resistor
        squares (float): desired number of squares
        max_length (float or None): maximum desired length of device
        meander_pitch (float or None): desired pitch of meander in microns
        contact_size (tuple[float, float]): (width, height) of resistor<->superconductor contact
        outline_sc (float): superconductor extra width on each side of contact
        layer_res (LayerSpec): resistor GDS layer
        layer_sc (LayerSpec): superconductor GDS layer
        layer_keepout (LayerSpec): layer to do keepout on
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: the resistor meander
    """
    D = gf.Component()

    if meander_pitch is None:
        meander_pitch = np.inf

    res = D << meander(
        layer=layer_res,
        width=width,
        pitch=max(meander_pitch, width + 1),
        squares=squares,
        max_length=max_length,
    )
    if layer_keepout is not None:
        res_ko = D << qg.geometries.rectangle(
            size=(res.xsize + 2 * width, res.ysize), layer=layer_keepout
        )
        res_ko.move(res_ko.center, res.center)
    stub = qg.geometries.compass(
        size=(width, outline_sc), layer=layer_res, port_type="electrical"
    )
    contact = qg.geometries.compass(
        size=contact_size, layer=layer_res, port_type="electrical"
    )
    contact_sc = qg.geometries.compass(
        size=(contact_size[0] + 2 * outline_sc, contact_size[1] + 2 * outline_sc),
        layer=layer_sc,
        port_type="electrical",
    )
    ports = []
    for p, port in enumerate(res.ports):
        s = D << stub
        s.connect(port=s.ports["e4"], other=port)
        c = D << contact
        c.connect(port=c.ports["e4"], other=s.ports["e2"], allow_width_mismatch=True)
        c_sc = D << contact_sc
        c_sc.center = c.center
        ports.append(c_sc.ports[f"e{2 + 2 * (p % 2)}"])

    Du = gf.Component()
    Du << qg.utilities.union(D)
    Du.flatten()
    for name, port in zip(("e1", "e2"), ports):
        Du.add_port(
            name=name,
            port=port,
        )
    for port in Du.ports:
        port.port_type = port_type
    return Du
