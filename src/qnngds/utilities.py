"""Utilies is used for building cells in design.

Cells are made of devices
(found in utilities) and a die_cell border, wich contains pads, text etc... The
device and its die are linked thanks to functions present in this module.
"""

import gdsfactory as gf
import kfactory as kf
from typing import Literal
from collections.abc import Callable, Sequence

from gdsfactory.typings import (
    ComponentSpec,
    ComponentSpecOrComponent,
    ComponentSpecsOrComponents,
    CrossSectionSpec,
    Spacing,
    Port,
    Ports,
    PortsDict,
)


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


def outline(
    component: gf.Component,
    outline_layers: dict[tuple, float] = {},
) -> gf.Component:
    """Outline polygons within component by layer.

    Args:
        component (gf.Component): component to merge
        outline_layers (dict[tuple, float]): map of desired outline amount per layer. If a layer is omitted, it will not be outlined

    Returns:
        gf.Component: the outlined component
    """
    comp_outlined = gf.Component()
    for layer in component.layers:
        r = component.get_region(layer=layer)
        if layer not in outline_layers.keys():
            comp_outlined.add_polygon(r, layer=layer)
        else:
            outline = outline_layers[layer] / gf.kcl.dbu
            if outline > 0:
                r_expanded = r.sized(outline)
            else:
                raise ValueError("outline must be greater than zero")
            comp_outlined.add_polygon(r_expanded - r, layer=layer)
    return comp_outlined


def invert(
    component: gf.Component,
    ext_bbox_layers: dict[tuple, float] = {},
) -> gf.Component:
    """Outline polygons within component by layer.

    Args:
        component (gf.Component): component to merge
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


def flex_grid(
    components: ComponentSpecsOrComponents = (gf.components.shapes.rectangle,),
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


def generate_experiment(
    dut: ComponentSpecOrComponent = gf.components.shapes.rectangle,
    pad_array: ComponentSpecOrComponent = gf.components.shapes.rectangle,
    port_groupings: Sequence[Ports] | None = None,
    route_cross_section: Sequence[CrossSectionSpec] | None = None,
    route_tapers: Sequence[ComponentSpec] | None = None,
    dut_offset: tuple[float, float] = (0, 0),
    pad_offset: tuple[float, float] = (0, 0),
    retries: int = 10,
) -> gf.Component:
    """Construct an experiment from a device/circuit (gf.Component).

    Includes dicing marks, text, pads, and routing to connect pads to devices

    Parameters:
        dut (ComponentSpec or Component): finished device to be connected to pads
        pad_array (ComponentSpec or Component or None): pad array to connect to device
        port_groupings (Sequence[Ports] or None): which sets of ports to route together (e.g. if they're on a different layer)
        route_cross_section (Sequence[CrossSectionSpec] or None): mapping of port collection to a cross section
        route_tapers (Sequence[ComponentSpec] or None): mapping of port collection to a taper
        dut_offset (tuple[float, float]): x,y offset for dut (mostly useful for linear pad arrays)
        pad_offset (tuple[float, float]): x,y offset for pad array (mostly useful for linear pad arrays)
        retries (int): how many times to try rerouting (may need to be larger for many port groupings)
    Returns:
        (gf.Component): experiment
    """
    dut_i = dut() if isinstance(dut, Callable) else dut
    if pad_array is not None:
        pads_i = pad_array() if isinstance(pad_array, Callable) else pad_array
        # check appropriate number of ports on pad_array and dut
        if len(dut_i.ports) != len(pads_i.ports):
            raise ValueError(
                f"DUT ({len(dut.ports)} ports) and pad array ({len(pad_array.ports)} ports) should have the same number of ports."
            )
    # check that length of port groupings is correct
    if len(dut_i.ports) != 0:
        num_assigned_ports = sum(len(group) for group in port_groupings)
        if num_assigned_ports != len(dut_i.ports):
            raise ValueError(
                f"invalid number of port groupings: got {num_assigned_ports}, expected {len(dut.ports)} based on number of ports on DUT"
            )
        # check route_cross_section and route_tapers have the right length
        if route_cross_section is not None and len(route_cross_section) != len(
            port_groupings
        ):
            raise ValueError(
                "invalid number of cross sections, must be a one-to-one mapping with port_groupings"
            )
        if route_tapers is not None and len(route_tapers) != len(port_groupings):
            raise ValueError(
                "invalid number of tapers, must be a one-to-one mapping with port_groupings"
            )
    else:
        if pad_array is not None:
            raise ValueError("cannot route pad array to DUT with zero ports")

    experiment = gf.Component()
    dut_ref = experiment.add_ref(dut_i)
    dut_ref.move(dut_offset)
    if pad_array is None:
        return experiment
    pads_ref = experiment.add_ref(pads_i)
    pads_ref.move(pad_offset)

    # get sorted list of ports
    def _get_port_direction(port: Port) -> str:
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
        ports = {x: [] for x in ["E", "N", "W", "S"]}
        # group by direction
        for p in component.ports:
            ports[_get_port_direction(p)].append(p)
        return ports

    def _sort_ports(
        ports: PortsDict, sort_map: dict[str, Callable], direction_order: Sequence[str]
    ) -> PortsDict:
        # sort
        for direction in sort_map.keys():
            ports[direction].sort(key=sort_map[direction])
        flat_ports = []
        for direction in direction_order:
            flat_ports += ports[direction]
        return flat_ports

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
        _get_component_port_direction(dut_i), sort_cw, ("W", "N", "E", "S")
    )
    # sort pads ccw
    pad_ports = _sort_ports(
        _get_component_port_direction(pads_i), sort_ccw, ("E", "S", "W", "N")
    )

    # create mapping
    dut_pad_map = {dp.name: pp for (dp, pp) in zip(dut_ports, pad_ports)}

    # shift pad ports if it's possible to do a straight route between dut and pad without exceeding pad extent
    for gid, group in enumerate(port_groupings):
        for p in group:
            dut_port = dut_i.ports[p]
            pad_port = dut_pad_map[p]
            if (dut_port.orientation - pad_port.orientation) % 360 == 180:
                # ports are facing each other
                w_route = route_cross_section[gid].width
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
                dut_pad_map[p] = Port(
                    name=pad_port.name,
                    width=pad_port.width + dwidth,
                    center=center,
                    orientation=pad_port.orientation,
                    layer=pad_port.layer,
                    port_type=pad_port.port_type,
                )

    problem_groups = set([])

    for _ in range(retries + 1):
        routed = gf.Component()
        routed.add_ref(experiment)
        # for each grouping, try route_bundle, if that fails use route_bundle_sbend
        complete = True
        for gid, group in enumerate(port_groupings):
            # get list of pad ports
            dut_group = [dut_i.ports[p] for p in group]
            pad_group = [dut_pad_map[p] for p in group]
            if gid not in problem_groups:
                try:
                    # loop over each orientation
                    ports = {x: [[], []] for x in ["N", "E", "S", "W"]}
                    for d, p in zip(dut_group, pad_group):
                        direction = _get_port_direction(d)
                        ports[direction][0].append(d)
                        ports[direction][1].append(p)
                    for direction, portmap in ports.items():
                        if len(portmap[0]) == 0:
                            continue
                        gf.routing.route_bundle(
                            routed,
                            portmap[0],
                            portmap[1],
                            cross_section=route_cross_section[gid],
                            taper=(
                                route_tapers[gid] if route_tapers is not None else None
                            ),
                            auto_taper=True,
                            on_collision="error",
                            router="optical",
                        )
                except RuntimeError:
                    problem_groups.add(gid)
                    complete = False
                    break
            else:
                # add autotapers and regenerate port groups
                dut_group_new = gf.routing.auto_taper.add_auto_tapers(
                    routed, dut_group, route_cross_section[gid]
                )
                pad_group_new = gf.routing.auto_taper.add_auto_tapers(
                    routed, pad_group, route_cross_section[gid]
                )
                gf.routing.route_bundle_sbend(
                    routed,
                    pad_group_new,
                    dut_group_new,
                    enforce_port_ordering=True,
                )
        if complete:
            return routed
    raise RuntimeError(f"failed to route design after {retries} iterations")
