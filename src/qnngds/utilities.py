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
    Ports,
    PortsDict,
)


def union(component: gf.Component) -> gf.Component:
    comp_union = gf.Component()
    for layer in component.layers:
        temp = gf.Component()
        temp.add_polygon(component.get_region(layer), layer=layer)
        comp_union << gf.boolean(temp, temp, operation="or", layer=layer)
    return comp_union


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
    dut_i = dut() if isinstance(dut, ComponentSpec) else dut
    if pad_array is not None:
        pads_i = pad_array() if isinstance(pad_array, ComponentSpec) else pad_array
        # check appropriate number of ports on pad_array and dut
        if len(dut.ports) != len(pad_array.ports):
            raise ValueError(
                f"DUT ({len(dut.ports)} ports) and pad array ({len(pad_array.ports)} ports) should have the same number of ports."
            )
    # check that length of port groupings is correct
    if len(dut.ports) != 0:
        num_assigned_ports = sum(len(group) for group in port_groupings)
        if num_assigned_ports != len(dut.ports):
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
    def _get_port_direction(component: gf.Component) -> PortsDict:
        ports = {x: [] for x in ["E", "N", "W", "S"]}
        # group by direction
        for p in component.ports:
            angle = p.orientation % 360
            if angle <= 45 or angle >= 315:
                ports["E"].append(p)
            elif angle <= 135 and angle >= 45:
                ports["N"].append(p)
            elif angle <= 225 and angle >= 135:
                ports["W"].append(p)
            else:
                ports["S"].append(p)
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
    dut_ports = _sort_ports(_get_port_direction(dut), sort_cw, ("E", "N", "W", "S"))
    # sort pads ccw
    pad_ports = _sort_ports(
        _get_port_direction(pad_array), sort_ccw, ("W", "S", "N", "E")
    )
    # create mapping
    dut_pad_map = {dp: pp for (dp, pp) in zip(dut_ports, pad_ports)}

    problem_groups = set([])

    for _ in range(retries):
        routes = gf.Component()
        routes.add_ref(experiment)
        # for each grouping, try route_bundle, if that fails use route_bundle_sbend
        complete = True
        for gid, group in enumerate(port_groupings):
            # get list of pad ports
            dut_group = group
            pad_group = [dut_pad_map[dut_pad] for dut_pad in dut_group]
            if gid not in problem_groups:
                try:
                    gf.routing.route_bundle(
                        routes,
                        dut_group,
                        pad_group,
                        cross_section=route_cross_section[gid],
                        taper=route_tapers[gid],
                        on_collision="error",
                        router="optical",
                    )
                except RuntimeError:
                    problem_groups.add(gid)
                    complete = False
                    break
            else:
                gf.routing.route_bundle_sbend(
                    routes,
                    dut_group,
                    pad_group,
                    enforce_port_ordering=False,
                )
        if complete:
            return routes
    raise RuntimeError(f"failed to route design after {retries} iterations")
