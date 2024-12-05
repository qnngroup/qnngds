"""Library of pre-built cells containing text, border marks, and an experiment,
connected to pads for wirebonding."""

from phidl import Device
import phidl.geometry as pg
import phidl.routing as pr
from typing import Tuple, List, Union, Optional
import math
import numpy as np
from numpy.typing import ArrayLike

import qnngds.tests as test
import qnngds.devices as devices
import qnngds.circuits as circuit
import qnngds.utilities as utility

# basics


def alignment(
    die_parameters: utility.DieParameters = utility.DieParameters(),
    layers_to_align: List[int] = [2, 3],
    text: Union[None, str] = None,
) -> Device:
    """Creates alignment marks in an integer number of unit cells.

    Parameters:
        die_parameters (DieParameters): the die's parameters.
        layers_to_align (list of int): Layers to align.
        text (str, optional): If None, the text is f"lay={layers_to_align}".

    Returns:
        DIE_ALIGN (Device): A device that centers the alignment marks in an n*m unit cell.
    """

    if text is None:
        text = f"lay={layers_to_align}"
    DIE = Device(f"CELL.ALIGN({text})")

    ALIGN = test.alignment_mark(layers_to_align)

    n = math.ceil((ALIGN.xsize) / die_parameters.unit_die_size[0])
    m = math.ceil((ALIGN.ysize) / die_parameters.unit_die_size[1])

    BORDER = utility.die_cell(
        die_parameters=die_parameters,
        n_m_units=(n, m),
        device_max_size=(ALIGN.xsize + 20, ALIGN.ysize + 20),
        ports={},
        ports_gnd={},
        text=f"ALIGN {text}",
    )

    DIE << BORDER.flatten()
    DIE << ALIGN

    return DIE


def vdp(
    die_parameters: utility.DieParameters = utility.DieParameters(),
    layers_to_probe: List[int] = [2],
    layers_to_outline: Union[None, List[int]] = None,
    text: Union[None, str] = None,
) -> Device:
    r"""Creates an experiment containing a Van Der Pauw structure between 4 contact
    pads.

    Parameters:
        die_parameters (DieParameters): the die's parameters.
        layers_to_probe (list of int): The layers on which to place the VDP structure.
        layers_to_outline (list of int): Among the VDP layers, the ones for which structure must not be filled but outlined.
        text (str, optional): If None, the text is f"lay={layers_to_probe}".
    Returns:
        DIE_VANDP (Device): The created device.
    """
    # Initialize parameters left to default (=None)

    if text is None:
        text = f"lay={layers_to_probe}"
    if layers_to_outline is None:
        layers_to_outline = [
            die_parameters.die_layer
        ]  # default layer to outline if None is given

    DIE_VANDP = Device(f"CELL.VDP({text})")

    device_max_w = min(die_parameters.unit_die_size) - 2 * (
        die_parameters.pad_size[1] + 2 * die_parameters.outline
    )  # width of max device size for this cell
    contact_w = device_max_w / 10  # choosing a contact width 10 times smaller
    device_w = (
        device_max_w - 2 * contact_w
    )  # choosing a smaller device to have space for routing from pad to contact

    # Creates the DIE, it contains only the cell text and bordure

    DIE = utility.die_cell(
        die_parameters=die_parameters,
        device_max_size=(device_max_w, device_max_w),
        ports={},
        ports_gnd=[],
        text=f"VDP \n{text}",
    )
    DIE_VANDP << DIE.flatten()

    # Creates the vdp structure, add pads and route

    VDP = Device()

    ## VDP probed area
    AREA = test.vdp(device_w, contact_w)
    VDP << AREA

    ## pads (creates a die and keeps the pads only)
    pads_parameters = utility.DieParameters(
        unit_die_size=die_parameters.unit_die_size,
        pad_size=die_parameters.pad_size,
        contact_l=0,
        outline=die_parameters.outline,
        die_layer=0,
        pad_layer=die_parameters.pad_layer,
        positive_tone=die_parameters.positive_tone,
        fill_pad_layer=False,
        text_size=die_parameters.text_size,
        pad_tolerance=0
    )

    PADS = utility.die_cell(
        die_parameters=pads_parameters,
        contact_w=die_parameters.pad_size[0],
        device_max_size=(device_max_w, device_max_w),
        ports={"N": 1, "E": 1, "W": 1, "S": 1},
        ports_gnd=["N", "E", "W", "S"],
        text="PADS ONLY",
    )
    PADS.remove_layers([die_parameters.pad_layer], invert_selection=True)
    VDP << PADS

    ## routes from pads to probing area
    ROUTES = utility.route_to_dev(PADS.get_ports(), AREA.ports)
    VDP << ROUTES

    VDP.flatten(0)

    # Outline the vdp structure for layers that need to be outlined

    DEVICE = Device(f"VDP(lay={layers_to_probe})")

    for layer in layers_to_probe:
        TEST_LAYER = pg.deepcopy(VDP)
        if layer in layers_to_outline:
            TEST_LAYER = pg.outline(TEST_LAYER, die_parameters.outline)
        TEST_LAYER.name = f"VDP(lay={layer})"
        DEVICE << TEST_LAYER.flatten(single_layer=layer)

    DIE_VANDP << DEVICE

    # Add pads if they are not in already present
    if die_parameters.pad_layer not in layers_to_probe:
        PADS = pg.union(PADS, layer=die_parameters.pad_layer)
        PADS.name = "PADS"
        DIE_VANDP << PADS

    return DIE_VANDP


def etch_test(
    die_parameters: utility.DieParameters = utility.DieParameters(),
    layers_to_etch: List[List[int]] = [[3]],
    text: Union[None, str] = None,
) -> Device:
    """Creates etch test structures in an integer number of unit cells.

    These test structures are thought to be used by probing on pads (with a
    simple multimeter) that should be isolated one from another if the etching
    is complete.

    Parameters:
        die_parameters (DieParameters): the die's parameters.
        layers_to_etch (list of list of int): Each element of the list corresponds to one test point, to put on the list of layers specified.
                                               Example: [[1, 2], [1], [2]]
        text (str, optional): If None, the text is f"lay={layers_to_etch}".

    Returns:
        DIE_ETCH_TEST (Device): A device (with size n*m of unit cells) with etch tests in its center.
    """

    if text is None:
        text = f"lay={layers_to_etch}"
    DIE_ETCH_TEST = Device(f"CELL.ETCH_TEST({text})")

    TEST = Device(f"ETCH_TEST({text})")

    ## Create the probing areas

    margin = 0.12 * min(die_parameters.unit_die_size)
    rect = pg.rectangle(
        (
            die_parameters.unit_die_size[0] - 2 * margin,
            die_parameters.unit_die_size[1] - 2 * margin,
        )
    )
    for i, layer_to_etch in enumerate(layers_to_etch):
        probe = Device()
        probe.add_array(rect, 2, 1, die_parameters.unit_die_size)
        for layer in layer_to_etch:
            TEST << pg.outline(probe, -die_parameters.outline, layer=layer).movey(
                i * die_parameters.unit_die_size[1]
            )

    ## Create the die

    n = math.ceil(
        (TEST.xsize + 2 * die_parameters.die_border_w) / die_parameters.unit_die_size[0]
    )
    m = math.ceil(
        (TEST.ysize + 2 * die_parameters.die_border_w) / die_parameters.unit_die_size[1]
    )
    BORDER = utility.die_cell(
        die_parameters=die_parameters,
        n_m_units=(n, m),
        ports={},
        ports_gnd={},
        text=f"ETCH TEST {text}",
    )

    BORDER.move(TEST.center)
    DIE_ETCH_TEST << BORDER.flatten()
    DIE_ETCH_TEST << TEST.flatten()
    DIE_ETCH_TEST.move(DIE_ETCH_TEST.center, (0, 0))

    return DIE_ETCH_TEST


def resolution_test(
    die_parameters: utility.DieParameters = utility.DieParameters(),
    layer_to_resolve: int = 1,
    resolutions_to_test: List[float] = [
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        1,
        1.5,
        2.0,
    ],
    text: Union[None, str] = None,
) -> Device:
    r"""Creates an experiment containing a resolution test.

    Parameters:
        die_parameters (DieParameters): the die's parameters.
        layer_to_resolve (int): The layer to put the resolution test on.
        resolutions_to_test (list of float): The resolutions to test in µm.
        text (str, optional): If None, the text is f"lay={layer_to_resolve}".

    Returns:
        DIE_RES_TEST (Device): The created device.
    """

    if text is None:
        text = f"lay={layer_to_resolve}"
    DIE_RES_TEST = Device(f"CELL.RESOLUTION_TEST({text})")

    ## Create the test structure
    TEST_RES = Device(f"RESOLUTION_TEST({text})")
    test_res = TEST_RES << test.resolution_test(
        resolutions=resolutions_to_test, inverted=False, layer=layer_to_resolve
    )
    test_res_invert = TEST_RES << test.resolution_test(
        resolutions=resolutions_to_test,
        inverted=resolutions_to_test[-1],
        layer=layer_to_resolve,
    )
    test_res_invert.movey(
        test_res_invert.ymin, test_res.ymax + 5 * resolutions_to_test[-1]
    )

    DIE_RES_TEST << TEST_RES.move(TEST_RES.center, (0, 0))

    ## Create the die
    n = math.ceil((TEST_RES.xsize) / die_parameters.unit_die_size[0])
    m = math.ceil((TEST_RES.ysize) / die_parameters.unit_die_size[1])
    BORDER = utility.die_cell(
        die_parameters=die_parameters,
        n_m_units=(n, m),
        ports={},
        ports_gnd=[],
        text=f"RES TEST \n{text}",
    )

    DIE_RES_TEST << BORDER.flatten()
    return DIE_RES_TEST


## devices:

def experiment(
        device: ArrayLike = devices.nanowire.spot(),
        die_parameters: utility.DieParameters = utility.DieParameters(),
        device_layer: int = 1,
        outline_dev: Union[int, float] = 1,
        text: Union[None, str] = None,
        device_y = 0
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
    cell_scaling_factor_y = device[0].pads.cell_scaling_factor_y
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
        (2*max_x_num*(num_dev+1) * die_parameters.pad_size[0])
        / die_parameters.unit_die_size[0]
    )
    
    default_contact_w = USER_DEVICES.xsize + die_parameters.contact_l
    if default_contact_w < die_parameters.pad_size[0]:
        die_contact_w = default_contact_w
    else:
        die_contact_w = die_parameters.pad_size[0]
    dev_contact_w = USER_DEVICES.xsize
    routes_margin = 4 * die_contact_w

    device_max_x = max_x_num * num_dev * max(die_parameters.pad_size[0]*cell_scaling_factor_x, USER_DEVICES.xsize+2*die_parameters.outline)
    
    if device[0].pads.tight_y_spacing == True:
        device_max_y = USER_DEVICES.ysize+2*die_parameters.contact_l
    else:
        device_max_y = USER_DEVICES.ysize+routes_margin

    dev_max_size = (
        device_max_x,
        device_max_y,
    )

    ports = {"N": num_pads_n*num_dev, "S": num_pads_s*num_dev, 
               "E": num_pads_e*num_dev, "W": num_pads_w*num_dev}
    ports = {key:val for key, val in ports.items() if val != 0}

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
        num_devices= len(device),
        device_y=device_y
    )

    if 'N' in ports:
        side = 'N'
    elif 'E' in ports:
        side = 'E'

    for i, ref in enumerate(refs):
        x_offset = BORDER.ports[f"{side}{i*max_x_num+1}"].x 
        if max_x_num > 1:
            x_offset = (x_offset + BORDER.ports[f"{side}{i*max_x_num+max_x_num}"].x)/2
        if side == 'E':
            x_offset -= device[0].pads.probe_tip.pad_length
        ref.movex(x_offset)
        print(port_map_x.items())
        for dev_port, pad_port in port_map_x.items():
            #print(f"{pad_port[0]}{max_x_num*i+pad_port[1]}")
            USER_DEVICES.add_port(port=ref.ports[dev_port], name=f"{pad_port[0]}{max_x_num*i+pad_port[1]}")
        for dev_port, pad_port in port_map_y.items():
            USER_DEVICES.add_port(port=ref.ports[dev_port], name=f"{pad_port[0]}{max_y_num*i+pad_port[1]}")

    ## Route the nanowires and the die

    # hyper tapers
    taper_contact = min(dev_contact_w, device[0].pads.contact_w/2)
    HT, dev_ports = utility.add_hyptap_to_cell(
        BORDER.get_ports(), die_parameters.contact_l, taper_contact, positive_tone=die_parameters.positive_tone
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
