"""Single nanowire constriction."""

from phidl import Device

import phidl.geometry as pg
from typing import Tuple, Optional

from qnngds.utilities import PadPlacement, QnnDevice


def spot(
    channel_w: float = 0.1,
    source_w: float = 0.3,
    layer: int = 1,
    num_pts: int = 100,
) -> QnnDevice:
    """Creates a single wire, made of two optimal steps from channel_w to
    source_w.

    Args:
        channel_w (int or float): The width of the channel (at the hot-spot location).
        source_w (int or float): The width of the nanowire's "source".
        layer (int): The layer where to put the device.
        num_pts (int): The number of points comprising the optimal_steps geometries.

    Returns:
        Device: A device containing 2 optimal steps joined at their channel_w end.
    """

    nw_padplace = PadPlacement()

    NANOWIRE = Device()
    wire = pg.optimal_step(channel_w, source_w, symmetric=True, num_pts=num_pts)
    source = NANOWIRE << wire
    gnd = NANOWIRE << wire
    source.connect(source.ports[1], gnd.ports[1])

    NANOWIRE = pg.union(NANOWIRE, layer=layer)
    NANOWIRE.add_port(name=1, port=source.ports[2])
    NANOWIRE.add_port(name=2, port=gnd.ports[2])
    NANOWIRE.rotate(-90)
    NANOWIRE.move(NANOWIRE.center, (0, 0))
    NANOWIRE.name = f"NANOWIRE.SPOT(w={channel_w})"

    return QnnDevice(NANOWIRE, nw_padplace)


def variable_length(
    channel_w: float = 0.1,
    source_w: float = 0.3,
    constr_length: float = 1,
    layer: int = 1,
    num_pts: int = 100,
) -> QnnDevice:
    """Creates a single wire, made of two optimal steps from channel_w to
    source_w with a constriction of the chosen length in the middle.

    Args:
        channel_w (int or float): The width of the channel (at the hot-spot location).
        source_w (int or float): The width of the nanowire's "source".
        constr_length (int or float): The length of the interior constriction.
        layer (int): The layer where to put the device.
        num_pts (int): The number of points comprising the optimal_steps geometries.

    Returns:
        Device: A device containing 2 optimal steps to/from a narrow wire.
    """
    nw_padplace = PadPlacement(
        cell_scaling_factor_x= 1.5,
        num_pads_n=2,
        num_pads_s=2,
        port_map_x={
            1: ("N", 1),
            2: ("S", 1),
            3: ("N", 2),
            4: ("S", 2)
        }
    )

    NANOWIRE = Device()
    wire = pg.optimal_step(channel_w, source_w, symmetric=True, num_pts=num_pts)
    line = pg.rectangle((constr_length, channel_w), layer=layer)
    line.center = [0, 0]
    line.add_port(
        "top", midpoint=(-constr_length / 2, 0), orientation=180, width=channel_w
    )
    line.add_port(
        "bottom", midpoint=(constr_length / 2, 0), orientation=0, width=channel_w
    )

    source = NANOWIRE << wire
    constriction = NANOWIRE << line
    gnd = NANOWIRE << wire
    source.connect(source.ports[1], constriction.ports["top"])
    constriction.connect(constriction.ports["bottom"], gnd.ports[1])

    NANOWIRE = pg.union(NANOWIRE, layer=layer)
    NANOWIRE.add_port(name=1, port=source.ports[2])
    NANOWIRE.add_port(name=2, port=gnd.ports[2])
    NANOWIRE.rotate(-90)
    NANOWIRE.add_port(name=3, 
                    midpoint = (NANOWIRE.xmin + channel_w/2, NANOWIRE.ymax),
                    width = channel_w/2,
                    orientation=90)
    NANOWIRE.add_port(name=4, 
                    midpoint = (NANOWIRE.xmin + channel_w/2, NANOWIRE.ymin),
                    width = channel_w/2,
                    orientation=-90)
    NANOWIRE.move(NANOWIRE.center, (0, 0))
    NANOWIRE.name = f"NANOWIRE.VAR(w={channel_w} l={constr_length})"

    return QnnDevice(NANOWIRE, nw_padplace)
