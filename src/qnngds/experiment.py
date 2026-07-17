"""Utilities for generating experiments from devices or circuits, automatically routing
between device/circuit and pads and performing outlining and boolean
keepout operations based on PDK requirements."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

from collections.abc import Callable, Sequence

from functools import partial

import numpy as np

from numpy.typing import ArrayLike
from qnngds.typing import DeviceSpec, CrossSectionSpec
from qnngds import Device, Port

import qnngds as qg

from phidl import Path, CrossSection

import phidl.path as pp
import phidl.routing as pr


class RouteGroup:
    """Stores information for routing DUTs to pads.

    Stores a cross section and mapping of DUT ports to optional pad
    ports. If a DUT port is mapped to None, then a pad port
    will be automatically assigned in :py:func:`generate`
    """

    def __init__(
        self,
        cross_section: CrossSectionSpec,
        port_mapping: dict | tuple,
        ground: bool = False,
        ignore_dut_bbox: bool = False,
    ):
        """Initialize route group

        Args:
            cross_section (CrossSectionSpec): factory method for desired cross section used for routing
            port_mapping (dict | tuple): either dictionary manually specifying mapping of DUT port names
                to pad port names or a tuple of DUT port names that should be mapped automatically to
                pad ports.
            ignore_dut_bbox (bool): if False, then routes DUT ports to edge of bounding box before attempting
                to route to pad ports.
            ground (bool): If True, then all dut ports will not be connected to a pad port. This allows
                connection to ground plane for positive-tone layouts.
        Returns:
            None
        """
        self.cross_section = cross_section
        self.ground = ground
        self.ignore_dut_bbox = ignore_dut_bbox
        if isinstance(port_mapping, dict):
            self.port_mapping = port_mapping
            if ground:
                raise ValueError(
                    f"{ground=}, but a dictionary port mapping was specified. "
                    "Please set ground=True or list the dut ports you wish to "
                    "ground in a tuple."
                )
        elif isinstance(port_mapping, tuple):
            self.port_mapping = {p: None for p in port_mapping}
        else:
            raise TypeError(
                f"got port_mapping of type {type(port_mapping)}, expected "
                "dict or tuple."
            )


def _get_segment_from_path(path: Path, p: int) -> ArrayLike:
    """Gets the segment starting from the p'th point in path.

    Helper method for :py:func:`generate`.

    Args:
        path (Path): path to get segment from
        p (int): index of the first point in the line segment

    Returns:
        (ArrayLike): line segment defined by two points
    """
    points = path.points
    return np.array([points[p % len(points)], points[(p + 1) % len(points)]])


def _segments_overlap(segment_1: ArrayLike, segment_2: ArrayLike) -> bool:
    """Determines if two line segments on a manhattan grid overlap.

    Helper method for :py:func:`generate`.

    Args:
        segment_1 (ArrayLike): first segment
        segment_2 (ArrayLike): second segment

    Returns:
        (bool): True if the segments overlap, False otherwise.
    """
    for i in range(2):
        x_1_min = np.min(segment_1[:, i])
        x_1_max = np.max(segment_1[:, i])
        x_2_min = np.min(segment_2[:, i])
        x_2_max = np.max(segment_2[:, i])
        if x_1_min > x_2_max or x_2_min > x_1_max:
            return False
    return True


def _path_self_intersects(path: Path) -> bool:
    """Determines if a manhattan path has any self-intersections

    Helper method for :py:func:`generate`.

    Args:
        path (Path): path to check

    Returns:
        (bool): True if the path intersects itself, False otherwise.
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


def _paths_intersect(path_1: Path, path_2: Path) -> tuple[bool, tuple[Path, Path]]:
    """Determines if two manhattan paths intersect

    Helper method for :py:func:`generate`.

    Args:
        path_1 (Path): first path to check
        path_2 (Path): second path to check

    Returns:
        (tuple[bool, tuple[Path, Path] | None]): True if the paths intersect,
            False otherwise. Also returns which segments intersected if an
            intersection is found.
    """
    for p in range(len(path_1.points) - 1):
        segment_1 = _get_segment_from_path(path_1, p)
        for q in range(len(path_2.points) - 1):
            segment_2 = _get_segment_from_path(path_2, q)
            if _segments_overlap(segment_1, segment_2):
                return True, (segment_1, segment_2)
    return False, None


def _sort_ports(
    ports: dict[str, Sequence[Port]],
    sort_map: dict[str, Callable],
    direction_order: Sequence[str],
) -> Sequence[Port]:
    """Sorts collections of ports all facing the same direction.

    Helper method for :py:func:`generate`.

    Args:
        ports (dict[str, Sequence[Port]): dictionary of ports.
        sort_map dict[str, Callable]: dictionary mapping a direction to a sort key that takes the port as an input.
        direction_order Sequence[str]: order of keys in port dictionary to use when flattening.

    Returns:
        (Ports): list of sorted ports
    """
    # sort
    for direction in sort_map.keys():
        ports[direction].sort(key=sort_map[direction])
    flat_ports = []
    for direction in direction_order:
        flat_ports += ports[direction]
    return flat_ports


def _define_routes(
    dut_ref: Device,
    pads_ref: Device,
    route_groups: Sequence[RouteGroup] | None,
) -> tuple[Sequence[RouteGroup], dict[str, tuple[Port, Port]]]:
    """Automatically fills in missing entries in route_groups

    based on ports in dut_ref and pads_ref.

    Parameters
        dut_ref (DeviceReference): reference to DUT
        pads_ref (DeviceReference): reference to pads
        route_groups (Sequence[RouteGroup] | None): partially or fully defined RouteGroup
            list that specifies routing between DUT and pads

    Returns
        tuple[Sequence[RouteGroup], dict[str, tuple[Port, Port]]]: updated route_groups,
            and dut_pad_map which specifies which dut port goes to which pad port
    """
    # keys for sorting ports to auto-assign them
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
        ports=qg.utilities.get_device_port_direction(dut_ref),
        sort_map=sort_cw,
        direction_order=("W", "N", "E", "S"),
    )
    # sort pads ccw
    pad_ports = _sort_ports(
        ports=qg.utilities.get_device_port_direction(pads_ref),
        sort_map=sort_ccw,
        direction_order=("E", "S", "W", "N"),
    )
    # create mapping from dut ports to pad ports
    # first define route groups if it isn't initialized
    dut_pad_map = {}
    if route_groups is None:
        # add remaining ports
        dut_pad_map |= {dp.name: pp for (dp, pp) in zip(dut_ports, pad_ports)}
        # try to group in a reaonsable way:
        # all port pairs with the same start/end layer go in a group together
        # all remaining port pairs with the same end layer go in a group together
        port_maps = {}
        cross_sections = {}
        for dut_port_name, pad_port in dut_pad_map.items():
            dut_port = dut_ref.ports[dut_port_name]
            if dut_port.layer == pad_port.layer:
                pair = (dut_port.layer, pad_port.layer)
                if pair not in port_maps:
                    port_maps[pair] = {}
            else:
                pair = (None, pad_port.layer)
                if pair not in port_maps:
                    port_maps[pair] = {}
            port_maps[pair][dut_port_name] = pad_port.name
            # create a cross section for the layer
            xc = qg.utilities.get_cross_section_with_layer(pad_port.layer)
            if xc is None:
                raise Warning(
                    "Failed to automatically select a cross section for "
                    f"dut/pad pair {dut_port.name}/{pad_port.name}. "
                    f"Selecting cross section 'default'. This may cause "
                    "errors if the appropriate transitions aren't defined"
                )
            else:
                cross_sections[pair] = xc
        # create route_groups
        route_groups = []
        for pair, xc in cross_sections.items():
            route_groups.append(
                RouteGroup(cross_section=xc, port_mapping=port_maps[pair])
            )
        route_groups = tuple(route_groups)
    else:
        # reserve routes for any that are defined in route_groups
        for group in route_groups:
            for dut_port_name, pad_port_name in group.port_mapping.items():
                if (pad_port_name is None) and not (group.ground):
                    # auto mapped later
                    continue
                try:
                    dut_port_index = next(
                        i
                        for i in range(len(dut_ports))
                        if dut_ports[i].name == dut_port_name
                    )
                    if not group.ground:
                        # determine pad port to connect to
                        try:
                            pad_port_index = next(
                                i
                                for i in range(len(pad_ports))
                                if pad_ports[i].name == pad_port_name
                            )
                        except StopIteration as e:
                            raise ValueError(
                                f"Port {pad_port_name} not found in pad ports {pad_ports}"
                            ) from e
                        dut_pad_map[dut_port_name] = pad_ports[pad_port_index]
                        pad_ports.pop(pad_port_index)
                except StopIteration as e:
                    raise ValueError(
                        f"Port {dut_port_name} not found in DUT ports {dut_ports}"
                    ) from e
                dut_ports.pop(dut_port_index)
        # add remaining ports
        dut_pad_map |= {dp.name: pp for (dp, pp) in zip(dut_ports, pad_ports)}
    return route_groups, dut_pad_map


def _add_autotapers(
    device: Device,
    cross_section: CrossSection,
    layer_transitions: dict[tuple, DeviceSpec],
    ports: Sequence[Port],
) -> Sequence[Port]:
    """Helper method for :py:`_route_dut`

    Automatically adds tapers to DUT or ports to adapt to specified routing
    cross section for the current RouteGroup.

    device (Device): device to add autotapers to.
    cross_section (CrossSection): cross section to taper to.
    layer_transitions (dict[tuple, DeviceSpec]): allowed layer transitions for auto tapers
    ports (Sequence[Port]): DUT ports to autotaper

    Returns:
        new_ports (Sequence[Port]): updated ports for routing
    """
    new_ports = []
    for p, port in enumerate(ports):
        # loop over DUT ports
        port_layer = qg.get_layer(port.layer).tuple
        xc_layer = qg.get_layer(cross_section.sections[0]["layer"]).tuple
        key = port_layer
        if port_layer != xc_layer:
            key = (port_layer, xc_layer)
        taper = layer_transitions.get(key)
        widths = (port.width, cross_section.sections[0]["width"])
        if taper is None and isinstance(key, tuple):
            # in case the opposite transition is available,
            # just go the other direction
            taper = layer_transitions.get((key[1], key[0]))
            widths = (cross_section.sections[0]["width"], port.width)
        if taper is None:
            raise KeyError(
                f"could not find an appropriate auto taper "
                f"between port {port} and cross_section "
                f"{cross_section.sections}"
            )
        taper_i = qg.get_device(partial(taper, width1=widths[0], width2=widths[1]))
        # add taper to DUT and update ports
        t = device << taper_i
        if qg.get_layer(t.ports[1].layer).tuple == port_layer:
            t.connect(port=t.ports[1], destination=port)
            new_port = t.ports[2]
        else:
            t.connect(port=t.ports[2], destination=port)
            new_port = t.ports[1]
        new_ports.append(
            Port(
                width=new_port.width,
                midpoint=new_port.midpoint,
                orientation=new_port.orientation,
                layer=port_layer,
                name=port.name,
            )
        )
    return new_ports


def _extend_port_to_bbox(port: Port, bbox: tuple, space: float):
    """Helper method for :py:`_route_dut`

    Parameters
        port (Port): port to route to outside of bounding box
        bbox (tuple): ((xmin, ymin), (xmax, ymax)) bounding box
        space (float): extra space to add

    Returns:
        (Port): new port that is outside of bounding box
    """
    midpoint = [port.x, port.y]
    if space < 0:
        raise ValueError("extra space cannot be less than zero")
    if port.orientation == 0:
        # go to xmax
        midpoint[0] = max(midpoint[0], bbox[1][0] + space)
    elif port.orientation == 90:
        # go to ymax
        midpoint[1] = max(midpoint[1], bbox[1][1] + space)
    elif port.orientation == 180:
        # go to xmin
        midpoint[0] = min(midpoint[0], bbox[0][0] - space)
    elif port.orientation == 270:
        # go to ymin
        midpoint[1] = min(midpoint[1], bbox[0][1] - space)
    else:
        print(
            "WARNING, unable to extend port beyond bounding box if port is not aligned to manhattan grid"
        )
        return port
    return Port(
        name=port.name,
        midpoint=midpoint,
        width=port.width,
        orientation=port.orientation,
        layer=port.layer,
    )


def _route_dut(
    experiment: Device,
    dut_bbox: tuple,
    dut_bbox_keepout: float,
    name: str,
    route_groups: Sequence[RouteGroup] | None,
    dut_groups: Sequence[Sequence[Port]],
    pad_groups: Sequence[Sequence[Port]],
    layer_transitions: dict[tuple, DeviceSpec],
    retries: int,
    debug: bool,
) -> Device:
    """Helper method for :py:`generate`

    Parameters
        experiment (Device): DUT (and pads) Device that will be routed
        dut_bbox (tuple): for route_groups which have ignore_dut_bbox set to False,
            all DUT ports will first be routed to the outside of the bbox before additional
            routing is performed
        dut_bbox_keepout (float): distance to route outside of bounding box of DUT
        name (str): original name of DUT
        route_groups (Sequence[RouteGroup] | None): route groups between DUT and pads
        dut_groups (Sequence[Sequence[Port]]): DUT-only ports from route_groups
        pad_groups (Sequence[Sequence[Port]]): pad-only ports from route_groups
        layer_transitions (dict[tuple, DeviceSpec]): transitions between layers
        retries (int): max number of retries
        ignore_dut_bbox (bool): whether or not to ignore the dut bounding box when routing
        debug (bool): if True, generate quickplot before throwing error

    Returns:
        (Device): the routed device
    """
    problem_groups = set([])
    # first add autotapers
    autotapered = Device()
    autotapered << experiment
    for gid, route_group in enumerate(route_groups):
        if route_group.ground:
            continue
        xc = qg.get_cross_section(route_group.cross_section)
        dut_groups[gid] = _add_autotapers(
            device=autotapered,
            cross_section=xc,
            layer_transitions=layer_transitions,
            ports=dut_groups[gid],
        )
        pad_groups[gid] = _add_autotapers(
            device=autotapered,
            cross_section=xc,
            layer_transitions=layer_transitions,
            ports=pad_groups[gid],
        )
    for _ in range((retries + 1) * len(route_groups)):
        routed = Device()
        routed << autotapered
        # for each grouping, try route_bundle, if that fails use route_bundle_sbend
        complete = True
        for gid, route_group in enumerate(route_groups):
            if route_group.ground:
                continue
            all_paths = []
            # get list of pad ports
            dut_group = dut_groups[gid]
            pad_group = pad_groups[gid]
            xc = qg.get_cross_section(route_group.cross_section)
            if gid not in problem_groups:
                try:
                    # loop over each orientation
                    ports = {x: [[], []] for x in ["N", "E", "S", "W"]}
                    for d, p in zip(dut_group, pad_group):
                        direction = qg.utilities._get_port_direction(
                            d, warn_not_90=True
                        )
                        ports[direction][0].append(d)
                        ports[direction][1].append(p)
                    for direction in ports.keys():
                        portmap = ports[direction]
                        if len(portmap[0]) == 0:
                            continue
                        for port1, port2 in zip(portmap[0], portmap[1]):
                            route_path = Path()
                            route_path.center = port1.midpoint
                            if not route_group.ignore_dut_bbox:
                                # first route to edge of bbox
                                # get cardinal direction
                                port1_new = _extend_port_to_bbox(
                                    port=port1, bbox=dut_bbox, space=dut_bbox_keepout
                                )
                                if (
                                    np.sum(np.abs(port1_new.midpoint - port1.midpoint))
                                    > 1e-6
                                ):
                                    route_path.append(
                                        pr.path_straight(port1, port1_new)
                                    )
                                port1 = port1_new
                            route_path.append(
                                pr.path_manhattan(port1, port2, radius=2 * xc.radius)
                            )
                            route_path = pp.smooth(
                                route_path, radius=xc.radius, use_eff=False, num_pts=50
                            )
                            if _path_self_intersects(route_path):
                                raise RuntimeError(
                                    "After including auto_tapers, routed paths are "
                                    "self-intersecting. Try increasing the spacing "
                                    "between the pads and DUT or using s_bend routing."
                                )
                            # move end of route path to port2
                            # extrude path
                            extruded = routed << xc.extrude(route_path)
                            dorientation = (
                                port2.orientation - extruded.ports[2].orientation + 180
                            ) % 360
                            extruded.rotate(dorientation)
                            dcenter = port2.midpoint - extruded.ports[2].midpoint
                            extruded.move(dcenter)
                            route_path.rotate(dorientation)
                            route_path.move(dcenter)
                            all_paths.append(route_path)

                except RuntimeError:
                    problem_groups.add(gid)
                    complete = False
                    continue
                except ValueError as e:
                    message = (
                        "Routing failed, try manually specifying port mapping "
                        "between DUT and pads with route_groups."
                    )
                    if debug:
                        print(message)
                        from phidl import quickplot as qp

                        qp(routed)
                    raise RuntimeError(message) from e
            else:
                # TODO implement s-bend routing
                pass
            # check for intersections between paths that were routed separately
            for m in range(len(all_paths) - 1):
                for n in range(m + 1, len(all_paths)):
                    # check that all_paths[p] and all_paths[q] do not intersect
                    intersection, pair = _paths_intersect(all_paths[m], all_paths[n])
                    if intersection:
                        message = (
                            "Could not route without intersections. Found "
                            f"intersection between paths {pair} "
                            "Try manually "
                            "specifying port mapping between DUT and pads with "
                            "route_groups. Also try increasing the spacing between "
                            "DUT and pads."
                        )
                        if debug:
                            print(message)
                            from phidl import quickplot as qp

                            qp(routed)
                        raise Warning(message)
        if complete:
            routed.name = f"experiment_{name}"
            return routed
    raise RuntimeError(f"failed to route design after {retries} iterations")


def generate(
    dut: DeviceSpec | Device,
    pad_array: DeviceSpec | Device,
    label: DeviceSpec | Device | None,
    route_groups: Sequence[RouteGroup],
    dut_offset: tuple[float, float] = (0, 0),
    pad_offset: tuple[float, float] = (0, 0),
    label_offset: tuple[float, float] | None = (-100, -100),
    ignore_port_count_mismatch: bool = False,
    dut_bbox_keepout: float = 10,
    retries: int = 10,
    debug: bool = False,
) -> Device:
    """Construct an experiment from a device/circuit (Device).

    Includes text, pads, and routing to connect pads to devices

    Parameters:
        dut (DeviceSpec or Device): finished device to be connected to pads
        pad_array (DeviceSpec or Device or None): pad array to connect to device
        label (DeviceSpec or Device or None): text label or factory.
        route_groups (Sequence[RouteGroup]): how to route DUT to pads
        dut_offset (tuple[float, float]): x,y offset for dut (mostly useful for linear pad arrays)
        pad_offset (tuple[float, float]): x,y offset for pad array (mostly useful for linear pad arrays)
        label_offset (tuple[float, float] or None): x,y offset of label
        ignore_port_count_mismatch (bool): if True, ignores mismatched number of DUT and pads ports,
            only if route_groups defines a mapping to all pad ports, or lists all DUT ports.
        dut_bbox_keepout (float): if ignore_dut_bbox is False, distance to extend ports
            outside of DUT bounding box before performing routing.
        retries (int): how many times to try rerouting with s_bend (may need to be larger for many port groupings)
        debug (bool): if True, quickplot DUT + pads before throwing error when routing fails

    Returns:
        (Device): experiment

    Example:
        Using the example qnngds PDK: `<https://github.com/qnngroup/qnngds-pdk/>`_,
        we can generate an example nTron test layout including pads. The pad array
        is just a linear array from gdsfactory, although a custom array could be defined.
        The mapping of nTron device ports to pad ports is defined manually with ``route_groups``,
        but it's possible to use autoassignment by setting ``route_groups=None``.
        However, autoassignment only works in some cases, and in the case of this nTron,
        it would most likely fail.

        >>> c = qg.experiment.generate(
        >>>     dut=qg.devices.ntron.sharp,
        >>>     pad_array=qg.pads.array(
        >>>         pad_specs=(qg.pads.stack(size=(200, 200), layers=("EBEAM_COARSE",)),),
        >>>         columns=1,
        >>>         rows=3,
        >>>         pitch=250,
        >>>     ),
        >>>     label=None,
        >>>     route_groups=(
        >>>         qg.experiment.RouteGroup(
        >>>             qg.get_cross_section("ebeam"), {"g": 2, "s": 1, "d": 3}
        >>>         ),
        >>>     ),
        >>>     dut_offset=(250, 250),
        >>>     pad_offset=(0, 0),
        >>>     label_offset=(0, 0),
        >>>     retries=1,
        >>> )
        >>> qp(c)
    """
    # check if route_groups is complete so we can handle ignore_port_count_mismatch flag
    route_groups_complete = False
    if route_groups is not None and pad_array is not None:
        # make sure all dut ports are assigned to a pad port
        dut_i = qg.get_device(dut)
        all_dut_ports = set(dut_i.ports[port_name].name for port_name in dut_i.ports)
        mapped_dut_ports = set([])
        for route_group in route_groups:
            if route_group.ground:
                continue
            for dut_port, pad_port in route_group.port_mapping.items():
                mapped_dut_ports.add(dut_port)
        if len(all_dut_ports - mapped_dut_ports) == 0:
            route_groups_complete = True

    allow_port_count_mismatch = route_groups_complete and ignore_port_count_mismatch

    dut_i = qg.get_device(dut)
    if pad_array is not None:
        pads_i = qg.get_device(pad_array)
        # check appropriate number of ports on pad_array and dut
        if len(dut_i.ports) != len(pads_i.ports):
            if not (allow_port_count_mismatch):
                raise ValueError(
                    f"DUT ({len(dut_i.ports)} ports) and pad array "
                    f"({len(pads_i.ports)} ports) should have the same number of ports."
                )
    # check that number of DUT ports assigned in route_groups is correct
    if len(dut_i.ports) != 0 and route_groups is not None:
        num_assigned_ports = sum(
            len(group.port_mapping.keys()) for group in route_groups
        )
        if num_assigned_ports != len(dut_i.ports):
            if not (allow_port_count_mismatch):
                raise ValueError(
                    f"invalid number of port groupings: got {num_assigned_ports}, "
                    f"expected {len(dut_i.ports)} based on number of ports on DUT"
                )
    elif route_groups is not None:
        if pad_array is not None:
            raise ValueError(
                "cannot route pad array to DUT with zero ports, "
                "did you remember to add ports to your DUT?"
            )

    experiment = Device()

    # figure out which layers to outline
    outline_layers = qg.utilities.get_outline_layers(qg.get_active_pdk().layers)
    keepout_layers = qg.utilities.get_keepout_layers(qg.get_active_pdk().layers)

    # outline and add DUT
    outlined = qg.utilities.outline(dut_i, outline_layers)
    dut_ref = experiment.add_ref(
        qg.utilities.keepout(outlined, outline_layers, keepout_layers)
    )
    dut_ref.move(dut_offset)
    if pad_array is None:
        return experiment

    # add pads
    # don't outline, and add to dummy component.
    # after pad port adjustment, perform the outline
    dummy_pads = Device()
    pads_ref = dummy_pads.add_ref(pads_i)
    pads_ref.move(pad_offset)

    # add text label (don't outline)
    if label is not None:
        label_i = label() if isinstance(label, Callable) else label
        label_ref = experiment.add_ref(label_i)
        label_ref.move(label_offset)

    route_groups, dut_pad_map = _define_routes(
        dut_ref=dut_ref, pads_ref=pads_ref, route_groups=route_groups
    )
    # shift pad ports if it's possible to do a straight route between dut and pad without exceeding pad extent
    for gid, route_group in enumerate(route_groups):
        if route_group.ground:
            continue
        for dut_port_name in route_group.port_mapping:
            dut_port = dut_ref.ports[dut_port_name]
            pad_port = dut_pad_map[dut_port_name]
            if (dut_port.orientation - pad_port.orientation) % 360 == 180:
                # ports are facing each other
                w_route = qg.get_cross_section(route_group.cross_section).sections[0][
                    "width"
                ]
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
                    midpoint=center,
                    orientation=pad_port.orientation,
                    layer=pad_port.layer,
                )
                dummy_pads.add_port(port=pad_port)
                dut_pad_map[dut_port_name] = pad_port
            else:
                dummy_pads.add_port(port=pad_port)

    # add pads to actual device
    experiment.add_ref(qg.utilities.outline(dummy_pads, outline_layers))

    # get layer transitions for computing taper lengths (to allow addition of autotapers)
    layer_transitions = qg.get_active_pdk().layer_transitions

    dut_groups = []
    pad_groups = []
    for route_group in route_groups:
        dut_groups.append([dut_ref.ports[p] for p in route_group.port_mapping])
        pad_groups.append([dut_pad_map[p] for p in route_group.port_mapping])
    # actually do routing
    routed = _route_dut(
        experiment=experiment,
        dut_bbox=dut_ref.bbox,
        dut_bbox_keepout=dut_bbox_keepout,
        name=dut_i.name,
        route_groups=route_groups,
        dut_groups=dut_groups,
        pad_groups=pad_groups,
        layer_transitions=layer_transitions,
        retries=retries,
        debug=debug,
    )
    return routed
