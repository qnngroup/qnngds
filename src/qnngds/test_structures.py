"""Teststructures contains lithographic and electrical test structures."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import qnngds as qg
import phidl.geometry as pg

from typing import List, Optional, Tuple

import numpy as np

from functools import partial

from qnngds.typing import LayerSpec, LayerSpecs, DeviceSpec
from qnngds import Device


def _create_comb(
    pitch1: int | float = 0.5,
    pitch2: int | float = 0.1,
    layer1: LayerSpec = (1, 0),
    layer2: LayerSpec = (2, 0),
    text_angle: int | float = 0,
) -> Device:
    """Creates vernier caliper comb.

    Helper method for alignment_mark
    Args:
        pitch1 (int or float): pitch of top comb
        pitch2 (int or float): pitch of bottom comb
        layer1 (LayerSpec): center comb GDS layer tuple (layer, type)
        layer2 (LayerSpec): top/bottom comb GDS layer tuple (layer, type)
        text_angle (int or float): angle to rotate text labels

    Returns:
        Device: alignment vernier calipers
    """

    COMB = Device("comb")

    # middle comb (made of layer1), pitch = 10
    rect1 = pg.rectangle(size=(5, 30), layer=qg.get_layer(layer1).tuple)
    middle_comb = COMB.add_array(rect1, columns=21, rows=1, spacing=(10, 0))
    middle_comb.move(COMB.center, (0, 0))

    # top and bottom combs (made of layer2), pitchs = 10+pitch1, 10+pitch2
    rect2 = pg.rectangle(size=(5, 30), layer=qg.get_layer(layer2).tuple)
    top_comb = COMB.add_array(rect2, columns=21, rows=1, spacing=(10 + pitch1, 0))
    top_comb.move(top_comb.center, (middle_comb.center[0], middle_comb.center[1] + 30))
    top_text = COMB.add_ref(
        pg.text(f"{round(pitch1 * 1e3)}NM", size=10, layer=qg.get_layer(layer2).tuple)
    )
    top_text.rotate(-text_angle)
    top_text.move(top_text.center, (140, 30))

    bottom_comb = COMB.add_array(rect2, columns=21, rows=1, spacing=(10 + pitch2, 0))
    bottom_comb.move(
        bottom_comb.center, (middle_comb.center[0], middle_comb.center[1] - 30)
    )
    bottom_text = COMB.add_ref(
        pg.text(f"{round(pitch2 * 1e3)}NM", size=10, layer=qg.get_layer(layer2).tuple)
    )
    bottom_text.rotate(-text_angle)
    bottom_text.move(bottom_text.center, (140, -30))

    # additional markers (made of layer1), for clarity
    rect1a = pg.rectangle(size=(5, 20), layer=qg.get_layer(layer1).tuple)
    marksa = COMB.add_array(rect1a, columns=3, rows=2, spacing=(100, 110))
    marksa.move(marksa.center, middle_comb.center)

    rect1b = pg.rectangle(size=(5, 10), layer=qg.get_layer(layer1).tuple)
    marksb = COMB.add_array(rect1b, columns=2, rows=2, spacing=(100, 100))
    marksb.move(marksb.center, middle_comb.center)

    return COMB


def _create_marker(layer1: LayerSpec = (1, 0), layer2: LayerSpec = (2, 0)) -> Device:
    """Creates vernier caliper comb

    Helper method for alignment_mark
    Args:
        layer1 (LayerSpec): center comb GDS layer tuple (layer, type)
        layer2 (LayerSpec): top/bottom comb GDS layer tuple (layer, type)

    Returns:
        Device: alignment cross with vernier calipers
    """

    MARK = Device("interlayer_align")

    # central part with cross

    CROSS = Device()
    cross = CROSS << pg.cross(length=200, width=2, layer=qg.get_layer(layer1).tuple)
    rect = pg.rectangle(size=(45, 45), layer=qg.get_layer(layer2).tuple)
    window = CROSS.add_array(rect, rows=2, columns=2, spacing=(155, 155))
    window.move(window.center, cross.center)
    CROSS.flatten()

    MARK << CROSS

    VERNIER = Device()
    for n, pitches in enumerate(((0.5, 0.1), (0.2, 0.05))):
        p1, p2 = pitches
        for i in range(2):
            index = n * 2 + i
            comb = _create_comb(
                pitch1=p1,
                pitch2=p2,
                layer1=layer1,
                layer2=layer2,
                text_angle=index * 90,
            )
            v = VERNIER.add_ref(comb)
            v.rotate(index * 90)
            if index == 0:
                v.move((0, 0), (0, 200))
            elif index == 1:
                v.move((0, 0), (-200, 0))
            elif index == 2:
                v.move((0, 0), (0, -200))
            elif index == 3:
                v.move((0, 0), (200, 0))

    VERNIER.flatten()
    MARK << VERNIER

    MARK.move(MARK.center, (0, 0))

    # text
    TEXT = Device()
    layer1_str = qg.get_layer(layer1).name.split("_")[0]
    layer2_str = qg.get_layer(layer2).name.split("_")[0]
    bg_label = (
        layer2_str[:3] if len(layer2_str) < 4 else layer2_str[:2] + layer2_str[-1]
    )
    sm_label = ""
    if len(layer2_str) < 5:
        sm_label += layer2_str
    else:
        sm_label += f"{layer2_str[:4]}{layer2_str[-1]}"
    sm_label += " ON "
    if len(layer1_str) < 5:
        sm_label += layer1_str
    else:
        sm_label += f"{layer1_str[:4]}{layer1_str[-1]}"
    for layer in (layer1, layer2):
        text1 = TEXT << pg.text(bg_label, size=50, layer=qg.get_layer(layer).tuple)
        text1.move(text1.center, (-200, 190))
    text2 = TEXT << pg.text(sm_label, size=10, layer=qg.get_layer(layer2).tuple)
    text2.move(text2.center, (-200, 250))
    if isinstance(layer1, tuple):
        layer1_numeric = f"{layer1[0]}/{layer1[1]}"
    else:
        layer1_enum = qg.get_layer(layer1).tuple
        layer1_numeric = f"{layer1_enum[0]}/{layer1_enum[1]}"
    if isinstance(layer2, tuple):
        layer2_numeric = f"{layer2[0]}/{layer2[1]}"
    else:
        layer2_enum = qg.get_layer(layer2).tuple
        layer2_numeric = f"{layer2_enum[0]}/{layer2_enum[1]}"
    text3 = TEXT << pg.text(
        layer2_numeric + " ON " + layer1_numeric,
        size=10,
        layer=qg.get_layer(layer2).tuple,
    )
    text3.move(text3.center, (-200, 235))
    TEXT.flatten()
    MARK << TEXT

    return MARK


def alignment_mark(
    layers: LayerSpecs = ["PHOTO1", "PHOTO2"],
) -> Device:
    """Creates an alignment mark for each lithography layer.

    Args:
        layers (LayerSpecs): A list of GDS layers

    Returns:
        Device: alignment marks between each layer pair
    """

    ALIGN = Device("alignment_marks")
    markers_pitch = 600
    for i, layer1 in enumerate(layers):
        n = len(layers) - i - 1
        if n != 0:
            for j, layer2 in enumerate(layers[-n:]):
                mark = ALIGN << _create_marker(layer1, layer2)
                mark.move((j * markers_pitch, i * markers_pitch))

    num_layers = len(layers)
    offset = -(num_layers - 2) * markers_pitch / 2
    ALIGN.move((0, 0), (offset, offset))
    return ALIGN


def _create_waffle(res: float | int = 1, layer: LayerSpec = (1, 0)) -> Device:
    """Creates waffle test structures for determining process resolution.

    Helper method for resolution_test
    Args:
        res (float or int): Resolution (in µm) to be tested.
        layer (LayerSpec): GDS layer tuple (layer, type)

    Returns:
        Device: the resolution test structure
    """

    WAFFLE = Device("waffle")
    W = pg.rectangle(size=(res * 80, res * 80), layer=layer)

    pattern = [(res * x, res * 80) for x in [2, 1, 1, 2, 3, 5, 8, 13, 21, 15]]
    DUMMY = Device()
    WOut = DUMMY << pg.gridsweep(
        function=pg.rectangle, param_x={"size": pattern}, param_y={}, spacing=res
    )
    WOut.move(WOut.center, W.center)
    WAFFLE << pg.kl_boolean(A=W, B=WOut, operation="A-B", layer=layer)
    WOut.rotate(90, center=WOut.center)
    WAFFLE << pg.kl_boolean(A=W, B=WOut, operation="A-B", layer=layer)

    text = WAFFLE << pg.text(str(res), size=20, layer=layer)
    text.move((text.xmin, text.ymax), (W.xmin, W.ymin - min(10, 10 * res)))

    WAFFLEu = Device()
    WAFFLEu << pg.union(WAFFLE, by_layer=True)
    WAFFLEu.flatten()
    return WAFFLEu


def _create_3L(res: float | int = 1, layer: LayerSpec = (1, 0)) -> Device:
    """Creates L-shaped test structures for determining process resolution.

    Helper method for resolution_test
    Args:
        res (float or int): Resolution (in µm) to be tested.
        layer (LayerSpec): GDS layer tuple (layer, type)

    Returns:
        Device: the resolution test structure
    """

    LLL = Device("LLL")
    grid_spacing = (15 * res, 15 * res)

    deviation = [0.8, 1, 1.2]
    for i, percent in enumerate(deviation):
        bars = Device()
        w = percent * res
        spacing = 2 * res
        bar = pg.rectangle(size=(min(100 * res, 100), w), layer=layer)
        h_bars = bars.add_array(bar, columns=1, rows=5, spacing=(0, spacing))
        v_bars = bars.add_array(bar, columns=1, rows=5, spacing=(0, spacing))
        h_bars.rotate(90)
        h_bars.move((h_bars.xmin, h_bars.ymin), (0, 0))
        v_bars.move((v_bars.xmin, v_bars.ymin), (0, 0))
        lll = LLL << bars
        lll.move([i * offset for offset in grid_spacing])

    text = LLL << pg.text(str(res), size=20, layer=layer)
    start = (text.xmin, text.ymin)
    text.move(start, [(len(deviation) + 0.5) * offset for offset in grid_spacing])
    LLLu = Device()
    LLLu << pg.union(LLL, by_layer=True)
    LLLu.flatten()
    return LLLu


def resolution_test(
    resolutions: List[float] = [0.6, 0.8, 1.0],
    outline: Optional[float] = None,
    layer: LayerSpec = (2, 0),
) -> Device:
    """Creates L and waffle structures for determining process resolution.

    Args:
        resolutions (List[float]): List of resolutions (in µm) to be tested.
        outline (Optional[float]): If none, do not invert. If zero, invert the device, otherwise outline the device by this width.
        layer (LayerSpec): GDS layer tuple (layer, type)

    Returns:
        Device: the resolution test structures
    """

    RES_TEST = Device("resolution_test")
    for test_fn in [_create_3L, _create_waffle]:
        for res in resolutions:
            RES_TEST << test_fn(res, layer)
    RES_TEST.distribute(direction="y", spacing=0, separation=False, edge="ymin")
    RES_TEST.distribute(direction="x", spacing=10, edge="ymin")
    RES_TEST.move(RES_TEST.center, (0, 0))

    if outline is not None:
        if outline > 0:
            RES_TEST = qg.utilities.outline(RES_TEST, {layer: outline})
        else:
            RES_TEST = qg.utilities.invert(RES_TEST, {layer: 5})

    RES_TESTu = Device()
    RES_TESTu << pg.union(RES_TEST, by_layer=True)
    RES_TESTu.flatten()
    return RES_TESTu


def _litho_steps(
    resolutions: List[float] = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    width: float = 5,
    spacing: float = 5,
    layer: LayerSpec = (2, 0),
) -> Device:
    """Creates step pattern for lithographic resolution test

    Adapted from PHIDL

    Args:
        resolutions (List[float]): List of resolutions (in µm) to be tested.
        width (float): width of stripes
        spacing (float): spacing between stripes
        layer (LayerSpec): GDS layer tuple (layer, type)

    Returns:
        Device: the test structure
    """

    D = Device()

    R1 = pg.rectangle(size=(width, spacing), layer=layer)
    r = D << R1
    r.xmin = -width
    r.ymin = 0
    offset = 0.0
    for resolution in reversed(resolutions):
        offset += spacing + resolution
        R2 = pg.rectangle(size=(width, resolution), layer=layer)
        r = D << R1
        r.xmin = 0
        r.ymin = 0
        r.movey(offset)
        r.movex(-width)
        r = D << R2
        r.xmin = 0
        r.ymin = 0
        r.movey(offset - resolution)

    return D


def litho_checkerboard(
    resolutions: List[float] = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    layer: LayerSpec = (2, 0),
    label_interval: int = 5,
    label_size: float = 10,
) -> Device:
    """Creates crossed lith_steps pattern for lithographic resolution test

    Args:
        resolutions (List[float]): List of resolutions (in µm) to be tested.
        layer (LayerSpec): GDS layer tuple (layer, type)
        label_interval (bool): how often to label (set to 0 to disable all labels)
        label_size (float): size of text label

    Returns:
        Device: the litho test structure
    """

    D = Device("litho_checkerboard")
    max_res = np.max(resolutions)
    widths = list(resolutions) + list(max_res * np.linspace(2, 10, 9)) + [100 * max_res]
    xmax = 0
    spacing = 2 * max_res
    for width in widths:
        steps = D << _litho_steps(
            resolutions=resolutions,
            spacing=spacing,
            width=width,
            layer=layer,
        )
        steps.movex(xmax - steps.xmax)
        xmax = steps.xmin

    # add labels
    offset = 0
    for n, resolution in enumerate(reversed(resolutions)):
        offset += spacing + resolution
        if label_interval == 0:
            continue
        if n % label_interval == 0:
            label = D << pg.text(
                f"{round(resolution * 10) / 10}UM", size=label_size, layer=layer
            )
            label.move((label.xmin, label.y), (2 * label_size, offset - resolution / 2))
            # add wider rectangle
            tick = D << pg.rectangle(
                size=(label_size, max(spacing / 2, 1.5)), layer=layer
            )
        else:
            # add narrower rectangle
            tick = D << pg.rectangle(
                size=(label_size / 2, max(spacing / 2, 1.5)), layer=layer
            )
        tick.move((tick.xmin, tick.y), (label_size / 2, offset - resolution / 2))

    return D


def vdp(
    diagonal: float = 400,
    contact_width: float = 40,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> Device:
    """Creates a Van der Pauw (VDP) device with specified dimensions.

    Args:
        diagonal (float): Length of the VDP device, overall maximum dimension, in µm.
        contact_width (float): Width of the contact points (width of the ports), in µm.
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        Device: Van der Pauw cell
    """
    VDP = Device("vdp")

    xpts = [
        -contact_width / 2,
        contact_width / 2,
        diagonal / 2,
        diagonal / 2,
        contact_width / 2,
        -contact_width / 2,
        -diagonal / 2,
        -diagonal / 2,
    ]
    ypts = [
        diagonal / 2,
        diagonal / 2,
        contact_width / 2,
        -contact_width / 2,
        -diagonal / 2,
        -diagonal / 2,
        -contact_width / 2,
        contact_width / 2,
    ]

    polygon = pg.polygon_ports(xpts=xpts, ypts=ypts, layer=layer)
    VDP << polygon
    VDP.flatten()

    VDP.add_port(port=polygon.ports["1"], name="N1", layer=layer)
    VDP.add_port(port=polygon.ports["3"], name="E1", layer=layer)
    VDP.add_port(port=polygon.ports["5"], name="S1", layer=layer)
    VDP.add_port(port=polygon.ports["7"], name="W1", layer=layer)

    return VDP


def rect_tlm(
    contact_l: float = 10,
    spacings: List[float] = [10, 10, 20, 50, 80, 100, 200],
    contact_w: float = 100,
    via_layer: LayerSpec | None = (2, 0),
    finger_layer: LayerSpec = (3, 0),
    pad_layer: LayerSpec | None = (3, 0),
    mesa_layer: LayerSpec = (4, 0),
    pad_size: Tuple[float, float] = (80, 80),
) -> Device:
    """Creates rectangular transfer-length-method test structures.

    Args:
        contact_l (float): length of metal contact on semiconductor
        spacings (List[float]): list of spacings between contacts
        contact_w (float): width of contact/semiconductor
        via_layer (LayerSpec | None): layer specification for via between mesa and fingers.
            If None, don't include via.
        finger_layer (LayerSpec): layer for fingers that periodically contact mesa
        pad_layer (LayerSpec | None): layer for probable pads. If None, don't include.
        mesa_layer (LayerSpec): layer for semiconductor
        pad_size (tuple(float,float)): width, height of pad

    Returns:
        Device: TLM structure
    """
    TLM = Device("rect_tlm")
    xoff = 0
    for n, space in enumerate(spacings):
        fp_w = space + 2 * contact_l
        w = contact_w * 1.2 + 10
        for i in range(2):
            fp = TLM << pg.flagpole(
                size=(fp_w, pad_size[1]),
                stub_size=(contact_l, w),
                shape=("d" if i % 2 else "p"),
                taper_type=None,
                layer=finger_layer,
            )
            if i % 2:
                fp.movey(-fp.ymax + contact_w / 2 + 5)
                fp.movex(xoff - fp.xmax)
            else:
                fp.movey(-fp.ymin - contact_w / 2 - 5)
                fp.movex(xoff - fp.xmin + 50)
            xoff = fp.xmax
            if via_layer is not None:
                via = TLM << pg.rectangle(
                    size=(contact_l, contact_w + 10), layer=via_layer
                )
                if i % 2:
                    via.move((fp.xmax - contact_l / 2 - via.x, -via.y))
                else:
                    via.move((fp.xmin + contact_l / 2 - via.x, -via.y))
                # add vias to lower metal pads
                pad_via = TLM << pg.rectangle(size=(fp_w, pad_size[1]), layer=via_layer)
                pad_via.movex(fp.xmax - pad_via.xmax)
                if i % 2:
                    pad_via.movey(fp.ymin - pad_via.ymin)
                else:
                    pad_via.movey(fp.ymax - pad_via.ymax)
                top_pad = TLM << pg.rectangle(
                    size=(fp_w + 2, pad_size[1] + 2), layer=pad_layer
                )
                top_pad.move(top_pad.center, pad_via.center)
        text = TLM << pg.text(str(space), layer=finger_layer)
        text.move((xoff - text.xmin + 5, -w / 2 - pad_size[1] + 10 - text.ymin))
    # add mesa
    center = (TLM.x, 0)
    mesa = TLM << pg.rectangle(size=(TLM.xsize + 50, contact_w), layer=mesa_layer)
    mesa.move(mesa.center, center)
    return TLM


def circ_tlm(
    ext_radius: float = 100,
    int_radius: List[float] = [50, 70, 80, 90, 95, 98, 99],
    pad_layer: LayerSpec = (3, 0),
    mesa_layers: LayerSpecs = [(1, 0), (2, 0)],
    text_size: float = 10,
) -> Device:
    """Creates rectangular transfer-length-method test structures.

    Args:
        ext_radius (float): external radius of hole that defines outer pad
        int_radius (List[float]): list of internal radii. The gap is d = ext_radius - int_radius.
        pad_layer (LayerSpec): layer for probable pads.
        mesa_layers (LayerSpecs): layer(s) for bottom metal/semiconductor and/or vias
        text_size (float): size of text label

    Returns:
        Device: TLM structure
    """
    TLM = Device("circ_tlm")

    cuts = []
    for r_i in int_radius:
        d = ext_radius - r_i
        r = (ext_radius + r_i) / 2
        CUT = Device()
        r = CUT << pg.ring(radius=r, width=d, angle_resolution=2.5, layer=pad_layer)
        t = CUT << pg.text(
            text=f"{ext_radius}/{r_i}", size=text_size, justify="right", layer=pad_layer
        )
        t.move((t.xmax, t.ymax), (r.xmax, r.ymax))
        cuts.append(CUT)
    c = pg.grid(
        cuts,
        spacing=(10, 10),
        shape=(len(cuts), 1),
        align_x="x",
        align_y="y",
    )
    # make the mesa
    for layer in mesa_layers:
        m = TLM << pg.rectangle(size=(c.xsize + 10, c.ysize + 10), layer=layer)
        m.move(m.center, c.center)
    DUMMY = Device()
    p = DUMMY << pg.rectangle(size=(c.xsize + 10, c.ysize + 10), layer=pad_layer)
    p.move(p.center, c.center)
    TLM << pg.kl_boolean(
        A=p,
        B=c,
        operation="A-B",
        layer=pad_layer,
    )
    return TLM


def via_chain(
    via_spec: DeviceSpec | Device = qg.geometries.via,
    num_vias: int = 5,
    spacing: float = 10,
    tap_period: int = 1,
) -> Device:
    """Makes a chain of vias, with optional taps along the length of the chain

    Args:
        via_spec (DeviceSpec | Device): function, component name, or component for the via
        num_vias (int): number of vias to include in chain
        spacing (float): spacing between vias
        tap_period (int): number of vias between each tap. If zero, doesn't place any taps.

    Returns:
        Device: the via chain
    """
    if tap_period < 0:
        raise ValueError(f"{tap_period=} must be positive")
    if tap_period > 1:
        raise ValueError("tap_period > 1 has not been implemented yet")

    VC = Device("via_chain")
    via = qg.get_active_pdk().get_device(via_spec)
    # get layers
    port_dict = qg.utilities._get_component_port_direction(via)
    east_layers = set(port.layer for port in port_dict["E"])
    west_layers = set(port.layer for port in port_dict["W"])
    if len(east_layers) == 1 and len(west_layers) == 1:
        if east_layers == west_layers:
            raise ValueError("bad via_spec, did not receive ports on different layers")
        east_layer = east_layers.pop()
        west_layer = west_layers.pop()
    else:
        if east_layers != west_layers:
            raise ValueError(
                f"got multiple layers on east/west side of via, but they are not identical. please check via spec: {port_dict=}"
            )
        east_layer = east_layers.pop()
        west_layer = (west_layers - set([east_layer])).pop()
    east_port = [port for port in port_dict["E"] if port.layer == east_layer]
    west_port = [port for port in port_dict["W"] if port.layer == west_layer]
    if len(east_port) > 1 or len(west_port) > 1:
        raise ValueError(f"got too many ports, please check via spec: {port_dict=}")
    east_port = east_port[0]
    west_port = west_port[0]
    if east_port.width != west_port.width:
        raise ValueError(f"width mismatch between ports {east_port=} and {west_port=}")

    width = east_port.width
    if tap_period == 0:
        connector = partial(pg.straight, size=(spacing, width))
    else:
        connector = partial(
            qg.geometries.tee,
            size=(spacing, width),
            stub_size=(width, width),
            taper_type="fillet",
            taper_radius=width / 2,
        )

    vias = VC.add_array(
        via,
        columns=num_vias,
        rows=1,
        spacing=(via.xsize + spacing, 0),
    )

    east_end_port_layer = west_layer if num_vias % 2 == 0 else east_layer
    east_end_port_name = [
        port for port in port_dict["E"] if port.layer == east_end_port_layer
    ][0].name
    end_ports = [
        vias.ports[0, 0][west_port.name],
        vias.ports[0, num_vias - 1][east_end_port_name],
    ]
    conn_ports = []
    for i in range(2):
        layer = east_layer if i == 0 else west_layer
        port = east_port if i == 0 else west_port
        odd = i
        n_conn = (num_vias - odd) // 2
        if n_conn > 0:
            conn = VC.add_array(
                connector(layer=layer),
                columns=n_conn,
                rows=1,
                spacing=(2 * (via.xsize + spacing), 1),
            )
            conn.movey(-width / 2)
            if odd:
                conn.rotate(180)
                conn.movex(vias.xmin + 2 * via.xsize + spacing - conn.xmin)
            else:
                conn.movex(vias.xmin + via.xsize - conn.xmin)
            if tap_period > 0:
                conn_ports.append([conn.ports[0, n][3] for n in range(n_conn)])
        else:
            conn_ports.append([])
    ports = [end_ports[0]]
    if len(conn_ports) > 0:
        ports += conn_ports[0]
    ports += [end_ports[1]]
    if len(conn_ports) > 1:
        ports += conn_ports[1]

    for n, port in enumerate(ports):
        VC.add_port(name=f"{n + 1}", port=port)

    return VC


def etch_test(
    layer: LayerSpec = (1, 0),
    pad_size: tuple[float, float] = (2000, 2000),
    trench_width: float = 20,
) -> Device:
    """Construct side-by-side pads for performing electrical etch tests

    Args:
        layer (LayerSpec): desired layer specification
        pad_size (tuple[float, float]): width, height of each pad
        trench_width (float): width of trench around each pad

    Returns:
        Device: etch test structure
    """
    TRENCHES = Device("etch_trench")
    # create trench
    rect = pg.rectangle(size=pad_size, layer=layer)
    qg.utilities._create_layered_ports(rect, layer)
    pad_outlined = qg.utilities.outline(
        device=rect,
        outline_layers={layer: trench_width},
        kl_tile_size=max(pad_size[0], pad_size[1]),
    )
    t = TRENCHES.add_array(
        pad_outlined, columns=2, rows=1, spacing=(pad_size[0] + 5 * trench_width, 0)
    )
    t.move(t.center, (0, 0))
    return TRENCHES


def cross_bridge_kelvin_resistor(
    size: float = 50,
    lead_length: float = 50,
    layer_top: LayerSpec = "PHOTO1",
    layer_bot: LayerSpec = "EBEAM_COARSE",
    layer_via: LayerSpec | None = None,
    port_type: str = "electrical",
) -> Device:
    """Generate a cross-bridge Kelvin resistor

    See `this paper <http://ieeexplore.ieee.org/document/913141/>`_.

    Args:
        size (float): side length of square junction
        lead_length (float): length of leads to junction
        layer_top (LayerSpec): layer of top conductor
        layer_bot (LayerSpec): layer of bottom conductor
        layer_via (LayerSpec | None): if not None, create via on specified layer
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        Device: cross-bridge Kelvin resistor
    """
    CBKR = Device("cbkr")
    if layer_via is not None:
        center = qg.geometries.via(
            size=(size, size),
            via_undersize=1,
            layer_bottom=layer_bot,
            layer_via=layer_via,
            layer_top=layer_top,
        )
    else:
        center = Device()
        cbot = center << pg.compass(size=(size, size), layer=layer_bot)
        ctop = center << pg.compass(size=(size, size), layer=layer_top)
        for n, port in enumerate(cbot.ports):
            center.add_port(name=f"e2{n + 1}", port=port)
        for n, port in enumerate(ctop.ports):
            center.add_port(name=f"e1{n + 1}", port=port)
    top_ext = pg.compass(size=(lead_length, size), layer=layer_top)
    bot_ext = pg.compass(size=(lead_length, size), layer=layer_bot)
    center_i = CBKR << center
    ports = []
    for layer_i in range(2):
        for lead_i in range(2):
            lead = CBKR << (bot_ext if layer_i == 0 else top_ext)
            con_port = f"e{2 - layer_i}{lead_i + 1 + 2 * layer_i}"
            lead.connect(port=lead.ports["e1"], other=center_i.ports[con_port])
            ports.append(lead.ports["e3"])
    prefix = "e" if port_type == "electrical" else "o"
    for n, port in enumerate(ports):
        CBKR.add_port(name=f"{prefix}{n + 1}", port=port)
    for port in CBKR.ports:
        port.port_type = port_type
    return CBKR
