"""Design's module is though for users to be able to access pre-built cells
that are made of circuits, devices or test structures already integrated in a
die cell.

It is a module that is sufficient in itself to build an entire new
design.
"""

from phidl import Device
import phidl.geometry as pg
from typing import Tuple, List, Union, Optional
import os

import qnngds.cells as cell
import qnngds.utilities as utility

Free = True
Occupied = False


def create_chip(
    chip_w: Union[int, float] = 10000,
    margin: Union[int, float] = 100,
    N_dies: int = None,
    die_w: Union[None, int, float] = 980,
    annotations_layer: int = 0,
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

    if N_dies is not None:
        die_w = useful_w / N_dies
        return_N_or_w = die_w
    else:
        N_dies = int(useful_w / die_w)
        return_N_or_w = N_dies
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
            cell_name = cell.name.replace("\n", "")
            try:
                if chip_map[coordinates[1] + m][coordinates[0] + n] == Occupied:
                    print(
                        f"Warning, placing Device {cell_name} "
                        + f"in an occupied state ({coordinates[1]+m}, {coordinates[0]+n})"
                    )
                else:
                    chip_map[coordinates[1] + m][coordinates[0] + n] = Occupied
            except IndexError:
                print(
                    f"Error, Device {cell_name} "
                    + f"falls out of the chip map ({coordinates[1]+m}, {coordinates[0]+n})"
                )
                return False

    # move the cell
    cell_bottom_left = (
        -n_cell * 0.5 * die_w,
        -m_cell * 0.5 * die_w,
    )
    cell.move(cell_bottom_left, ((coordinates[0]) * die_w, (coordinates[1]) * die_w))

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
        fill_pad_layer (bool): If True, the space reserved for pads in the
            die_cell in filled in pad's layer.

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
        chip_w=10000,
        chip_margin=100,
        N_dies=None,
        unit_die_size=(980, 980),
        pad_size=(150, 250),
        device_outline=0.5,
        die_outline=10,
        ebeam_overlap=10,
        annotation_layer=0,
        device_layer=1,
        die_layer=2,
        pad_layer=3,
        fill_pad_layer=False,
    ):
        """
        Args:
            name (str): The name of the design.
            chip_w (int or float): The overall width of the chip.
            chip_margin (int or float): The width of the outline of the chip where no device should be placed.
            N_dies (int): Number of dies/units to be placed by row and column.
            die_w (int or float, optional): Width of a unit die/cell in the
                design (the output device will be an integer number of unit cells).
            pad_size (tuple of int or float): Dimensions of the die's pads (width, height).
            device_outline (int or float): The width of the device's outline.
            die_outline (int or float): The width of the pads outline.
            ebeam_overlap (int or float): Extra length of the routes above the
                die's ports to assure alignment with the device (useful for ebeam
                lithography).
            annotation_layer (int): The layer where to put the annotations.
            device_layer (int or array-like[2]): The layer where the device is placed.
            die_layer (int or array-like[2]): The layer where the die is placed.
            pad_layer (int or array-like[2]): The layer where the pads are placed.
            fill_pad_layer (bool): If True, the space reserved for pads in the
                die_cell in filled in pad's layer.
        """

        self.name = name

        self.chip_w = chip_w
        self.chip_margin = chip_margin
        self.N_dies = N_dies
        self.die_size = unit_die_size
        self.die_w = unit_die_size[0]
        self.die_h = unit_die_size[1]

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

        self.fill_pad_layer = fill_pad_layer

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

        if self.N_dies is not None:
            self.die_w = N_or_w
        else:
            self.N_dies = N_or_w

        self.die_parameters = utility.DieParameters(
            (self.die_w, self.die_w),
            self.pad_size,
            self.ebeam_overlap,
            self.die_outline,
            self.layers["die"],
            self.layers["pad"],
            self.fill_pad_layer,
        )
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

    def write_gds(self, text: Union[None, str] = None) -> Union[None, str]:
        """Write a GDS file.

        Args:
            text (str or None): The filename for the GDS file.
                If None, the name of the Design will be used.

        Returns:
            str or None: The filename of the written GDS file, or None if no file was written.
        """
        if text is None:
            text = self.name
        return self.CHIP.write_gds(filename=f"{text}.gds", max_cellname_length=32000)

    # basics:

    def alignment_cell(
        self, layers_to_align: List[int], text: Union[None, str] = None
    ) -> Device:
        """Creates alignment marks in an integer number of unit cells.

        Parameters:
            layers_to_align (List[int]): Layers to align.
            text (str, optional): If None, the text is f"lay={layers_to_align}".

        Returns:
            Device: A device that centers the alignment marks in an n*m unit cell.
        """
        return cell.alignment(
            die_parameters=self.die_parameters,
            layers_to_align=layers_to_align,
            text=text,
        )

    def vdp_cell(
        self,
        layers_to_probe: List[int],
        layers_to_outline: Union[List[int], None] = None,
        text: Union[None, str] = None,
    ) -> Device:
        r"""Creates a cell containing a Van Der Pauw structure between 4 contact
        pads.

        Parameters:
            layers_to_probe (List[int]): The layers on which to place the VDP structure.
            layers_to_outline (List[int]): Among the VDP layers, the ones for which structure must not be filled but outlined.
            text (str, optional): If None, the text is f"lay={layers_to_probe}".

        Returns:
            Device: The created device.
        """

        return cell.vdp(
            die_parameters=self.die_parameters,
            layers_to_probe=layers_to_probe,
            layers_to_outline=layers_to_outline,
            text=text,
        )

    def etch_test_cell(
        self, layers_to_etch: List[List[int]], text: Union[None, str] = None
    ) -> Device:
        """Creates etch test structures in an integer number of unit cells.

        These test structures are thought to be used by probing on pads (with a simple multimeter)
        that should be isolated one from another if the etching is complete.

        Parameters:
            layers_to_etch (List[List[int]]): Each element of the list corresponds to one test point,
                to put on the list of layers specified. Example: [[1, 2], [1], [2]].
            text (str, optional): If None, the text is f"lay={layers_to_etch}".

        Returns:
            Device: A device (with size n*m of unit cells) with etch tests in its center.
        """

        return cell.etch_test(
            die_parameters=self.die_parameters,
            layers_to_etch=layers_to_etch,
            text=text,
        )

    def resolution_test_cell(
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
        text: Union[None, str] = None,
    ) -> Device:
        r"""Creates a cell containing a resolution test.

        Parameters:
            layer_to_resolve (int): The layer to put the resolution test on.
            resolutions_to_test (List[float]): The resolutions to test in µm.
            text (str, optional): If None, the text is f"lay={layer_to_resolve}".

        Returns:
            Device: The created device.
        """

        return cell.resolution_test(
            die_parameters=self.die_parameters,
            layer_to_resolve=layer_to_resolve,
            resolutions_to_test=resolutions_to_test,
            text=text,
        )

    # devices:

    def nanowires_cell(
        self,
        channels_sources_w: List[Tuple[float, float]],
        text: Union[None, str] = None,
    ) -> Device:
        """Creates a cell containing several nanowires of given channel and
        source.

        Parameters:
            channels_sources_w (List[Tuple[float, float]]): The list of
                (channel_w, source_w) of the nanowires to create.
            text (str, optional): If None, the text is f"w={channels_w}".

        Returns:
            Device: A device containing the nanowires, the border of the die
            (created with die_cell function), and the connections between the
            nanowires and pads.
        """

        return cell.nanowires(
            die_parameters=self.die_parameters,
            channels_sources_w=channels_sources_w,
            outline_dev=self.device_outline,
            device_layer=self.layers["device"],
            text=text,
        )

    def ntron_cell(
        self,
        choke_w: float,
        channel_w: float,
        gate_w: Union[float, None] = None,
        source_w: Union[float, None] = None,
        drain_w: Union[float, None] = None,
        choke_shift: Union[float, None] = None,
        text: Union[str, None] = None,
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
            text (str, optional): If None, the text is f"chk: {choke_w} \\nchnl: {channel_w}".

        Returns:
            Device: A device containing the ntron, the border of the die (created with die_cell function),
            and the connections between the ports.
        """

        return cell.ntron(
            die_parameters=self.die_parameters,
            choke_w=choke_w,
            channel_w=channel_w,
            gate_w=gate_w,
            source_w=source_w,
            drain_w=drain_w,
            choke_shift=choke_shift,
            outline_dev=self.device_outline,
            device_layer=self.layers["device"],
            text=text,
        )

    def snspds_cell(
        self,
        snspds_width_pitch: List[Tuple[float, float]] = [(0.2, 0.6)],
        snspd_size: Tuple[Union[int, float], Union[int, float]] = (100, 100),
        snspd_num_squares: Optional[int] = None,
        text: Union[None, str] = None,
    ) -> Device:
        """Creates a cell that contains vertical superconducting nanowire
        single-photon detectors (SNSPD).

        Parameters:

            snspds_width_pitch (list of tuple of float): list of (width, pitch) of the nanowires.
            snspd_size (tuple of int or float): Size of the detectors in squares (width, height).
            snspd_num_squares (Optional[int]): Number of squares in the detectors.
            text (string, optional): If None, the text is f"w={snspds_width}".

        Returns:
            Device: A cell (of size n*m unit die_cells) containing the SNSPDs.
        """

        return cell.snspds(
            die_parameters=self.die_parameters,
            snspds_width_pitch=snspds_width_pitch,
            snspd_size=snspd_size,
            snspd_num_squares=snspd_num_squares,
            outline_dev=self.device_outline,
            device_layer=self.layers["device"],
            text=text,
        )

    def snspd_ntron_cell(
        self,
        w_choke: float,
        w_snspd: Union[float, None] = None,
        text: Union[str, None] = None,
    ) -> Device:
        """Creates a cell that contains an SNSPD coupled to an NTRON. The
        device's parameters are sized according to the SNSPD's width and the
        NTRON's choke.

        Parameters:
            w_choke (int or float): The width of the NTRON choke in µm.
            w_snspd (int or float, optional): The width of the SNSPD nanowire in µm. If None, scaled to 5*w_choke.
            text (string, optional): If None, the text is f"w={w_snspd}, {w_choke}".

        Returns:
            Device: A cell containing a die in die_layer, pads in pad layer, and an SNSPD-NTRON properly routed in the device layer.
        """

        return cell.snspd_ntron(
            die_parameters=self.die_parameters,
            w_choke=w_choke,
            w_snspd=w_snspd,
            outline_dev=self.device_outline,
            device_layer=self.layers["device"],
            text=text,
        )
