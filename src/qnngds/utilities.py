"""Utilies is used for building cells in design.

Cells are made of devices
(found in utilities) and a die_cell border, wich contains pads, text etc... The
device and its die are linked thanks to functions present in this module.
"""

import gdsfactory as gf
import kfactory as kf
from typing import Literal
from collections.abc import Callable, Sequence

from functools import partial

import numpy as np

from numpy.typing import ArrayLike

from gdsfactory.typings import (
    ComponentSpecOrComponent,
    ComponentSpecsOrComponents,
    CrossSectionSpec,
    Port,
    Ports,
    PortsDict,
    Spacing,
)


@gf.cell
def union(component: gf.Component) -> gf.Component:
    """Merge all polygons within a Component by layer

    Args:
        component (gf.Component): component to merge

    Returns:
        gf.Component: the merged component
    """
    comp_union = gf.Component()
    for layer in component.layers:
        temp = gf.Component()
        temp.add_polygon(component.get_region(layer), layer=layer)
        comp_union << gf.boolean(temp, temp, operation="or", layer=layer)
    return comp_union


def get_outline_layers(layer_map: gf.LayerEnum) -> dict[tuple, float]:
    """Get dictionary maping a layer tuple to the desired outline amount as specified by the LayerMap

    Args:
        layer_map (gf.LayerEnum): enum layer equipped with outline method

    Returns:
        dict[tuple, float]: mapping of GDS tuple to outline distance. Layers that aren't outlined are omitted.
    """
    # outline
    outline_layers = {}
    for layer in layer_map:
        ol = layer_map.outline(layer)
        if ol > 0:
            outline_layers[str(gf.get_layer(layer))] = ol
    return outline_layers


@gf.cell
def outline(
    component: gf.Component,
    outline_layers: dict[str, float] | None = None,
) -> gf.Component:
    """Outline polygons within component by layer.

    Args:
        component (gf.Component): component to outline
        outline_layers (dict[tuple, float]): map of desired outline amount per layer. If a layer is omitted, it will not be outlined

    Returns:
        gf.Component: the outlined component
    """
    comp_outlined = gf.Component()
    # extend ports
    comp_extended = gf.Component()
    comp = comp_extended.add_ref(component)
    if outline_layers is None:
        outline_layers = {}
    for k, v in outline_layers.items():
        if v <= 0:
            raise ValueError(f"outline must be greater than zero, got {outline_layers}")
    new_ports = []
    processed_ports = []
    for layer in outline_layers.keys():
        for port in gf.port.select_ports(comp, gf.get_layer(layer)):
            ext = comp_extended.add_ref(
                gf.components.compass(
                    size=(outline_layers[layer], port.width),
                    layer=port.layer,
                    port_type=port.port_type,
                )
            )
            prefix = "o" if port.port_type == "optical" else "e"
            ext.connect(port=ext.ports[f"{prefix}1"], other=port)
            p = ext.ports[f"{prefix}3"]
            p.name = port.name
            new_ports.append(p)
            processed_ports.append(port)

    new_ports += [p for p in comp.ports if p not in processed_ports]
    outline_layer_values = {
        gf.get_layer(k).value: str(gf.get_layer(k)) for k in outline_layers.keys()
    }
    for layer in comp_extended.layers:
        r = component.get_region(layer=layer)
        if gf.get_layer(layer) not in outline_layer_values:
            comp_outlined.add_polygon(r, layer=layer)
        else:
            layer = outline_layer_values[gf.get_layer(layer)]
            outline_dbu = outline_layers[layer] / gf.kcl.dbu
            r_expanded = r.sized(outline_dbu)
            comp_outlined.add_polygon(
                r_expanded - comp_extended.get_region(layer=layer), layer=layer
            )
    # add ports
    comp_outlined.add_ports(new_ports)
    return comp_outlined


@gf.cell
def invert(
    component: gf.Component,
    ext_bbox_layers: dict[tuple, float] = {},
) -> gf.Component:
    """Outline polygons within component by layer.

    Args:
        component (gf.Component): component to invert
        ext_bbox_layers (dict[tuple, float]): amount to expand bounding box for each layer. If a layer is omitted, it will not be inverted.

    Returns:
        gf.Component: the inverted component
    """
    comp_inverted = gf.Component()
    for layer in component.layers:
        r = component.get_region(layer=layer)
        if layer not in ext_bbox_layers.keys():
            comp_inverted.add_polygon(r, layer=layer)
        else:
            ext = ext_bbox_layers[layer]
            r_expanded = gf.components.shapes.bbox(
                component, top=ext, bottom=ext, left=ext, right=ext, layer=layer
            ).get_region(layer=layer)
            comp_inverted.add_polygon(r_expanded - r, layer=layer)
    return comp_inverted


@gf.cell
def flex_grid(
    components: ComponentSpecsOrComponents,
    spacing: Spacing | float = (5.0, 5.0),
    shape: tuple[int, int] | None = None,
    align_x: Literal["origin", "xmin", "xmax", "center"] = "center",
    align_y: Literal["origin", "ymin", "ymax", "center"] = "center",
    rotation: int = 0,
    mirror: bool = False,
) -> gf.Component:
    """Implement gdsfactory grid using kfactory's flex_grid method"""
    c = gf.Component()
    instances = kf.flexgrid(
        c,
        kcells=[gf.get_component(component) for component in components],
        shape=shape,
        spacing=(
            (float(spacing[0]), float(spacing[1]))
            if isinstance(spacing, tuple | list)
            else float(spacing)
        ),
        align_x=align_x,
        align_y=align_y,
        rotation=rotation,
        mirror=mirror,
    )
    for i, instance in enumerate(instances):
        c.add_ports(instance.ports, prefix=f"{i}_")
    return c


#########################
# Experiment generation
#########################


class RouteGroup:
    """Stores information for routing DUTs to pads.

    Stores a cross section and mapping of DUT ports to optional pad
    ports. If a DUT port is mapped to None, then a pad port
    will be automatically assigned in :py:func:`generate_experiment`
    """

    def __init__(self, cross_section: CrossSectionSpec, port_mapping: dict | tuple):
        """Initialize route group

        Args:
            cross_section (CrossSectionSpec): factory method for desired cross section used for routing
            port_mapping (dict | tuple): either dictionary manually specifying mapping of DUT port names to pad port names
                or a tuple of DUT port names that should be mapped automatically to pad ports.
        Returns:
            None
        """
        self.cross_section = cross_section
        if isinstance(port_mapping, dict):
            self.port_mapping = port_mapping
        else:
            self.port_mapping = {p: None for p in port_mapping}


def _get_segment_from_path(path: gf.Path, p: int) -> ArrayLike:
    """Gets the segment starting from the p'th point in path.

    Helper method for :py:func:`generate_experiment`.

    Args:
        path (gf.Path): path to get segment from
        p (int): index of the first point in the line segment

    Returns:
        ArrayLike: line segment defined by two points
    """
    points = path.points
    return (
        np.array([points[p % len(points)], points[(p + 1) % len(points)]]) / gf.kcl.dbu
    ).astype(int)


def _segments_overlap(segment_1: ArrayLike, segment_2: ArrayLike) -> bool:
    """Determines if two line segments on a manhattan grid overlap.

    Helper method for :py:func:`generate_experiment`.

    Args:
        segment_1 (ArrayLike): first segment
        segment_2 (ArrayLike): second segment

    Returns:
        bool: True if the segments overlap, False otherwise.
    """
    for i in range(2):
        x_1_min = np.min(segment_1[:, i])
        x_1_max = np.max(segment_1[:, i])
        x_2_min = np.min(segment_2[:, i])
        x_2_max = np.max(segment_2[:, i])
        if x_1_min > x_2_max or x_2_min > x_1_max:
            return False
    return True


def _path_self_intersects(path: gf.Path) -> bool:
    """Determines if a manhattan path has any self-intersections

    Helper method for :py:func:`generate_experiment`.

    Args:
        path (gf.Path): path to check

    Returns:
        bool: True if the path intersects itself, False otherwise.
    """
    # points are on manhattan grid so checking intersection is pretty easy
    for p in range(len(path.points) - 1):
        segment_1 = _get_segment_from_path(path, p)
        for q in range(p + 2, len(path.points) - 1):
            segment_2 = _get_segment_from_path(path, q)
            # check that segment_1 and segment_2's x and y projections don't overlap
            if _segments_overlap(segment_1, segment_2):
                return True
    return False


def _paths_intersect(path_1: gf.Path, path_2: gf.Path) -> bool:
    """Determines if two manhattan paths intersect

    Helper method for :py:func:`generate_experiment`.

    Args:
        path_1 (gf.Path): first path to check
        path_2 (gf.Path): second path to check

    Returns:
        bool: True if the paths intersect, False otherwise.
    """
    for p in range(len(path_1.points) - 1):
        segment_1 = _get_segment_from_path(path_1, p)
        for q in range(len(path_2.points) - 1):
            segment_2 = _get_segment_from_path(path_2, q)
            if _segments_overlap(segment_1, segment_2):
                return True
    return False


def _get_port_direction(port: Port) -> str:
    """Gets string port direction ("N", "S", "E" or "W") of a port

    Args:
        port (gf.Port): port

    Returns:
        str: string of port orientation
    """
    angle = port.orientation % 360
    if angle <= 45 or angle >= 315:
        return "E"
    elif angle <= 135 and angle >= 45:
        return "N"
    elif angle <= 225 and angle >= 135:
        return "W"
    else:
        return "S"


def _get_component_port_direction(component: gf.Component) -> PortsDict:
    """Returns ports of a component organized by direction.

    Helper method for :py:func:`generate_experiment`.

    Args:
        component (gf.Component): component to get ports from

    Returns:
        dict[str, Ports]: list of ports for each direction
    """
    ports = {x: [] for x in ["E", "N", "W", "S"]}
    # group by direction
    for p in component.ports:
        ports[_get_port_direction(p)].append(p)
    return ports


def _sort_ports(
    ports: PortsDict, sort_map: dict[str, Callable], direction_order: Sequence[str]
) -> Ports:
    """Sorts collections of ports all facing the same direction.

    Helper method for :py:func:`generate_experiment`.

    Args:
        ports (gf.PortsDict): dictionary of ports.
        sort_map dict[str, Callable]: dictionary mapping a direction to a sort key that takes the port as an input.
        direction_order Sequence[str]: order of keys in port dictionary to use when flattening.

    Returns:
        Ports: list of sorted ports
    """
    # sort
    for direction in sort_map.keys():
        ports[direction].sort(key=sort_map[direction])
    flat_ports = []
    for direction in direction_order:
        flat_ports += ports[direction]
    return flat_ports


@gf.cell
def generate_experiment(
    dut: ComponentSpecOrComponent,
    pad_array: ComponentSpecOrComponent,
    label: ComponentSpecOrComponent | None,
    route_groups: Sequence[RouteGroup] | None,
    dut_offset: tuple[float, float] = (0, 0),
    pad_offset: tuple[float, float] = (0, 0),
    label_offset: tuple[float, float] | None = (-100, -100),
    ignore_port_count_mismatch: bool = False,
    retries: int = 10,
) -> gf.Component:
    """Construct an experiment from a device/circuit (gf.Component).

    Includes text, pads, and routing to connect pads to devices

    Parameters:
        dut (ComponentSpec or Component): finished device to be connected to pads
        pad_array (ComponentSpec or Component or None): pad array to connect to device
        label (ComponentSpecOrComponent or None): text label or factory.
        route_groups (Sequence[RouteGroup] or None): how to route DUT to pads
        dut_offset (tuple[float, float]): x,y offset for dut (mostly useful for linear pad arrays)
        pad_offset (tuple[float, float]): x,y offset for pad array (mostly useful for linear pad arrays)
        label_offset (tuple[float, float] or None): x,y offset of label
        ignore_port_count_mismatch (bool): if True, ignores mismatched number of DUT and pads ports, only if route_groups defines a mapping to all pad ports
        retries (int): how many times to try rerouting with s_bend (may need to be larger for many port groupings)
    Returns:
        (gf.Component): experiment

    Example:
        Using the example qnngds PDK: `<https://github.com/qnngroup/qnngds-pdk/>`_,
        we can generate an example nTron test layout including pads. The pad array
        is just a linear array from gdsfactory, although a custom array could be defined.
        The mapping of nTron device ports to pad ports is defined manually with ``route_groups``,
        but it's possible to use autoassignment if the ports are facing the same direction
        (e.g. ``pads_tri`` in ``qnngds-pdk``)

        >>> c = qg.utilities.generate_experiment(
        >>>         dut=qg.devices.ntron.sharp,
        >>>         pad_array=gf.components.pads.pad_array(
        >>>             pad=gf.components.pads.pad,
        >>>             columns=1,
        >>>             rows=3,
        >>>             column_pitch=1,
        >>>             row_pitch=250,
        >>>             port_orientation=0,
        >>>             size=(200,200),
        >>>             layer="EBEAM_COARSE"
        >>>         ),
        >>>         label=None,
        >>>         route_groups=(
        >>>             qg.utilities.RouteGroup(
        >>>                 PDK.get_cross_section("ebeam"), {"g": "e21", "s": "e11", "d": "e31"}
        >>>             ),
        >>>         ),
        >>>         dut_offset=(250, 250),
        >>>         pad_offset=(0, 0),
        >>>         label_offset=(0, 0),
        >>>         retries=1,
        >>>     )
        >>> c.show()

        Or, perhaps we want to create an hTron (now using a custom pad array ``pad_quad``
        defined in `<https://github.com/qnngroup/qnngds-pdk/>`_:

        >>> from pdk.components import pad_quad
        >>> c = qg.utilities.generate_experiment(
        >>>         dut=qg.devices.htron.multilayer(
        >>>             gate_spec=qg.devices.htron.heater(
        >>>                 pad_outline=0,
        >>>                 pad_layer="PHOTO",
        >>>                 heater_layer="PHOTO",
        >>>             ),
        >>>         ),
        >>>         pad_array=pad_quad(space=200),
        >>>         label=None,
        >>>         route_groups=(
        >>>             # route ebeam channel layer: c1 and c2 to pads e1 and e3
        >>>             qg.utilities.RouteGroup(
        >>>                 PDK.get_cross_section("ebeam"), {"c1": "e1", "c2": "e3"}
        >>>             ),
        >>>             # route photolitho heater layer: g2 and g5 to pads e4 and e2
        >>>             # note that DUT ports g1,g3,g4,g6 are not mapped
        >>>             # however, all pad ports (e1-e4) are mapped
        >>>             qg.utilities.RouteGroup(
        >>>                 PDK.get_cross_section("photo"), {"g2": "e4", "g5": "e2"}
        >>>             ),
        >>>         ),
        >>>         dut_offset=(0, 0),
        >>>         pad_offset=(0, 0),
        >>>         label_offset=(50, 240),
        >>>         ignore_port_count_mismatch=True,
        >>>         retries=1,
        >>>     )
        >>> c.show()

        Here, the hTron devices has 8 ports, but the pads only have 4, so we have to assign
        every pad a port on the DUT and pass the ``ignore_port_count_mismatch`` flag.
    """
    # check if route_groups is complete so we can handle ignore_port_count_mismatch flag
    route_groups_complete = False
    if route_groups is not None and pad_array is not None:
        route_groups_complete = True
        # first figure out all of the assigned pad ports
        mapped_pad_ports = set([])
        for route_group in route_groups:
            for _, pad_port in route_group.port_mapping.items():
                mapped_pad_ports.add(pad_port)
        # next, for each port in the pad_array, check that its
        # name appears in a route_group
        pads_i = gf.get_component(pad_array)
        for port in pads_i.ports:
            if port.name not in mapped_pad_ports:
                route_groups_complete = False
                break

    allow_port_count_mismatch = route_groups_complete and ignore_port_count_mismatch

    dut_i = gf.get_component(dut)
    if pad_array is not None:
        pads_i = gf.get_component(pad_array)
        # check appropriate number of ports on pad_array and dut
        if len(dut_i.ports) != len(pads_i.ports):
            if not (allow_port_count_mismatch):
                raise ValueError(
                    f"DUT ({len(dut_i.ports)} ports) and pad array ({len(pads_i.ports)} ports) should have the same number of ports."
                )
    # check that number of DUT ports assigned in route_groups is correct
    if len(dut_i.ports) != 0 and route_groups is not None:
        num_assigned_ports = sum(
            len(group.port_mapping.keys()) for group in route_groups
        )
        if num_assigned_ports != len(dut_i.ports):
            if not (allow_port_count_mismatch):
                raise ValueError(
                    f"invalid number of port groupings: got {num_assigned_ports}, expected {len(dut_i.ports)} based on number of ports on DUT"
                )
    elif route_groups is not None:
        if pad_array is not None:
            raise ValueError(
                "cannot route pad array to DUT with zero ports, did you remember to add ports to your DUT?"
            )

    experiment = gf.Component()

    # figure out which layers to outline
    outline_layers = get_outline_layers(gf.get_active_pdk().layers)

    # outline and add DUT
    dut_ref = experiment.add_ref(outline(dut_i, outline_layers))
    dut_ref.move(dut_offset)
    if pad_array is None:
        return experiment

    # add pads
    # don't outline, and add to dummy component.
    # after pad port adjustment, perform the outline
    dummy_pads = gf.Component()
    pads_ref = dummy_pads.add_ref(pads_i)
    pads_ref.move(pad_offset)

    # add text label (don't outline)
    if label is not None:
        label_i = label() if isinstance(label, Callable) else label
        label_ref = experiment.add_ref(label_i)
        label_ref.move(label_offset)

    sort_cw = {
        "E": lambda p: -p.y,  # north to south
        "N": lambda p: +p.x,  # west to east
        "W": lambda p: +p.y,  # south to north
        "S": lambda p: -p.x,  # east to west
    }
    sort_ccw = {
        "E": lambda p: +p.y,  # south to north
        "N": lambda p: -p.x,  # east to west
        "W": lambda p: -p.y,  # north to south
        "S": lambda p: +p.x,  # west to east
    }

    # sort dut cw
    dut_ports = _sort_ports(
        _get_component_port_direction(dut_ref), sort_cw, ("W", "N", "E", "S")
    )
    # sort pads ccw
    pad_ports = _sort_ports(
        _get_component_port_direction(pads_ref), sort_ccw, ("E", "S", "W", "N")
    )

    # create mapping from dut ports to pad ports
    # first define route groups if it isn't initialized
    dut_pad_map = {}
    if route_groups is None:
        try:
            cross_section = gf.get_active_pdk().get_cross_section("default")
        except ValueError as e:
            error_msg = "'default' cross section required if route_groups is None."
            error_msg += "Please either specify the desired cross section by defining"
            error_msg += (
                "route_groups, or define a 'default' cross section in the current Pdk"
            )
            raise ValueError(error_msg) from e
        route_groups = (
            RouteGroup(
                cross_section=cross_section,
                port_mapping=tuple(p.name for p in dut_ports),
            ),
        )
    else:
        # reserve routes for any that are defined in route_groups
        for group in route_groups:
            for dut_port_name, pad_port_name in group.port_mapping.items():
                if pad_port_name is not None:
                    try:
                        pad_port_index = next(
                            i
                            for i in range(len(pad_ports))
                            if pad_ports[i].name == pad_port_name
                        )
                    except StopIteration as e:
                        error_msg = (
                            f"Port {pad_port_name} not found in pad ports {pad_ports}"
                        )
                        raise ValueError(error_msg) from e
                    try:
                        dut_port_index = next(
                            i
                            for i in range(len(dut_ports))
                            if dut_ports[i].name == dut_port_name
                        )
                        dut_pad_map[dut_port_name] = pad_ports[pad_port_index]
                    except StopIteration as e:
                        error_msg = (
                            f"Port {dut_port_name} not found in DUT ports {dut_ports}"
                        )
                        raise ValueError(error_msg) from e
                    pad_ports.pop(pad_port_index)
                    dut_ports.pop(dut_port_index)
    # add remaining ports
    dut_pad_map |= {dp.name: pp for (dp, pp) in zip(dut_ports, pad_ports)}

    # shift pad ports if it's possible to do a straight route between dut and pad without exceeding pad extent
    for gid, route_group in enumerate(route_groups):
        for dut_port_name in route_group.port_mapping:
            dut_port = dut_ref.ports[dut_port_name]
            pad_port = dut_pad_map[dut_port_name]
            if (dut_port.orientation - pad_port.orientation) % 360 == 180:
                # ports are facing each other
                w_route = route_group.cross_section.width
                w_pad = pad_port.width
                dw = w_pad - w_route
                dwidth = 0
                center = (pad_port.x, pad_port.y)
                if dut_port.orientation % 180 == 0:
                    # route along x
                    if pad_port.y - dw / 2 <= dut_port.y <= pad_port.y + dw / 2:
                        # change port location on pad
                        dwidth = -2 * abs(dut_port.y - pad_port.y)
                        center = (pad_port.x, dut_port.y)
                else:
                    # route along y
                    if pad_port.x - dw / 2 <= dut_port.x <= pad_port.x + dw / 2:
                        dwidth = -2 * abs(dut_port.x - pad_port.x)
                        center = (dut_port.x, pad_port.y)
                pad_port = Port(
                    name=pad_port.name,
                    width=pad_port.width + dwidth,
                    center=center,
                    orientation=pad_port.orientation,
                    layer=pad_port.layer,
                    port_type=pad_port.port_type,
                )
                dummy_pads.add_port(port=pad_port)
                dut_pad_map[dut_port_name] = pad_port
            else:
                dummy_pads.add_port(port=pad_port)

    # add pads to actual device
    experiment.add_ref(outline(dummy_pads, outline_layers))

    # actually do routing
    problem_groups = set([])
    for _ in range(retries + 1):
        routed = gf.Component()
        routed.add_ref(experiment)
        # for each grouping, try route_bundle, if that fails use route_bundle_sbend
        complete = True
        for gid, route_group in enumerate(route_groups):
            all_paths = []
            # get list of pad ports
            dut_group = [dut_ref.ports[p] for p in route_group.port_mapping]
            pad_group = [dut_pad_map[p] for p in route_group.port_mapping]
            if gid not in problem_groups:
                try:
                    # loop over each orientation
                    ports = {x: [[], []] for x in ["N", "E", "S", "W"]}
                    for d, p in zip(dut_group, pad_group):
                        direction = _get_port_direction(d)
                        ports[direction][0].append(d)
                        ports[direction][1].append(p)
                    for _, portmap in ports.items():
                        if len(portmap[0]) == 0:
                            continue
                        routes = gf.routing.route_bundle(
                            component=routed,
                            ports1=portmap[0],
                            ports2=portmap[1],
                            cross_section=route_group.cross_section,
                            taper=None,
                            auto_taper=True,
                            on_collision="error",
                            router="optical",
                        )
                        # check for self-intersecting paths
                        for r, route in enumerate(routes):
                            # route.backbone doesn't include tapers, so add the original ports to either end of
                            # route.backbone and then check for intersection.
                            # this assumes that all auto_tapers are straight (e.g. no 90 deg bends)
                            points = [portmap[0][r].center]
                            points += [
                                [point.x * gf.kcl.dbu, point.y * gf.kcl.dbu]
                                for point in route.backbone
                            ]
                            points += [portmap[1][r].center]
                            path = gf.Path(points)
                            if _path_self_intersects(path):
                                error_msg = "After including auto_tapers, routed paths are self-intersecting."
                                error_msg += " Try increasing the spacing between the pads and DUT or using s_bend routing."
                                print(f"WARNING: {error_msg}")
                                raise RuntimeError(error_msg)
                            # add route to route list for checking intersections later
                            all_paths.append(path)

                except RuntimeError:
                    problem_groups.add(gid)
                    complete = False
                    break
                except kf.routing.generic.PlacerError as e:
                    error_msg = "Routing failed, try manually specifying port mapping between DUT"
                    error_msg += " and pads with route_groups."
                    raise RuntimeError(error_msg) from e
            else:
                # add autotapers and regenerate port groups
                dut_group_new = gf.routing.auto_taper.add_auto_tapers(
                    routed, dut_group, route_group.cross_section
                )
                pad_group_new = gf.routing.auto_taper.add_auto_tapers(
                    routed, pad_group, route_group.cross_section
                )
                try:
                    gf.routing.route_bundle_sbend(
                        component=routed,
                        ports1=pad_group_new,
                        ports2=dut_group_new,
                        enforce_port_ordering=True,
                        bend_s=partial(
                            gf.components.bends.bend_s,
                            cross_section=route_group.cross_section,
                        ),
                    )
                except ValueError as e:
                    if "radius" in str(e):
                        error_msg = (
                            str(e)
                            + "\nTry increasing spacing between DUT and pads or adjust DUT placement relative to pads."
                        )
                        raise ValueError(error_msg) from e
                    else:
                        raise
            # check for intersections between paths that were routed separately
            for m in range(len(all_paths) - 1):
                for n in range(m + 1, len(all_paths)):
                    # check that all_paths[p] and all_paths[q] do not intersect
                    if _paths_intersect(all_paths[m], all_paths[n]):
                        error_msg = "Could not route without intersections."
                        error_msg += " Try manually specifying port mapping between DUT and pads with route_groups."
                        error_msg += (
                            " Also try increasing the spacing between DUT and pads."
                        )
                        print(error_msg)
                        # raise RuntimeError(error_msg)
        if complete:
            return routed
    raise RuntimeError(f"failed to route design after {retries} iterations")
