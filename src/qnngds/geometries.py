"""Geometries contains useful shapes/tools that are not available in phidl's
geometry library."""

import gdsfactory as gf
import numpy as np


from gdsfactory.typings import LayerSpec
from typing import Union


@gf.cell
def taper(
    length: Union[int, float] = 10,
    width1: Union[int, float] = 5,
    width2: Union[int, float] = 2,
    layer: LayerSpec = (1, 0),
    port_type: str = "electrical",
) -> gf.Component:
    """Linear taper (solid).

    Args:
        length (int or float): Length of taper
        width1 (int or float): Width of first end of taper
        width2 (int or float): Width of second end of taper
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: a single taper
    """
    T = gf.Component()
    pts = [
        (0, -width1 / 2),
        (length, -width2 / 2),
        (length, width2 / 2),
        (0, width1 / 2),
    ]
    T.add_polygon(pts, layer=layer)
    T.add_port(
        name="e1" if port_type == "electrical" else "o1",
        center=[0, 0],
        width=width1,
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    T.add_port(
        name="e2" if port_type == "electrical" else "o2",
        center=[length, 0],
        width=width2,
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

    Args:
        length (int or float): Length of taper
        wide_section (int or float): Width of wide end of taper
        narrow_section (int or float): Width of narrow end of taper
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
        gf.Component: a single taper
    """
    HT = gf.Component()

    taper_length = length
    wide = wide_section
    narrow = narrow_section
    swap = False
    if wide < narrow:
        wide, narrow = narrow, wide
        swap = True
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
        name="e2" if swap else "e1",
        center=[0, 0],
        width=narrow,
        orientation=180,
        layer=layer,
        port_type=port_type,
    )
    HT.add_port(
        name="e1" if swap else "e2",
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

    Args:
        wire_width (int or float): Width of wide end of taper
        constr_width (int or float): Width of narrow end of taper
        angle (int or float): Angle between taper ends in degrees
        layer (LayerSpec): GDS layer tuple (layer, type)
        port_type (string): gdsfactory port type. default "electrical"

    Returns:
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
def flagpole(
    size: tuple[float, float] = (4, 2),
    stub_size: tuple[float, float] = (2, 1),
    shape: str = "p",
    taper_type: str | None = "straight",
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
        taper_amount = min([abs(f[0] - p[0]), abs(p[1])]) / gf.kcl.dbu
        for poly in D.get_polygons()[gf.get_layer(layer)]:
            D.add_polygon(poly.round_corners(taper_amount, 0, 300), layer=layer)
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
