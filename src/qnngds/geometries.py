"""Geometries contains useful shapes/tools that are not available in phidl's
geometry library."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import gdsfactory as gf
import numpy as np

import qnngds as qg

from gdsfactory.typings import LayerSpec, Ints, Size
from gdsfactory.config import valid_port_orientations
from typing import Union


@gf.cell
def taper(
    length: Union[int, float] = 10,
    start_width: Union[int, float] = 5,
    end_width: Union[int, float] = 2,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Linear taper (solid).

    Args:
        length (int or float): Length of taper
        start_width (int or float): Width of first end of taper
        end_width (int or float): Width of second end of taper
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: a single taper
    """
    T = gf.Component()
    pts = [
        (0, -start_width / 2),
        (length, -end_width / 2),
        (length, end_width / 2),
        (0, start_width / 2),
    ]
    T.add_polygon(pts, layer=layer)
    T.add_port(
        name="e1" if port_type == "electrical" else "o1",
        center=[0, 0],
        width=start_width,
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    T.add_port(
        name="e2" if port_type == "electrical" else "o2",
        center=[length, 0],
        width=end_width,
        orientation=0,
        layer=layer,
        port_type=port_type,
    )
    return T


@gf.cell
def hyper_taper(
    length: Union[int, float] = 10,
    start_width: Union[int, float] = 5,
    end_width: Union[int, float] = 50,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Hyperbolic taper (solid). Designed by colang.

    Args:
        length (int or float): Length of taper
        start_width (int or float): Width of start of taper
        end_width (int or float): Width of end of taper
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: a single taper
    """
    prefix = "e" if port_type == "electrical" else "o"
    section = gf.Section(
        width=0,
        width_function=lambda t: qg.utilities.hyper_taper_fn(t, start_width, end_width),
        offset=0,
        layer=layer,
        port_types=(port_type, port_type),
        port_names=(f"{prefix}1", f"{prefix}2"),
    )
    xc = gf.CrossSection(sections=(section,))
    return gf.path.extrude(gf.path.straight(length=length, npoints=200), xc)


@gf.cell
def angled_taper(
    end_width: Union[int, float] = 0.2,
    start_width: Union[int, float] = 0.1,
    angle: Union[int, float] = 60,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Create an angled taper with euler curves.

    Args:
        end_width (int or float): Width of wide end of taper
        start_width (int or float): Width of narrow end of taper
        angle (int or float): Angle between taper ends in degrees
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: a single taper
    """

    if start_width > end_width:
        raise ValueError("{start_width=} > {end_width=} is not yet implemented")

    D = gf.Component()
    # heuristic for length between narrow end and bend
    l_constr = start_width * 2 + end_width * 2
    # heuristic for length between wide end and bend
    l_wire = start_width * 2 + end_width * 2
    sin = np.sin(angle * np.pi / 180)
    cos = np.cos(angle * np.pi / 180)
    # path along the center of the taper
    p_center = np.array(
        [[0, 0], [l_constr, 0], [l_constr + l_wire * cos, l_wire * sin]]
    )
    # upper (shorter) path along the inside edge of the taper
    p_upper = np.array(
        [
            [0, start_width / 2],
            [0, start_width / 2],
            p_center[2] + [-end_width / 2 * sin, end_width / 2 * cos],
        ]
    )
    p_upper[1, 0] = (start_width / 2 - p_upper[2, 1]) * cos / sin + p_upper[2, 0]
    # lower (longer) path along the outside edge of the taper
    p_lower = np.array(
        [
            [0, -start_width / 2],
            [0, -start_width / 2],
            p_center[2] + [end_width / 2 * sin, -end_width / 2 * cos],
        ]
    )
    p_lower[1, 0] = (-start_width / 2 - p_lower[2, 1]) * cos / sin + p_lower[2, 0]
    # interpolate euler curve between points
    P_upper = gf.path.smooth(
        points=p_upper, radius=end_width, bend=gf.path.euler, use_eff=False
    )
    P_lower = gf.path.smooth(
        points=p_lower, radius=end_width, bend=gf.path.euler, use_eff=False
    )

    # create a polygon
    points = np.concatenate((P_upper.points, P_lower.points[::-1]))
    D.add_polygon(points, layer=layer)

    # port 1: narrow/start_width end, port 2: wide/end_width end
    D.add_port(
        name="e1",
        center=(P_upper.points[0] + P_lower.points[0]) / 2,
        width=start_width,
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    D.add_port(
        name="e2",
        center=(P_upper.points[-1] + P_lower.points[-1]) / 2,
        width=end_width,
        orientation=angle,
        layer=layer,
        port_type=port_type,
    )

    return D


@gf.cell
def flagpole(
    size: tuple[float, float] = (4, 2),
    stub_size: tuple[float, float] = (2, 1),
    shape: str = "p",
    taper_type: str | None = "fillet",
    taper_radius: float | None = None,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Creates a flagpole geometry of one of four configurations, all
    involving a vertical central column and a outward-pointing flag.

    Adapted from phidl

    Args:
        size (array-like): (width, height) of the flag.
        stub_size : (array-like): (width, height) of the pole stub.
        shape (str): {'p', 'q', 'b', 'd'}
            Configuration of the flagpole, where the curved portion of the
            letters represents the flag and the straight portion the pole.
        taper_type (str | None) : {'straight', 'fillet', None}
            Type of taper between the bottom corner of the stub on the side of
            the flag and the corner of the flag closest to the stub.
        taper_radius (float | None) : radius of taper. If None, uses stub_size
        layer (int | array-like[2] | set)
            Specific layer(s) to put polygon geometry on.
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: Flagpole
    """
    f = np.array(size).astype(float)
    p = np.array(stub_size).astype(float)
    shape = shape.lower()

    assert shape in "pqbd", "[DEVICE]  flagpole() shape must be p, q, b, or d"
    assert taper_type in [
        "straight",
        "fillet",
        None,
    ], 'flagpole() taper_type must "straight"  or "fillet" or None'

    if shape == "p":
        orientation = -90
    elif shape == "q":
        f[0], p[0] = -size[0], -stub_size[0]
        orientation = -90
    elif shape == "b":
        f[1], p[1] = -size[1], -stub_size[1]
        orientation = 90
    elif shape == "d":
        f[1], p[1] = -size[1], -stub_size[1]
        f[0], p[0] = -size[0], -stub_size[0]
        orientation = 90
    xpts = [0, 0, f[0], f[0], p[0], p[0], 0]
    ypts = [0, f[1], f[1], 0, 0, -p[1], -p[1]]

    D = gf.Component()
    D.add_polygon(zip(xpts, ypts), layer=layer)
    if taper_type == "fillet":
        if taper_radius is None:
            taper_radius = min([abs(f[0] - p[0]), abs(p[1])]) / gf.kcl.dbu
        else:
            taper_radius = taper_radius / gf.kcl.dbu
        for poly in D.get_polygons()[gf.get_layer(layer)]:
            D.add_polygon(poly.round_corners(taper_radius, 0, 300), layer=layer)
    elif taper_type == "straight":
        D.add_polygon(zip(xpts[3:6], ypts[3:6]), layer=layer)

    D.add_port(
        name="e1" if port_type == "electrical" else "o1",
        center=(p[0] / 2, -p[1]),
        width=abs(p[0]),
        orientation=orientation,
        layer=layer,
        port_type=port_type,
    )
    D.add_port(
        name="e2" if port_type == "electrical" else "o2",
        center=(f[0] / 2, f[1]),
        width=abs(f[0]),
        orientation=orientation - 180,
        layer=layer,
        port_type=port_type,
    )
    return D


@gf.cell
def tee(
    size: tuple[float, float] = (4, 2),
    stub_size: tuple[float, float] = (2, 1),
    taper_type: str | None = "fillet",
    taper_radius: float | None = None,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Creates a T-shaped geometry

    Adapted from phidl

    Args:
        size (array-like): (width, height) of the flag.
        stub_size : (array-like): (width, height) of the pole stub.
        taper_type (str | None) : {'straight', 'fillet', None}
            Type of taper between the bottom corner of the stub on the side of
            the flag and the corner of the flag closest to the stub.
        taper_radius (float | None) : radius of taper. If None, uses stub_size
        layer (int | array-like[2] | set)
            Specific layer(s) to put polygon geometry on.
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: tee
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

    D = gf.Component()
    D.add_polygon(zip(xpts, ypts), layer=layer)
    if taper_type == "fillet":
        if taper_radius is None:
            taper_radius = min([abs(f[0] - p[0]), abs(p[1])]) / gf.kcl.dbu
        else:
            taper_radius = taper_radius / gf.kcl.dbu
        for poly in D.get_polygons()[gf.get_layer(layer)]:
            D.add_polygon(poly.round_corners(taper_radius, 0, 300), layer=layer)
    elif taper_type == "straight":
        D.add_polygon(zip(xpts[1:4], ypts[1:4]), layer=layer)
        D.add_polygon(zip(xpts[4:7], ypts[4:7]), layer=layer)

    D.add_port(
        name="e1" if port_type == "electrical" else "o1",
        center=(f[0] / 2, f[1] / 2),
        width=abs(f[1]),
        orientation=0,
        layer=layer,
        port_type=port_type,
    )
    D.add_port(
        name="e2" if port_type == "electrical" else "o2",
        center=(-f[0] / 2, f[1] / 2),
        width=abs(f[1]),
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    D.add_port(
        name="e3" if port_type == "electrical" else "o3",
        center=(0, -p[1]),
        width=abs(p[0]),
        orientation=270,
        layer=layer,
        port_type=port_type,
    )
    return D


@gf.cell
def via(
    size: tuple[float, float] = (5, 5),
    via_undersize: float = 0.5,
    layer_bottom: LayerSpec = (1, 0),
    layer_via: LayerSpec = (2, 0),
    layer_top: LayerSpec = (3, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Creates a via between two layers

    Args:
        size (tuple[float, float]): width, height of top/bottom pads
        via_undersize (float): amount on each side to compensate overetch of via
        layer_bottom (LayerSpec): bottom layer specification
        layer_via (LayerSpec): via layer specification
        layer_top (LayerSpec): top layer specification
        port_type (string): "electrical" or "optical"

    Returns:
        gf.Component: via
    """
    VIA = gf.Component()
    if 2 * via_undersize > min(size[0], size[1]):
        raise ValueError(f"{via_undersize=} is too small for a pad with {size=}.")
    bot_pad = VIA << qg.geometries.compass(size=size, layer=layer_bottom)
    via = VIA << qg.geometries.compass(
        size=(size[0] - 2 * via_undersize, size[1] - 2 * via_undersize), layer=layer_via
    )
    top_pad = VIA << qg.geometries.compass(size=size, layer=layer_top)
    bot_pad.move(bot_pad.center, (0, 0))
    via.move(via.center, (0, 0))
    top_pad.move(top_pad.center, (0, 0))
    prefix = "e" if port_type == "electrical" else "o"
    for n, comp in enumerate([top_pad, bot_pad]):
        for m, port in enumerate(comp.ports):
            VIA.add_port(name=f"{prefix}{n + 1}{m + 1}", port=port)
    for port in VIA.ports:
        port.port_type = port_type
    return VIA


@gf.cell
def optimal_hairpin(
    width: float = 0.2,
    pitch: float = 0.6,
    length: float = 10,
    turn_ratio: float = 4,
    num_pts: int = 50,
    layer: LayerSpec = (1, 0),
) -> gf.Component:
    """Returns an optimally-rounded hairpin geometry, with a 180 degree turn.

    based on phidl.geometry and gdsfactory. Used instead of gdsfactory due to
    `snapping issue <https://github.com/gdsfactory/gdsfactory/pull/3816>`_.

    Modifications from gdsfactory/phidl:
        - Centers apex of hairpin at (0, 0)
        - If ``length`` is too short to fit all the points in the hairpin,
            the device length is increased to the minimum required length to fit
            the points.

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
    # if length is too short, artificially extend it
    xmin = min(max(xpts) - length, min(xpts))
    # snap point to twice grid spacing so that there's no gap
    # between hairpin and port
    xmin = round(xmin / (2 * gf.kcl.dbu)) * (2 * gf.kcl.dbu)
    xpts.append(xmin)
    ypts.append(-a)
    xpts.append(xpts[-1])
    ypts.append(-a + width)
    xpts.append(xpts[0])
    ypts.append(ypts[0])

    xpts_np = np.array(xpts)
    ypts_np = np.array(ypts)

    # ==========================================================================
    #  Create a blank device, add the geometry, and define the ports
    # ==========================================================================
    c = gf.Component()
    c.add_polygon(list(zip(xpts_np, +ypts_np)), layer=layer)
    c.add_polygon(list(zip(xpts_np, -ypts_np)), layer=layer)
    port_type = "electrical"

    xports = float(np.min(xpts_np))
    yports = -a + width / 2
    c.add_port(
        name="e1",
        center=(xports, -yports),
        width=width,
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    c.add_port(
        name="e2",
        center=(xports, yports),
        width=width,
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    c.move(apex, (0, 0))
    return c


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
def optimal_90deg(
    width: float = 100,
    num_pts: int = 15,
    length_adjust: float = 1,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Returns optimally-rounded 90 degree bend that is sharp on the outer corner.

    Wrapper for gdsfactory to allow port_type to be defined

    Args:
        width (float): Width of the ports on either side of the bend.
        num_pts (int): The number of points comprising the curved section of the bend.
        length_adjust (float): Adjusts the length of the non-curved portion of the bend.
        layer (LayerSpec): Specific layer(s) to put polygon geometry on.

    Notes:
        Optimal structure from https://doi.org/10.1103/PhysRevB.84.174510
        Clem, J., & Berggren, K. (2011). Geometry-dependent critical currents in
        superconducting nanocircuits. Physical Review B, 84(17), 1-27.
    """
    L = gf.Component()
    bend = L << gf.components.superconductors.optimal_90deg(
        width=width,
        num_pts=num_pts,
        length_adjust=length_adjust,
        layer=layer,
    )
    L.add_ports(bend.ports)
    for port in L.ports:
        port.port_type = port_type
    return L


@gf.cell
def compass(
    size: Size = (4.0, 2.0),
    layer: LayerSpec = (1, 0),
    port_type: str | None = "electrical",
    port_inclusion: float = 0.0,
    port_orientations: Ints | None = (180, 90, 0, -90),
    auto_rename_ports: bool = True,
) -> gf.Component:
    """Rectangle with ports on each edge (north, south, east, and west).

    Copied from gdsfactory to deal with snapping issue for dbu less than 1nm.
    See `this PR <https://github.com/gdsfactory/gdsfactory/pull/3816V>`_.

    Args:
        size: rectangle size.
        layer: tuple (int, int).
        port_type: optical, electrical.
        port_inclusion: from edge.
        port_orientations: list of port_orientations to add. None does not add ports.
        auto_rename_ports: auto rename ports.
    """
    c = gf.Component()
    dx, dy = size
    port_orientations = port_orientations or []

    c << rectangle(size=size, layer=layer)

    if port_type:
        for port_orientation in port_orientations:
            if port_orientation not in valid_port_orientations:
                raise ValueError(
                    f"{port_orientation=} must be in {valid_port_orientations}"
                )

        if 180 in port_orientations:
            c.add_port(
                name="e1",
                center=(-dx / 2 + port_inclusion, 0),
                width=dy,
                orientation=180,
                layer=layer,
                port_type=port_type,
            )
        if 90 in port_orientations:
            c.add_port(
                name="e2",
                center=(0, dy / 2 - port_inclusion),
                width=dx,
                orientation=90,
                layer=layer,
                port_type=port_type,
            )
        if 0 in port_orientations:
            c.add_port(
                name="e3",
                center=(dx / 2 - port_inclusion, 0),
                width=dy,
                orientation=0,
                layer=layer,
                port_type=port_type,
            )
        if -90 in port_orientations or 270 in port_orientations:
            c.add_port(
                name="e4",
                center=(0, -dy / 2 + port_inclusion),
                width=dx,
                orientation=-90,
                layer=layer,
                port_type=port_type,
            )

        if auto_rename_ports:
            c.auto_rename_ports()
    return c


@gf.cell
def rectangle(
    size: Size = (4.0, 2.0),
    layer: LayerSpec = (1, 0),
) -> gf.Component:
    """Rectangle with no ports

    Args:
        size: rectangle size.
        layer: tuple (int, int).
    """
    c = gf.Component()
    dx, dy = size

    if dx <= 0 or dy <= 0:
        raise ValueError(f"dx={dx} and dy={dy} must be > 0")

    points = [
        (-dx / 2.0, -dy / 2.0),
        (-dx / 2.0, dy / 2),
        (dx / 2, dy / 2),
        (dx / 2, -dy / 2.0),
    ]

    c.add_polygon(points, layer=layer)

    return c


@gf.cell
def cross(
    length: float = 10.0,
    width: float = 3.0,
    layer: LayerSpec = (1, 0),
) -> gf.Component:
    """Returns a cross from two rectangles of length and width.

    Args:
        length: float Length of the cross from one end to the other.
        width: float Width of the arms of the cross.
        layer: layer for geometry.
    """
    layer = gf.get_layer(layer)
    c = gf.Component()
    R = rectangle(size=(width, length), layer=layer)
    r1 = c.add_ref(R).rotate(90)
    r2 = c.add_ref(R)
    r1.center = (0, 0)
    r2.center = (0, 0)
    c.flatten()
    return c


@gf.cell
def fine_to_coarse(
    width1: float = 2.0,
    width2: float = 5.0,
    layer1: LayerSpec = "PHOTO1",
    layer2: LayerSpec = "PHOTO2",
    port_type: str = "electrical",
) -> gf.Component:
    """Create transition between fine and coarse layers

    Automatically performs outlining for positive-tone resist
    Args:
        width1 (float): starting width on first layer
        width2 (float): ending width on second layer
        layer1 (LayerSpec): layer specification (string or tuple) for first layer
        layer2 (LayerSpec): layer specification (string or tuple) for second layer
        port_type (str): "electrical" or "optical"

    Returns:
        gf.Component: transition between fine and coarse layers
    """
    taper = gf.Component()
    outline_layers = qg.utilities.get_outline_layers(gf.get_active_pdk().layers)
    pos_tone = False
    for layer in outline_layers.keys():
        if (gf.get_layer(layer) == gf.get_layer(layer1)) or (
            gf.get_layer(layer) == gf.get_layer(layer2)
        ):
            pos_tone = True
            break
    if pos_tone:
        # positive tone
        t2 = gf.components.straight(
            length=outline_layers[str(gf.get_layer(layer2))],
            npoints=2,
            cross_section=qg.utilities.get_cross_section_with_layer(layer2),
            width=None,
        )
        wide = outline_layers[str(gf.get_layer(layer2))] * 2 + width2
        if wide < width1:
            wide = width2
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
            t1_i.ports["e1"],
            t2_i.ports["e2"],
            allow_width_mismatch=True,
            allow_layer_mismatch=True,
        )
        t1_i.movex(-outline_layers[str(gf.get_layer(layer2))] / 2)
        ports = [t1_i.ports["e2"], t2_i.ports["e1"]]
    else:
        t2 = gf.components.superconductors.optimal_step(
            start_width=0.7 * width1,
            end_width=width2,
            num_pts=500,
            anticrowding_factor=0.6,
            symmetric=True,
            layer=layer2,
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
            t1_i.ports["e1"],
            t2_i.ports["e1"],
            allow_width_mismatch=True,
            allow_layer_mismatch=True,
        )
        t1_i.movex(0.8 * t1_i.xsize)
        ports = [t1_i.ports["e2"], t2_i.ports["e2"]]

    for n, port in enumerate(ports):
        taper.add_port(
            name=f"e{n + 1}",
            center=port.center,
            orientation=port.orientation,
            width=port.width,
            layer=layer1 if n == 0 else layer2,
            port_type=port_type,
        )
    return taper
