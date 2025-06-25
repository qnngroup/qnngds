"""Pads contains functions for generation of pads and pad arrays."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

from gdsfactory.typings import LayerSpecs, ComponentSpecs
import gdsfactory as gf
import numpy as np

import qnngds as qg


@gf.cell
def stack(
    size: tuple[float, float] = (200, 200),
    layers: LayerSpecs = ("EBEAM_COARSE",),
    port_type: str = "electrical",
    port_span: tuple[float, float] = (0, 1),
) -> gf.Component:
    """Create pad stack for use in other pad arrays

    Has a single port facing to the right

    Args:
        size (tuple[float, float]): width, height of pad
        layers (LayerSpecs): One or more layers to stack. First layer will have a port,
            which is the layer that will be used for routing to the pad.
        port_type (str): port type, either "electrical" or "optical"
        port_span (tuple[float, float]): fraction on [0,1] for starting and ending point of port


    Returns:
        gf.Component: pad stack
    """
    if port_span[1] <= port_span[0]:
        a, b = port_span
        error_msg = "Port span must be a tuple (a,b) with both a and "
        error_msg += f"b on the unit interval and a < b. Got {a=} and {b=}."
        raise ValueError(error_msg)
    PAD = gf.Component()
    pad = PAD << qg.geometries.compass(
        size=size,
        layer=layers[0],
        port_inclusion=0,
        port_orientations=(0,),
    )
    if len(layers) > 1:
        for layer in layers[1:]:
            extra_pad = PAD << qg.geometries.compass(
                size=size,
                layer=layer,
                port_orientations=None,
            )
            extra_pad.move(extra_pad.center, pad.center)
    dcenter = (0, pad.ports["e1"].width * ((port_span[0] + port_span[1]) / 2 - 0.5))
    port_center = np.array(pad.ports["e1"].center) + np.array(dcenter)
    port_width = pad.ports["e1"].width * (port_span[1] - port_span[0])
    PAD.add_port(
        name="e1",
        center=port_center,
        orientation=0,
        width=port_width,
        port_type=port_type,
        layer=pad.ports["e1"].layer,
    )
    return PAD


@gf.cell
def array(
    pad_specs: ComponentSpecs = (stack,),
    columns: int = 1,
    rows: int = 1,
    pitch: float = 150,
) -> gf.Component:
    """Creates a linear array of pads

    Args:
        pad_spec (ComponentSpec): specification for pad or pad stack to use
        columns (int): number of columns
        rows (int): number of rows
        pitch (float): pitch of pads (same for rows/columns)

    Returns:
        gf.Component: linear pad array
    """
    PADS = gf.Component()
    sub_pad = gf.Component()
    offset = 0
    port_i = 0
    for n, pad_spec in enumerate(pad_specs):
        p_i = sub_pad << gf.get_component(pad_spec)
        width = p_i.xsize
        height = p_i.ysize
        p_i.movey(offset - p_i.y)
        offset += pitch
        for port in p_i.ports:
            sub_pad.add_port(name=f"e{port_i}", port=port)
            port_i += 1
    pads = PADS.add_ref(
        sub_pad,
        columns=columns,
        rows=rows,
        column_pitch=sub_pad.xsize + pitch - width,
        row_pitch=sub_pad.ysize + pitch - height,
    )
    for p, port in enumerate(pads.ports):
        PADS.add_port(name=f"e{p + 1}", port=port)
    return PADS


@gf.cell
def vdp(
    pad_specs: ComponentSpecs = (stack,),
    space: float = 500,
) -> gf.Component:
    """Create pads for Van der Pauw probing

    Args:
        pad_specs (ComponentSpecs): specification for pad or pad stack to use.
            Can be a single element tuple or 4 different pads.
        space (float): Spacing between pads (diagonal of VDP cell)

    Returns:
        gf.Component: Van der Pauw pad structure
    """
    pads = gf.Component()
    if len(pad_specs) not in (1, 4):
        raise ValueError(
            f"length of pad_specs must be either 1 or 4, got {len(pad_specs)=}"
        )
    for i in range(4):
        pad = pads << gf.get_component(pad_specs[i % len(pad_specs)])
        pad.rotate(-90 * i)
        x = -((-1) ** (i // 2)) * space / 2 if i % 2 == 0 else 0
        y = (-1) ** (i // 2) * space / 2 if i % 2 == 1 else 0
        pad.move(pad.ports["e1"].center, (x, y))
        pads.add_port(
            name=f"e{i + 1}",
            port=pad.ports["e1"],
        )
    return pads
