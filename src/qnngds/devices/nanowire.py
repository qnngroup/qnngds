"""Single nanowire constriction."""

import gdsfactory as gf


@gf.cell
def variable_length(
    constr_width: float = 0.1,
    wire_width: float = 0.3,
    length: float = 1,
    layer: tuple = (1, 0),
    num_pts: int = 100,
) -> gf.Component:
    """Creates a single wire, made of two optimal steps from constr_width to
    wire_width with a constriction of the chosen length in the middle.

    Args:
        constr_width (int or float): The width of the channel (at the hot-spot location).
        wire_width (int or float): The width of connections to source/drain
        length (int or float): The length of the interior constriction.
        layer (tuple): GDS layer tuple (layer, type)
        num_pts (int): The number of points comprising the optimal_steps geometries.

    Returns:
        gf.Component: 2 optimal steps to/from a narrow wire.
    """
    NANOWIRE = gf.Component()
    wire = gf.components.superconductors.optimal_step(
        constr_width, wire_width, symmetric=True, num_pts=num_pts, layer=layer
    )
    compass_size = (constr_width, length)
    constr = NANOWIRE << gf.components.compass(
        size=compass_size, layer=layer, port_type="electrical"
    )
    constr.center = [0, 0]
    top = NANOWIRE << wire
    bot = NANOWIRE << wire
    top.connect(
        port=top.ports["e1"], other=constr.ports["e2"], allow_type_mismatch=True
    )
    bot.connect(
        port=bot.ports["e1"], other=constr.ports["e4"], allow_type_mismatch=True
    )
    NANOWIRE.add_port(name="e1", port=top.ports["e2"])
    NANOWIRE.add_port(name="e2", port=bot.ports["e2"])

    return NANOWIRE
