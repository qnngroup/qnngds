"""Teststructures contains lithographic and electrical test structures."""

import gdsfactory as gf

import qnngds as qg

from gdsfactory.typings import LayerSpec, LayerSpecs
from typing import Union, List, Optional, Tuple


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
    for layer in (layer1, layer2):
        text1 = TEXT << gf.components.texts.text(
            f"{layer2[0]}/{layer2[1]}", size=50, layer=layer
        )
        text1.move(text1.center, (-200, 200))
    text2 = TEXT << gf.components.texts.text(
        f"{layer2[0]}/{layer2[1]} ON {layer1[0]}/{layer1[1]}", size=10, layer=layer2
    )
    text2.move(text2.center, (-200, 250))
    TEXT.flatten()
    MARK << TEXT

    return MARK


@gf.cell
def alignment_mark(
    layers: List[tuple] = [(1, 0), (2, 0), (3, 0), (4, 0)],
) -> gf.Component:
    """Creates an alignment mark for each photolithography.

    Args:
        layers (List[tuple]): A list of GDS layer tuples (layer, type)

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
    text.move(start, (2 * res, -2 * res))

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
    grid_spacing = (13 * res, 13 * res)

    space = [0.8, 1, 1.2]
    for i, percent in enumerate(space):
        bars = gf.Component()
        w = percent * res
        spacing = 2 * res
        bar = gf.components.shapes.rectangle(size=(min(100 * w, 100), w), layer=layer)
        h_bars = bars.add_ref(bar, columns=1, rows=5, column_pitch=0, row_pitch=spacing)
        v_bars = bars.add_ref(bar, columns=1, rows=5, column_pitch=0, row_pitch=spacing)
        h_bars.rotate(90)
        h_bars.move((LLL.xmin - h_bars.xmin, LLL.ymin - h_bars.ymin))
        v_bars.move((LLL.xmin - v_bars.xmin, LLL.ymin - v_bars.ymin))
        lll = LLL << bars
        lll.move([i * space for space in grid_spacing])

    text = LLL << gf.components.texts.text(str(res), size=20, layer=layer)
    start = (text.xmin, text.ymin)
    text.move(start, [(i + 1) * space for space in grid_spacing])
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
    mesa_layers: LayerSpecs = [(4, 0), (2, 0)],
) -> gf.Component:
    """Creates rectangular transfer-length-method test structures.

    Args:
        ext_radius (float): external radius of hole that defines outer pad
        int_radius (List[float]): list of internal radii. The gap is d = ext_radius - int_radius.
        pad_layer (LayerSpec): layer for probable pads.
        mesa_layers (LayerSpecs): layer(s) for bottom metal/semiconductor and/or vias

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
            text=f"{ext_radius}/{r_i}", size=10, justify="right", layer=pad_layer
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
