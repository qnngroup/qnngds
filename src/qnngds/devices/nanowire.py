"""Single nanowire constriction."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import gdsfactory as gf

from gdsfactory.typings import LayerSpec

import qnngds as qg


@gf.cell
def variable_length(
    constr_width: float = 0.1,
    wire_width: float = 0.3,
    length: float = 1,
    num_pts: int = 100,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Creates a single wire, made of two optimal steps from constr_width to
    wire_width with a constriction of the chosen length in the middle.

    Args:
        constr_width (int or float): The width of the channel (at the hot-spot location).
        wire_width (int or float): The width of connections to source/drain
        length (int or float): The length of the interior constriction.
        num_pts (int): The number of points comprising the optimal_steps geometries.
        layer (LayerSpec): GDS layer
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: 2 optimal steps to/from a narrow wire.

    Raises:
        ValueError if constr_width > wire_width
    """
    NANOWIRE = gf.Component()
    if constr_width > wire_width:
        raise ValueError(
            f"constriction width {constr_width=} cannot be larger than wire width {wire_width=}"
        )
    # if constriction and wire width are the same, just return a straight wire
    if constr_width == wire_width:
        constr = NANOWIRE << gf.components.compass(
            size=(constr_width, length), layer=layer, port_type="electrical"
        )
        constr.center = (0, 0)
        NANOWIRE.add_port(name="e1", port=constr.ports["e2"])
        NANOWIRE.add_port(name="e2", port=constr.ports["e4"])
        return NANOWIRE
    # otherwise, create tapers
    wire = gf.components.superconductors.optimal_step(
        constr_width, wire_width, symmetric=True, num_pts=num_pts, layer=layer
    )
    top = NANOWIRE << wire
    bot = NANOWIRE << wire
    if length > 0:
        compass_size = (constr_width, length)
        constr = NANOWIRE << gf.components.compass(
            size=compass_size, layer=layer, port_type="electrical"
        )
        constr.center = [0, 0]
        top.connect(
            port=top.ports["e1"], other=constr.ports["e2"], allow_type_mismatch=True
        )
        bot.connect(
            port=bot.ports["e1"], other=constr.ports["e4"], allow_type_mismatch=True
        )
    else:
        bot.rotate(90)
        bot.move(bot.ports["e1"].center, (0, 0))
        top.connect(
            port=top.ports["e1"], other=bot.ports["e1"], allow_type_mismatch=True
        )
    for p, port in enumerate([top.ports["e2"], bot.ports["e2"]]):
        NANOWIRE.add_port(name=f"e{p + 1}", port=port)
    for port in NANOWIRE.ports:
        port.port_type = port_type

    return NANOWIRE


@gf.cell
def sharp(
    constr_width: float = 0.1,
    wire_width: float = 0.3,
    length: float = 1,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Creates a single wire, made of two linear tapers starting at
    wire_width tapering down to constriction of width constr_width.

    Args:
        constr_width (int or float): The width of the channel (at the hot-spot location).
        wire_width (int or float): The width of connections to source/drain
        length (int or float): The length of the interior constriction.
        layer (LayerSpec): GDS layer
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: sharp constriction
    """
    NANOWIRE = gf.Component()
    tap = qg.geometries.taper(
        length=length / 2,
        start_width=constr_width,
        end_width=wire_width,
        layer=layer,
    )
    taps = []
    for i in range(2):
        taps.append(NANOWIRE << tap)
    taps[0].connect(taps[0].ports["e1"], taps[1].ports["e1"])
    NANOWIREu = gf.Component()
    NANOWIREu << qg.utilities.union(NANOWIRE)
    for n, tap in enumerate(taps):
        NANOWIREu.add_port(name=f"e{n + 1}", port=tap.ports["e2"])
    for port in NANOWIREu.ports:
        port.port_type = port_type
    return NANOWIREu
