"""Teststructures contains lithographic and electrical test structures."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import gdsfactory as gf

import qnngds as qg

from gdsfactory.typings import LayerSpec, LayerSpecs, ComponentSpecOrComponent
from typing import Union, List, Optional, Tuple

from functools import partial


@gf.cell
def _create_comb(
    pitch1: Union[int, float] = 0.5,
    pitch2: Union[int, float] = 0.1,
    layer1: tuple = (1, 0),
    layer2: tuple = (2, 0),
    text_angle: Union[int, float] = 0,
) -> gf.Component:
    """Creates vernier caliper comb.

    Helper method for alignment_mark
    Args:
        pitch1 (int or float): pitch of top comb
        pitch2 (int or float): pitch of bottom comb
        layer1 (tuple): center comb GDS layer tuple (layer, type)
        layer2 (tuple): top/bottom comb GDS layer tuple (layer, type)
        text_angle (int or float): angle to rotate text labels

    Returns:
        gf.Component: alignment vernier calipers
    """

    COMB = gf.Component()

    # middle comb (made of layer1), pitch = 10
    rect1 = gf.components.shapes.rectangle(size=(5, 30), layer=layer1)
    middle_comb = COMB.add_ref(rect1, columns=21, rows=1, column_pitch=10, row_pitch=0)
    middle_comb.move(COMB.center, (0, 0))

    # top and bottom combs (made of layer2), pitchs = 10+pitch1, 10+pitch2
    rect2 = gf.components.shapes.rectangle(size=(5, 30), layer=layer2)
    top_comb = COMB.add_ref(
        rect2, columns=21, rows=1, column_pitch=10 + pitch1, row_pitch=0
    )
    top_comb.move(top_comb.center, (middle_comb.center[0], middle_comb.center[1] + 30))
    top_text = COMB.add_ref(
        gf.components.texts.text(f"{round(pitch1 * 1e3)}NM", size=10, layer=layer2)
    )
    top_text.rotate(-text_angle)
    top_text.move(top_text.center, (140, 30))

    bottom_comb = COMB.add_ref(
        rect2, columns=21, rows=1, column_pitch=10 + pitch2, row_pitch=0
    )
    bottom_comb.move(
        bottom_comb.center, (middle_comb.center[0], middle_comb.center[1] - 30)
    )
    bottom_text = COMB.add_ref(
        gf.components.texts.text(f"{round(pitch2 * 1e3)}NM", size=10, layer=layer2)
    )
    bottom_text.rotate(-text_angle)
    bottom_text.move(bottom_text.center, (140, -30))

    # additional markers (made of layer1), for clarity
    rect1a = gf.components.shapes.rectangle((5, 20), layer=layer1)
    marksa = COMB.add_ref(rect1a, columns=3, rows=2, column_pitch=100, row_pitch=110)
    marksa.move(marksa.center, middle_comb.center)

    rect1b = gf.components.shapes.rectangle((5, 10), layer=layer1)
    marksb = COMB.add_ref(rect1b, columns=2, rows=2, column_pitch=100, row_pitch=100)
    marksb.move(marksb.center, middle_comb.center)

    return COMB


@gf.cell
def _create_marker(layer1: tuple = (1, 0), layer2: tuple = (2, 0)) -> gf.Component:
    """Creates vernier caliper comb

    Helper method for alignment_mark
    Args:
        layer1 (tuple): center comb GDS layer tuple (layer, type)
        layer2 (tuple): top/bottom comb GDS layer tuple (layer, type)

    Returns:
        gf.Component: alignment cross with vernier calipers
    """

    MARK = gf.Component()

    # central part with cross

    CROSS = gf.Component()
    cross = CROSS << gf.components.shapes.cross(length=200, width=2, layer=layer1)
    rect = gf.components.shapes.rectangle(size=(45, 45), layer=layer2)
    window = CROSS.add_ref(rect, rows=2, columns=2, row_pitch=155, column_pitch=155)
    window.move(window.center, cross.center)
    CROSS.flatten()

    MARK << CROSS

    VERNIER = gf.Component()
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
    TEXT = gf.Component()
    layer1_str = str(gf.get_layer(layer1)).split("_")[0]
    layer2_str = str(gf.get_layer(layer2)).split("_")[0]
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
        text1 = TEXT << gf.components.texts.text(bg_label, size=50, layer=layer)
        text1.move(text1.center, (-200, 190))
    text2 = TEXT << gf.components.texts.text(sm_label, size=10, layer=layer2)
    text2.move(text2.center, (-200, 250))
    if isinstance(layer1, tuple):
        layer1_numeric = f"{layer1[0]}/{layer1[1]}"
    else:
        layer1_enum = gf.get_layer(layer1)
        layer1_numeric = f"{layer1_enum[0]}/{layer1_enum[1]}"
    if isinstance(layer2, tuple):
        layer2_numeric = f"{layer2[0]}/{layer2[1]}"
    else:
        layer2_enum = gf.get_layer(layer2)
        layer2_numeric = f"{layer2_enum[0]}/{layer2_enum[1]}"
    text3 = TEXT << gf.components.texts.text(
        layer2_numeric + " ON " + layer1_numeric,
        size=10,
        layer=layer2,
    )
    text3.move(text3.center, (-200, 235))
    TEXT.flatten()
    MARK << TEXT

    return MARK


@gf.cell
def alignment_mark(
    layers: LayerSpecs = ["EBEAM_COARSE", "PHOTO1", "PHOTO2"],
) -> gf.Component:
    """Creates an alignment mark for each lithography layer.

    Args:
        layers (LayerSpecs): A list of GDS layers

    Returns:
        gf.Component: alignment marks between each layer pair
    """

    ALIGN = gf.Component()
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


@gf.cell
def _create_waffle(
    res: Union[float, int] = 1, layer: LayerSpec = (1, 0)
) -> gf.Component:
    """Creates waffle test structures for determining process resolution.

    Helper method for resolution_test
    Args:
        res (float or int): Resolution (in µm) to be tested.
        layer (LayerSpec): GDS layer tuple (layer, type)

    Returns:
        gf.Component: the resolution test structure
    """

    WAFFLE = gf.Component()
    W = gf.components.shapes.rectangle(size=(res * 80, res * 80), layer=layer)

    pattern = [(res * x, res * 80) for x in [2, 1, 1, 2, 3, 5, 8, 13, 21, 15]]
    DUMMY = gf.Component()
    WOut = DUMMY << qg.utilities.flex_grid(
        tuple(gf.components.shapes.rectangle(size=p, layer=layer) for p in pattern),
        spacing=res,
    )
    WOut.move(WOut.center, W.center)
    WAFFLE << gf.boolean(W, WOut, "-", layer=layer)
    WOut.rotate(90, center=WOut.center)
    WAFFLE << gf.boolean(W, WOut, "-", layer=layer)

    text = WAFFLE << gf.components.texts.text(str(res), size=20, layer=layer)
    start = (text.xmin, text.ymax)
    dy = -min(20, 20 * res)
    text.move(start, (0, dy))

    WAFFLEu = gf.Component()
    WAFFLEu << qg.utilities.union(WAFFLE)
    WAFFLEu.flatten()
    return WAFFLEu


@gf.cell
def _create_3L(res: Union[float, int] = 1, layer: LayerSpec = (1, 0)) -> gf.Component:
    """Creates L-shaped test structures for determining process resolution.

    Helper method for resolution_test
    Args:
        res (float or int): Resolution (in µm) to be tested.
        layer (LayerSpec): GDS layer tuple (layer, type)

    Returns:
        gf.Component: the resolution test structure
    """

    LLL = gf.Component()
    grid_spacing = (15 * res, 15 * res)

    deviation = [0.8, 1, 1.2]
    for i, percent in enumerate(deviation):
        bars = gf.Component()
        w = percent * res
        spacing = 2 * res
        bar = gf.components.shapes.rectangle(size=(min(100 * res, 100), w), layer=layer)
        h_bars = bars.add_ref(bar, columns=1, rows=5, column_pitch=0, row_pitch=spacing)
        v_bars = bars.add_ref(bar, columns=1, rows=5, column_pitch=0, row_pitch=spacing)
        h_bars.rotate(90)
        h_bars.move((h_bars.xmin, h_bars.ymin), (0, 0))
        v_bars.move((v_bars.xmin, v_bars.ymin), (0, 0))
        lll = LLL << bars
        lll.move([i * offset for offset in grid_spacing])

    text = LLL << gf.components.texts.text(str(res), size=20, layer=layer)
    start = (text.xmin, text.ymin)
    text.move(start, [(len(deviation) + 0.5) * offset for offset in grid_spacing])
    LLLu = gf.Component()
    LLLu << qg.utilities.union(LLL)
    LLLu.flatten()
    return LLLu


@gf.cell
def resolution_test(
    resolutions: List[float] = [0.8, 1, 1.2, 1.4, 1.6, 1.8, 2.0],
    outline: Optional[float] = None,
    layer: LayerSpec = (2, 0),
) -> gf.Component:
    """Creates test structures for determining a process resolution.

    Args:
        resolutions (List[float]): List of resolutions (in µm) to be tested.
        outline (Optional[float]): If none, do not invert. If zero, invert the device, otherwise outline the device by this width.
        layer (LayerSpec): GDS layer tuple (layer, type)

    Returns:
        gf.Component: the resolution test structures
    """

    tests = []
    for test_fn in (_create_3L, _create_waffle):
        tests.append(
            gf.grid(
                tuple(test_fn(res, layer) for res in resolutions),
                spacing=10,
                shape=(1, len(resolutions)),
                align_y="ymin",
            )
        )
    RES_TEST = gf.Component()
    rt = RES_TEST << gf.grid(tests, spacing=20, align_x="xmin")
    rt.move(rt.center, (0, 0))

    if outline is not None:
        if outline > 0:
            RES_TEST = qg.utilities.outline(RES_TEST, {layer: outline})
        else:
            RES_TEST = qg.utilities.invert(RES_TEST, {layer: 5})

    RES_TESTu = gf.Component()
    RES_TESTu << qg.utilities.union(RES_TEST)
    RES_TESTu.flatten()
    return RES_TESTu


@gf.cell
def vdp(
    diagonal: float = 400,
    contact_width: float = 40,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Creates a Van der Pauw (VDP) device with specified dimensions.

    Args:
        diagonal (float): Length of the VDP device, overall maximum dimension, in µm.
        contact_width (float): Width of the contact points (width of the ports), in µm.
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: Van der Pauw cell
    """
    VDP = gf.Component()

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

    VDP.add_polygon(zip(xpts, ypts), layer=layer)

    for i in range(4):
        x = -((-1) ** (i // 2)) * diagonal / 2 if i % 2 == 0 else 0
        y = (-1) ** (i // 2) * diagonal / 2 if i % 2 == 1 else 0
        VDP.add_port(
            name=f"e{i + 1}",
            center=[x, y],
            width=contact_width,
            orientation=180 - 90 * i,
            layer=layer,
            port_type=port_type,
        )

    return VDP


@gf.cell
def rect_tlm(
    contact_l: float = 10,
    spacings: List[float] = [10, 10, 20, 50, 80, 100, 200],
    contact_w: float = 100,
    via_layer: LayerSpec | None = (2, 0),
    finger_layer: LayerSpec = (3, 0),
    pad_layer: LayerSpec | None = (3, 0),
    mesa_layer: LayerSpec = (4, 0),
    pad_size: Tuple[float, float] = (80, 80),
) -> gf.Component:
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
        gf.Component: TLM structure
    """
    TLM = gf.Component()
    xoff = 0
    for n, space in enumerate(spacings):
        fp_w = space + 2 * contact_l
        w = contact_w * 1.2 + 10
        for i in range(2):
            fp = TLM << qg.geometries.flagpole(
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
                via = TLM << gf.components.rectangle(
                    size=(contact_l, contact_w + 10), layer=via_layer
                )
                if i % 2:
                    via.move((fp.xmax - contact_l / 2 - via.x, -via.y))
                else:
                    via.move((fp.xmin + contact_l / 2 - via.x, -via.y))
                # add vias to lower metal pads
                pad_via = TLM << gf.components.rectangle(
                    size=(fp_w, pad_size[1]), layer=via_layer
                )
                pad_via.movex(fp.xmax - pad_via.xmax)
                if i % 2:
                    pad_via.movey(fp.ymin - pad_via.ymin)
                else:
                    pad_via.movey(fp.ymax - pad_via.ymax)
                top_pad = TLM << gf.components.rectangle(
                    size=(fp_w + 2, pad_size[1] + 2), layer=pad_layer
                )
                top_pad.move(top_pad.center, pad_via.center)
        text = TLM << gf.components.texts.text(str(space), layer=finger_layer)
        text.move((xoff - text.xmin + 5, -w / 2 - pad_size[1] + 10 - text.ymin))
    # add mesa
    mesa = TLM << gf.components.rectangle(
        size=(TLM.xsize + 50, contact_w), layer=mesa_layer
    )
    mesa.move(mesa.center, (TLM.x, 0))
    return TLM


@gf.cell
def circ_tlm(
    ext_radius: float = 100,
    int_radius: List[float] = [50, 70, 80, 90, 95, 98, 99],
    pad_layer: LayerSpec = (3, 0),
    mesa_layers: LayerSpecs = [(1, 0), (2, 0)],
    text_size: float = 10,
) -> gf.Component:
    """Creates rectangular transfer-length-method test structures.

    Args:
        ext_radius (float): external radius of hole that defines outer pad
        int_radius (List[float]): list of internal radii. The gap is d = ext_radius - int_radius.
        pad_layer (LayerSpec): layer for probable pads.
        mesa_layers (LayerSpecs): layer(s) for bottom metal/semiconductor and/or vias
        text_size (float): size of text label

    Returns:
        gf.Component: TLM structure
    """
    TLM = gf.Component()

    cuts = []
    for r_i in int_radius:
        d = ext_radius - r_i
        r = (ext_radius + r_i) / 2
        CUT = gf.Component()
        r = CUT << gf.components.ring(
            radius=r, width=d, angle_resolution=2.5, layer=pad_layer, angle=360
        )
        t = CUT << gf.components.text(
            text=f"{ext_radius}/{r_i}", size=text_size, justify="right", layer=pad_layer
        )
        t.move((t.xmax, t.ymax), (r.xmax, r.ymax))
        cuts.append(CUT)
    c = qg.utilities.flex_grid(
        cuts,
        spacing=(10, 10),
        shape=(1, len(cuts)),
        align_x="center",
        align_y="center",
        rotation=0,
        mirror=False,
    )
    # make the mesa
    for layer in mesa_layers:
        m = TLM << gf.components.shapes.compass(
            size=(c.xsize + 10, c.ysize + 10), layer=layer
        )
        m.move(m.center, c.center)
    DUMMY = gf.Component()
    p = DUMMY << gf.components.shapes.compass(
        size=(c.xsize + 10, c.ysize + 10), layer=pad_layer
    )
    p.move(p.center, c.center)
    TLM << gf.boolean(
        A=p,
        B=c,
        operation="A-B",
        layer1=pad_layer,
        layer2=pad_layer,
        layer=pad_layer,
    )
    return TLM


@gf.cell
def via_chain(
    via_spec: ComponentSpecOrComponent = qg.geometries.via,
    num_vias: int = 5,
    spacing: float = 10,
    tap_period: int = 1,
    port_type: str = "electrical",
) -> gf.Component:
    """Makes a chain of vias, with optional taps along the length of the chain

    Args:
        via_spec (ComponentSpec | Component): function, component name, or component for the via
        num_vias (int): number of vias to include in chain
        spacing (float): spacing between vias
        tap_period (int): number of vias between each tap. If zero, doesn't place any taps.
        port_type (str): "electrical" or "optical"

    Returns:
        gf.Component: the via chain
    """
    if tap_period < 0:
        raise ValueError(f"{tap_period=} must be positive")
    if tap_period > 1:
        raise ValueError("tap_period > 1 has not been implemented yet")

    VC = gf.Component()
    via = gf.get_component(via_spec)
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
        p = gf.path.straight(length=spacing, npoints=2)
        connector = partial(gf.path.extrude, p=p, width=width)
    else:
        connector = partial(
            qg.geometries.tee,
            size=(spacing, width),
            stub_size=(width, width),
            taper_type="fillet",
            taper_radius=width / 2,
            port_type="optical",
        )

    vias = VC.add_ref(
        via, columns=num_vias, rows=1, column_pitch=via.xsize + spacing, row_pitch=1
    )
    east_end_port_layer = west_layer if num_vias % 2 == 0 else east_layer
    east_end_port_name = [
        port for port in port_dict["E"] if port.layer == east_end_port_layer
    ][0].name
    if num_vias > 1:
        end_ports = [
            vias.ports[west_port.name, 0, 0],
            vias.ports[east_end_port_name, num_vias - 1, 0],
        ]
    else:
        end_ports = [vias.ports[west_port.name], vias.ports[east_end_port_name]]
    conn_ports = []
    for i in range(2):
        layer = east_layer if i == 0 else west_layer
        port = east_port if i == 0 else west_port
        odd = i
        n_conn = (num_vias - odd) // 2
        if n_conn > 0:
            conn = VC.add_ref(
                connector(layer=layer),
                columns=n_conn,
                rows=1,
                column_pitch=2 * (via.xsize + spacing),
                row_pitch=1,
            )
            conn.connect(
                conn.ports["o1"],
                vias.ports[port.name, 2 if odd else 0, 0],
                allow_type_mismatch=True,
            )
            if tap_period > 0:
                if odd:
                    conn_ports.append(
                        [
                            conn.ports["o3", n, 0] if n_conn > 1 else conn.ports["o3"]
                            for n in range(n_conn - 1, -1, -1)
                        ]
                    )
                else:
                    conn_ports.append(
                        [
                            conn.ports["o3", n, 0] if n_conn > 1 else conn.ports["o3"]
                            for n in range(n_conn)
                        ]
                    )
        else:
            conn_ports.append([])
    ports = [end_ports[0]]
    if len(conn_ports) > 0:
        ports += conn_ports[0]
    ports += [end_ports[1]]
    if len(conn_ports) > 1:
        ports += conn_ports[1]

    prefix = "e" if port_type == "electrical" else "o"
    for n, port in enumerate(ports):
        VC.add_port(name=f"{prefix}{n + 1}", port=port)
    for port in VC.ports:
        port.port_type = port_type

    return VC
