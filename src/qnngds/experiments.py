"""Library of pre-built cells containing text, border marks, and an experiment,
connected to pads for wirebonding."""

from phidl import Device
import phidl.geometry as pg
from typing import Union
import math
import numpy as np
from numpy.typing import ArrayLike

import qnngds.devices as devices
import qnngds.utilities as utility

## devices:


def experiment(
    device: ArrayLike = devices.nanowire.variable_length,
    die_parameters: utility.DieParameters = utility.DieParameters(),
    device_layer: int = 1,
    outline_dev: Union[int, float] = 1,
    text: Union[None, str] = None,
    device_y=0,
) -> Device:
    """
    Creates an experiment containing Device[s]

    Parameters
    --------------------
    device: ArrayLike of Devices
        Device[s] to place in cell
    die_paramaters: DieParameters
        design-wide specifications
    device_layer: int
        layer on which to place Device[s]
    outline_dev: int or float
        width of outline for CPW-type architecture
    text: str or None
        label text for cell

    Returns
    ----------------
    Cell: a Device containing the input devices, pads, and routing
    """

    device_array = np.array(device)
    if device_array.shape == ():
        device = np.array([device])
    else:
        device = np.array(device)

    cell_scaling_factor_x = device[0].pads.cell_scaling_factor_x
    # cell_scaling_factor_y = device[0].pads.cell_scaling_factor_y
    num_pads_n = device[0].pads.num_pads_n
    num_pads_s = device[0].pads.num_pads_s
    num_pads_e = device[0].pads.num_pads_e
    num_pads_w = device[0].pads.num_pads_w
    ports_gnd = device[0].pads.ports_gnd
    port_map_x = device[0].pads.port_map_x
    port_map_y = device[0].pads.port_map_y

    max_x_num = max(num_pads_n, num_pads_s, num_pads_e)
    max_y_num = max(num_pads_e, num_pads_w)

    if text is None:
        text = f"{device[0].name}"
    cell_text = text.replace(" \n", ", ")

    DIE = Device(f"CELL.{cell_text}")
    FULL_DEVICES = Device(f"{cell_text}")

    USER_DEVICES = Device(f"{cell_text}")
    refs = []
    for dev in device:
        ref = USER_DEVICES << dev
        refs.append(ref)

    FULL_DEVICES << USER_DEVICES

    ## Create the DIE

    # die parameters, checkup conditions
    num_dev = len(device)
    n = math.ceil(
        (2 * max_x_num * (num_dev + 1) * die_parameters.pad_size[0])
        / die_parameters.unit_die_size[0]
    )

    default_contact_w = USER_DEVICES.xsize + die_parameters.contact_l
    if default_contact_w < die_parameters.pad_size[0]:
        die_contact_w = default_contact_w
    else:
        die_contact_w = die_parameters.pad_size[0]
    dev_contact_w = USER_DEVICES.xsize
    routes_margin = 4 * die_contact_w

    device_max_x = (
        max_x_num
        * num_dev
        * max(
            die_parameters.pad_size[0] * cell_scaling_factor_x,
            USER_DEVICES.xsize + 2 * die_parameters.outline,
        )
    )

    if device[0].pads.tight_y_spacing:
        device_max_y = USER_DEVICES.ysize + 2 * die_parameters.contact_l
    else:
        device_max_y = USER_DEVICES.ysize + routes_margin

    dev_max_size = (
        device_max_x,
        device_max_y,
    )

    ports = {
        "N": num_pads_n * num_dev,
        "S": num_pads_s * num_dev,
        "E": num_pads_e * num_dev,
        "W": num_pads_w * num_dev,
    }
    ports = {key: val for key, val in ports.items() if val != 0}

    # die, with calculated parameters
    BORDER = utility.die_cell(
        die_parameters=die_parameters,
        n_m_units=(n, 1),
        contact_w=die_contact_w,
        device_max_size=dev_max_size,
        ports=ports,
        ports_gnd=ports_gnd,
        text=f"{cell_text}",
        probe_tip=device[0].pads.probe_tip,
        num_devices=len(device),
        device_y=device_y,
    )

    if "N" in ports:
        side = "N"
    elif "E" in ports:
        side = "E"

    for i, ref in enumerate(refs):
        x_offset = BORDER.ports[f"{side}{i * max_x_num + 1}"].x
        if max_x_num > 1:
            x_offset = (
                x_offset + BORDER.ports[f"{side}{i * max_x_num + max_x_num}"].x
            ) / 2
        if side == "E":
            x_offset -= device[0].pads.probe_tip.pad_length
        ref.movex(x_offset)
        print(port_map_x.items())
        for dev_port, pad_port in port_map_x.items():
            # print(f"{pad_port[0]}{max_x_num*i+pad_port[1]}")
            USER_DEVICES.add_port(
                port=ref.ports[dev_port],
                name=f"{pad_port[0]}{max_x_num * i + pad_port[1]}",
            )
        for dev_port, pad_port in port_map_y.items():
            USER_DEVICES.add_port(
                port=ref.ports[dev_port],
                name=f"{pad_port[0]}{max_y_num * i + pad_port[1]}",
            )

    ## Route the nanowires and the die

    # hyper tapers
    taper_contact = min(dev_contact_w, device[0].pads.contact_w / 2)
    HT, dev_ports = utility.add_hyptap_to_cell(
        BORDER.get_ports(),
        die_parameters.contact_l,
        taper_contact,
        positive_tone=die_parameters.positive_tone,
    )
    FULL_DEVICES.ports = dev_ports.ports
    FULL_DEVICES << HT

    # routes from nanowires to hyper tapers
    ROUTES = utility.route_to_dev(HT.get_ports(), USER_DEVICES.ports)
    FULL_DEVICES << ROUTES

    FULL_DEVICES.ports = dev_ports.ports
    if die_parameters.positive_tone:
        FULL_DEVICES = pg.outline(
            FULL_DEVICES, outline_dev, open_ports=2 * outline_dev, layer=device_layer
        )
    FULL_DEVICES.name = f"{cell_text}"

    DIE << FULL_DEVICES
    DIE << BORDER

    return DIE
