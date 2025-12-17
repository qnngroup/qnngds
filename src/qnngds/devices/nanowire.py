"""Single nanowire constriction."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import qnngds as qg
import phidl.geometry as pg


from qnngds.typing import LayerSpec
from qnngds import Device


@qg.device
def variable_length(
    constr_width: float = 0.1,
    wire_width: float = 0.3,
    length: float = 1,
    num_pts: int = 100,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Creates a single wire, made of two optimal steps from constr_width to
    wire_width with a constriction of the chosen length in the middle.

    Args:
        constr_width (int or float): The width of the channel (at the hot-spot location).
        wire_width (int or float): The width of connections to source/drain
        length (int or float): The length of the interior constriction.
        num_pts (int): The number of points comprising the optimal_steps geometries.
        layer (LayerSpec): GDS layer specification

    Returns:
        Device: 2 optimal steps to/from a narrow wire.

    Raises:
        ValueError if constr_width > wire_width
    """
    NANOWIRE = Device("nw_smooth")
    if constr_width > wire_width:
        raise ValueError(
            f"constriction width {constr_width=} cannot be larger than wire width {wire_width=}"
        )
    # if constriction and wire width are the same, just return a straight wire
    if constr_width == wire_width:
        constr = NANOWIRE << pg.straight(
            size=(constr_width, length), layer=qg.get_layer(layer)
        )
        constr.center = (0, 0)
        NANOWIRE.add_port(name=1, port=constr.ports[1])
        NANOWIRE.add_port(name=2, port=constr.ports[2])
        return NANOWIRE
    # otherwise, create tapers
    step = pg.optimal_step(
        start_width=constr_width,
        end_width=wire_width,
        symmetric=True,
        num_pts=num_pts,
        layer=qg.get_layer(layer),
    )
    top = NANOWIRE << step
    bot = NANOWIRE << step
    if length > 0:
        constr = NANOWIRE << pg.straight(
            size=(constr_width, length),
            layer=qg.get_layer(layer),
        )
        constr.center = [0, 0]
        top.connect(port=top.ports[1], destination=constr.ports[1])
        bot.connect(port=bot.ports[1], destination=constr.ports[2])
    else:
        bot.rotate(90)
        bot.move(bot.ports[1].center, (0, 0))
        top.connect(
            port=top.ports[1], destination=bot.ports[1], allow_type_mismatch=True
        )
    NANOWIREu = Device("nw_smooth")
    NANOWIREu << pg.union(NANOWIRE, layer=qg.get_layer(layer))
    for p, port in enumerate([top.ports[2], bot.ports[2]]):
        NANOWIREu.add_port(name=p + 1, port=port)
    qg.utilities._create_layered_ports(NANOWIRE, layer)

    return NANOWIREu


@qg.device
def sharp(
    constr_width: float = 0.1,
    wire_width: float = 0.3,
    length: float = 1,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Creates a single wire, made of two linear tapers starting at
    wire_width tapering down to constriction of width constr_width.

    Args:
        constr_width (int or float): The width of the channel (at the hot-spot location).
        wire_width (int or float): The width of connections to source/drain
        length (int or float): The length of the interior constriction.
        layer (LayerSpec): GDS layer specification

    Returns:
        Device: sharp constriction
    """
    NANOWIRE = Device("nw_sharp")
    tap = qg.geometries.taper(
        length=length / 2,
        start_width=constr_width,
        end_width=wire_width,
        layer=layer,
    )
    taps = []
    for i in range(2):
        taps.append(NANOWIRE << tap)
    taps[0].connect(taps[0].ports[1], taps[1].ports[1])
    NANOWIREu = Device("nw_sharp")
    NANOWIREu << pg.union(NANOWIRE, qg.get_layer(layer))
    for n, tap in enumerate(taps):
        NANOWIREu.add_port(name=n + 1, port=tap.ports[2])
    return NANOWIREu
