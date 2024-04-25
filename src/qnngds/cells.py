"""Library of pre-built cells containing text, border marks, and an experiment,
connected to pads for wirebonding."""

from phidl import Device
import phidl.geometry as pg
import phidl.routing as pr
from typing import Tuple, List, Union
import math

import qnngds.tests as test
import qnngds.devices as device
import qnngds.circuits as circuit
import qnngds.utilities as utility
import qnngds._default_param as dflt

# basics


def alignment(
    die_w: Union[int, float] = dflt.die_w,
    layers_to_align: List[int] = [dflt.layers["die"], dflt.layers["pad"]],
    outline_die: Union[int, float] = dflt.die_outline,
    die_layer: int = dflt.layers["die"],
    text: Union[None, str] = dflt.text,
) -> Device:
    """Creates alignment marks in an integer number of unit cells.

    Parameters:
        die_w (int or float): Width of a unit die/cell in the design (the output device will be an integer number of unit cells).
        layers_to_align (list of int): Layers to align.
        outline_die (int or float): The width of the die's outline.
        die_layer (int): The layer where the die is placed.
        text (str): Text to be displayed.

    Returns:
        DIE_ALIGN (Device): A device that centers the alignment marks in an n*m unit cell.
    """

    if text is None:
        text = ""
    DIE = Device(f"DIE ALIGN {text} ")

    ALIGN = test.alignment_mark(layers_to_align)

    n = math.ceil((ALIGN.xsize) / die_w)
    m = math.ceil((ALIGN.ysize) / die_w)

    BORDER = utility.die_cell(
        die_size=(n * die_w, m * die_w),
        device_max_size=(ALIGN.xsize + 20, ALIGN.ysize + 20),
        ports={},
        ports_gnd={},
        isolation=outline_die,
        text=f"ALIGN {text}",
        layer=die_layer,
        invert=True,
    )

    DIE << BORDER.flatten()
    DIE << ALIGN

    return DIE


def vdp(
    die_w: Union[int, float] = dflt.die_w,
    pad_size: Tuple[float] = dflt.pad_size,
    layers_to_probe: List[int] = [dflt.layers["die"]],
    layers_to_outline: Union[None, List[int]] = dflt.auto_param,
    outline: Union[int, float] = dflt.die_outline,
    die_layer: Union[int, float] = dflt.layers["die"],
    pad_layer: int = dflt.layers["pad"],
    text: Union[None, str] = dflt.text,
) -> Device:
    r"""Creates a cell containing a Van Der Pauw structure between 4 contact
    pads.

    Parameters:
        die_w (int or float): Width of a unit die/cell in the design (the output device will be an integer number of unit cells).
        pad_size (tuple of int or float): Dimensions of the die's pads (width, height).
        layers_to_probe (list of int): The layers on which to place the VDP structure.
        layers_to_outline (list of int): Among the VDP layers, the ones for which structure must not be filled but outlined.
        outline (int or float): The width of the VDP and die's outline.
        die_layer (int or tuple of int): The layer where the die is placed.
        pad_layer (int or tuple of int): The layer where the pads are placed.
        text (str, optional): If None, the text is f"VDP \n{layers_to_probe}".

    Returns:
        DIE_VANDP (Device): The created device.
    """
    # Initialize parameters left to default (=None)

    if text is None:
        text = str(layers_to_probe)
    if layers_to_outline is None:
        layers_to_outline = [die_layer]  # default layer to outline if None is given

    DIE_VANDP = Device(f"DIE VAN DER PAUW {text} ")

    device_max_w = die_w - 2 * (
        pad_size[1] + 2 * outline
    )  # width of max device size for this cell
    contact_w = device_max_w / 10  # choosing a contact width 10 times smaller
    device_w = (
        device_max_w - 2 * contact_w
    )  # choosing a smaller device to have space for routing from pad to contact

    # Creates the DIE, it contains only the cell text and bordure

    DIE = utility.die_cell(
        die_size=(die_w, die_w),
        device_max_size=(device_max_w, device_max_w),
        ports={},
        ports_gnd=[],
        isolation=outline,
        text=text,
        layer=die_layer,
        pad_layer=pad_layer,
        invert=True,
    )
    DIE_VANDP << DIE

    # Creates the vdp structure, add pads and route

    VDP = Device()

    ## VDP probed area
    AREA = test.vdp(device_w, contact_w)
    VDP << AREA

    ## pads
    PADS = utility.die_cell(
        die_size=(die_w, die_w),
        device_max_size=(device_max_w, device_max_w),
        pad_size=pad_size,
        contact_w=pad_size[0],
        contact_l=0,
        ports={"N": 1, "E": 1, "W": 1, "S": 1},
        ports_gnd=["N", "E", "W", "S"],
        isolation=outline,
        text="PADS ONLY",
        layer=0,
        pad_layer=pad_layer,
        invert=False,
    )
    PADS.remove_layers([pad_layer], invert_selection=True)
    VDP << PADS

    ## routes from pads to probing area
    ROUTES = utility.route_to_dev(PADS.get_ports(), AREA.ports)
    VDP << ROUTES

    VDP.flatten(0)

    # Outline the vdp structure for layers that need to be outlined

    DEVICE = Device("VAN DER PAUW")

    for layer in layers_to_probe:
        TEST_LAY = pg.deepcopy(VDP)
        if layer in layers_to_outline:
            TEST_LAY = pg.outline(TEST_LAY, outline)
        DEVICE << TEST_LAY.flatten(single_layer=layer)

    DIE_VANDP << DEVICE

    # Add pads if they are not in already present
    if pad_layer not in layers_to_probe:
        PADS = pg.union(PADS, layer=pad_layer)
        PADS.name = "PADS"
        DIE_VANDP << PADS

    return DIE_VANDP


def etch_test(
    die_w: Union[int, float] = dflt.die_w,
    layers_to_etch: List[List[int]] = [[dflt.layers["pad"]]],
    outline_die: Union[int, float] = dflt.die_outline,
    die_layer: int = dflt.layers["die"],
    text: Union[None, str] = dflt.text,
) -> Device:
    """Creates etch test structures in an integer number of unit cells.

    These test structures are thought to be used by probing on pads (with a
    simple multimeter) that should be isolated one from another if the etching
    is complete.

    Parameters:
        die_w (int or float): Width of a unit die/cell in the design (the output device will be an integer number of unit cells).
        layers_to_etch (list of list of int): Each element of the list corresponds to one test point, to put on the list of layers specified.
                                               Example: [[1, 2], [1], [2]]
        outline_die (int or float): The width of the die's outline.
        die_layer (int): The layer where the die is placed.
        text (str): Text to be displayed.

    Returns:
        DIE_ETCH_TEST (Device): A device (with size n*m of unit cells) with etch tests in its center.
    """

    if text is None:
        text = f"{layers_to_etch}"
    DIE_ETCH_TEST = Device(f"DIE ETCH TEST {text} ")

    TEST = Device()

    ## Create the probing areas

    margin = 0.12 * die_w
    rect = pg.rectangle((die_w - 2 * margin, die_w - 2 * margin))
    for i, layer_to_etch in enumerate(layers_to_etch):
        probe = Device()
        probe.add_array(rect, 2, 1, (die_w, die_w))
        for layer in layer_to_etch:
            TEST << pg.outline(probe, -outline_die, layer=layer).movey(i * die_w)

    ## Create the die

    n = math.ceil((TEST.xsize + 2 * dflt.die_cell_border) / die_w)
    m = math.ceil((TEST.ysize + 2 * dflt.die_cell_border) / die_w)
    BORDER = utility.die_cell(
        die_size=(n * die_w, m * die_w),
        ports={},
        ports_gnd={},
        text=f"ETCH TEST {text}",
        isolation=10,
        layer=die_layer,
        invert=True,
    )

    BORDER.move(TEST.center)
    DIE_ETCH_TEST << BORDER.flatten()
    DIE_ETCH_TEST << TEST
    DIE_ETCH_TEST.move(DIE_ETCH_TEST.center, (0, 0))

    return DIE_ETCH_TEST


def resolution_test(
    die_w: Union[int, float] = dflt.die_w,
    layer_to_resolve: int = dflt.layers["device"],
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
    outline: Union[int, float] = dflt.die_outline,
    die_layer: int = dflt.layers["die"],
    text: Union[None, str] = dflt.text,
) -> Device:
    r"""Creates a cell containing a resolution test.

    Parameters:
        die_w (int or float): Width of a unit die/cell in the design (the output device will be an integer number of unit cells).
        layer_to_resolve (int): The layer to put the resolution test on.
        resolutions_to_test (list of float): The resolutions to test in µm.
        outline (int or float): The width of the VDP and die's outline.
        die_layer (int or tuple of int): The layer where the die is placed.
        text (str, optional): If None, the text is f"RES TEST \n{layer_to_resolve}".

    Returns:
        DIE_RES_TEST (Device): The created device.
    """

    if text is None:
        text = layer_to_resolve
    DIE_RES_TEST = Device(f"DIE RESOLUTION TEST {text} ")

    ## Create the test structure
    TEST_RES = Device(f"RESOLUTION TEST {text} ")
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
    n = math.ceil((TEST_RES.xsize) / die_w)
    m = math.ceil((TEST_RES.ysize) / die_w)
    BORDER = utility.die_cell(
        die_size=(n * die_w, m * die_w),
        ports={},
        ports_gnd=[],
        text=f"RES TEST \n{text} ",
        isolation=outline,
        layer=die_layer,
        invert=True,
    )

    DIE_RES_TEST << BORDER.flatten()

    return DIE_RES_TEST


## devices:


def nanowires(
    die_w: Union[int, float] = dflt.die_w,
    pad_size: Tuple[float] = dflt.pad_size,
    channels_sources_w: List[Tuple[float, float]] = [(0.1, 1), (0.5, 3), (1, 10)],
    overlap_w: Union[int, float] = dflt.ebeam_overlap,
    outline_die: Union[int, float] = dflt.die_outline,
    outline_dev: Union[int, float] = dflt.device_outline,
    device_layer: int = dflt.layers["device"],
    die_layer: int = dflt.layers["die"],
    pad_layer: int = dflt.layers["pad"],
    text: Union[None, str] = dflt.text,
) -> Device:
    """Creates a cell that contains several nanowires of given channel and
    source.

    Parameters:
        die_w (int or float): Width of a unit die/cell in the design (the output device will be an integer number of unit cells).
        pad_size (tuple of int or float): Dimensions of the die's pads (width, height).
        channels_sources_w (list of tuple of float): The list of (channel_w, source_w) of the nanowires to create.
        overlap_w (int or float): Extra length of the routes above the die's ports to assure alignment with the device
                                   (useful for ebeam lithography).
        outline_die (int or float): The width of the pads outline.
        outline_dev (int or float): The width of the device's outline.
        device_layer (int or tuple of int): The layer where the device is placed.
        die_layer (int or tuple of int): The layer where the die is placed.
        pad_layer (int or tuple of int): The layer where the pads are placed.
        text (str, optional): If None, the text is "NWIRES".

    Returns:
        Device: A device (of size n*m unit cells) containing the nanowires, the
        border of the die (created with die_cell function), and the connections
        between the nanowires and pads.
    """

    if text is None:
        text = ""

    NANOWIRES_DIE = Device(f"DIE NWIRES {text} ")

    DEVICE = Device(f"NWIRES {text} ")

    ## Create the NANOWIRES

    NANOWIRES = Device()
    nanowires_ref = []
    for i, channel_source_w in enumerate(channels_sources_w):
        nanowire_ref = NANOWIRES << device.nanowire.spot(
            channel_source_w[0], channel_source_w[1]
        )
        nanowires_ref.append(nanowire_ref)
    DEVICE << NANOWIRES

    ## Create the DIE

    # die parameters, checkup conditions
    n = len(channels_sources_w)
    die_size = (math.ceil((2 * (n + 1) * pad_size[0]) / die_w) * die_w, die_w)
    die_contact_w = NANOWIRES.xsize + overlap_w
    dev_contact_w = NANOWIRES.xsize
    routes_margin = 4 * die_contact_w
    dev_max_size = (2 * n * pad_size[0], NANOWIRES.ysize + routes_margin)

    # die, with calculated parameters
    BORDER = utility.die_cell(
        die_size=die_size,
        device_max_size=dev_max_size,
        pad_size=pad_size,
        contact_w=die_contact_w,
        contact_l=overlap_w,
        ports={"N": n, "S": n},
        ports_gnd=["S"],
        isolation=outline_die,
        text=f"NWIRES {text}",
        layer=die_layer,
        pad_layer=pad_layer,
        invert=True,
    )

    ## Place the nanowires

    for i, nanowire_ref in enumerate(nanowires_ref):
        nanowire_ref.movex(BORDER.ports[f"N{i+1}"].x)
        NANOWIRES.add_port(port=nanowire_ref.ports[1], name=f"N{i+1}")
        NANOWIRES.add_port(port=nanowire_ref.ports[2], name=f"S{i+1}")

    ## Route the nanowires and the die

    # hyper tapers
    HT, dev_ports = utility.add_hyptap_to_cell(
        BORDER.get_ports(), overlap_w, dev_contact_w
    )
    DEVICE.ports = dev_ports.ports
    DEVICE << HT

    # routes from nanowires to hyper tapers
    ROUTES = utility.route_to_dev(HT.get_ports(), NANOWIRES.ports)
    DEVICE << ROUTES

    DEVICE.ports = dev_ports.ports
    DEVICE = pg.outline(DEVICE, outline_dev, open_ports=2 * outline_dev)
    DEVICE = pg.union(DEVICE, layer=device_layer)
    DEVICE.name = f"NWIRES {text} "

    NANOWIRES_DIE << DEVICE
    NANOWIRES_DIE << BORDER

    NANOWIRES_DIE = pg.union(NANOWIRES_DIE, by_layer=True)
    NANOWIRES_DIE.name = f"DIE NWIRES {text} "
    return NANOWIRES_DIE


def ntron(
    die_w: Union[int, float] = dflt.die_w,
    pad_size: Tuple[float, float] = dflt.pad_size,
    choke_w: Union[int, float] = 0.1,
    channel_w: Union[int, float] = 0.5,
    gate_w: Union[None, int, float] = dflt.auto_param,
    source_w: Union[None, int, float] = dflt.auto_param,
    drain_w: Union[None, int, float] = dflt.auto_param,
    choke_shift: Union[None, int, float] = dflt.auto_param,
    overlap_w: Union[None, int, float] = dflt.ebeam_overlap,
    outline_die: Union[None, int, float] = dflt.die_outline,
    outline_dev: Union[None, int, float] = dflt.device_outline,
    device_layer: int = dflt.layers["device"],
    die_layer: int = dflt.layers["die"],
    pad_layer: int = dflt.layers["pad"],
    text: Union[None, str] = dflt.text,
) -> Device:
    """Creates a standardized cell specifically for a single ntron.

    Unless specified, scales the ntron parameters as:
    gate_w = drain_w = source_w = 3 * channel_w
    choke_shift = -3 * channel_w

    Parameters:
        die_w (int or float): Width of a unit die/cell in the design (the output device will be an integer number of unit cells).
        pad_size (tuple of int or float): Dimensions of the die's pads (width, height).
        choke_w (int or float): The width of the ntron's choke in µm.
        channel_w (int or float): The width of the ntron's channel in µm.
        gate_w (int or float, optional): If None, gate width is 3 times the channel width.
        source_w (int or float, optional): If None, source width is 3 times the channel width.
        drain_w (int or float, optional): If None, drain width is 3 times the channel width.
        choke_shift (int or float, optional): If None, choke shift is -3 times the channel width.
        overlap_w (int or float): Extra length of the routes above the die's ports to assure alignment with the device
                                             (useful for ebeam lithography).
        outline_die (int or float): The width of the pads outline.
        outline_dev (int or float): The width of the device's outline.
        device_layer (int or array-like[2]): The layer where the device is placed.
        die_layer (int or array-like[2]): The layer where the die is placed.
        pad_layer (int or array-like[2]): The layer where the pads are placed.
        text (string, optional): If None, the text is the ntron's choke and channel widths.

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

    NTRON = device.ntron.smooth_compassPorts(
        choke_w, gate_w, channel_w, source_w, drain_w, choke_shift, device_layer
    )

    if text is None:
        text = f"chk: {choke_w} \nchnl: {channel_w}"
    DIE_NTRON = Device(f"DIE NTRON {text} ")

    DEVICE = Device(f"NTRON {text} ")
    DEVICE << NTRON

    ## Create the DIE

    # die parameters, checkup conditions
    die_contact_w = NTRON.ports["N1"].width + overlap_w
    routes_margin = 2 * die_contact_w
    dev_min_w = (
        die_contact_w + 3 * outline_die
    )  # condition imposed by the die parameters (contacts width)
    device_max_w = max(2 * routes_margin + max(NTRON.size), dev_min_w)

    # the die with calculated parameters
    BORDER = utility.die_cell(
        die_size=(die_w, die_w),
        device_max_size=(device_max_w, device_max_w),
        pad_size=pad_size,
        contact_w=die_contact_w,
        contact_l=overlap_w,
        ports={"N": 1, "W": 1, "S": 1},
        ports_gnd=["S"],
        text=text,
        isolation=10,
        layer=die_layer,
        pad_layer=pad_layer,
        invert=True,
    )

    # place the ntron
    NTRON.movex(NTRON.ports["N1"].midpoint[0], BORDER.ports["N1"].midpoint[0])

    # Route DIE and NTRON

    # hyper tapers
    dev_contact_w = NTRON.ports["N1"].width
    HT, device_ports = utility.add_hyptap_to_cell(
        BORDER.get_ports(), overlap_w, dev_contact_w, device_layer
    )
    DEVICE << HT
    DEVICE.ports = device_ports.ports
    # routes
    ROUTES = utility.route_to_dev(HT.get_ports(), NTRON.ports, device_layer)
    DEVICE << ROUTES

    DEVICE = pg.outline(DEVICE, outline_dev, precision=0.000001, open_ports=outline_dev)
    DEVICE = pg.union(DEVICE, layer=device_layer)
    DEVICE.name = f"NTRON {text} "

    DIE_NTRON << DEVICE
    DIE_NTRON << BORDER

    DIE_NTRON = pg.union(DIE_NTRON, by_layer=True)
    DIE_NTRON.name = f"DIE NTRON {text} "
    return DIE_NTRON


def snspd_ntron(
    die_w: Union[int, float] = dflt.die_w,
    pad_size: Tuple[float, float] = dflt.pad_size,
    w_choke: Union[int, float] = 0.1,
    w_snspd: Union[int, float] = dflt.auto_param,
    overlap_w: Union[int, float] = dflt.ebeam_overlap,
    outline_die: Union[int, float] = dflt.die_outline,
    outline_dev: Union[int, float] = dflt.device_outline,
    device_layer: int = dflt.layers["device"],
    die_layer: int = dflt.layers["die"],
    pad_layer: int = dflt.layers["pad"],
    text: Union[None, str] = dflt.text,
) -> Device:
    """Creates a cell that contains an SNSPD coupled to an NTRON. The device's
    parameters are sized according to the SNSPD's width and the NTRON's choke.

    Parameters:
        die_w (int or float): Width of a unit die/cell in the design (the output device will be an integer number of unit cells).
        pad_size (tuple of int or float): Dimensions of the die's pads (width, height).
        w_choke (int or float): The width of the NTRON choke in µm.
        w_snspd (int or float, optional): The width of the SNSPD nanowire in µm (if None, scaled to 5 * w_choke).
        overlap_w (int or float): Extra length of the routes above the die's ports to assure alignment with the device
                                             (useful for ebeam lithography).
        outline_die (int or float): The width of the pads outline.
        outline_dev (int or float): The width of the device's outline.
        device_layer (int or array-like[2]): The layer where the device is placed.
        die_layer (int or array-like[2]): The layer where the die is placed.
        pad_layer (int or array-like[2]): The layer where the pads are placed.
        text (string, optional): If None, text = f'SNSPD {w_choke}'.

    Returns:
        Device: A cell containing a die in die_layer, pads in pad layer,
        and an SNSPD-NTRON properly routed in the device layer.
    """

    # Create SNSPD-NTRON
    if w_snspd is None:
        w_snspd = 5 * w_choke

    if text is None:
        text = f"SNSPD \n{w_snspd} {w_choke} "
    DIE_SNSPD_NTRON = Device(f"DIE {text} ")
    DEVICE = Device(f"{text} ")

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
        10 * SNSPD_NTRON.ports["N1"].width + overlap_w, 0.5 * pad_size[0]
    )

    routes_margin = 2 * die_contact_w
    margin = 2 * (pad_size[1] + outline_die + routes_margin)
    n = max(2, math.ceil((SNSPD_NTRON.xsize + margin) / die_w))
    m = max(1, math.ceil((SNSPD_NTRON.ysize + margin) / die_w))

    dev_min_size = [
        (die_contact_w + 3 * outline_die) * x for x in (5, 3)
    ]  # condition imposed by the die parameters (contacts width)
    device_max_size = (
        max(
            min(n * die_w - margin, 8 * routes_margin + SNSPD_NTRON.size[0]),
            dev_min_size[0],
        ),
        max(
            min(m * die_w - margin, 2 * routes_margin + SNSPD_NTRON.size[1]),
            dev_min_size[1],
        ),
    )

    BORDER = utility.die_cell(
        die_size=(n * die_w, m * die_w),
        device_max_size=device_max_size,
        pad_size=pad_size,
        contact_w=die_contact_w,
        contact_l=overlap_w,
        ports={"N": 3, "E": 1, "W": 1, "S": 2},
        ports_gnd=["S"],
        text=text,
        isolation=outline_die,
        layer=die_layer,
        pad_layer=pad_layer,
        invert=True,
    )

    # Route DIE and SNSPD-NTRON

    # hyper tapers
    dev_contact_w = min(4 * SNSPD_NTRON.ports["N1"].width, 0.8 * die_contact_w)
    HT, device_ports = utility.add_hyptap_to_cell(
        BORDER.get_ports(), overlap_w, dev_contact_w, device_layer
    )
    DEVICE << HT
    DEVICE.ports = device_ports.ports

    # routes
    ROUTES = utility.route_to_dev(HT.get_ports(), SNSPD_NTRON.ports, device_layer)
    DEVICE << ROUTES

    DEVICE = pg.outline(DEVICE, outline_dev, precision=0.000001, open_ports=outline_dev)
    DEVICE = pg.union(DEVICE, layer=device_layer)
    DEVICE.name = f"DIE {text} "

    DIE_SNSPD_NTRON << DEVICE
    DIE_SNSPD_NTRON << BORDER

    DIE_SNSPD_NTRON = pg.union(DIE_SNSPD_NTRON, by_layer=True)
    DIE_SNSPD_NTRON.name = f"SNSPD \n{w_snspd} {w_choke} "

    return DIE_SNSPD_NTRON
