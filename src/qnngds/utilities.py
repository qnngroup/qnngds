"""Utilies is used for building cells in design.

Cells are made of devices
(found in utilities) and a die_cell border, wich contains pads, text etc... The
device and its die are linked thanks to functions present in this module.
"""

import gdsfactory as gf
import kfactory as kf
from phidl import Device, Port
import phidl.geometry as pg
import phidl.routing as pr
from typing import Tuple, List, Union, Dict, Set, Literal
import qnngds.geometries as geometry

from gdsfactory.typings import (
    ComponentSpecsOrComponents,
    Spacing,
)


def union(component: gf.Component) -> gf.Component:
    comp_union = gf.Component()
    for layer in component.layers:
        temp = gf.Component()
        temp.add_polygon(component.get_region(layer), layer=layer)
        comp_union << gf.boolean(temp, temp, operation="or", layer=layer)
    return comp_union


def flex_grid(
    components: ComponentSpecsOrComponents = (gf.components.shapes.rectangle),
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
    die_parameters: DieParameters = DieParameters(),
    n_m_units: Tuple[int, int] = (1, 1),
    contact_w: Union[int, float] = 50,
    device_max_size: Tuple[Union[int, float], Union[int, float]] = (
        round(DieParameters().unit_die_w / 3),
        round(DieParameters().unit_die_h / 3),
    ),
    ports: Dict[str, int] = {"N": 1, "E": 1, "W": 1, "S": 1},
    ports_gnd: List[str] = ["E", "S"],
    text: str = "",
    text_size: Union[None, int, float] = None,
    probe_tip: Union[None, MultiProbeTip] = WireBond(),
    num_devices=1,
    device_y=0,
) -> Device:
    """Creates a die cell with dicing marks, text, and pads to connect to a
    device.

    Parameters:
        die_parameters (DieParameters): the die's parameters.
        n_m_units (tuple of int): number of unit dies that compose the cell in width and height.
        device_max_size (tuple of int or float): Max dimensions of the device
            inside the cell (width, height).
        ports (dict): The ports of the device, format must be {'N':m, 'E':n, 'W':p, 'S':q}.
        ports_gnd (list of string): The ports connected to ground.
        text (string): The text to be displayed on the cell.
        text_size (int or float): If specified, overwrites the Die's
            text_size. Size of text, corresponds to phidl geometry std.

    Returns:
        DIE (Device): The cell, with ports of width contact_w positioned around a device_max_size area.
    """
    contact_w = probe_tip.contact_w

    def offset(overlap_port):
        port_name = overlap_port.name[0]
        if port_name == "N":
            overlap_port.midpoint[1] += -die_parameters.contact_l
        elif port_name == "S":
            overlap_port.midpoint[1] += die_parameters.contact_l
        elif port_name == "W":
            overlap_port.midpoint[0] += die_parameters.contact_l
        elif port_name == "E":
            overlap_port.midpoint[0] += -die_parameters.contact_l

    die_name = text.replace("\n", "")
    die_size = [n_m_units[i] * die_parameters.unit_die_size[i] for i in [0, 1]]
    DIE = Device(f"DIE {die_name} ")

    border = pg.rectangle(die_size)
    border.move(border.center, (0, 0))

    borderOut = Device()

    ## Make the routes and pads
    padOut = Device()

    pad_block_size = (
        die_size[0]
        - 2 * probe_tip.pad_length
        - 4 * die_parameters.outline
        - die_parameters.xspace,
        die_size[1]
        - 2 * probe_tip.pad_length
        - 4 * die_parameters.outline
        - die_parameters.yspace
        - device_y,
    )
    # standard pad definition for wirebonding
    if isinstance(probe_tip, WireBond):
        inner_block = pg.compass_multi(device_max_size, ports)
        outer_block = pg.compass_multi(pad_block_size, ports)

    # pad definition for specific probe tip
    elif isinstance(probe_tip, MultiProbeTip):
        unit_size = probe_tip.num_tips * probe_tip.pad_pitch
        inner_block = pg.compass_multi(
            (unit_size * num_devices, device_max_size[1]), ports
        )
        outer_block = Device()
        if "N" in ports:
            side = "N"
        elif "E" in ports:
            side = "E"
        ports_per_dev = int(ports[side] / num_devices)
        block_i = pg.compass_multi(
            (unit_size, pad_block_size[1] / 2), {side: probe_tip.num_tips}
        )
        for i in range(num_devices):
            ref = outer_block << block_i
            ref.center = [-unit_size * num_devices / 2 + (i + 1 / 2) * unit_size, 0]
            for j in range(ports_per_dev):
                port = list(ref.ports.values())[j]
                outer_block.add_port(f"{side}{i * ports_per_dev + j + 1}", port=port)
        device_max_size = inner_block.size

    inner_ports = list(inner_block.ports.values())
    Connects = Device()
    for i, port in enumerate(list(outer_block.ports.values())):
        CONNECT = Device()
        port.rotate(180)
        # create the pad
        pad = pad_with_offset(die_parameters, probe_tip)
        pad.add_port(
            "1",
            midpoint=(probe_tip.pad_width / 2, 0),
            width=probe_tip.pad_width,
            orientation=90,
        )
        pad_ref = CONNECT << pad
        pad_ref.connect(pad.ports["1"], port)

        # create the route from pad to contact
        port.width = probe_tip.pad_width
        inner_ports[i].width = contact_w
        CONNECT << pr.route_quad(port, inner_ports[i], layer=die_parameters.die_layer)

        # create the route from contact to overlap
        overlap_port = CONNECT.add_port(port=inner_ports[i])
        offset(overlap_port)
        overlap_port.rotate(180)

        CONNECT << pr.route_quad(
            inner_ports[i], overlap_port, layer=die_parameters.die_layer
        )

        # isolate the pads that are not grounded
        port_grounded = any(port.name[0] == P for P in ports_gnd)
        if not port_grounded:
            padOut << pg.outline(
                CONNECT,
                distance=die_parameters.outline,
                join="round",
                open_ports=2 * die_parameters.outline,
            )
            Connects << CONNECT

        # add the port to the die
        DIE.add_port(port=inner_ports[i].rotate(180))
        DIE << CONNECT

    borderOut << padOut

    ## Add the die markers

    # mark the corners
    cornersOut = Device()

    corners_coord = [
        (
            -die_size[0] / 2 + die_parameters.die_border_w / 2,
            -die_size[1] / 2 + die_parameters.die_border_w / 2,
        ),
        (
            die_size[0] / 2 - die_parameters.die_border_w / 2,
            -die_size[1] / 2 + die_parameters.die_border_w / 2,
        ),
        (
            die_size[0] / 2 - die_parameters.die_border_w / 2,
            die_size[1] / 2 - die_parameters.die_border_w / 2,
        ),
        (
            -die_size[0] / 2 + die_parameters.die_border_w / 2,
            die_size[1] / 2 - die_parameters.die_border_w / 2,
        ),
    ]
    for corner_coord in corners_coord:
        corner = pg.rectangle(
            (
                die_parameters.die_border_w - die_parameters.outline,
                die_parameters.die_border_w - die_parameters.outline,
            )
        )
        corner = pg.outline(corner, -1 * die_parameters.outline)
        corner.move(corner.center, corner_coord)
        cornersOut << corner

    borderOut << cornersOut

    # label the cell
    if text_size is not None:
        label_size = text_size
    else:
        label_size = die_parameters.text_size

    label = pg.text(text, size=label_size, layer=die_parameters.die_layer)
    label.move((label.xmin, label.ymin), (0, 0))
    pos = [
        x + 2 * die_parameters.outline + 10
        for x in (-die_size[0] / 2, -die_size[1] / 2)
    ]
    label.move(pos)
    DIE << label
    labelOut = pg.outline(label, die_parameters.outline)

    borderOut << labelOut

    border = pg.boolean(border, borderOut, "A-B", layer=die_parameters.die_layer)
    DIE << border

    if die_parameters.fill_pad_layer:
        border_filled = pg.rectangle(die_size)
        center = pg.rectangle(device_max_size)
        border_filled.move(border_filled.center, (0, 0))
        center.move(center.center, (0, 0))
        border_filled = pg.boolean(border_filled, center, "A-B")

        border_filled = pg.boolean(
            border_filled, borderOut, "A-B", layer=die_parameters.pad_layer
        )
        border_filled = pg.offset(
            border_filled, -die_parameters.pad_tolerance, layer=die_parameters.pad_layer
        )
        DIE << border_filled

    DIE.flatten()
    ports = DIE.get_ports()
    DIE = pg.union(DIE, by_layer=True)

    PADS = pg.deepcopy(DIE)
    PADS.remove_layers([die_parameters.die_layer])
    PADS.name = "pads"
    DIE = pg.invert(DIE, border=0, layer=die_parameters.die_layer)
    DIE << PADS
    for port in ports:
        DIE.add_port(port)

    DIE.name = f"DIE {die_name}"
    # DIE << pg.copy_layer(Connects, layer=die_parameters.die_layer, new_layer=3)
    return DIE


def pad_with_offset(die_parameters: DieParameters = DieParameters(), probe_tip=None):
    """
    Creates a pad with a gold contact that is smaller than the superconducting layer
    by some amount specified in die_parameters to account for MLA offset

    die_parameters (DieParameters): for specifying pad shape
    probe_tip (ConnectToPCB inheritor, optional): can override pad shape
    """
    DEVICE = Device()
    if probe_tip is None:
        pad_size = die_parameters.pad_size
    else:
        pad_size = (probe_tip.pad_width, probe_tip.pad_length)
    outer_pad = pg.rectangle(
        pad_size,
        layer=die_parameters.die_layer,
    )
    inner_pad = pg.rectangle(
        [dim - die_parameters.pad_tolerance for dim in pad_size],
        layer=die_parameters.pad_layer,
    )
    inner_pad.center = outer_pad.center

    DEVICE << outer_pad
    DEVICE << inner_pad
    return DEVICE


def rename_ports_to_compass(DEVICE: Device, depth: Union[int, None] = 0) -> Device:
    """Rename ports of a Device based on compass directions.

    Parameters:
        DEVICE (Device): The Phidl Device object whose ports are to be renamed.

    Returns:
        Device: A new Phidl Device object with ports renamed to compass directions.
    """

    ports = DEVICE.get_ports(depth=depth)
    # Create a new Device object to store renamed ports
    DEV_COMPASS = Device(DEVICE.name)

    # Copy ports from the original device to the new device
    DEV_COMPASS << DEVICE

    # Initialize counters for each direction
    E_count = 1
    N_count = 1
    W_count = 1
    S_count = 1

    # Iterate through each port in the original device
    for port in ports:
        # Determine the orientation of the port and rename it accordingly
        if port.orientation % 360 == 0:
            DEV_COMPASS.add_port(port=port, name=f"E{E_count}")
            E_count += 1
        elif port.orientation % 360 == 90:
            DEV_COMPASS.add_port(port=port, name=f"N{N_count}")
            N_count += 1
        elif port.orientation % 360 == 180:
            DEV_COMPASS.add_port(port=port, name=f"W{W_count}")
            W_count += 1
        elif port.orientation % 360 == 270:
            DEV_COMPASS.add_port(port=port, name=f"S{S_count}")
            S_count += 1

    return DEV_COMPASS


def add_optimalstep_to_dev(
    DEVICE: Device, ratio: Union[int, float] = 10, layer: int = 1
) -> Device:
    """Add an optimal step to the device's ports.

    Note that the subports of the input Device are ignored but still conserved
    in the returned device.

    Parameters:
        DEVICE (Device): The Phidl Device to add the optimal steps to.
        ratio (int or float): the ratio between the width at the end of the step
            and the width of the device's ports.
        layer (int or array-like[2]): the layer to place the optimal steps into.

    Returns:
        (Device): The given Device, with additional steps on its ports. The
        ports of the returned device have the same name than the ports of the
        input device and correspond to the steps extremities.
    """
    DEV_STP = Device(DEVICE.name)

    DEV_STP << DEVICE
    for port in DEVICE.flatten().get_ports():
        STP = pg.optimal_step(
            port.width, port.width * ratio, symmetric=True, layer=layer
        )
        STP.name = f"optimal step x{ratio} "
        stp = DEV_STP << STP
        stp.connect(port=1, destination=port)
        DEV_STP.add_port(port=stp.ports[2], name=port.name)

    return DEV_STP


def add_hyptap_to_cell(
    die_ports: List[Port],
    contact_l: Union[int, float] = 10,
    contact_w: Union[int, float] = 5,
    layer: int = 1,
    positive_tone=True,
) -> Tuple[Device, Device]:
    """Takes the cell and adds hyper taper at its ports.

    Parameters:
        die_ports (list of Port): The ports of the die cell (use .get_ports()).
        contact_l (int or float): The overlap width (accounts for
            misalignment between 1st and 2nd ebeam exposures). Will also
            correspond to the hyper taper's length.
        contact_w (int or float): The width of the contact with the device's
            route (width of hyper taper's end).
        layer (int or array-like[2]): The layer on which to place the tapers
            (usually the same as the circuit's layer).

    Returns:
        Tuple[Device, Device]: a tuple containing:

        - **HT** (*Device*): The hyper tapers, positioned at the die's ports.
          Ports of the same name as the die's ports are added to the output of
          the tapers.
        - **device_ports** (*Device*): A device containing only the input ports
          of the tapers, named as the die's ports.
    """

    HT = Device("HYPER TAPERS ")
    device_ports = Device()

    for port in die_ports:
        if positive_tone:
            ht_w = port.width + 2 * contact_l
        else:
            ht_w = port.width
        ht = HT << geometry.hyper_taper(contact_l, ht_w, contact_w)
        ht.connect(ht.ports[2], port)
        HT.add_port(port=ht.ports[1], name=port.name)
        device_ports.add_port(port=ht.ports[2], name=port.name)

    HT.flatten(single_layer=layer)
    return HT, device_ports


def route_to_dev(ext_ports: List[Port], dev_ports: Set[Port], layer: int = 1) -> Device:
    """Creates smooth routes from external ports to the device's ports. If
    route_smooth is not working, routes quad.

    Parameters:
        ext_ports (list of Port): The external ports, e.g., of the die or hyper tapers (use .get_ports()).
        dev_ports (set of Port): The device's ports, should be named as the external ports (use .ports).
        layer (int or array-like[2]): The layer to put the routes on.

    Returns:
        ROUTES (Device): The routes from ports to ports, on the specified layer.
    """

    ROUTES = Device("ROUTES ")

    for port in ext_ports:
        print(dev_ports)
        dev_port = dev_ports[port.name]
        try:
            radius = port.width
            length1 = 2 * radius
            length2 = 2 * radius
            ROUTES << pr.route_smooth(
                port, dev_port, radius, path_type="Z", length1=length1, length2=length2
            )
        except ValueError:
            try:
                radius = dev_port.width
                length1 = radius
                length2 = radius
                ROUTES << pr.route_smooth(
                    port,
                    dev_port,
                    radius,
                    path_type="Z",
                    length1=length1,
                    length2=length2,
                )
            except ValueError:
                ROUTES << pr.route_quad(port, dev_port)
    ROUTES.flatten(single_layer=layer)
    return ROUTES
