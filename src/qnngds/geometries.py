"""Geometries contains useful shapes/tools that are not available in phidl's
geometry library."""

import gdsfactory as gf
import numpy as np

import qnngds.utilities as qu

from gdsfactory.typings import LayerSpec
from typing import Union, List, Optional


@gf.cell
def taper(
    length: Union[int, float] = 10,
    wide: Union[int, float] = 5,
    narrow: Union[int, float] = 2,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Linear taper (solid).

    Parameters
        length (int or float): Length of taper
        wide (int or float): Width of wide end of taper
        narrow (int or float): Width of narrow end of taper
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns
        gf.Component: a single taper
    """
    if wide < narrow:
        wide, narrow = narrow, wide
    T = gf.Component()
    pts = [
        (0, -wide / 2),
        (length, -narrow / 2),
        (length, narrow / 2),
        (0, wide / 2),
    ]
    T.add_polygon(pts, layer=layer)
    T.add_port(
        name="e1" if port_type == "electrical" else "o1",
        center=[0, 0],
        width=wide,
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    T.add_port(
        name="e2" if port_type == "electrical" else "o2",
        center=[length, 0],
        width=narrow,
        orientation=0,
        layer=layer,
        port_type=port_type,
    )
    return T


@gf.cell
def hyper_taper(
    length: Union[int, float] = 10,
    wide_section: Union[int, float] = 50,
    narrow_section: Union[int, float] = 5,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Hyperbolic taper (solid). Designed by colang.

    Parameters
        length (int or float): Length of taper
        wide_section (int or float): Width of wide end of taper
        narrow_section (int or float): Width of narrow end of taper
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns
        gf.Component: a single taper
    """
    HT = gf.Component()

    taper_length = length
    wide = wide_section
    narrow = narrow_section
    if wide < narrow:
        wide, narrow = narrow, wide
    dx = narrow_section / 1000
    x_list = np.linspace(0, taper_length, int(taper_length / dx), endpoint=True)
    pts = []

    a = np.arccosh(wide / narrow) / taper_length

    for x in x_list:
        pts.append((x, np.cosh(a * x) * narrow / 2))
    for x in reversed(x_list):
        pts.append((x, -np.cosh(a * x) * narrow / 2))
    HT.add_polygon(pts, layer=layer)
    HT.add_port(
        name="e1",
        center=[0, 0],
        width=narrow,
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    HT.add_port(
        name="e2",
        center=[taper_length, 0],
        width=wide,
        orientation=0,
        layer=layer,
        port_type=port_type,
    )
    return HT


@gf.cell
def angled_taper(
    wire_width: Union[int, float] = 0.2,
    constr_width: Union[int, float] = 0.1,
    angle: Union[int, float] = 60,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Create an angled taper with euler curves.

    Parameters
        wire_width (int or float): Width of wide end of taper
        constr_width (int or float): Width of narrow end of taper
        angle (int or float): Angle between taper ends in degrees
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns
        gf.Component: a single taper
    """

    D = gf.Component()
    # heuristic for length between narrow end and bend
    l_constr = constr_width * 2 + wire_width * 2
    # heuristic for length between wide end and bend
    l_wire = constr_width * 2 + wire_width * 2
    sin = np.sin(angle * np.pi / 180)
    cos = np.cos(angle * np.pi / 180)
    # path along the center of the taper
    p_center = np.array(
        [[0, 0], [l_constr, 0], [l_constr + l_wire * cos, l_wire * sin]]
    )
    # upper (shorter) path along the inside edge of the taper
    p_upper = np.array(
        [
            [0, constr_width / 2],
            [0, constr_width / 2],
            p_center[2] + [-wire_width / 2 * sin, wire_width / 2 * cos],
        ]
    )
    p_upper[1, 0] = (constr_width / 2 - p_upper[2, 1]) * cos / sin + p_upper[2, 0]
    # lower (longer) path along the outside edge of the taper
    p_lower = np.array(
        [
            [0, -constr_width / 2],
            [0, -constr_width / 2],
            p_center[2] + [wire_width / 2 * sin, -wire_width / 2 * cos],
        ]
    )
    p_lower[1, 0] = (-constr_width / 2 - p_lower[2, 1]) * cos / sin + p_lower[2, 0]
    # interpolate euler curve between points
    P_upper = gf.path.smooth(
        points=p_upper, radius=wire_width, bend=gf.path.euler, use_eff=False
    )
    P_lower = gf.path.smooth(
        points=p_lower, radius=wire_width, bend=gf.path.euler, use_eff=False
    )

    # create a polygon
    points = np.concatenate((P_upper.points, P_lower.points[::-1]))
    D.add_polygon(points, layer=layer)

    # port 1: narrow/constr_width end, port 2: wide/wire_width end
    D.add_port(
        name="e1",
        center=(P_upper.points[0] + P_lower.points[0]) / 2,
        width=constr_width,
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    D.add_port(
        name="e2",
        center=(P_upper.points[-1] + P_lower.points[-1]) / 2,
        width=wire_width,
        orientation=angle,
        layer=layer,
        port_type=port_type,
    )

    return D


@gf.cell
def optimal_step(
    start_width: float = 10,
    end_width: float = 22,
    num_pts: int = 50,
    width_tol: float = 1e-3,
    anticrowding_factor: float = 1.2,
    symmetric: bool = False,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Returns an optimally-rounded step geometry.

    Wrapper for gdsfactory.components.superconductors.optimal_step that provides a port_type
    Args:
        start_width (float): Width of the connector on the left end of the step.
        end_width (float): Width of the connector on the right end of the step.
        num_pts (int): number of points comprising the entire step geometry.
        width_tol (float): Point at which to terminate the calculation of the optimal step
        anticrowding_factor (float): Factor to reduce current crowding by elongating
            the structure and reducing the curvature
        symmetric: If True, adds a mirrored copy of the step across the x-axis to the
            geometry and adjusts the width of the ports.
        layer (LayerSpec): GDS layer spec, string or tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Optimal structure from https://doi.org/10.1103/PhysRevB.84.174510
    Clem, J., & Berggren, K. (2011). Geometry-dependent critical currents in
    superconducting nanocircuits. Physical Review B, 84(17), 1-27.
    """
    S = gf.Component()
    step = gf.components.superconductors.optimal_step(
        start_width=start_width,
        end_width=end_width,
        num_pts=num_pts,
        width_tol=width_tol,
        anticrowding_factor=anticrowding_factor,
        symmetric=symmetric,
        layer=layer,
    )
    S.add_ref(step)
    S.add_ports(step.ports)
    for port in S.ports:
        port.port_type = port_type
    return S


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
    Parameters
        pitch1 (int or float): pitch of top comb
        pitch2 (int or float): pitch of bottom comb
        layer1 (tuple): center comb GDS layer tuple (layer, type)
        layer2 (tuple): top/bottom comb GDS layer tuple (layer, type)
        text_angle (int or float): angle to rotate text labels

    Returns
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
    Parameters
        layer1 (tuple): center comb GDS layer tuple (layer, type)
        layer2 (tuple): top/bottom comb GDS layer tuple (layer, type)

    Returns
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

    Parameters
        layers (List[tuple]): A list of GDS layer tuples (layer, type)

    Returns
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
    WOut = qu.flex_grid(
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
    WAFFLEu << qu.union(WAFFLE)
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
    LLLu << qu.union(LLL)
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
    RES_TEST = gf.grid(tests, spacing=20, align_x="xmin")
    RES_TEST.move(RES_TEST.center, (0, 0))

    if outline is not None:
        if outline > 0:
            RES_TEST = qu.outline(RES_TEST, {layer: outline})
        else:
            RES_TEST = qu.invert(RES_TEST, {layer: 5})

    RES_TESTu = gf.Component()
    RES_TESTu << qu.union(RES_TEST)
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
