"""Design's module is though for users to be able to access pre-built cells
that are made of circuits, devices or test structures already integrated in a
die cell.

It is a module that is sufficient in itself to build an entire new
design.
"""

from phidl import Device

# from phidl import quickplot as qp
# from phidl import set_quickplot_options
import phidl.geometry as pg
import phidl.routing as pr
from typing import Tuple, List, Union, Optional
import math
import os
import qnngds.geometries as qg
import qnngds.devices as qd
import qnngds.circuits as qc
import qnngds.utilities as qu

Free = True
Occupied = False

auto_param = None
die_cell_border = 80

# default parameters
dflt_chip_w = 10000
dflt_chip_margin = 100
dflt_N_dies = 11
dflt_die_w = 980
dflt_pad_size = (150, 250)
dflt_device_outline = 0.5
dflt_die_outline = 10
dflt_ebeam_overlap = 10
dflt_layers = {"annotation": 0, "device": 1, "die": 2, "pad": 3}
dflt_text = auto_param

## to build a design


def create_chip(
    chip_w: Union[int, float] = dflt_chip_w,
    margin: Union[int, float] = dflt_chip_margin,
    N_dies: int = dflt_N_dies,
    die_w: Union[None, int, float] = auto_param,
    annotations_layer: int = dflt_layers["annotation"],
    unpack_chip_map: bool = True,
    create_devices_map_txt: Union[bool, str] = False,
) -> Union[
    Tuple[Device, Union[int, float], List[List[bool]], str],
    Tuple[Device, Union[int, float], str],
    Tuple[Device, Union[int, float], List[List[bool]]],
    Tuple[Device, Union[int, float]],
]:
    """Creates a chip map in the annotations layer.

    If unpack_chip_map is set to True, creates a map (2D array) to monitor the
    states of each cell of the chip. The user should input N_dies xor die_w.

    Parameters:
        chip_w (int or float): The overall width (in um) of the chip.
        margin (int or float): The width (in um) of the outline of the chip where no device should be placed.
        N_dies (int): Number of dies/units to be placed by row and column.
        die_w (None, int, or float): If specified, the width of each die/unit to be placed by row and column.
        annotations_layer (int or array-like[2]): The layer where to put the device.
        unpack_chip_map (bool): If True, the function returns a map (2D array) of states to be filled later (e.g., with place_on_chip()).
        create_devices_map_txt (bool or string): If True or string, the function creates a txt file that will map the devices.

    Returns:
        Tuple[Device, float, List[List[bool]], str]: A tuple containing from 2 to 4 elements, depending on what needs to be extracted (parameters dependent):

        - **CHIP** (*Device*): The chip map.
        - **die_w** (*float*): The width of each die. (returned if die_w was None)
        - **N_dies** (*float*): The number of dies/units on each row and column. (returned if die_w was not None)
        - **chip_map** (*array-like[N_dies][N_dies] of bool*): A 2D array filled with "Free" (=True) states. (returned if unpack_chip_map is True)
        - **file_name** (*str*): The name of the created devices map text file. (returned if create_devices_map_txt is not False)
    """

    CHIP = Device("CHIP ")
    CHIP.add_polygon(
        [(0, 0), (chip_w, 0), (chip_w, chip_w), (0, chip_w)], layer=annotations_layer
    )

    useful_w = chip_w - margin * 2
    useful_area = CHIP.add_polygon(
        [(0, 0), (useful_w, 0), (useful_w, useful_w), (0, useful_w)],
        layer=annotations_layer,
    )
    useful_area.move((margin, margin))

    if die_w is not None:
        N_dies = useful_w / die_w
        return_N_or_w = N_dies
    else:
        die_w = useful_w / N_dies
        return_N_or_w = die_w
    CELL = pg.rectangle([die_w, die_w], layer=annotations_layer)
    array = CHIP.add_array(CELL, columns=N_dies, rows=N_dies, spacing=(die_w, die_w))
    array.move((0, 0), (margin, margin))

    CHIP.flatten()
    CHIP.move((margin, margin), (0, 0))

    if create_devices_map_txt:
        ## create a devices map ...
        if create_devices_map_txt == True:
            file_name = "devices map"
        else:
            file_name = f"{create_devices_map_txt}"

        # check that file does not already exist, in which case it will add a int to its name:
        i = 0
        file_to_find = file_name
        while True:
            if i != 0:
                file_to_find = file_name + f"({i})"
            file_already_exists = os.path.exists(f"{file_to_find}.txt")
            i += 1
            if not file_already_exists:
                file_name = file_to_find
                break
        with open(f"{file_name}.txt", "a") as file:
            file.write("Devices placed on the chip: \n\n")
            file.write("(row, col) : device.name\n\n")

        ## ... and return the devices map filename in the outputs
        if unpack_chip_map:
            chip_map = [[Free for _ in range(N_dies)] for _ in range(N_dies)]
            return CHIP, return_N_or_w, chip_map, file_name
        else:
            return CHIP, return_N_or_w, file_name
    else:
        if unpack_chip_map:
            chip_map = [[Free for _ in range(N_dies)] for _ in range(N_dies)]
            return CHIP, return_N_or_w, chip_map
        else:
            return CHIP, return_N_or_w


def place_on_chip(
    cell: Device,
    coordinates: Tuple[int, int],
    chip_map: List[List[bool]],
    die_w: Union[int, float],
    devices_map_txt: Union[None, str] = None,
) -> bool:
    """Moves the chip to the coordinates specified.

    Update the chip map with Occupied states where the device has been placed.

    NB: The cell is aligned from its bottom left corner to the coordinates.

    Parameters:
        cell (Device): Device to be moved.
        coordinates (tuple of int): (i, j) indices of the chip grid, where to place the cell.
            Note that the indices start at 0.
        chip_map (2D array): The 2D array mapping the free cells in the chip map.
        die_w (int or float): The width of a die/unit in the chip map.
        devices_map_txt (str or None): Name of the devices map text file to write placement information.
            If None, no file will be written.

    Returns:
        bool: False, if the Device falls out of the chip map, prints an error
        message and does not place the device. True, otherwise.

    Raises:
        Warning: Prints a warning if the Device is overlapping with already occupied coordinates.
    """

    # update the chip's availabilities
    n_cell = round(cell.xsize / die_w)
    m_cell = round(cell.ysize / die_w)
    for n in range(n_cell):
        for m in range(m_cell):
            try:
                if chip_map[coordinates[1] + m][coordinates[0] + n] == Occupied:
                    print(
                        f"Warning, placing Device {cell.name} "
                        + f"in an occupied state ({coordinates[1]+m}, {coordinates[0]+n})"
                    )
                else:
                    chip_map[coordinates[1] + m][coordinates[0] + n] = Occupied
            except IndexError:
                print(
                    f"Error, Device {cell.name} "
                    + f"falls out of the chip map ({coordinates[1]+m}, {coordinates[0]+n})"
                )
                return False

    # move the cell
    cell_bottom_left = cell.get_bounding_box()[0]
    cell.move(cell_bottom_left, (coordinates[0] * die_w, coordinates[1] * die_w))

    # write the cell's place on the devices map text file
    if devices_map_txt is not None:
        with open(f"{devices_map_txt}.txt", "a") as file:
            try:
                name = cell.name.replace("\n", "")
            except AttributeError:
                name = "unnamed"
            file.write(f"({coordinates[0]}, {coordinates[1]}) : {name}\n")

    return True


def place_remaining_devices(
    devices_to_place: List[Device],
    chip_map: List[List[bool]],
    die_w: Union[int, float],
    write_devices_map_txt: Union[bool, str] = False,
) -> Optional[None]:
    """Go through the chip map and place the devices given, where the chip map
    is Free.

    Parameters:
        devices_to_place (list of Device objects): The devices to be placed.
        chip_map (2D array): The 2D array mapping the free cells in the chip map.
        die_w (int or float): The width of a die/unit in the chip map.
        write_devices_map_txt (bool or str): If True, write a .txt file mapping the devices that were placed.
            If str, specifies the filename of the .txt file.

    Note:
        The list of devices is not re-ordered to fit as many of them as possible.
        Some edges of the chip may remain empty because the list contained 2-units long devices (for e.g.).
    """

    # name and create the file if no file was given
    if write_devices_map_txt == True:

        file_name = "remaining_cells_map"
        with open(f"{file_name}.txt", "a") as file:
            file.write("Remaining devices placed on the chip:\n\n")
            file.write("(row, col) : device.name\n\n")
    # use the file's name is a file was given
    elif write_devices_map_txt:
        file_name = write_devices_map_txt
    # pass false if no txt file should be created
    else:
        file_name = None

    for row_i, row in enumerate(chip_map):
        for col_i, status in enumerate(row):
            if status == Free and devices_to_place:
                if place_on_chip(
                    devices_to_place[0], (col_i, row_i), chip_map, die_w, file_name
                ):
                    devices_to_place.pop(0)

    if devices_to_place:
        print(
            "Some devices are still to be placed, " + "no place remaining on the chip."
        )


## basics:


def create_alignment_cell(
    die_w: Union[int, float] = dflt_die_w,
    layers_to_align: List[int] = [dflt_layers["die"], dflt_layers["pad"]],
    outline_die: Union[int, float] = dflt_die_outline,
    die_layer: int = dflt_layers["die"],
    text: Union[None, str] = dflt_text,
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

    ALIGN = qg.alignment_mark(layers_to_align)

    n = math.ceil((ALIGN.xsize) / die_w)
    m = math.ceil((ALIGN.ysize) / die_w)

    BORDER = qu.die_cell(
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


def create_vdp_cell(
    die_w: Union[int, float] = dflt_die_w,
    pad_size: Tuple[float] = dflt_pad_size,
    layers_to_probe: List[int] = [dflt_layers["pad"]],
    layers_to_outline: Union[None, List[int]] = auto_param,
    outline: Union[int, float] = dflt_die_outline,
    die_layer: Union[int, float] = dflt_layers["die"],
    pad_layer: int = dflt_layers["pad"],
    text: Union[None, str] = dflt_text,
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

    if text is None:
        text = layers_to_probe
    DIE_VANDP = Device(f"DIE VAN DER PAUW {text} ")

    ## Create the die
    w = die_w - 2 * (pad_size[1] + 2 * outline)  # width of max device size
    BORDER = qu.die_cell(
        die_size=(die_w, die_w),
        device_max_size=(w, w),
        pad_size=pad_size,
        contact_w=pad_size[0],
        contact_l=0,
        ports={"N": 1, "E": 1, "W": 1, "S": 1},
        ports_gnd=["N", "E", "W", "S"],
        text=f"VDP \n{text} ",
        isolation=outline,
        layer=die_layer,
        pad_layer=pad_layer,
        invert=True,
    )
    PADS = pg.deepcopy(BORDER)
    PADS = PADS.remove_layers([pad_layer], invert_selection=True)

    DIE_VANDP << BORDER.flatten()

    ## Create the test structure
    DEVICE = Device()

    # the test structure is an hexagonal shape between the die's ports
    TEST = Device()
    TEST << PADS
    rect = TEST << pg.straight((PADS.ports["E1"].x - PADS.ports["W1"].x, pad_size[0]))
    rect.move(rect.center, (0, 0))
    TEST << pr.route_quad(PADS.ports["N1"], rect.ports[1])
    TEST << pr.route_quad(PADS.ports["S1"], rect.ports[2])
    TEST = pg.union(TEST)

    # outline the test structure for layers that need to be outlined

    if layers_to_outline is None:
        layers_to_outline = [die_layer]
    for layer in layers_to_probe:
        TEST_LAY = pg.deepcopy(TEST)
        if layer in layers_to_outline:
            TEST_LAY = pg.outline(TEST_LAY, outline)
        DEVICE << TEST_LAY.flatten(single_layer=layer)

    DIE_VANDP << DEVICE

    DIE_VANDP = pg.union(DIE_VANDP, by_layer=True)
    DIE_VANDP.name = f"DIE VAN DER PAUW {text} "
    return DIE_VANDP


def create_etch_test_cell(
    die_w: Union[int, float] = dflt_die_w,
    layers_to_etch: List[List[int]] = [[dflt_layers["pad"]]],
    outline_die: Union[int, float] = dflt_die_outline,
    die_layer: int = dflt_layers["die"],
    text: Union[None, str] = dflt_text,
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

    n = math.ceil((TEST.xsize + 2 * die_cell_border) / die_w)
    m = math.ceil((TEST.ysize + 2 * die_cell_border) / die_w)
    BORDER = qu.die_cell(
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


def create_resolution_test_cell(
    die_w: Union[int, float] = dflt_die_w,
    layer_to_resolve: int = dflt_layers["device"],
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
    outline: Union[int, float] = dflt_die_outline,
    die_layer: int = dflt_layers["die"],
    text: Union[None, str] = dflt_text,
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
    test_res = TEST_RES << qg.resolution_test(
        resolutions=resolutions_to_test, inverted=False, layer=layer_to_resolve
    )
    test_res_invert = TEST_RES << qg.resolution_test(
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
    BORDER = qu.die_cell(
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


def create_nanowires_cell(
    die_w: Union[int, float] = dflt_die_w,
    pad_size: Tuple[float] = dflt_pad_size,
    channels_sources_w: List[Tuple[float, float]] = [(0.1, 1), (0.5, 3), (1, 10)],
    overlap_w: Union[int, float] = dflt_ebeam_overlap,
    outline_die: Union[int, float] = dflt_die_outline,
    outline_dev: Union[int, float] = dflt_device_outline,
    device_layer: int = dflt_layers["device"],
    die_layer: int = dflt_layers["die"],
    pad_layer: int = dflt_layers["pad"],
    text: Union[None, str] = dflt_text,
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
        nanowire_ref = NANOWIRES << qd.nanowire(
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
    BORDER = qu.die_cell(
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
    HT, dev_ports = qu.add_hyptap_to_cell(BORDER.get_ports(), overlap_w, dev_contact_w)
    DEVICE.ports = dev_ports.ports
    DEVICE << HT

    # routes from nanowires to hyper tapers
    ROUTES = qu.route_to_dev(HT.get_ports(), NANOWIRES.ports)
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


def create_ntron_cell(
    die_w: Union[int, float] = dflt_die_w,
    pad_size: Tuple[float, float] = dflt_pad_size,
    choke_w: Union[int, float] = 0.1,
    channel_w: Union[int, float] = 0.5,
    gate_w: Union[None, int, float] = auto_param,
    source_w: Union[None, int, float] = auto_param,
    drain_w: Union[None, int, float] = auto_param,
    choke_shift: Union[None, int, float] = auto_param,
    overlap_w: Union[None, int, float] = dflt_ebeam_overlap,
    outline_die: Union[None, int, float] = dflt_die_outline,
    outline_dev: Union[None, int, float] = dflt_device_outline,
    device_layer: int = dflt_layers["device"],
    die_layer: int = dflt_layers["die"],
    pad_layer: int = dflt_layers["pad"],
    text: Union[None, str] = dflt_text,
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

    NTRON = qd.ntron_compassPorts(
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
    BORDER = qu.die_cell(
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
    HT, device_ports = qu.add_hyptap_to_cell(
        BORDER.get_ports(), overlap_w, dev_contact_w, device_layer
    )
    DEVICE << HT
    DEVICE.ports = device_ports.ports
    # routes
    ROUTES = qu.route_to_dev(HT.get_ports(), NTRON.ports, device_layer)
    DEVICE << ROUTES

    DEVICE = pg.outline(DEVICE, outline_dev, precision=0.000001, open_ports=outline_dev)
    DEVICE = pg.union(DEVICE, layer=device_layer)
    DEVICE.name = f"NTRON {text} "

    DIE_NTRON << DEVICE
    DIE_NTRON << BORDER

    DIE_NTRON = pg.union(DIE_NTRON, by_layer=True)
    DIE_NTRON.name = f"DIE NTRON {text} "
    return DIE_NTRON


def create_snspd_ntron_cell(
    die_w: Union[int, float] = dflt_die_w,
    pad_size: Tuple[float, float] = dflt_pad_size,
    w_choke: Union[int, float] = 0.1,
    w_snspd: Union[int, float] = auto_param,
    overlap_w: Union[int, float] = dflt_ebeam_overlap,
    outline_die: Union[int, float] = dflt_die_outline,
    outline_dev: Union[int, float] = dflt_device_outline,
    device_layer: int = dflt_layers["device"],
    die_layer: int = dflt_layers["die"],
    pad_layer: int = dflt_layers["pad"],
    text: Union[None, str] = dflt_text,
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

    SNSPD_NTRON = qc.snspd_ntron(
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

    BORDER = qu.die_cell(
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
    HT, device_ports = qu.add_hyptap_to_cell(
        BORDER.get_ports(), overlap_w, dev_contact_w, device_layer
    )
    DEVICE << HT
    DEVICE.ports = device_ports.ports

    # routes
    ROUTES = qu.route_to_dev(HT.get_ports(), SNSPD_NTRON.ports, device_layer)
    DEVICE << ROUTES

    DEVICE = pg.outline(DEVICE, outline_dev, precision=0.000001, open_ports=outline_dev)
    DEVICE = pg.union(DEVICE, layer=device_layer)
    DEVICE.name = f"DIE {text} "

    DIE_SNSPD_NTRON << DEVICE
    DIE_SNSPD_NTRON << BORDER

    DIE_SNSPD_NTRON = pg.union(DIE_SNSPD_NTRON, by_layer=True)
    DIE_SNSPD_NTRON.name = f"SNSPD \n{w_snspd} {w_choke} "

    return DIE_SNSPD_NTRON


class Design:
    """A class for a design on a single layer of superconducting material, and
    additional contact pads.

    It is though for a process like:

    - exposing the superconductiong material using e-beam lithography. Two
      exposures at low and high currents are possible by distinguishing two
      layers: device layer and die layer. Equivalently, the shapes outlines
      (though for positive tone resist) have two different widths for the device
      and die layers.
    - exposing the pads layer using photolithography.

    Args:
        name (str): The name of the design.
        chip_w (int or float): The overall width of the chip.
        chip_margin (int or float): The width of the outline of the chip where
            no device should be placed.
        N_dies (int): Number of dies/units to be placed by row and column.
        die_w (int or float, optional): Width of a unit die/cell in the design
            (the output device will be an integer number of unit cells).
        pad_size (tuple of int or float): Dimensions of the die's pads (width, height).
        device_outline (int or float): The width of the device's outline.
        die_outline (int or float): The width of the pads outline.
        ebeam_overlap (int or float): Extra length of the routes above the die's
            ports to assure alignment with the device (useful for ebeam
            lithography).
        annotation_layer (int): The layer where to put the annotations.
        device_layer (int or array-like[2]): The layer where the device is placed.
        die_layer (int or array-like[2]): The layer where the die is placed.
        pad_layer (int or array-like[2]): The layer where the pads are placed.

    Example:
        Here is an example of how to create the class.

        >>> # Choose some design parameters, let the others to default
        >>> chip_w = 10000
        >>> N_dies = 11
        >>> device_outline = 0.3
        >>> die_outline = 10

        >>> # Create the design and initialize the chip
        >>> demo_project = Design(name="demo design",
        >>>                       chip_w=chip_w,
        >>>                       N_dies=N_dies,
        >>>                       device_outline=device_outline,
        >>>                       die_outline=die_outline)
        >>> demo_project.create_chip()

        >>> # Quickplot the chip skeletton!
        >>> qp(demo_project.CHIP)
    """

    def __init__(
        self,
        name="new_design",
        chip_w=dflt_chip_w,
        chip_margin=dflt_chip_margin,
        N_dies=dflt_N_dies,
        die_w=auto_param,
        pad_size=dflt_pad_size,
        device_outline=dflt_device_outline,
        die_outline=dflt_die_outline,
        ebeam_overlap=dflt_ebeam_overlap,
        annotation_layer=dflt_layers["annotation"],
        device_layer=dflt_layers["device"],
        die_layer=dflt_layers["die"],
        pad_layer=dflt_layers["pad"],
    ):
        """
        Args:
            name (str): The name of the design.
            chip_w (int or float): The overall width of the chip.
            chip_margin (int or float): The width of the outline of the chip where no device should be placed.
            N_dies (int): Number of dies/units to be placed by row and column.
            die_w (int or float, optional): Width of a unit die/cell in the design (the output device will be an integer number of unit cells).
            pad_size (tuple of int or float): Dimensions of the die's pads (width, height).
            device_outline (int or float): The width of the device's outline.
            die_outline (int or float): The width of the pads outline.
            ebeam_overlap (int or float): Extra length of the routes above the die's ports to assure alignment with the device (useful for ebeam lithography).
            annotation_layer (int): The layer where to put the annotations.
            device_layer (int or array-like[2]): The layer where the device is placed.
            die_layer (int or array-like[2]): The layer where the die is placed.
            pad_layer (int or array-like[2]): The layer where the pads are placed.
        """

        self.name = name

        self.chip_w = chip_w
        self.chip_margin = chip_margin
        self.N_dies = N_dies
        self.die_w = die_w

        self.pad_size = pad_size
        self.device_outline = device_outline
        self.die_outline = die_outline
        self.ebeam_overlap = ebeam_overlap

        self.layers = {
            "annotation": annotation_layer,
            "device": device_layer,
            "die": die_layer,
            "pad": pad_layer,
        }

    # help building a design

    def create_chip(self, create_devices_map_txt: Union[bool, str] = True) -> Device:
        """Creates the chip, with unit cells.

        The CHIP created will be the foundation of the design, the Device to add
        all references to. The function creates a chip_map (2D array) to help placing
        the cells on the chip (aligned with the unit cells). The function also generates
        a txt file if create_devices_map_txt is True to follow the devices placements
        on the chip.

        Parameters:
            create_devices_map_txt (bool or str): If True, generates a text file
                to follow the devices placements on the chip. If string, the text file
                is named after the string.

        Returns:
            CHIP (Device): The chip map, in the annotations layer
        """
        if create_devices_map_txt:
            if create_devices_map_txt == True:
                create_devices_map_txt = f"{self.name} devices map"
            else:
                create_devices_map_txt = f"{create_devices_map_txt}"
            self.CHIP, N_or_w, self.chip_map, self.devices_map_txt = create_chip(
                chip_w=self.chip_w,
                margin=self.chip_margin,
                N_dies=self.N_dies,
                die_w=self.die_w,
                annotations_layer=self.layers["annotation"],
                unpack_chip_map=True,
                create_devices_map_txt=create_devices_map_txt,
            )
        else:
            self.devices_map_txt = None
            create_devices_map_txt = False
            self.CHIP, N_or_w, self.chip_map = create_chip(
                chip_w=self.chip_w,
                margin=self.chip_margin,
                N_dies=self.N_dies,
                die_w=self.die_w,
                annotations_layer=self.layers["annotation"],
                unpack_chip_map=True,
                create_devices_map_txt=create_devices_map_txt,
            )

        if self.die_w is not None:
            self.N_dies = N_or_w
        else:
            self.die_w = N_or_w

        return self.CHIP

    def place_on_chip(
        self, cell: Device, coordinates: Tuple[int, int], add_to_chip: bool = True
    ) -> bool:
        """Moves the chip to the coordinates specified. Update the chip map
        with Occupied states where the device has been placed.

        NB: the cell is aligned from its bottom left corner to the coordinates.

        Parameters:
            cell (Device): Device to be moved.
            coordinates (tuple of int): (i, j) indices of the chip grid, where to place the cell.
                Note that the indices start at 0.

        Returns:
            bool: False, if the Device falls out of the chip map, prints an error message and does not place the device. True, otherwise.

        Raises:
            Warning: Prints a warning if the Device is overlapping with already occupied coordinates.

        Examples:
            Here is an example of placing alignment cells on two given positions of the chip.

            >>> align_left  = demo_project.create_alignment_cell(layers_to_align=[2, 3])
            >>> align_right = demo_project.create_alignment_cell(layers_to_align=[2, 3])
            >>> demo_project.place_on_chip(cell=align_left,  coordinates=(0, 5))
            >>> demo_project.place_on_chip(cell=align_right, coordinates=(10, 5))
        """

        if add_to_chip:
            self.CHIP << cell
        return place_on_chip(
            cell=cell,
            coordinates=coordinates,
            chip_map=self.chip_map,
            die_w=self.die_w,
            devices_map_txt=self.devices_map_txt,
        )

    def place_remaining_devices(
        self,
        devices_to_place: List[Device],
        add_to_chip: bool = True,
        write_remaining_devices_map_txt: Union[bool, str] = False,
    ) -> Optional[None]:
        """Go through the chip map and place the devices given, where the chip
        map is Free.

        Parameters:
            devices_to_place (list of Device objects): The devices to be placed.
            add_to_chip (bool): Add the devices provided to the Design's CHIP.
            write_remaining_devices_map_txt (bool or string): If True, write a .txt
                file mapping the devices that were placed. If string, the filename is
                the given string, except if a file has already been created.

        Note:
            The list of devices is not re-ordered to fit as many of them as possible.
            Some edges of the chip may remain empty because the list contained 2-units long devices (for e.g.).

        Examples:
            Here is a typical example of why this function is useful and how to
            use it. If design is a Design class initalized, and the
            create_chip() function has previously been executed.

            >>> channels_w = [0.5, 0.75, 1, 1.25, 1.5]
            >>> ntrons_to_place = []
            >>> for channel_w in channels_w:
            >>>     ntron = design.create_ntron_cell(choke_w=0.05, channel_w=channel_w)
            >>>     ntrons_to_place.append(ntron)
            >>> design.place_remaining_cells(ntrons_to_place)
        """
        if self.devices_map_txt is not None:
            # the decision taken when creating the chip overwrites this one
            write_devices_map_txt = self.devices_map_txt
        else:
            # a devices map can still be created, as decided when calling this function
            write_devices_map_txt = write_remaining_devices_map_txt

        if add_to_chip:
            self.CHIP << devices_to_place
        place_remaining_devices(
            devices_to_place=devices_to_place,
            chip_map=self.chip_map,
            die_w=self.die_w,
            write_devices_map_txt=write_devices_map_txt,
        )

    def write_gds(self, text: Union[None, str] = dflt_text) -> Union[None, str]:
        """Write a GDS file.

        Args:
            text (str or None): The filename for the GDS file.
                If None, the name of the Design will be used.

        Returns:
            str or None: The filename of the written GDS file, or None if no file was written.
        """
        if text is None:
            text = self.name
        return self.CHIP.write_gds(filename=f"{text}.gds")

    # basics:

    def create_alignment_cell(
        self, layers_to_align: List[int], text: Union[None, str] = dflt_text
    ) -> Device:
        """Creates alignment marks in an integer number of unit cells.

        Parameters:
            layers_to_align (List[int]): Layers to align.
            text (str): The text of the cell is f"ALIGN {text}".

        Returns:
            Device: A device that centers the alignment marks in an n*m unit cell.
        """
        return create_alignment_cell(
            die_w=self.die_w,
            layers_to_align=layers_to_align,
            outline_die=self.die_outline,
            die_layer=self.layers["die"],
            text=text,
        )

    def create_vdp_cell(
        self,
        layers_to_probe: List[int],
        layers_to_outline: Union[List[int], None] = auto_param,
        text: Union[None, str] = dflt_text,
    ) -> Device:
        r"""Creates a cell containing a Van Der Pauw structure between 4 contact
        pads.

        Parameters:
            layers_to_probe (List[int]): The layers on which to place the VDP structure.
            layers_to_outline (List[int]): Among the VDP layers, the ones for which structure must not be filled but outlined.
            text (str, optional): If None, the text is f"VDP \n{layers_to_probe}". Otherwise, f"VDP \n{text}".

        Returns:
            Device: The created device.
        """

        return create_vdp_cell(
            die_w=self.die_w,
            pad_size=self.pad_size,
            layers_to_probe=layers_to_probe,
            layers_to_outline=layers_to_outline,
            outline=self.die_outline,
            die_layer=self.layers["die"],
            pad_layer=self.layers["pad"],
            text=text,
        )

    def create_etch_test_cell(
        self, layers_to_etch: List[List[int]], text: Union[None, str] = dflt_text
    ) -> Device:
        """Creates etch test structures in an integer number of unit cells.

        These test structures are thought to be used by probing on pads (with a simple multimeter)
        that should be isolated one from another if the etching is complete.

        Parameters:
            layers_to_etch (List[List[int]]): Each element of the list corresponds to one test point,
                to put on the list of layers specified. Example: [[1, 2], [1], [2]].
            text (str, optional): If None, the cell text is f"ETCH TEST {layers_to_etch}".

        Returns:
            Device: A device (with size n*m of unit cells) with etch tests in its center.
        """

        return create_etch_test_cell(
            die_w=self.die_w,
            layers_to_etch=layers_to_etch,
            outline_die=self.die_outline,
            die_layer=self.layers["die"],
            text=text,
        )

    def create_resolution_test_cell(
        self,
        layer_to_resolve: int,
        resolutions_to_test: List[float] = [
            0.025,
            0.05,
            0.075,
            0.1,
            0.25,
            0.5,
            1,
            1.5,
            2,
        ],
        text: Union[None, str] = dflt_text,
    ) -> Device:
        r"""Creates a cell containing a resolution test.

        Parameters:
            layer_to_resolve (int): The layer to put the resolution test on.
            resolutions_to_test (List[float]): The resolutions to test in µm.
            text (str, optional): If None, the text is f"RES TEST \n{layer_to_resolve}".

        Returns:
            Device: The created device.
        """

        return create_resolution_test_cell(
            die_w=self.die_w,
            layer_to_resolve=layer_to_resolve,
            resolutions_to_test=resolutions_to_test,
            outline=self.die_outline,
            die_layer=self.layers["die"],
            text=text,
        )

    # devices:

    def create_nanowires_cell(
        self,
        channels_sources_w: List[Tuple[float, float]],
        text: Union[None, str] = dflt_text,
    ) -> Device:
        """Creates a cell containing several nanowires of given channel and
        source.

        Parameters:
            channels_sources_w (List[Tuple[float, float]]): The list of
                (channel_w, source_w) of the nanowires to create.
            text (str, optional): If None, the text is "NWIRES".

        Returns:
            Device: A device containing the nanowires, the border of the die
            (created with die_cell function), and the connections between the
            nanowires and pads.
        """

        return create_nanowires_cell(
            die_w=self.die_w,
            pad_size=self.pad_size,
            channels_sources_w=channels_sources_w,
            overlap_w=self.ebeam_overlap,
            outline_die=self.die_outline,
            outline_dev=self.device_outline,
            device_layer=self.layers["device"],
            die_layer=self.layers["die"],
            pad_layer=self.layers["pad"],
            text=text,
        )

    def create_ntron_cell(
        self,
        choke_w: float,
        channel_w: float,
        gate_w: Union[float, None] = auto_param,
        source_w: Union[float, None] = auto_param,
        drain_w: Union[float, None] = auto_param,
        choke_shift: Union[float, None] = auto_param,
        text: Union[str, None] = dflt_text,
    ) -> Device:
        r"""Creates a standardized cell specifically for a single ntron.

        Unless specified, scales the ntron parameters as:
        gate_w = drain_w = source_w = 3*channel_w
        choke_shift = -3*channel_w

        Parameters:
            choke_w (int or float): The width of the ntron's choke in µm.
            channel_w (int or float): The width of the ntron's channel in µm.
            gate_w (int or float, optional): If None, gate width is 3 times the channel width.
            source_w (int or float, optional): If None, source width is 3 times the channel width.
            drain_w (int or float, optional): If None, drain width is 3 times the channel width.
            choke_shift (int or float, optional): If None, choke shift is -3 times the channel width.
            text (str, optional): If None, the text is f"chk: {choke_w} /n chnl: {channel_w}".

        Returns:
            Device: A device containing the ntron, the border of the die (created with die_cell function),
            and the connections between the ports.
        """

        return create_ntron_cell(
            die_w=self.die_w,
            pad_size=self.pad_size,
            choke_w=choke_w,
            channel_w=channel_w,
            gate_w=gate_w,
            source_w=source_w,
            drain_w=drain_w,
            choke_shift=choke_shift,
            overlap_w=self.ebeam_overlap,
            outline_die=self.die_outline,
            outline_dev=self.device_outline,
            device_layer=self.layers["device"],
            die_layer=self.layers["die"],
            pad_layer=self.layers["pad"],
            text=text,
        )

    def create_snspd_ntron_cell(
        self,
        w_choke: float,
        w_snspd: Union[float, None] = auto_param,
        text: Union[str, None] = dflt_text,
    ) -> Device:
        """Creates a cell that contains an SNSPD coupled to an NTRON. The
        device's parameters are sized according to the SNSPD's width and the
        NTRON's choke.

        Parameters:
            w_choke (int or float): The width of the NTRON choke in µm.
            w_snspd (int or float, optional): The width of the SNSPD nanowire in µm. If None, scaled to 5*w_choke.
            text (str, optional): If None, text = f'SNSPD {w_choke}'.

        Returns:
            Device: A cell containing a die in die_layer, pads in pad layer, and an SNSPD-NTRON properly routed in the device layer.
        """

        return create_snspd_ntron_cell(
            die_w=self.die_w,
            pad_size=self.pad_size,
            w_choke=w_choke,
            w_snspd=w_snspd,
            overlap_w=self.ebeam_overlap,
            outline_die=self.die_outline,
            outline_dev=self.device_outline,
            device_layer=self.layers["device"],
            die_layer=self.layers["die"],
            pad_layer=self.layers["pad"],
            text=text,
        )
