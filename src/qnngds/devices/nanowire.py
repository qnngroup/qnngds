"""Single nanowire constriction."""

from phidl import Device

import phidl.geometry as pg
from typing import Tuple, Optional, Union

from qnngds.utilities import PadPlacement, QnnDevice, WireBond, MultiProbeTip


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
    NANOWIRE = Device('nanowire')
    wire = pg.optimal_step(channel_w, source_w, symmetric=True, num_pts=num_pts, layer=layer)
    source = NANOWIRE << wire
    gnd = NANOWIRE << wire
    source.connect(source.ports[1], gnd.ports[1])

    NANOWIRE = pg.union(NANOWIRE, layer=layer)
    NANOWIRE.add_port(name=1, port=source.ports[2])
    NANOWIRE.add_port(name=2, port=gnd.ports[2])

    final_NANOWIRE = QnnDevice('nanowire')
    final_NANOWIRE << NANOWIRE
    for p, port in NANOWIRE.ports.items():
        final_NANOWIRE.add_port(name=p, port=port)

    nw_padplace = PadPlacement()
    final_NANOWIRE.set_pads(nw_padplace)
    final_NANOWIRE.rotate(-90)
    final_NANOWIRE.move(NANOWIRE.center, (0, 0))
    final_NANOWIRE.name = f"NANOWIRE.SPOT(w={channel_w:0.1f})"

    return final_NANOWIRE


def variable_length(
    channel_w: float = 0.1,
    source_w: float = 0.3,
    constr_length: float = 1,
    four_point_probe: bool = False,
    layer: int = 1,
    num_pts: int = 100,
    rotation: float = -90
) -> QnnDevice:
    """Creates a single wire, made of two optimal steps from channel_w to
    source_w with a constriction of the chosen length in the middle.

    Args:
        channel_w (int or float): The width of the channel (at the hot-spot location).
        source_w (int or float): The width of the nanowire's "source".
        constr_length (int or float): The length of the interior constriction.
        four_point_probe (bool): Whether to create pads for four-point-probe configuration
        layer (int): The layer where to put the device.
        num_pts (int): The number of points comprising the optimal_steps geometries.

    Returns:
        Device: A device containing 2 optimal steps to/from a narrow wire.
    """
    NANOWIRE = Device('nanowire')
    wire = pg.optimal_step(channel_w, source_w, symmetric=True, num_pts=num_pts, layer=layer)
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
    gnd.connect( gnd.ports[1], constriction.ports["bottom"])

    NANOWIRE.rotate(rotation)
    #NANOWIRE = pg.union(NANOWIRE, layer=layer)
    if four_point_probe and rotation == -90:
        add_voltage_probe(NANOWIRE, channel_w)
    
        nw_padplace = PadPlacement(
        cell_scaling_factor_x= 2.5,
        num_pads_n=2,
        num_pads_s=2,
        port_map_x={
            1: ("N", 2),
            2: ("S", 1),
            3: ("N", 1),
            4: ("S", 2)
        },
        probe_tip=WireBond()
        
        )
        NANOWIRE.add_port(name=1, port=source.ports[2])
        NANOWIRE.add_port(name=2, port=gnd.ports[2])

    elif four_point_probe and rotation == 0:

        turn = pg.optimal_90deg(source_w, layer=layer)
        source_turn = NANOWIRE << turn
        source_turn.connect(source_turn.ports[1], source.ports[2])
        source_turn.mirror((0,0),(1,0))
        flip_source = NANOWIRE << turn 
        flip_source.connect(flip_source.ports[2], source_turn.ports[2])
        flip_source.rotate(180, center=flip_source.center+(-flip_source.xsize/2+source_w/2, -flip_source.ysize/2))
        gnd_turn = NANOWIRE << turn 
        gnd_turn.connect(gnd_turn.ports[1], gnd.ports[2]) 
        flip_gnd = NANOWIRE << turn 
        flip_gnd.connect(flip_gnd.ports[2], gnd_turn.ports[2])
        flip_gnd.mirror((gnd_turn.xmin, gnd_turn.ymax), (gnd_turn.xmax, gnd_turn.ymax))

        nw_padplace = PadPlacement(
            cell_scaling_factor_x=1,
            num_pads_n=4,
            num_pads_s=0,
            port_map_x={
                1:("N", 2),
                2:("N", 3),
                3:("N", 1),
                4:("N", 4)
            },
            probe_tip=MultiProbeTip()
        )
        NANOWIRE.add_port(name=1, port=source_turn.ports[2])
        NANOWIRE.add_port(name=2, port=gnd_turn.ports[2])
        NANOWIRE.add_port(name=3, port=flip_source.ports[1])
        NANOWIRE.add_port(name=4, port=flip_gnd.ports[1])
    else:
        nw_padplace = PadPlacement()
        NANOWIRE.add_port(name=1, port=source.ports[2])
        NANOWIRE.add_port(name=2, port=gnd.ports[2])

    ports = NANOWIRE.ports
    NANOWIRE = pg.union(NANOWIRE, layer=layer)
    final_nw = QnnDevice('nanowire')
    final_nw << NANOWIRE
    for p, port in ports.items():
        final_nw.add_port(name=p, port=port)
    final_nw.set_pads(nw_padplace)
    final_nw.move(NANOWIRE.center, (0, 0))
    final_nw.name = f"NANOWIRE.VAR(w={channel_w:.2f} l={constr_length:.1f})"
    #NANOWIRE.simplify(1e-3)

    return final_nw

def add_voltage_probe(device: Device, channel_w: Union[int, float]):
    """
    Creates the ports necessary for four-point probing of nanowire
    device (PHIDL Device): device to which to add ports
    channel_w (int or float): width of channel to probe
    """
    device.add_port(name=3, 
                    midpoint = (device.center[0], device.ymax),
                    width = channel_w*3,
                    orientation=90)
    device.add_port(name=4, 
                    midpoint = (device.center[0], device.ymin),
                    width = channel_w*3,
                    orientation=-90)