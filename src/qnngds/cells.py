"""Library of pre-built cells containing text, border marks, and an experiment,
connected to pads for wirebonding."""

from phidl import Device
import phidl.geometry as pg
import phidl.routing as pr
from typing import Tuple, List, Union, Optional
import math

import qnngds.tests as test
import qnngds.devices as device
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
    r"""Creates a cell containing a Van Der Pauw structure between 4 contact
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
        invert=False,
        fill_pad_layer=False,
        text_size=die_parameters.text_size,
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
    r"""Creates a cell containing a resolution test.

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


def nanowires(
    die_parameters: utility.DieParameters = utility.DieParameters(),
    channels_sources_w: List[Tuple[float, float]] = [(0.1, 1), (0.5, 3), (1, 10)],
    outline_dev: Union[int, float] = 0.5,
    device_layer: int = 1,
    text: Union[None, str] = None,
) -> Device:
    """Creates a cell that contains several nanowires of given channel and
    source.

    Parameters:
        die_parameters (DieParameters): the die's parameters.
        channels_sources_w (list of tuple of float): The list of (channel_w,
            source_w) of the nanowires to create.
        outline_dev (int or float): The width of the device's outline.
        device_layer (int or tuple of int): The layer where the device is placed.
        text (str, optional): If None, the text is f"w={channels_w}".

    Returns:
        Device: A device (of size n*m unit cells) containing the nanowires, the
        border of the die (created with die_cell function), and the connections
        between the nanowires and pads.
    """

    if text is None:
        channels_w = [item[0] for item in channels_sources_w]
        text = f"w={channels_w}"
    cell_text = text.replace(" \n", ", ")

    NANOWIRES_DIE = Device(f"CELL.NWIRES({cell_text})")

    DEVICE = Device(f"NWIRES({cell_text})")

    ## Create the NANOWIRES

    NANOWIRES = Device(f"NWIRES({cell_text})")
    nanowires_ref = []
    for i, channel_source_w in enumerate(channels_sources_w):
        nanowire_ref = NANOWIRES << device.nanowire.spot(
            channel_source_w[0], channel_source_w[1]
        )
        nanowires_ref.append(nanowire_ref)
    DEVICE << NANOWIRES

    ## Create the DIE

    # die parameters, checkup conditions
    num_nw = len(channels_sources_w)
    n = math.ceil(
        (2 * (num_nw + 1) * die_parameters.pad_size[0])
        / die_parameters.unit_die_size[0]
    )
    die_contact_w = NANOWIRES.xsize + die_parameters.contact_l
    dev_contact_w = NANOWIRES.xsize
    routes_margin = 4 * die_contact_w
    dev_max_size = (
        2 * num_nw * die_parameters.pad_size[0],
        NANOWIRES.ysize + routes_margin,
    )

    # die, with calculated parameters
    BORDER = utility.die_cell(
        die_parameters=die_parameters,
        n_m_units=(n, 1),
        contact_w=die_contact_w,
        device_max_size=dev_max_size,
        ports={"N": num_nw, "S": num_nw},
        ports_gnd=["S"],
        text=f"NWIRES\n{text}",
    )

    ## Place the nanowires

    for i, nanowire_ref in enumerate(nanowires_ref):
        nanowire_ref.movex(BORDER.ports[f"N{i+1}"].x)
        NANOWIRES.add_port(port=nanowire_ref.ports[1], name=f"N{i+1}")
        NANOWIRES.add_port(port=nanowire_ref.ports[2], name=f"S{i+1}")

    ## Route the nanowires and the die

    # hyper tapers
    HT, dev_ports = utility.add_hyptap_to_cell(
        BORDER.get_ports(), die_parameters.contact_l, dev_contact_w
    )
    DEVICE.ports = dev_ports.ports
    DEVICE << HT

    # routes from nanowires to hyper tapers
    ROUTES = utility.route_to_dev(HT.get_ports(), NANOWIRES.ports)
    DEVICE << ROUTES

    DEVICE.ports = dev_ports.ports
    DEVICE = pg.outline(
        DEVICE, outline_dev, open_ports=2 * outline_dev, layer=device_layer
    )
    DEVICE.name = f"NWIRES({cell_text})"

    NANOWIRES_DIE << DEVICE
    NANOWIRES_DIE << BORDER

    return NANOWIRES_DIE


def ntron(
    die_parameters: utility.DieParameters = utility.DieParameters(),
    choke_w: Union[int, float] = 0.1,
    channel_w: Union[int, float] = 0.5,
    gate_w: Union[None, int, float] = None,
    source_w: Union[None, int, float] = None,
    drain_w: Union[None, int, float] = None,
    choke_shift: Union[None, int, float] = None,
    outline_dev: Union[None, int, float] = 0.5,
    device_layer: int = 1,
    text: Union[None, str] = None,
) -> Device:
    r"""Creates a standardized cell specifically for a single ntron.

    Unless specified, scales the ntron parameters as:
    gate_w = drain_w = source_w = 3 * channel_w
    choke_shift = -3 * channel_w

    Parameters:
        die_parameters (DieParameters): the die's parameters.
        choke_w (int or float): The width of the ntron's choke in µm.
        channel_w (int or float): The width of the ntron's channel in µm.
        gate_w (int or float, optional): If None, gate width is 3 times the channel width.
        source_w (int or float, optional): If None, source width is 3 times the channel width.
        drain_w (int or float, optional): If None, drain width is 3 times the channel width.
        choke_shift (int or float, optional): If None, choke shift is -3 times the channel width.
        outline_dev (int or float): The width of the device's outline.
        device_layer (int or array-like[2]): The layer where the device is placed.
        text (string, optional): If None, the text is f"chk: {choke_w} \\nchnl: {channel_w}".

    Returns:
        Device: A device containing the ntron, the border of the die (created with die_cell function),
        and the connections between the ports.
    """

    ## Create the NTRON

    # sizes the ntron parameters that were not given
    if source_w is None and drain_w is None:
        drain_w = source_w = 3 * channel_w
    elif source_w is None:
        source_w = drain_w
    else:
        drain_w = source_w
    if gate_w is None:
        gate_w = source_w
    if choke_shift is None:
        choke_shift = -3 * channel_w

    NTRON = device.ntron.smooth(
        choke_w, gate_w, channel_w, source_w, drain_w, choke_shift, device_layer
    )
    NTRON = utility.rename_ports_to_compass(NTRON)
    if text is None:
        text = f"chk: {choke_w} \nchnl: {channel_w}"
    cell_text = text.replace(" \n", ", ")
    DIE_NTRON = Device(f"CELL.NTRON({cell_text})")

    DEVICE = Device(f"NTRON({cell_text})")
    DEVICE << NTRON

    ## Create the DIE

    # die parameters, checkup conditions
    die_contact_w = NTRON.ports["N1"].width + die_parameters.contact_l
    routes_margin = 2 * die_contact_w
    dev_min_w = (
        die_contact_w + 3 * die_parameters.outline
    )  # condition imposed by the die parameters (contacts width)
    device_max_w = max(2 * routes_margin + max(NTRON.size), dev_min_w)

    # the die with calculated parameters
    BORDER = utility.die_cell(
        die_parameters=die_parameters,
        contact_w=die_contact_w,
        device_max_size=(device_max_w, device_max_w),
        ports={"N": 1, "W": 1, "S": 1},
        ports_gnd=["S"],
        text=f"NTRON \n{text}",
    )

    # place the ntron
    NTRON.movex(NTRON.ports["N1"].midpoint[0], BORDER.ports["N1"].midpoint[0])

    # Route DIE and NTRON

    # hyper tapers
    dev_contact_w = NTRON.ports["N1"].width
    HT, device_ports = utility.add_hyptap_to_cell(
        BORDER.get_ports(), die_parameters.contact_l, dev_contact_w, device_layer
    )
    DEVICE << HT
    DEVICE.ports = device_ports.ports
    # routes
    ROUTES = utility.route_to_dev(HT.get_ports(), NTRON.ports, device_layer)
    DEVICE << ROUTES

    DEVICE = pg.outline(DEVICE, outline_dev, precision=0.000001, open_ports=outline_dev)
    DEVICE = pg.union(DEVICE, layer=device_layer)
    DEVICE.name = f"NTRON({cell_text})"

    DIE_NTRON << DEVICE
    DIE_NTRON << BORDER

    return DIE_NTRON


def snspds(
    die_parameters: utility.DieParameters = utility.DieParameters(),
    snspds_width_pitch: List[Tuple[float, float]] = [
        (0.1, 0.3),
        (0.2, 0.6),
        (0.3, 0.9),
    ],
    snspd_size: Tuple[Union[int, float], Union[int, float]] = tuple(
        round(x / 3)
        for x in utility.DieParameters().calculate_available_space_for_dev()
    ),
    snspd_num_squares: Optional[int] = None,
    outline_dev: Union[int, float] = 0.5,
    device_layer: int = 1,
    text: Union[None, str] = None,
) -> Device:
    """Creates a cell that contains vertical superconducting nanowire single-
    photon detectors (SNSPD).

    Parameters:
        die_parameters (DieParameters): the die's parameters.
        snspds_width_pitch (list of tuple of float): list of (width, pitch) of
            the nanowires. For creating n SNSPD, the list of snspds_width_pitch
            should have a size of n.
        snspd_size (tuple of int or float): Size of the detectors in squares (width, height).
        snspd_num_squares (Optional[int]): Number of squares in the detectors.
        outline_dev (int or float): The width of the device's outline.
        device_layer (int or array-like[2]): The layer where the device is placed.
        text (string, optional): If None, the text is f"w={snspds_width}".

    Returns:
        Device: A cell (of size n*m unit die_cells) containing the SNSPDs.
    """
    if text is None:
        snspds_width = [item[0] for item in snspds_width_pitch]
        text = f"w={snspds_width}"
    cell_text = text.replace(" \n", ", ")

    SNSPD_CELL = Device(f"CELL.SNSPD({cell_text})")
    DEVICE = Device(f"SNSPD({cell_text})")

    # create SNSPD, make its ports compass, add safe optimal step
    snspds_ref = []
    for i, snspd_width_pitch in enumerate(snspds_width_pitch):
        SNSPD = device.snspd.vertical(
            wire_width=snspd_width_pitch[0],
            wire_pitch=snspd_width_pitch[1],
            size=snspd_size,
            num_squares=snspd_num_squares,
            layer=device_layer,
        )
        SNSPD = utility.rename_ports_to_compass(SNSPD)
        SNSPD = utility.add_optimalstep_to_dev(SNSPD, ratio=10)
        snspd_ref = DEVICE << SNSPD
        snspds_ref.append(snspd_ref)

    # create die
    num_snspds = len(snspds_width_pitch)
    die_contact_w = die_parameters.calculate_contact_w(
        circuit_ports=DEVICE.get_ports(depth=1)
    )
    device_max_y = DEVICE.ysize + 2 * die_parameters.contact_l
    device_max_x = num_snspds * max(
        die_parameters.pad_size[0] * 1.5, DEVICE.xsize + 2 * die_parameters.outline
    )
    device_max_size = (device_max_x, device_max_y)

    n, m = die_parameters.find_num_diecells_for_dev(
        device_max_size,
        {"N": num_snspds, "S": num_snspds},
    )

    BORDER = utility.die_cell(
        die_parameters=die_parameters,
        n_m_units=(n, m),
        contact_w=die_contact_w,
        device_max_size=device_max_size,
        ports={"N": num_snspds, "S": num_snspds},
        ports_gnd=["S"],
        text=f"SNSPD \n{text}",
    )

    # align SNSPDs to the die's ports
    for i, ref in enumerate(snspds_ref):
        ref.movex(0, BORDER.ports[f"N{i+1}"].x)
    DEVICE = utility.rename_ports_to_compass(DEVICE, depth=1)
    snspds_ports = DEVICE.ports

    # add hyper tapers at die pads
    dev_contact_w = max([port.width for port in DEVICE.get_ports()])
    HT, dev_ports = utility.add_hyptap_to_cell(
        BORDER.get_ports(), die_parameters.contact_l, dev_contact_w, device_layer
    )
    DEVICE.ports = dev_ports.ports
    DEVICE << HT

    # link hyper tapers to the device
    ROUTES = utility.route_to_dev(HT.get_ports(), snspds_ports)
    DEVICE << ROUTES

    DEVICE = pg.outline(
        DEVICE, outline_dev, open_ports=2 * outline_dev, layer=device_layer
    )
    DEVICE.name = f"SNSPD({cell_text})"

    SNSPD_CELL << DEVICE
    SNSPD_CELL << BORDER
    return SNSPD_CELL


def snspd_ntron(
    die_parameters: utility.DieParameters = utility.DieParameters(),
    w_choke: Union[int, float] = 0.1,
    w_snspd: Union[int, float] = None,
    outline_dev: Union[int, float] = 0.5,
    device_layer: int = 1,
    text: Union[None, str] = None,
) -> Device:
    """Creates a cell that contains an SNSPD coupled to an NTRON. The device's
    parameters are sized according to the SNSPD's width and the NTRON's choke.

    Parameters:
        die_parameters (DieParameters): the die's parameters.
        w_choke (int or float): The width of the NTRON choke in µm.
        w_snspd (int or float, optional): The width of the SNSPD nanowire in µm (if None, scaled to 5 * w_choke).
        outline_dev (int or float): The width of the device's outline.
        device_layer (int or array-like[2]): The layer where the device is placed.
        text (string, optional): If None, the text is f"w={w_snspd}, {w_choke}".

    Returns:
        Device: A cell containing a die in die_layer, pads in pad layer,
        and an SNSPD-NTRON properly routed in the device layer.
    """

    # Create SNSPD-NTRON
    if w_snspd is None:
        w_snspd = 5 * w_choke

    if text is None:
        text = f"w={w_snspd}, {w_choke}"
    cell_text = text.replace(" \n", ", ")

    DIE_SNSPD_NTRON = Device(f"CELL.SNSPD-NTRON({cell_text})")
    DEVICE = Device(f"SNSPD-NTRON({cell_text})")

    SNSPD_NTRON = circuit.snspd_ntron(
        w_snspd=w_snspd,
        pitch_snspd=3 * w_snspd,
        size_snspd=(30 * w_snspd, 30 * w_snspd),
        w_inductor=3 * w_snspd,
        pitch_inductor=6 * w_snspd,
        k_inductor13=20 * w_snspd,
        k_inductor2=8 * w_snspd,
        w_choke=w_choke,
        w_channel=6 * w_choke,
        w_pad=10 * w_snspd,
        layer=device_layer,
    )
    DEVICE << SNSPD_NTRON

    # Create DIE

    die_contact_w = min(
        10 * SNSPD_NTRON.ports["N1"].width + die_parameters.contact_l,
        0.5 * die_parameters.pad_size[0],
    )

    routes_margin = 2 * die_contact_w
    margin = 2 * (die_parameters.pad_size[1] + die_parameters.outline + routes_margin)
    n = max(
        2, math.ceil((SNSPD_NTRON.xsize + margin) / die_parameters.unit_die_size[0])
    )
    m = max(
        1, math.ceil((SNSPD_NTRON.ysize + margin) / die_parameters.unit_die_size[1])
    )

    dev_min_size = [
        (die_contact_w + 3 * die_parameters.outline) * x for x in (5, 3)
    ]  # condition imposed by the die parameters (contacts width)
    device_max_size = (
        max(
            min(
                n * die_parameters.unit_die_size[0] - margin,
                8 * routes_margin + SNSPD_NTRON.size[0],
            ),
            dev_min_size[0],
        ),
        max(
            min(
                m * die_parameters.unit_die_size[1] - margin,
                2 * routes_margin + SNSPD_NTRON.size[1],
            ),
            dev_min_size[1],
        ),
    )

    BORDER = utility.die_cell(
        die_parameters=die_parameters,
        n_m_units=(n, m),
        device_max_size=device_max_size,
        contact_w=die_contact_w,
        ports={"N": 3, "E": 1, "W": 1, "S": 2},
        ports_gnd=["S"],
        text=f"SNSPD-NTRON\n{text}",
    )

    # Route DIE and SNSPD-NTRON

    # hyper tapers
    dev_contact_w = min(4 * SNSPD_NTRON.ports["N1"].width, 0.8 * die_contact_w)
    HT, device_ports = utility.add_hyptap_to_cell(
        BORDER.get_ports(), die_parameters.contact_l, dev_contact_w, device_layer
    )
    DEVICE << HT
    DEVICE.ports = device_ports.ports

    # routes
    ROUTES = utility.route_to_dev(HT.get_ports(), SNSPD_NTRON.ports, device_layer)
    DEVICE << ROUTES

    DEVICE = pg.outline(DEVICE, outline_dev, precision=0.000001, open_ports=outline_dev)
    DEVICE = pg.union(DEVICE, layer=device_layer)
    DEVICE.name = f"SNSPD-NTRON({cell_text})"

    DIE_SNSPD_NTRON << DEVICE
    DIE_SNSPD_NTRON << BORDER

    return DIE_SNSPD_NTRON
