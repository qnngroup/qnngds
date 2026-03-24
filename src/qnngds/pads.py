"""Pads contains functions for generation of pads and pad arrays."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

from qnngds.typing import LayerSpecs, DeviceSpecs, DeviceSpec
import numpy as np

from qnngds import Device

import qnngds as qg
import phidl.geometry as pg
import phidl.routing as pr


@qg.device
def stack(
    size: tuple[float, float] = (200, 100),
    layers: LayerSpecs = ("EBEAM_COARSE",),
    port_span: tuple[float, float] = (0, 1),
) -> Device:
    """Create pad stack for use in other pad arrays

    Has a single port facing to the right

    Args:
        size (tuple[float, float]): width, height of pad
        layers (LayerSpecs): One or more layers to stack. First layer will have a port,
            which is the layer that will be used for routing to the pad.
        port_span (tuple[float, float]): fraction on [0,1] for starting and ending point of port


    Returns:
        (Device): pad stack
    """
    if port_span[1] <= port_span[0]:
        a, b = port_span
        error_msg = "Port span must be a tuple (a,b) with both a and "
        error_msg += f"b on the unit interval and a < b. Got {a=} and {b=}."
        raise ValueError(error_msg)
    PAD = Device()
    pad = PAD << pg.rectangle(
        size=size,
        layer=qg.get_layer(layers[0]),
    )
    if len(layers) > 1:
        for layer in layers[1:]:
            extra_pad = PAD << pg.rectangle(
                size=size,
                layer=qg.get_layer(layer),
            )
            extra_pad.move(extra_pad.center, pad.center)
    port_dcenter = (0, size[1] * ((port_span[0] + port_span[1]) / 2 - 0.5))
    port_center = np.array((pad.xmax, pad.y)) + np.array(port_dcenter)
    port_width = size[1] * (port_span[1] - port_span[0])
    PAD.add_port(
        name=1,
        midpoint=port_center,
        orientation=0,
        width=port_width,
        layer=qg.get_layer(layers[0]),
    )
    return PAD


@qg.device
def array(
    pad_specs: DeviceSpecs = (stack,),
    columns: int = 1,
    rows: int = 3,
    pitch: float = 150,
) -> Device:
    """Creates a linear array of pads

    Args:
        pad_spec (DeviceSpec): specification for pad or pad stack to use
        columns (int): number of columns
        rows (int): number of rows
        pitch (float): pitch of pads (same for rows/columns)

    Returns:
        (Device): linear pad array
    """
    PADS = Device()
    sub_pad = Device()
    offset = 0
    port_i = 0
    for n, pad_spec in enumerate(pad_specs):
        p_i = sub_pad << qg.get_device(pad_spec)
        width = p_i.xsize
        height = p_i.ysize
        p_i.movey(offset - p_i.y)
        offset += pitch
        for port_name in p_i.ports:
            sub_pad.add_port(name=port_i, port=p_i.ports[port_name])
            port_i += 1
    pads = PADS.add_array(
        sub_pad,
        columns=columns,
        rows=rows,
        spacing=(sub_pad.xsize + pitch - width, sub_pad.ysize + pitch - height),
    )
    p = 1
    for row in range(rows):
        for col in range(columns):
            for port_name in pads.ports[row, col]:
                PADS.add_port(name=p, port=pads.ports[row, col][port_name])
                p += 1
    return PADS


@qg.device
def vdp(
    pad_specs: DeviceSpecs = (stack,),
    space: float = 500,
) -> Device:
    """Create pads for Van der Pauw probing

    Args:
        pad_specs (DeviceSpecs): specification for pad or pad stack to use.
            Can be a single element tuple or 4 different pads.
        space (float): Spacing between pads (diagonal of VDP cell)

    Returns:
        (Device): Van der Pauw pad structure
    """
    pads = Device()
    if len(pad_specs) not in (1, 4):
        raise ValueError(
            f"length of pad_specs must be either 1 or 4, got {len(pad_specs)=}"
        )
    for i in range(4):
        pad = pads << qg.get_device(pad_specs[i % len(pad_specs)])
        pad.rotate(-90 * i)
        x = -((-1) ** (i // 2)) * space / 2 if i % 2 == 0 else 0
        y = (-1) ** (i // 2) * space / 2 if i % 2 == 1 else 0
        pad.move(pad.ports[1].center, (x, y))
        pads.add_port(
            name=i + 1,
            port=pad.ports[1],
        )
    return pads


@qg.device
def quad_line(
    array_spec: DeviceSpec = array,
    port_width: float = 20,
    port_pitch: float = 50,
    port_offset: tuple[float, float] = (100, 0),
) -> Device:
    """Create pads with quad routing to intermediate ports

    Args:
        array_spec (DeviceSpec): spec for pad array (assumes 1D array along y-axis)
        port_width (float): width of intermediate ports
        port_pitch (float): pitch of intermediate ports
        port_offset (tuple[float, float]): offset of intermediate ports
            relative to pad array port center

    Returns:
        (Device): pads with intermediate finer ports
    """
    pads = Device()
    array = pads << qg.get_device(array_spec)
    for p, port_name in enumerate(array.ports):
        port = array.ports[port_name]
        dy = (p - (len(array.ports) - 1) / 2) * port_pitch
        center = (port.x + port_offset[0], array.y + port_offset[1] + dy)
        pads.add_port(
            name=port.name,
            width=port_width,
            midpoint=center,
            orientation=0,
            layer=port.layer,
        )
        pads << pr.route_quad(
            port1=port,
            port2=pads.ports[port.name],
            layer=qg.get_layer(port.layer),
        )
    return pads
