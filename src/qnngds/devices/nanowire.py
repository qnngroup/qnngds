"""Single nanowire constriction."""

import gdsfactory as gf

from gdsfactory.typings import LayerSpec


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
    """
    NANOWIRE = gf.Component()
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
