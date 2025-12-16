"""Geometries contains useful shapes/tools that are not available in phidl's
geometry library."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations


import numpy as np
import qnngds as qg
from qnngds import Device

from qnngds.typing import LayerSpec

from qnngds import CrossSection
import phidl.path as pp
import phidl.geometry as pg


def taper(
    length: int | float = 10,
    start_width: int | float = 5,
    end_width: int | float = 2,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Linear taper (solid).

    Args:
        length (int or float): Length of taper
        start_width (int or float): Width of first end of taper
        end_width (int or float): Width of second end of taper
        layer (LayerSpec): GDS layer tuple (layer, type) or string

    Returns:
        Device: a single taper
    """
    T = Device("taper")
    pts = [
        (0, -start_width / 2),
        (length, -end_width / 2),
        (length, end_width / 2),
        (0, start_width / 2),
    ]
    T.add_polygon(pts, layer=qg.get_layer(layer))
    T.add_port(
        name=1,
        midpoint=[0, 0],
        width=start_width,
        orientation=180,
        layer=layer,
    )
    T.add_port(
        name=2,
        midpoint=[length, 0],
        width=end_width,
        orientation=0,
        layer=layer,
    )
    return T


def hyper_taper(
    length: int | float = 10,
    start_width: int | float = 5,
    end_width: int | float = 50,
    layer: LayerSpec = (1, 0),
    num_points: int = 50,
) -> Device:
    """Hyperbolic taper (solid). Designed by colang.

    Args:
        length (int or float): Length of taper
        start_width (int or float): Width of start of taper
        end_width (int or float): Width of end of taper
        layer (LayerSpec): GDS layer tuple (layer, type) or string
        num_points (int): number of points to use

    Returns:
        Device: a single taper
    """
    path = pp.straight(length=length, num_pts=num_points)
    xc = CrossSection()
    xc.add(
        width=lambda t: qg.utilities.hyper_taper_fn(t, start_width, end_width),
        offset=0,
        layer=qg.get_layer(layer),
        ports=(1, 2),
    )
    taper = path.extrude(xc)
    qg.utilities._create_layered_ports(taper, layer)
    return taper


def euler_taper(
    start_width: int | float = 5,
    end_width: int | float = 50,
    layer: LayerSpec = (1, 0),
    num_points: int = 200,
) -> Device:
    """Hyperbolic taper (solid). Designed by reedf.

    Args:
        length (int | float): Length of taper
        start_width (int | float): Width of start of taper
        end_width (int | float): Width of end of taper
        layer (LayerSpec): GDS layer specification e.g. tuple (layer, type) or string
        num_points (int): number of points to use

    Returns:
        Device: a single taper
    """
    swapped = False
    if start_width > end_width:
        start_width, end_width = end_width, start_width
        swapped = True
    P_euler = pp.euler(
        radius=end_width / 2 - start_width / 2,
        angle=90,
        use_eff=True,
        p=1,
        num_pts=num_points,
    )

    D = Device("euler_taper")
    upper = np.array([(x, y + start_width / 2) for x, y in P_euler.points])
    lower = np.array([(x, -y - start_width / 2) for x, y in P_euler.points[::-1]])
    length = np.max(P_euler.points[:, 1])

    # create a polygon
    points = np.concatenate((upper, lower))
    points = np.array([(length - x if swapped else x, y) for x, y in points])
    D.add_polygon(points, layer=qg.get_layer(layer))

    if swapped:
        start_width, end_width = end_width, start_width

    # port 1: narrow/start_width end, port 2: wide/end_width end
    D.add_port(
        name=1,
        midpoint=(0, 0),
        width=start_width,
        orientation=180,
        layer=layer,
    )
    D.add_port(
        name=2,
        midpoint=(length, 0),
        width=end_width,
        orientation=0,
        layer=layer,
    )
    return D


def angled_taper(
    end_width: int | float = 0.2,
    start_width: int | float = 0.1,
    angle: int | float = 60,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Create an angled taper with euler curves.

    Args:
        end_width (int or float): Width of wide end of taper
        start_width (int or float): Width of narrow end of taper
        angle (int or float): Angle between taper ends in degrees
        layer (LayerSpec): GDS layer tuple (layer, type) or string

    Returns:
        Device: a single taper
    """

    if start_width > end_width:
        raise ValueError("{start_width=} > {end_width=} is not yet implemented")

    D = Device("angled_taper")
    # heuristic for length between narrow end and bend
    l_constr = start_width * 2 + end_width * 2
    # heuristic for length between wide end and bend
    l_wire = start_width * 2 + end_width * 2
    sin = np.sin(angle * np.pi / 180)
    cos = np.cos(angle * np.pi / 180)
    # path along the midpoint of the taper
    p_midpoint = np.array(
        [[0, 0], [l_constr, 0], [l_constr + l_wire * cos, l_wire * sin]]
    )
    # upper (shorter) path along the inside edge of the taper
    p_upper = np.array(
        [
            [0, start_width / 2],
            [0, start_width / 2],
            p_midpoint[2] + [-end_width / 2 * sin, end_width / 2 * cos],
        ]
    )
    p_upper[1, 0] = (start_width / 2 - p_upper[2, 1]) * cos / sin + p_upper[2, 0]
    # lower (longer) path along the outside edge of the taper
    p_lower = np.array(
        [
            [0, -start_width / 2],
            [0, -start_width / 2],
            p_midpoint[2] + [end_width / 2 * sin, -end_width / 2 * cos],
        ]
    )
    p_lower[1, 0] = (-start_width / 2 - p_lower[2, 1]) * cos / sin + p_lower[2, 0]
    # interpolate euler curve between points
    P_upper = pp.smooth(
        points=p_upper, radius=end_width, corner_fun=pp.euler, use_eff=False
    )
    P_lower = pp.smooth(
        points=p_lower, radius=end_width, corner_fun=pp.euler, use_eff=False
    )

    # create a polygon
    points = np.concatenate((P_upper.points, P_lower.points[::-1]))
    D.add_polygon(points, layer=qg.get_layer(layer))

    # port 1: narrow/start_width end, port 2: wide/end_width end
    D.add_port(
        name=1,
        midpoint=(P_upper.points[0] + P_lower.points[0]) / 2,
        width=start_width,
        orientation=180,
        layer=layer,
    )
    D.add_port(
        name=2,
        midpoint=(P_upper.points[-1] + P_lower.points[-1]) / 2,
        width=end_width,
        orientation=angle,
        layer=layer,
    )

    return D


def tee(
    size: tuple[float, float] = (4, 2),
    stub_size: tuple[float, float] = (2, 1),
    taper_type: str | None = "fillet",
    taper_radius: float | None = None,
    layer: LayerSpec = (1, 0),
) -> Device:
    """Creates a T-shaped geometry
    Adapted from phidl

    Args:
        size (array-like): (width, height) of the flag.
        stub_size : (array-like): (width, height) of the pole stub.
        taper_type (str | None) : {'straight', 'fillet', None}
            Type of taper between the bottom corner of the stub on the side of
            the flag and the corner of the flag closest to the stub.
        taper_radius (float | None) : radius of taper. If None, uses stub_size
        layer (LayerSpec): Specific layer(s) to put polygon geometry on.
    Returns:
        Device: tee
    """

    f = np.array(size).astype(np.float64)
    p = np.array(stub_size).astype(np.float64)

    assert taper_type in [
        "straight",
        "fillet",
        None,
    ], 'tee() taper_type must "straight"  or "fillet" or None'

    xpts = np.array([f[0], f[0], p[0], p[0], -p[0], -p[0], -f[0], -f[0]]) / 2
    ypts = [f[1], 0, 0, -p[1], -p[1], 0, 0, f[1]]

    D = Device("tee")
    tee = D.add_polygon([xpts, ypts], layer=qg.get_layer(layer))
    if taper_type == "fillet":
        if taper_radius is None:
            taper_radius = min([abs(f[0] - p[0]), abs(p[1])])
        tee.fillet([0, 0, taper_radius, 0, 0, taper_radius, 0, 0])
    elif taper_type == "straight":
        D.add_polygon([xpts[1:4], ypts[1:4]], layer=qg.get_layer(layer))
        D.add_polygon([xpts[4:7], ypts[4:7]], layer=qg.get_layer(layer))

    D.add_port(
        name=1,
        midpoint=(f[0] / 2, f[1] / 2),
        width=abs(f[1]),
        orientation=0,
        layer=layer,
    )
    D.add_port(
        name=2,
        midpoint=(-f[0] / 2, f[1] / 2),
        width=abs(f[1]),
        orientation=180,
        layer=layer,
    )
    D.add_port(
        name=3,
        midpoint=(0, -p[1]),
        width=abs(p[0]),
        orientation=270,
        layer=layer,
    )
    return D


def via(
    size: tuple[float, float] = (5, 5),
    via_undersize: float = 0.5,
    layer_bottom: LayerSpec = (1, 0),
    layer_via: LayerSpec = (10, 0),
    layer_top: LayerSpec = (20, 0),
) -> Device:
    """Creates a via between two layers

    Args:
        size (tuple[float, float]): width, height of top/bottom pads
        via_undersize (float): amount on each side to compensate overetch of via
        layer_bottom (LayerSpec): bottom layer specification
        layer_via (LayerSpec): via layer specification
        layer_top (LayerSpec): top layer specification

    Returns:
        Device: via
    """
    VIA = Device("via")
    if 2 * via_undersize > min(size[0], size[1]):
        raise ValueError(f"{via_undersize=} is too small for a pad with {size=}.")
    bot_pad = VIA << pg.compass(size=size, layer=qg.get_layer(layer_bottom))
    qg.utilities._create_layered_ports(bot_pad, layer_bottom)
    via = VIA << pg.compass(
        size=(size[0] - 2 * via_undersize, size[1] - 2 * via_undersize),
        layer=qg.get_layer(layer_via),
    )
    top_pad = VIA << pg.compass(size=size, layer=qg.get_layer(layer_top))
    qg.utilities._create_layered_ports(top_pad, layer_top)
    bot_pad.move(bot_pad.center, (0, 0))
    via.move(via.center, (0, 0))
    top_pad.move(top_pad.center, (0, 0))
    for n, comp in enumerate([top_pad, bot_pad]):
        for k, port in comp.ports.items():
            VIA.add_port(name=f"{n + 1}{k}", port=port)
    return VIA


def optimal_hairpin(
    width: float | int = 0.2,
    pitch: float | int = 0.6,
    length: float | int = 10,
    turn_ratio: float | int = 4,
    num_pts: float | int = 50,
    layer: LayerSpec = (1, 0),
) -> qg.Device:
    """Returns an optimally-rounded hairpin geometry, with a 180 degree turn.

    based on phidl.geometry. Used instead of phidl implementation to
    center the apex of the hairpin at (0, 0).

    Args:
        width: Width of the hairpin leads.
        pitch: Distance between the two hairpin leads. Must be greater than width.
        length: Length of the hairpin from the connectors to the opposite end of the curve.
        turn_ratio: int or float
            Specifies how much of the hairpin is dedicated to the 180 degree turn.
            A turn_ratio of 10 will result in 20% of the hairpin being comprised of the turn.
        num_pts: Number of points constituting the 180 degree turn.
        layer: Specific layer(s) to put polygon geometry on.

    Notes:
        Hairpin pitch must be greater than width.

        Optimal structure from https://doi.org/10.1103/PhysRevB.84.174510
        Clem, J., & Berggren, K. (2011). Geometry-dependent critical currents in
        superconducting nanocircuits. Physical Review B, 84(17), 1-27.
    """
    # ==========================================================================
    #  Create the basic geometry
    # ==========================================================================
    if pitch < width:
        raise Warning("Hairpin pitch must be greater than width")
    a = (pitch + width) / 2
    y = -(pitch - width) / 2
    x = -pitch
    dl = width / (num_pts * 2)
    n = 0

    # Get points of ideal curve from conformal mapping
    # TODO This is an inefficient way of finding points that you need
    xpts = [x]
    ypts = [y]
    while (y < 0) & (n < 1e6):
        s = x + 1j * y
        w = np.sqrt(1 - np.exp(np.pi * s / a))
        wx = np.real(w)
        wy = np.imag(w)
        wx = wx / np.sqrt(wx**2 + wy**2)
        wy = wy / np.sqrt(wx**2 + wy**2)
        x = x + wx * dl
        y = y + wy * dl
        xpts.append(x)
        ypts.append(y)
        n += 1
    ypts[-1] = 0  # Set last point be on the x=0 axis for sake of cleanliness
    ds_factor = len(xpts) // num_pts
    xpts = xpts[::-ds_factor]
    xpts = xpts[::-1]  # This looks confusing, but it's just flipping the arrays around
    ypts = ypts[::-ds_factor]
    ypts = ypts[::-1]  # so the last point is guaranteed to be included when downsampled

    apex = (xpts[-1], 0)

    # Add points for the rest of meander
    xpts.append(xpts[-1] + turn_ratio * width)
    ypts.append(0)
    xpts.append(xpts[-1])
    ypts.append(-a)
    xpts.append(xpts[0])
    ypts.append(-a)
    xpts.append(max(xpts) - length)
    ypts.append(-a)
    xpts.append(xpts[-1])
    ypts.append(-a + width)
    xpts.append(xpts[0])
    ypts.append(ypts[0])

    xpts = np.array(xpts)
    ypts = np.array(ypts)

    # ==========================================================================
    #  Create a blank device, add the geometry, and define the ports
    # ==========================================================================
    HP = qg.Device("optimal_hairpin")
    HP.add_polygon([xpts, +ypts], layer=layer)
    HP.add_polygon([xpts, -ypts], layer=layer)

    xports = float(np.min(xpts))
    yports = -a + width / 2
    HP.add_port(
        name=1,
        midpoint=(xports, -yports),
        width=width,
        orientation=180,
        layer=layer,
    )
    HP.add_port(
        name=2,
        midpoint=(xports, yports),
        width=width,
        orientation=180,
        layer=layer,
    )
    HP.move(apex, (0, 0))
    return HP


def default_cross_section(
    width: float = 25,
    layer: LayerSpec = (1, 0),
    radius: float = 30.0,
    force_no_outline: bool = False,
) -> CrossSection:
    """Return a default cross_section.

    Args:
        width (float): width of cross section
        layer (LayerSpec): desired layer for cross section
        radius (float): bend radius
        force_no_outline (bool): if True, ignores if layer is positive tone.

    Returns:
        CrossSection
    """
    outline = qg.get_layer(layer).outline
    XC = CrossSection(radius=radius)
    if (outline > 0) and not (force_no_outline):
        # if outline is greater than zero, then do a positive tone cross section
        # with the center of the cross section missing (hidden=True)
        XC.add(
            width=width,
            offset=0,
            layer=qg.get_layer(layer).tuple,
            hidden=True,
            ports=(1, 2),
        )
        for i in range(2):
            XC.add(
                width=outline,
                layer=qg.get_layer(layer).tuple,
                offset=(-1) ** i * (width + outline) / 2,
            )
    else:
        # just do a normal cross section
        XC.add(
            width=width,
            offset=0,
            layer=qg.get_layer(layer).tuple,
            ports=(1, 2),
        )
    return XC


def fine_to_coarse(
    width1: float = 2.0,
    width2: float = 20.0,
    layer1: LayerSpec = "EBEAM_FINE",
    layer2: LayerSpec = "EBEAM_COARSE",
) -> Device:
    """Create transition between fine and coarse layers

    Automatically performs outlining for positive-tone resist
    Args:
        width1 (float): starting width on first layer
        width2 (float): ending width on second layer
        layer1 (LayerSpec): layer specification (string or tuple) for first layer
        layer2 (LayerSpec): layer specification (string or tuple) for second layer

    Returns:
        Device: transition between fine and coarse layers
    """
    taper = Device()
    outline_layers = qg.utilities.get_outline_layers(qg.get_active_pdk().layers)
    pos_tone = False
    for layer in outline_layers.keys():
        if (qg.get_layer(layer).tuple == qg.get_layer(layer1).tuple) or (
            qg.get_layer(layer).tuple == qg.get_layer(layer2).tuple
        ):
            pos_tone = True
            break
    if pos_tone:
        outline = outline_layers[qg.get_layer(layer2).name]
        # positive tone
        t2 = qg.utilities.get_cross_section_with_layer(layer2).extrude(
            pp.straight(length=2 * outline)
        )
        wide = 2 * outline + width2
        if wide < width1:
            wide = width2
        wide += 2 * outline
        t1 = qg.geometries.hyper_taper(
            length=wide * 0.8,
            start_width=wide,
            end_width=width1,
            layer=layer1,
        )
        t1 = qg.utilities.outline(t1, outline_layers)
        t2_i = taper.add_ref(t2)
        t1_i = taper.add_ref(t1)
        t1_i.connect(
            port=t1_i.ports[1],
            destination=t2_i.ports[2],
        )
        t1_i.movex(-outline_layers[qg.get_layer(layer2).name] * 2)
        ports = [t1_i.ports[2], t2_i.ports[1]]
    else:
        t2 = pg.optimal_step(
            start_width=0.7 * width1,
            end_width=width2,
            num_pts=500,
            anticrowding_factor=0.6,
            symmetric=True,
            layer=qg.get_layer(layer2),
        )
        t1 = qg.geometries.hyper_taper(
            length=t2.xsize * 0.7,
            start_width=(width2 + width1) / 2,
            end_width=width1,
            layer=layer1,
        )
        t2_i = taper.add_ref(t2)
        t1_i = taper.add_ref(t1)
        t1_i.connect(
            port=t1_i.ports[1],
            destination=t2_i.ports[1],
        )
        t1_i.movex(0.8 * t1_i.xsize)
        ports = [t1_i.ports[2], t2_i.ports[2]]

    for n, port in enumerate(ports):
        taper.add_port(
            name=n + 1,
            midpoint=port.midpoint,
            orientation=port.orientation,
            width=port.width,
            layer=layer1 if n == 0 else layer2,
        )
    return taper
