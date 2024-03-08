from __future__ import division, print_function, absolute_import
from phidl import Device, Port
from phidl import quickplot as qp
from phidl import set_quickplot_options
import phidl.geometry as pg
import phidl.routing as pr
from typing import Tuple, List, Union, Dict, Set
import numpy as np
import math
import os

set_quickplot_options(blocking=True)

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
dflt_layers = {'annotation':0, 'device':1, 'die':2, 'pad':3}
dflt_text = auto_param


class Design:

    def __init__(self, 
                 name              = 'new_design',
                 chip_w            = dflt_chip_w, 
                 chip_margin       = dflt_chip_margin, 
                 N_dies            = dflt_N_dies, 
                 die_w             = auto_param,
                 pad_size          = dflt_pad_size,
                 device_outline    = dflt_device_outline,
                 die_outline       = dflt_die_outline,
                 ebeam_overlap     = dflt_ebeam_overlap,
                 annotation_layer  = dflt_layers['annotation'],
                 device_layer      = dflt_layers['device'],
                 die_layer         = dflt_layers['die'],
                 pad_layer         = dflt_layers['pad']):
        
        self.name = name

        self.chip_w      = chip_w
        self.chip_margin = chip_margin
        self.N_dies      = N_dies
        self.die_w       = die_w

        self.pad_size       = pad_size
        self.device_outline = device_outline
        self.die_outline    = die_outline
        self.ebeam_overlap  = ebeam_overlap

        self.layers = {'annotation':annotation_layer, 
                       'device'    :device_layer, 
                       'die'       :die_layer, 
                       'pad'       :pad_layer}
        
        
    # help building a design
        
    def create_chip(self,
                    create_devices_map_txt: Union[bool, str] = True):
        """ Creates the chip, with unit cells.

        The CHIP created will be the foundation of the design, the Device to add
        all references to.
        The function creates a chip_map (2D array) to help placing the cells on
        the chip (aligned with the unit cells).
        The function also generates a txt file if create_devices_map_txt is True
        to follow the devices placements on the chip.

        Parameters:
        create_devices_map_txt (bool or string): if True, generates a text file
        to follow the devices placements on the chip. If string, the text file
        is named after the string.

        Returns:
        CHIP (Device): The chip map, in the annotations layer
        
        """
        if create_devices_map_txt:
            if create_devices_map_txt == True: 
                self.devices_map_txt = f'{self.name} devices map'
            else:
                self.devices_map_txt = f'{create_devices_map_txt}'
            create_devices_map_txt = self.devices_map_txt
        else:
            self.devices_map_txt = None
            create_devices_map_txt = False

        self.CHIP, N_or_w, self.chip_map, self.devices_map_txt = create_chip(chip_w = self.chip_w, 
                                                                            margin = self.chip_margin, 
                                                                            N_dies = self.N_dies, 
                                                                            die_w = self.die_w, 
                                                                            annotations_layer = self.layers['annotation'], 
                                                                            unpack_chip_map = True,
                                                                            create_devices_map_txt = create_devices_map_txt)
        
        if self.die_w is not None:
            self.N_dies = N_or_w
        else:
            self.die_w = N_or_w

        return self.CHIP  
    
    def place_on_chip(self, 
                      cell:        Device, 
                      coordinates: Tuple[int, int], 
                      add_to_chip: bool = True):
        """ Moves the chip to the coordinates specified.
        Update the chip map with Occupied states where the device has been placed.

        NB: the cell is aligned from its bottom left corner to the coordinates.

        Parameters:
        cell (Device) : Device to be moved.
        coordinates (int, int) : (i, j) indices of the chip grid, where to place the cell.
            Note that the indices start at 0.
              
        Raises:
        Prints a warning if the Device is overlapping with already occupied coordinates.

        """
        
        place_on_chip(cell = cell,
                      coordinates = coordinates,
                      chip_map = self.chip_map,
                      die_w = self.die_w,
                      devices_map_txt = self.devices_map_txt)
        if add_to_chip: self.CHIP << cell
    
    def place_remaining_devices(self, 
                                devices_to_place:                List[Device], 
                                add_to_chip:                     bool             = True, 
                                write_remaining_devices_map_txt: Union[bool, str] = False):
        """ Go through the chip map and place the devices given, where the chip map is Free

        Warning: The list of devices is not re-ordered to fit as many of them as possible. 
        Some edges of the chip may remain empty because the list contained 2-units long devices (for e.g.).

        Parameters:
        devices_to_place (list of Device objects): The devices to be placed.
        add_to_chip (bool): add the devices provided to the Design's CHIP.
        write_remaining_devices_map_txt (bool or string): if True, write a .txt
        file mapping the devices that were placed. If string, the filename is
        the given string, except if a file has already been created.

        """

        if self.devices_map_txt is not None:
            # the decision taken when creating the chip overwrites this one
            write_devices_map_txt = self.devices_map_txt
        else:
            # a devices map can still be created, as decided when calling this function
            write_devices_map_txt = write_remaining_devices_map_txt

        if add_to_chip: self.CHIP << devices_to_place
        place_remaining_devices(devices_to_place      = devices_to_place,
                                chip_map              = self.chip_map,
                                die_w                 = self.die_w,
                                write_devices_map_txt = write_devices_map_txt)
    
    def write_gds(self, 
                  text: Union[None, str] = dflt_text):
        """ Write a gds file.
         
          Parameters:
           text (None or string): if None, the gds filename will be the name of
           the Design 
        
        """
        if text is None: text = self.name
        self.CHIP.write_gds(filename = f"{text}.gds")

    # basics:

    def create_alignement_cell(self, 
                               layers_to_align: List[int], 
                               text:            Union[None, str] = dflt_text):
        """ Creates alignement marks in a integer number of unit cells.
        
        Parameters:
        layers_to_align (list of int)
        text (string) : the text of the cell is f"ALIGN {text}"
        
        Returns:
        DIE_ALIGN (Device): A device that centers the alignement marks in a n*m
        unit cell
        
        """
        return create_alignement_cell(die_w           = self.die_w,
                                      layers_to_align = layers_to_align,
                                      outline_die     = self.die_outline,
                                      die_layer       = self.layers['die'],
                                      text            = text)
    
    def create_vdp_cell(self, 
                        layers_to_probe:   List[int], 
                        layers_to_outline: Union[List[int], None] = auto_param, 
                        text:              Union[None, str]       = dflt_text):
        """ Creates a cell containing a Van Der Pauw structure between 4 contact pads.

        Parameters: 
        layers_to_probe (list of int): the layers on which to place the vdp structure
        layers_to_outline (list of int): amoung the vdp layers, the ones for which
        structure must not be filled but outlined 
        text (string): if None, the text is f"VDP \n{layers_to_probe}", else f"VDP \n{text}"
        
        Returns:
        DIE_VANDP (Device)
        
        """
 
        return create_vdp_cell(die_w             = self.die_w,
                               pad_size          = self.pad_size,
                               layers_to_probe   = layers_to_probe,
                               layers_to_outline = layers_to_outline,
                               outline           = self.die_outline,
                               die_layer         = self.layers['die'],
                               pad_layer         = self.layers['pad'],
                               text              = text)
    
    def create_etch_test_cell(self, 
                              layers_to_etch: List[List[int]], 
                              text:           Union[None, str] = dflt_text):
        """ Creates etch test structures in integer number of unit cells.
        These tests structures are though to be used by probing on pads (with a
        simple multimeter) that should be isolated one with another if the etching
        is complete.
        
        Parameters:
        layers_to_etch (list of list of int): etch element of the list correspond to
        one test point, to put on the list of layers specified. e.g.: [[1, 2], 1, 2] or [[1]]
        text (string): if None, the cell text is f"ETCH TEST {layers_to_etch}"
        
        Returns:
        DIE_ETCH_TEST (Device): a device (with size n*m of unit cells) with etch
        tests in its center
        
        """
    
        return create_etch_test_cell(die_w          = self.die_w,
                                     layers_to_etch = layers_to_etch,
                                     outline_die    = self.die_outline,
                                     die_layer      = self.layers['die'],
                                     text           = text)
    
    def create_resolution_test_cell(self, 
                                    layer_to_resolve:    int, 
                                    resolutions_to_test: List[float]      = [0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1, 1.5, 2],
                                    text:                Union[None, str] = dflt_text):
        """ Creates a cell containing a resolution test.
        
        Parameters: 
        layer_to_resolve (int): the layer to put the resolution test on
        resolutions_to_test (list of float): the resolutions to test in µm
        text (string): if None, the text is f"RES TEST \n{layer_to_resolve}"
        
        Returns:
        DIE_RES_TEST (Device)
        
        """
 
        return create_resolution_test_cell(die_w  = self.die_w,
                                        layer_to_resolve = layer_to_resolve,
                                        resolutions_to_test = resolutions_to_test,
                                        outline   = self.die_outline,
                                        die_layer = self.layers['die'],
                                        text = text)

    # devices:

    def create_nanowires_cell(self, 
                              channels_sources_w: List[Tuple[float, float]], 
                              text:               Union[None, str]           = dflt_text):
        """ Creates a cell that contains several nanowires of given channel and source.
        
        Parameters: 
        channels_sources_w (List of (float, float)): the list of (channel_w,
        source_w) of the nanowires to create
        text (string): if None, the text is "NWIRES"
        
        Returns:
        NANOWIRES_DIE (Device) : a device (of size n*m unit cells) containing the
        nanowires, the border of the die (created with die_cell function), and the
        connections between the nanowires and pads
        
        """

        return create_nanowires_cell(die_w              = self.die_w,
                                     pad_size           = self.pad_size,
                                     channels_sources_w = channels_sources_w,
                                     overlap_w          = self.ebeam_overlap,
                                     outline_die        = self.die_outline,
                                     outline_dev        = self.device_outline,
                                     device_layer       = self.layers['device'],
                                     die_layer          = self.layers['die'],
                                     pad_layer          = self.layers['pad'],
                                     text               = text)
    
    def create_ntron_cell(self, 
                          choke_w:     float,
                          channel_w:   float,
                          gate_w:      Union[float, None] = auto_param,
                          source_w:    Union[float, None] = auto_param,
                          drain_w:     Union[float, None] = auto_param,
                          choke_shift: Union[float, None] = auto_param,
                          text:        Union[str, None]   = dflt_text):
        """ Creates a standardized cell specifically for a single ntron.

        Unless specified, scales the ntron parameters as:
        gate_w = drain_w = source_w = 3*channel_w
        choke_shift = -3*channel_w
        
        Parameters: 
        choke_w   (int or float): the width of the ntron's choke in µm
        channel_w (int or float): the width of the ntron's channel in µm
        gate_w, source_w, drain_w, choke_shift (int or float): if None, those
        parameters or sized with respect to choke_w and channel_w.
        text (string): if None, the text is f"chk: {choke_w} \nchnl: {channel_w}"
        
        Returns:
        DIE_NTRON : Device, a device containing the ntron, 
        the border of the die (created with die_cell function), 
        and the connections between the ports
        
        """

        return create_ntron_cell(die_w       = self.die_w,
                                pad_size     = self.pad_size,
                                choke_w      = choke_w,
                                channel_w    = channel_w,
                                gate_w       = gate_w,
                                source_w     = source_w,
                                drain_w      = drain_w,
                                choke_shift  = choke_shift,
                                overlap_w    = self.ebeam_overlap,
                                outline_die  = self.die_outline,
                                outline_dev  = self.device_outline,
                                device_layer = self.layers['device'],
                                die_layer    = self.layers['die'],
                                pad_layer    = self.layers['pad'],
                                text         = text)
    
    def create_snspd_ntron_cell(self, 
                                w_choke: float,
                                w_snspd: Union[float, None] = auto_param,
                                text:    Union[str, None]   = dflt_text):
        """ Creates a cell that contains an snspd coupled to ntron. 
        The device's parameters are sized according to the snspd's width and the ntron's choke.
        
        Parameters:
        w_choke (int or float): the width of the ntron choke in µm
        w_snspd (int or float): the width of the snspd nanowire in µm (if None,
        scaled to 5*w_choke)
        text (string): if None, text = f'SNSPD {w_choke}'

        Returns:
        DIE_SNSPD_NTRON (Device): a cell containg a die in die_layer, pads in pad layer 
        and a snspd-ntron properly routed in the device layer.
        """

        return create_snspd_ntron_cell(die_w     = self.die_w,
                                    pad_size     = self.pad_size,
                                    w_choke      = w_choke,
                                    w_snspd      = w_snspd,
                                    overlap_w    = self.ebeam_overlap,
                                    outline_die  = self.die_outline,
                                    outline_dev  = self.device_outline,
                                    device_layer = self.layers['device'],
                                    die_layer    = self.layers['die'],
                                    pad_layer    = self.layers['pad'],
                                    text         = text)




### Useful functions to create a new design ###

def create_chip(chip_w:                 Union[int, float]       = dflt_chip_w, 
                margin:                 Union[int, float]       = dflt_chip_margin, 
                N_dies:                 int                     = dflt_N_dies, 
                die_w:                  Union[None, int, float] = dflt_die_w, 
                annotations_layer:      int                     = dflt_layers['annotation'], 
                unpack_chip_map:        bool                    = True,
                create_devices_map_txt: Union[bool, str]        = True):
    """ Creates a chip map in the annotations layer.
    If unpack_chip_map is set to True, creates a map (2D array) to monitor the
    states of each cell of the chip.
    The user should input N_dies xor die_w.
     
      Parameters: 
      chip_w (int or float): The overall width (in um) of the chip
      margin (int or float): The width (in um) of the outline of the chip where
      no device should be placed
      N_dies (int): Number of dies/units to be placed by row and column
      die_w (None, int or float): if specified, the width of each die/unit to be
      placed by row and column
      annotations_layer (int, array-like[2]): The layer where to put the device
      unpack_chip_map (bool): if True, the function returns a map (2D array) of
      states to be filled later (e.g. with place_on_chip())
      create_devices_map_txt (bool or string): if True or string, the function
      creates a txt file that will map the devices

      Returns:
      CHIP (Device): The chip map.
      if die_w was None, die_w (float): The width of each die.
      if die_w was given, N_dies (float): The number of dies/units on each row and column
      chip_map (array-like[N_dies][N_dies]): A 2D array filled with "Free"
      (=True) states, returned only if unpack_chip_map == True
      file_name (str): The name of the created devices map text file
    
    """

    CHIP = Device("CHIP ")
    CHIP.add_polygon([(0,0), (chip_w, 0), (chip_w, chip_w), (0, chip_w)], layer = annotations_layer)

    useful_w = chip_w-margin*2
    useful_area = CHIP.add_polygon([(0,0), (useful_w, 0), (useful_w, useful_w), (0, useful_w)], layer = annotations_layer)
    useful_area.move((margin, margin))

    if die_w is not None:
        N_dies = useful_w/die_w
        return_N_or_w = N_dies
    else:
        die_w = useful_w/N_dies
        return_N_or_w = die_w
    CELL = pg.rectangle([die_w, die_w], layer=annotations_layer)
    array = CHIP.add_array(CELL, columns=N_dies, rows=N_dies, spacing=(die_w, die_w))
    array.move((0, 0), (margin, margin))

    CHIP.flatten()
    CHIP.move((margin, margin), (0, 0))

    if create_devices_map_txt:
        ## create a devices map ...
        if create_devices_map_txt == True:
            file_name = 'devices map'
        else:
            file_name = f'{create_devices_map_txt}'
        
        # check that file does not already exist, in which case it will add a int to its name:
        i = 0
        file_to_find = file_name
        while True:
            if i != 0:
                file_to_find = file_name + f'({i})'       
            file_already_exists = os.path.exists(f'{file_to_find}.txt')
            i += 1
            if not file_already_exists:
                file_name = file_to_find
                break
        with open(f'{file_name}.txt', 'a') as file:
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
  
def place_on_chip(cell:                  Device, 
                  coordinates:           Tuple[int, int], 
                  chip_map:              List[List[bool]], 
                  die_w:                 Union[int, float],
                  devices_map_txt:       Union[None, str]  = None):
    """ Moves the chip to the coordinates specified.
    Update the chip map with Occupied states where the device has been placed.

    NB: the cell is aligned from its bottom left corner to the coordinates.

    
    Parameters:
    cell (Device) : Device to be moved.
    coordinates (int, int) : (i, j) indices of the chip grid, where to place the cell.
        Note that the indices start at 0.
    chip_map (2D array): The 2D array mapping the free cells in the chip map.
    die_w (int or float): The width of a die/unit in the chip map.

    Returns:
    Returns False if the Device falls out of the chip map, 
     prints an error message and does not place the device.
    Prints a warning if the Device is overlapping with already occupied coordinates.

    """

    # update the chip's availabilities
    n_cell = round(cell.xsize/die_w)
    m_cell = round(cell.ysize/die_w)
    for n in range(n_cell):
        for m in range(m_cell):
            try:
                if chip_map[coordinates[1]+m][coordinates[0]+n] == Occupied:
                    print(f"Warning, placing Device {cell.name} " +
                          f"in an occupied state ({coordinates[1]+m}, {coordinates[0]+n})")
                else:
                    chip_map[coordinates[1]+m][coordinates[0]+n] = Occupied
            except IndexError:
                print(f"Error, Device {cell.name} " +
                      f"falls out of the chip map ({coordinates[1]+m}, {coordinates[0]+n})")
                return False
    
    # move the cell
    cell_bottom_left = cell.get_bounding_box()[0]
    cell.move(cell_bottom_left, (coordinates[0]*die_w, coordinates[1]*die_w))

    # write the cell's place on the devices map text file
    if devices_map_txt is not None:
        with open(f'{devices_map_txt}.txt', 'a') as file:
            try : 
                name = cell.name.replace("\n", "")
            except AttributeError : 
                name = 'unnamed'
            file.write(f"({coordinates[0]}, {coordinates[1]}) : {name}\n")

    return True

def place_remaining_devices(devices_to_place:      List[Device], 
                            chip_map:              List[List[bool]], 
                            die_w:                 Union[int,float],
                            write_devices_map_txt: Union[bool, str] = False):
    """ Go through the chip map and place the devices given, where the chip map is Free
        
        Warning: The list of devices is not re-ordered to fit as many of them as possible. 
        Some edges of the chip may remain empty because the list contained 2-units long devices (for e.g.).

    Parameters:
    devices_to_place (list of Device objects): The devices to be placed
    chip_map (2D array): The 2D array mapping the free cells in the chip map.
    die_w (int or float): The width of a die/unit in the chip map.
    write_devices_map_txt (bool or string): if True, write a .txt file mapping
    the devices that were placed
    
    """

    # name and create the file if no file was given
    if write_devices_map_txt == True:

        file_name = 'remaining_cells_map'
        with open(f'{file_name}.txt', 'a') as file:
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
                if place_on_chip(devices_to_place[0], (col_i, row_i), chip_map, die_w, file_name):
                    devices_to_place.pop(0)


    if devices_to_place:
        print("Some devices are still to be placed, " +
              "no place remaining on the chip.")



### Useful very common cells to be used as test vehicles during and after fab

def alignement_mark(layers: List[int] = [1, 2, 3, 4]):
    """ Creates an alignement mark for every photolithography
    
    Parameters:
    layers (array of int): an array of layers
      
    Returns:
    ALIGN (Device): a device containing the alignement marks, on each layer
    """

    def create_marker(layer1, layer2):

        MARK = Device()

        # central part with cross

        cross = MARK << pg.cross(length=190, width=20, layer=layer1)
        rect = pg.rectangle((65, 65), layer=layer2)
        window = MARK.add_array(rect, 2, 2, (125, 125))
        window.move(window.center, cross.center)

        # combs 
        def create_comb(pitch1 = 500, pitch2 = 100, layer1=1, layer2=2):

            COMB = Device()

            # middle comb (made of layer1), pitch = 10
            rect1 = pg.rectangle((5, 30), layer=layer1)
            middle_comb = COMB.add_array(rect1, 21, 1, spacing= (10, 0))
            middle_comb.move(COMB.center, (0, 0))
            
            # top and bottom combs (made of layer2), pitchs = 10+pitch1, 10+pitch2
            rect2 = pg.rectangle((5, 30), layer=layer2)
            top_comb    = COMB.add_array(rect2, 21, 1, spacing= (10+pitch1/1000, 0))
            top_comb   .move(top_comb.center, (middle_comb.center[0], middle_comb.center[1]+30))
            top_text = COMB.add_ref(pg.text(f'{pitch1}NM', size=10, layer=layer2))
            top_text.move(top_text.center, (140, 30))

            bottom_comb = COMB.add_array(rect2, 21, 1, spacing= (10+pitch2/1000, 0))
            bottom_comb.move(bottom_comb.center, (middle_comb.center[0], middle_comb.center[1]-30))            
            bottom_text = COMB.add_ref(pg.text(f'{pitch2}NM', size=10, layer=layer2))
            bottom_text.move(bottom_text.center, (140, -30))

            # additional markers (made of layer1), for clarity
            rect1a = pg.rectangle((5, 20), layer=layer1)
            marksa = COMB.add_array(rect1a, 3, 2, spacing=(100, 110))
            marksa.move(marksa.center, middle_comb.center)

            rect1b = pg.rectangle((5, 10), layer=layer1)
            marksb = COMB.add_array(rect1b, 2, 2, spacing=(100, 100))
            marksb.move(marksb.center, middle_comb.center)
            
            return COMB

        comb51 = create_comb(pitch1 = 500, pitch2= 100, layer1=layer1, layer2=layer2)
        
        top = MARK.add_ref(comb51)
        top.move((0,0), (0, 200))

        left = MARK.add_ref(comb51)
        left.rotate(90)
        left.move((0,0), (-200, 0))

        comb205 = create_comb(pitch1 = 200, pitch2 = 50, layer1=layer1, layer2=layer2)

        bottom = MARK.add_ref(comb205)
        bottom.rotate(180)
        bottom.move((0,0), (0, -200))

        right = MARK.add_ref(comb205)
        right.rotate(-90)
        right.move((0,0), (200, 0))

        MARK.move(MARK.center, (0,0))

        # text
        text1 = MARK << pg.text(str(layer2), size= 50,layer={layer1, layer2})
        text1.move(text1.center, (220, 200))
        text2 = MARK << pg.text(f'{layer2} ON {layer1}', size = 10, layer=layer2)
        text2.move(text2.center, (220, 240))


        return MARK
    
    ALIGN = Device('ALIGN ')
    markers_pitch = 600
    for i, layer1 in enumerate(layers):
        n = len(layers)-i-1
        if n!=0:
            for j, layer2 in enumerate(layers[-n:]):
                MARK = create_marker(layer1, layer2)
                MARK.move((j*markers_pitch, i*markers_pitch))
                ALIGN << MARK
            text = ALIGN << pg.text(str(layer1), size = 160, layer=layer1)
            text.move(text.center, (-340, i*markers_pitch))

    ALIGN.move(ALIGN.center, (0, 0))
    return ALIGN

def resolution_test(resolutions: List[float]        = [0.8, 1, 1.2, 1.4, 1.6, 1.8, 2.0], 
                    inverted:    Union[bool, float] = False, 
                    layer:       int                = dflt_layers['device']):
    """ Creates test structures for determining a process resolution
        
        Parameters:
        resolutions (array of int or float): list of resolutions (in um) to be tested
        inverted (bool or float): if True, invert the device. If float, outline the device by this width.
        layer (int): layer to put the device on

        # to add in later versions, wrap the test structures to fit a given unit cell:
        die_max_size: max size of the test structure to be returned (typically, the size of a single die) 
                       
        Returns:
        RES_TEST (Device): the test structures, in the specified layer
        """
    
    def create_3L(res = 1):

        LLL = Device()
        
        def create_L(w, spacing):

            L = Device()

            bar = pg.rectangle((min(100*w, 100), w))
            bars = Device()
            bars.add_array(bar, 1, 5, spacing=(0, spacing))
            v_bars = L << bars
            h_bars = L << bars 
            h_bars.rotate(90)

            L.align("all", 'xmin')
            L.move((L.xmin, L.ymin), (0, 0))
            return L
        
        grid_spacing = (13*res, 13*res)

        for i, percent in enumerate([0.8, 1, 1.2]):
            lll = LLL << create_L(percent*res, 2*res)
            lll.move([i*space for space in grid_spacing])

        text = LLL << pg.text(str(res), size = 20)
        text.move(text.get_bounding_box()[0], [(i+1)*space for space in grid_spacing])

        return LLL
    
    def create_waffle(res = 1):

        WAFFLE = Device()
        W = pg.rectangle(size = (res*80, res*80))
        
        pattern = [(res*x, res*80) for x in [2, 1, 1, 2, 3, 5, 8, 13, 21, 15]]
        WOut = pg.gridsweep(function = pg.rectangle,
                            param_x = {'size': pattern},
                            param_y = {},
                            spacing = res)
        
        WOut.move(WOut.center, W.center)
        W1 = pg.boolean(W, WOut, 'A-B')

        WOut.rotate(90, center = WOut.center)
        W2 = pg.boolean(W, WOut, 'A-B')

        WAFFLE << W1
        WAFFLE << W2
        text = WAFFLE << pg.text(str(res), size = 20)
        text.move((text.get_bounding_box()[0][0], text.get_bounding_box()[1][1]), (2*res, -2*res))

        return WAFFLE
    
    RES_TEST = Device("RESOLUTION TEST ")
    
    RES_TEST1 = pg.gridsweep(function = create_3L, 
                            param_x = {'res': resolutions}, 
                            param_y = {},
                            spacing = 10,
                            align_y = 'ymin')
    RES_TEST2 = pg.gridsweep(function = create_waffle, 
                            param_x = {'res': resolutions}, 
                            param_y = {},
                            spacing = 10,
                            align_y = 'ymax')

    RES_TEST << pg.grid(device_list = [[RES_TEST1], [RES_TEST2]],
                       spacing = 20,
                       align_x = 'xmin')

    if inverted :
        if inverted == True:
            RES_TEST = pg.invert(RES_TEST, border=5, precision=0.0000001, layer=layer)
        else:
            RES_TEST = pg.outline(RES_TEST, inverted)
        res_test_name ="RESOLUTION TEST INVERTED "
    else:
        res_test_name = "RESOLUTION TEST "

    RES_TEST = pg.union(RES_TEST, layer = layer)
    RES_TEST.move(RES_TEST.center, (0, 0))
    RES_TEST.name = res_test_name
    return RES_TEST



### Useful common nanowire-based devices

""" copied and adjusted from qnngds geometries"""
def ntron(choke_w=0.03, 
          gate_w=0.2, 
          channel_w=0.1, 
          source_w=0.3, 
          drain_w=0.3, 
          choke_shift=-0.3, 
          layer=1):
    
    D = Device()
    
    choke = pg.optimal_step(gate_w, choke_w, symmetric=True, num_pts=100)
    k = D<<choke
    
    channel = pg.compass(size=(channel_w, choke_w))
    c = D<<channel
    c.connect(channel.ports['W'],choke.ports[2])
    
    drain = pg.optimal_step(drain_w, channel_w)
    d = D<<drain
    d.connect(drain.ports[2], c.ports['N'])
    
    source = pg.optimal_step(channel_w, source_w)
    s = D<<source
    s.connect(source.ports[1], c.ports['S'])
    
    k.movey(choke_shift)

    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(name=3, port=k.ports[1])
    D.add_port(name=1, port=d.ports[1])
    D.add_port(name=2, port=s.ports[2])
    D.name = f"NTRON {choke_w} {channel_w} "
    D.info = locals()

    return D

""" copied and adjusted from qnngds geometries"""
def ntron_compassPorts(choke_w=0.03, 
          gate_w=0.2, 
          channel_w=0.1, 
          source_w=0.3, 
          drain_w=0.3, 
          choke_shift=-0.3, 
          layer=1):
    
    D = Device()
    
    choke = pg.optimal_step(gate_w, choke_w, symmetric=True, num_pts=100)
    k = D<<choke
    
    channel = pg.compass(size=(channel_w, choke_w))
    c = D<<channel
    c.connect(channel.ports['W'],choke.ports[2])
    
    drain = pg.optimal_step(drain_w, channel_w)
    d = D<<drain
    d.connect(drain.ports[2], c.ports['N'])
    
    source = pg.optimal_step(channel_w, source_w)
    s = D<<source
    s.connect(source.ports[1], c.ports['S'])
    
    k.movey(choke_shift)

    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(name='N1', port=d.ports[1])
    D.add_port(name='S1', port=s.ports[2])
    D.add_port(name='W1', port=k.ports[1])
    D.name = f"NTRON {choke_w} {channel_w} "
    D.info = locals()

    return D

def nanowire(channel_w: float = 0.1, 
             source_w:  float = 0.3, 
             layer:     int   = dflt_layers['device'], 
             num_pts:   int   = 100):
    
    NANOWIRE = Device(f"NANOWIRE {channel_w} ")
    wire = pg.optimal_step(channel_w, source_w, symmetric=True, num_pts=num_pts)
    source = NANOWIRE << wire
    gnd    = NANOWIRE << wire
    source.connect(source.ports[1], gnd.ports[1])

    NANOWIRE.flatten(single_layer=layer)
    NANOWIRE.add_port(name=1, port=source.ports[2])
    NANOWIRE.add_port(name=2, port=gnd.ports[2])
    NANOWIRE.rotate(-90)
    NANOWIRE.move(NANOWIRE.center, (0, 0))

    return NANOWIRE

def snspd_ntron(w_snspd:        float                    = 0.1, 
                pitch_snspd:    float                    = 0.3,
                size_snspd:     Tuple[Union[int, float]] =(3, 3),
                w_inductor:     float                    = 0.3,
                pitch_inductor: float                    = 0.6,
                k_inductor13:   Union[int, float]        = 10,
                k_inductor2:    Union[int, float]        = 4,
                w_choke:        float                    = 0.02,
                w_channel:      float                    = 0.12,
                w_pad:          Union[int, float]        = 1,
                layer:          int                      = dflt_layers['device']):
    """ Creates a snspd coupled to a ntron, with 3 inductors in the circuit as:

        |        |
        L1       L3
        |        |
        |__L2__ntron
        |        |
        SNSPD
        |
        
        The length of L1, L2 and L3 (long nanowires) where scaled against the snspd:
        L1 = L3 = k13 * L and L2 = k2 * L where L is the snspd kinetic inductance

        Param:
        w_snspd, pitch_snspd, size_snspd : parameters relative to snspd
        w_inductor, pitch_inductor : parameters relative to inductors
        k_inductor13, k_inductor2 : the factors for scaling the inductors
                                     to the snspd kinetic inductance
        w_choke, w_channel : parameters relative to the ntron 
                            (note: the ntron source and drain w will be
                            equal to w_inductor)
        w_pad : the width of the external connections to the cell
        layer : int
        
        Returns:
        SNSPD_NTRON : Device
        
        """
    
    def scale_inductors_to_snspd():

        l_snspd = size_snspd[0]*size_snspd[1]/pitch_snspd
        l_inductor13 = k_inductor13 * w_inductor/w_snspd * l_snspd
        l_inductor2  = k_inductor2  * w_inductor/w_snspd * l_snspd

        n_inductor13 = math.sqrt(l_inductor13 * pitch_inductor)
        n_inductor2  = math.sqrt(l_inductor2  * pitch_inductor)

        size_inductor13 = (n_inductor13, n_inductor13)
        size_inductor2  = (n_inductor2, n_inductor2)

        return size_inductor13, size_inductor2
        
    def crossA():

        D = Device()
        tee = pg.tee((3*w_inductor, w_inductor), (w_inductor, w_inductor), taper_type='fillet')
        first_tee  = D << tee.movey(-w_inductor/2)
        second_tee = D << tee
        second_tee.rotate(180)
        
        D = pg.union(D)
        D.add_port(port=first_tee.ports[1], name='E')
        D.add_port(port=first_tee.ports[2], name='W')
        D.add_port(port=first_tee.ports[3], name='S')
        D.add_port(port=second_tee.ports[3], name='N')

        D.flatten()
        return D
    
    def crossB():

        D = Device()
        tee = pg.tee((3*w_inductor, w_inductor), (w_inductor, w_inductor), taper_type='fillet')
        first_tee = D << tee.movey(-w_inductor/2)
        first_tee.rotate(180)
        
        D.add_port(port=first_tee.ports[1], name='W')
        D.add_port(port=first_tee.ports[2], name='E')
        D.add_port(port=first_tee.ports[3], name='N')

        D.flatten()
        return D

    def crossC():

        D = Device()
        tee = pg.tee((3*w_inductor, w_inductor), (w_inductor, w_inductor), taper_type='fillet')
        first_tee = D << tee.movey(-w_inductor/2)
        first_tee.rotate(90)
        
        D.add_port(port=first_tee.ports[1], name='N')
        D.add_port(port=first_tee.ports[2], name='S')
        D.add_port(port=first_tee.ports[3], name='E')

        D.flatten()
        return D
    
    def create_snspd():
        ## SNSPD
        SNSPD = SNSPD_NTRON << pg.snspd(wire_width = w_snspd,
                                        wire_pitch = pitch_snspd,
                                        size = size_snspd,
                                        num_squares = None,
                                        turn_ratio = 4,
                                        terminals_same_side = False,
                                        layer = layer)
        SNSPD.rotate(90)
        # port 1 connected to gnd
        route = SNSPD_NTRON << pg.optimal_step(SNSPD.ports[1].width, w_pad, symmetric = True)
        route.connect(route.ports[1], SNSPD.ports[1])
        SNSPD_NTRON.add_port(port = route.ports[2], name = "S1")
        # port 2 connected to crossA south
        route_step = SNSPD_NTRON << pg.optimal_step(SNSPD.ports[2].width, CROSSA.ports['S'].width, symmetric = True)
        route_step.connect(route_step.ports[1], SNSPD.ports[2])
        route = SNSPD_NTRON << pg.compass((w_inductor, w_pad/2))
        route.connect(route.ports['S'], route_step.ports[2])
        CROSSA.connect(CROSSA.ports['S'], route.ports['N'])

    def create_inductor1():
        ## INDUCTOR1
        INDUCTOR1 = SNSPD_NTRON << pg.snspd(wire_width = w_inductor, 
                                            wire_pitch = pitch_inductor, 
                                            size = size_inductor13,
                                            num_squares = None, 
                                            terminals_same_side = False,
                                            layer = layer)
        INDUCTOR1.rotate(90).mirror()
        # port 1 connected to crossA north
        route = SNSPD_NTRON << pg.compass((w_inductor, w_pad/2))
        route.connect(route.ports['S'], CROSSA.ports['N'])
        INDUCTOR1.connect(INDUCTOR1.ports[1], route.ports['N'])
        # port 2 connected to pad 
        route = SNSPD_NTRON << pg.optimal_step(INDUCTOR1.ports[2].width, w_pad, symmetric = True)
        route.connect(route.ports[1], INDUCTOR1.ports[2])
        SNSPD_NTRON.add_port(port = route.ports[2], name = "N1")

    def create_inductor2():
        ## INDUCTOR2
        INDUCTOR2 = Device()
        inductor2 = INDUCTOR2 << pg.snspd(wire_width = w_inductor, 
                                        wire_pitch = pitch_inductor, 
                                        size = size_inductor2,
                                        num_squares = None, 
                                        terminals_same_side = True,
                                        layer = layer)
        arcleft  = INDUCTOR2 << pg.arc(radius = 2*w_inductor, width = w_inductor, theta = 90)
        arcright = INDUCTOR2 << pg.arc(radius = 2*w_inductor, width = w_inductor, theta = 90)
        arcleft.connect(arcleft.ports[2], inductor2.ports[1])
        arcright.connect(arcright.ports[1], inductor2.ports[2])
        INDUCTOR2.add_port(port =  arcleft.ports[1])
        INDUCTOR2.add_port(port = arcright.ports[2])
        INDUCTOR2 = SNSPD_NTRON << INDUCTOR2
        # port 1 connected to crossA east
        INDUCTOR2.connect(INDUCTOR2.ports[1], CROSSA.ports['E'])
        # port 2 connected to crossB west
        route = SNSPD_NTRON << pg.compass((w_pad/2, w_inductor))
        route.connect(route.ports['W'], INDUCTOR2.ports[2])
        CROSSB.connect(CROSSB.ports['W'], route.ports['E'])

    def create_ntron():
        ## NTRON
        NTRON = SNSPD_NTRON << ntron(choke_w = w_choke, 
                                    gate_w = w_inductor, 
                                    channel_w = w_channel, 
                                    source_w = w_inductor, 
                                    drain_w = w_inductor, 
                                    choke_shift = -3*w_channel, 
                                    layer = layer)
        # port 3 connected to crossB east
        route = SNSPD_NTRON << pg.compass((w_pad/2, w_inductor))
        route.connect(route.ports['W'], CROSSB.ports['E'])
        NTRON.connect(NTRON.ports[3], route.ports['E']) 
        # port 1 connected to crossC south
        route = SNSPD_NTRON << pg.compass((w_inductor, w_pad/2))
        route.connect(route.ports['S'], NTRON.ports[1])
        CROSSC.connect(CROSSC.ports['S'], route.ports['N'])
        # port 2 connected to gnd
        route = SNSPD_NTRON << pg.optimal_step(NTRON.ports[2].width, w_pad, symmetric = True)
        route.connect(route.ports[1], NTRON.ports[2])
        SNSPD_NTRON.add_port(port = route.ports[2], name = "S2")

    def create_inductor3():
        ## INDUCTOR3
        INDUCTOR3 = SNSPD_NTRON << pg.snspd(wire_width = w_inductor, 
                                            wire_pitch = pitch_inductor, 
                                            size = size_inductor13,
                                            num_squares = None, 
                                            terminals_same_side = False,
                                            layer = layer)
        INDUCTOR3.rotate(90)
        # port 1 connected to crossC north
        route = SNSPD_NTRON << pg.compass((w_inductor, w_pad/2))
        route.connect(route.ports['S'], CROSSC.ports['N'])
        INDUCTOR3.connect(INDUCTOR3.ports[1], route.ports['N'])
        # port 2 connected to pad 
        route = SNSPD_NTRON << pg.optimal_step(INDUCTOR3.ports[2].width, w_pad, symmetric = True)
        route.connect(route.ports[1], INDUCTOR3.ports[2]) 
        SNSPD_NTRON.add_port(port = route.ports[2], name = "N3")
  
    def create_probing_routes():
        ## SNSPD PROBING PAD
        step  = SNSPD_NTRON << pg.optimal_step(w_inductor, w_pad, symmetric = True)
        step.connect(step.ports[1], CROSSA.ports['W'])
        route = SNSPD_NTRON << pg.compass((abs(SNSPD_NTRON.xmin - step.xmin), w_pad))
        route.connect(route.ports['E'], step.ports[2])
        SNSPD_NTRON.add_port(port = route.ports['W'], name = "W1")

        ## NTRON IN PROBING PAD
        step  = SNSPD_NTRON << pg.optimal_step(w_inductor, w_pad, symmetric = True)
        step.connect(step.ports[1], CROSSB.ports['N'])
        route = SNSPD_NTRON << pg.compass((w_pad, abs(SNSPD_NTRON.ymax - step.ymax)))
        route.connect(route.ports['S'], step.ports[2])
        SNSPD_NTRON.add_port(port = route.ports['N'], name = "N2")

        ## NTRON OUT PROBING PAD
        step  = SNSPD_NTRON << pg.optimal_step(w_inductor, w_pad, symmetric = True)
        step.connect(step.ports[1], CROSSC.ports['E'])
        route = SNSPD_NTRON << pg.compass((abs(SNSPD_NTRON.xmax - step.xmax), w_pad))
        route.connect(route.ports['W'], step.ports[2])
        SNSPD_NTRON.add_port(port = route.ports['E'], name = "E1")

    SNSPD_NTRON = Device(f"SNSPD NTRON {w_snspd} {w_choke} ")

    size_inductor13, size_inductor2 = scale_inductors_to_snspd()

    CROSSA = SNSPD_NTRON << crossA()
    CROSSB = SNSPD_NTRON << crossB()
    CROSSC = SNSPD_NTRON << crossC()

    create_snspd()
    create_inductor1()
    create_inductor2()
    create_ntron()
    create_inductor3()
    create_probing_routes()

    SNSPD_NTRON.flatten()
    
    ports = SNSPD_NTRON.get_ports()
    SNSPD_NTRON = pg.union(SNSPD_NTRON, layer = layer)
    for port in ports: SNSPD_NTRON.add_port(port)

    SNSPD_NTRON.move(SNSPD_NTRON.center, (0, 0))
    SNSPD_NTRON.name = f"SNSPD NTRON {w_snspd} {w_choke} "
    return SNSPD_NTRON


### Creating cells from devices

## tools for building a cell from scratch:

def die_cell(die_size:        Tuple[int, int]   = (dflt_die_w, dflt_die_w), 
             device_max_size: Tuple[int, int]   = (100, 100), 
             pad_size:        Tuple[int, int]   = dflt_pad_size, 
             contact_w:       Union[int, float] = 50, 
             contact_l:       Union[int, float] = dflt_ebeam_overlap, 
             ports:           Dict[str, int]    = {'N':1, 'E':1, 'W':1, 'S':1}, 
             ports_gnd:       List[str]         = ['E', 'S'], 
             isolation:       Union[int, float] = dflt_die_outline, 
             text:            str               = '', 
             text_size:       Union[int, float] = die_cell_border/2, 
             layer:           int               = dflt_layers['die'], 
             pad_layer:       int               = dflt_layers['pad'], 
             invert:          bool              = False):
    """ Creates a die cell with dicing marks, text, and pads to connect to a device.
    
    Parameters:
    die_size        (int or float, int or float): overall size of the cell (w, h)
    device_max_size (int or float, int or float): max dimensions of the device inside the cell (w, h)
    pad_size        (int or float, int or float): dimensions of the cell's pads (w, h)
    contact_w (int or float): width of the ports and route to be connected to a device
    contact_l (int or float): extra length of the routes above the ports to assure alignment with the device 
                              (useful for ebeam lithography)
    ports     (set): the ports of the device, format must be {'N':m, 'E':n, 'W':p, 'S':q}
    ports_gnd (array of string): the ports connected to ground
    isolation (int or float): the width of the pads outline
    text      (string): the text to be displayed on the cell
    text_size (int): size of text, corresponds to phidl geometry std
    layer     (int or array-like[2]): the layer where to put the cell
    pad_layer (int or array-like[2]): the layer where to put the contact pads
    invert    (bool): if True, the cell is inverted (useful for positive tone resists exposure)

      
    Returns:
    DIE (Device): the cell, with ports of width contact_w positionned around a device_max_size area
    
    """
    
    def offset(overlap_port):
        port_name = overlap_port.name[0]
        if   port_name == 'N' :
            overlap_port.midpoint[1] += -contact_l
        elif port_name == 'S' :
            overlap_port.midpoint[1] += contact_l
        elif port_name == 'W' :
            overlap_port.midpoint[0] += contact_l
        elif port_name == 'E' :
            overlap_port.midpoint[0] += -contact_l

    DIE = Device(f"DIE {text} ")

    border = pg.rectangle(die_size)
    border.move(border.center, (0, 0))
    borderOut = Device()

    ## Make the routes and pads
    padOut = Device()

    pad_block_size = (die_size[0]-2*pad_size[1]-4*isolation, die_size[1]-2*pad_size[1]-4*isolation)
    inner_block = pg.compass_multi(device_max_size, ports)
    outer_block = pg.compass_multi(pad_block_size, ports)
    inner_ports = list(inner_block.ports.values())

    for i, port in enumerate(list(outer_block.ports.values())):

        CONNECT = Device()
        port.rotate(180)

        # create the pad
        pad = pg.rectangle(pad_size, layer={layer, pad_layer})
        pad.add_port('1', midpoint=(pad_size[0]/2, 0), width=pad_size[0], orientation=90)
        pad_ref = CONNECT << pad
        pad_ref.connect(pad.ports['1'], port)

        # create the route from pad to contact
        port.width = pad_size[0]
        inner_ports[i].width = contact_w
        CONNECT << pr.route_quad(port, inner_ports[i], layer=layer)

        # create the route from contact to overlap
        overlap_port = CONNECT.add_port(port = inner_ports[i])
        offset(overlap_port)
        overlap_port.rotate(180)
        CONNECT << pr.route_quad(inner_ports[i], overlap_port, layer=layer)
       
        # isolate the pads that are not grounded
        port_grounded = any(port.name[0] == P for P in ports_gnd)
        if not port_grounded :
            padOut << pg.outline(CONNECT, distance=isolation, join='round', open_ports=2*isolation)

        # add the port to the die
        DIE.add_port(port = inner_ports[i].rotate(180))
        DIE << CONNECT

    borderOut << padOut

    ## Add the die markers
    
    # mark the corners
    cornersOut = Device()

    corners_coord = [(-die_size[0]/2 + die_cell_border/2, -die_size[1]/2 + die_cell_border/2), 
                     ( die_size[0]/2 - die_cell_border/2, -die_size[1]/2 + die_cell_border/2),
                     ( die_size[0]/2 - die_cell_border/2,  die_size[1]/2 - die_cell_border/2), 
                     (-die_size[0]/2 + die_cell_border/2,  die_size[1]/2 - die_cell_border/2)]
    for corner_coord in corners_coord:
        corner = pg.rectangle((die_cell_border-isolation, die_cell_border-isolation))
        corner = pg.outline(corner, -1*isolation)
        corner.move(corner.center, corner_coord)
        cornersOut << corner

    borderOut << cornersOut
    
    # label the cell
    label = pg.text(text, size=text_size, layer=layer)
    label.move((label.xmin, label.ymin), (0, 0))
    pos = [x + 2*isolation+10 for x in (-die_size[0]/2, -die_size[1]/2)]
    label.move(pos)
    DIE << label
    labelOut = pg.outline(label, isolation)

    borderOut << labelOut

    border = pg.boolean(border, borderOut, 'A-B', layer = layer)
    DIE << border

    DIE.flatten()
    ports = DIE.get_ports()
    DIE = pg.union(DIE, by_layer=True)
    if invert: 
        PADS = pg.deepcopy(DIE)
        PADS.remove_layers([layer])
        DIE = pg.invert(DIE, border = 0, layer = layer)
        DIE << PADS
    for port in ports: DIE.add_port(port)
    DIE.name = f"DIE {text}"
    return DIE

""" copied from qnngds geometries """
def hyper_taper(length = 10, wide_section = 50, narrow_section = 5, layer=dflt_layers['device']):
    """
    Hyperbolic taper (solid). Designed by colang.


    Parameters
    ----------
    length : FLOAT
        Length of taper.
    wide_section : FLOAT
        Wide width dimension.
    narrow_section : FLOAT
        Narrow width dimension.
    layer : INT, optional
        Layer for device to be created on. The default is 1.
        
        
    Returns
    -------
    HT :  DEVICE
        PHIDL device object is returned.
    """
    taper_length=length
    wide =  wide_section
    zero = 0
    narrow = narrow_section
    x_list = np.arange(0,taper_length+.1, .1)
    x_list2= np.arange(taper_length,-0.1,-0.1)
    pts = []

    a = np.arccosh(wide/narrow)/taper_length

    for x in x_list:
        pts.append((x, np.cosh(a*x)*narrow/2))
    for y in x_list2:
        pts.append((y, -np.cosh(a*y)*narrow/2))
        HT = Device('hyper_taper')
        hyper_taper = HT.add_polygon(pts)
        HT.add_port(name = 1, midpoint = [0, 0],  width = narrow, orientation = 180)
        HT.add_port(name = 2, midpoint = [taper_length, 0],  width = wide, orientation = 0)
        HT.flatten(single_layer = layer)
    return HT

def add_hyptap_to_cell(die_ports: List[Port], 
                       overlap_w: Union[int, float] = dflt_ebeam_overlap, 
                       contact_w: Union[int, float] = 5, 
                       layer:     int               = dflt_layers['device']):
    """ Takes the cell and add hyper taper at its ports
    
    Parameters:
    die_ports (list of Port, use .get_ports()): the ports of the die cell
    overlap_w (int or float): the overlap width in µm (accounts for misalignement between 1st and 2nd ebeam exposures)
    contact_w (int or float): the width of the contact with the device's route in µm
                            (width of hyper taper's end)
    layer (int or array-like[2]): the layer on which to place the device
                            
    Returns:
    HT (Device): the hyper tapers, positionned at the die's ports,
                ports of the same name than the die's ports are added to the output of the tapers
    device_ports (Device): a device containing only the input ports of the tapers, named as the die's ports
    """
    
    HT = Device("HYPER TAPERS ")
    device_ports = Device()

    for port in die_ports:
        ht_w = port.width + 2*overlap_w
        ht = HT << hyper_taper(overlap_w, ht_w, contact_w)
        ht.connect(ht.ports[2], port)
        HT.add_port(port = ht.ports[1], name = port.name)
        device_ports.add_port(port = ht.ports[2], name = port.name)
    
    HT.flatten(single_layer=layer)
    return HT, device_ports

def route_to_dev(ext_ports: List[Port],
                 dev_ports: Set[Port],
                 layer:     int = dflt_layers['device']):
    """ Creates smooth routes from external ports to the device's ports
    
    Parameters:
     ext_ports (List of Port, use .get_ports()): the external ports, e.g. of the die or hyper tapers 
     dev_ports (Set of Port,  use .ports): the device's ports, should be named as the external ports 
     layer (int or array-like[2]): the layer to put the routes on
     
    Returns:
     ROUTES (Device): the routes from ports to ports, on the specified layer
    """

    ROUTES = Device("ROUTES ")

    for port in ext_ports:
        dev_port = dev_ports[port.name]
        try:
            radius = port.width
            length1 = 2*radius
            length2 = 2*radius
            ROUTES << pr.route_smooth(port, dev_port, radius, path_type='Z', length1 = length1, length2 = length2)
        except ValueError:
            try:
                radius = dev_port.width
                length1 = radius
                length2 = radius
                ROUTES << pr.route_smooth(port, dev_port, radius, path_type='Z', length1 = length1, length2 = length2)
            except ValueError:
                print("Error: Could not route to device.")
                return ROUTES
    ROUTES.flatten(single_layer = layer)
    return ROUTES


## pre-built cells:

# basics:

def create_alignement_cell(die_w:           Union[int, float],
                           layers_to_align: List[int],
                           outline_die:     Union[int, float] = dflt_die_outline,
                           die_layer:       int               = dflt_layers['die'],
                           text:            Union[None, str]  = dflt_text):
    """ Creates alignement marks in a integer number of unit cells.
     
    Parameters:
    die_w (int or float): width of a unit die/cell in the design (the output
    device will be a integer number of unit cells)
    layers_to_align (list of int)
    outline_die (int or float): the width of the die's outline
    die_layer (int)
    text (string)
    
    Returns:
    DIE_ALIGN (Device): A device that centers the alignement marks in a n*m unit cell
    
    """

    if text is None: text = ''
    DIE = Device(f"DIE ALIGN {text} ")

    ALIGN = alignement_mark(layers_to_align)
    
    n = math.ceil((ALIGN.xsize)/die_w)
    m = math.ceil((ALIGN.ysize)/die_w)

    BORDER = die_cell(die_size=(n*die_w, m*die_w),
                    device_max_size=(ALIGN.xsize+20, ALIGN.ysize+20),
                    ports = {},
                    ports_gnd = {},
                    isolation = outline_die,
                    text = f"ALIGN {text}",
                    layer = die_layer,
                    invert = True)

    DIE << BORDER.flatten()
    DIE << ALIGN

    return DIE

def create_vdp_cell(die_w:             Union[int, float], 
                    pad_size:          Tuple[float], 
                    layers_to_probe:   List[int],
                    layers_to_outline: Union[None, List[int]] = auto_param,
                    outline:           Union[int, float]      = dflt_die_outline, 
                    die_layer:         Union[int, float]      = dflt_layers['die'], 
                    pad_layer:         int                    = dflt_layers['pad'],
                    text:              Union[None, str]       = dflt_text):
    """ Creates a cell containing a Van Der Pauw structure between 4 contact pads.
    
    Parameters: 
    die_w    (int or float): width of a unit die/cell in the design (the output
    device will be a integer number of unit cells)
    pad_size (int or float, int or float): dimensions of the die's pads (w, h)
    layers_to_probe (list of int): the layers on which to place the vdp structure
    layers_to_outline (list of int): amoung the vdp layers, the ones for which
    structure must not be filled but outlined 
    outline (int or float): the width of the vdp and die's outline
    die_layer    (int or array-like[2])
    pad_layer    (int or array-like[2])
    text (string): if None, the text is f"VDP \n{layers_to_probe}"
    
    Returns:
    DIE_VANDP (Device)
    
    """
    
    if text is None : text = layers_to_probe
    DIE_VANDP = Device(f"DIE VAN DER PAUW {text} ")

    ## Create the die 
    w = die_w-2*(pad_size[1]+2*outline)  # width of max device size
    BORDER = die_cell(die_size= (die_w, die_w),
                      device_max_size = (w, w),
                      pad_size = pad_size,
                      contact_w = pad_size[0],
                      contact_l = 0,
                      ports = {'N':1, 'E':1, 'W':1, 'S':1},
                      ports_gnd = ['N', 'E', 'W', 'S'],
                      text = f"VDP \n{text} ",
                      isolation = outline,
                      layer = die_layer,
                      pad_layer = pad_layer,
                      invert = True)
    PADS = pg.deepcopy(BORDER)
    PADS = PADS.remove_layers([pad_layer], invert_selection=True)

    DIE_VANDP << BORDER.flatten()

    ## Create the test structure
    DEVICE = Device()

    # the test structure is an hexagonal shape between the die's ports
    TEST = Device()
    TEST << PADS
    rect = TEST << pg.straight((PADS.ports['E1'].x-PADS.ports['W1'].x, pad_size[0]))
    rect.move(rect.center, (0, 0))
    TEST << pr.route_quad(PADS.ports['N1'], rect.ports[1])
    TEST << pr.route_quad(PADS.ports['S1'], rect.ports[2])
    TEST = pg.union(TEST)

    # outline the test structure for layers that need to be outlined

    if layers_to_outline is None:
        layers_to_outline = [die_layer]
    for layer in layers_to_probe:
        TEST_LAY = pg.deepcopy(TEST)
        if layer in layers_to_outline:
            TEST_LAY = pg.outline(TEST_LAY, outline)
        DEVICE << TEST_LAY.flatten(single_layer = layer)

    DIE_VANDP << DEVICE

    DIE_VANDP = pg.union(DIE_VANDP, by_layer=True)
    DIE_VANDP.name = f"DIE VAN DER PAUW {text} "
    return DIE_VANDP

def create_etch_test_cell(die_w:          Union[int, float],
                          layers_to_etch: List[List[int]],
                          outline_die:    Union[int, float] = dflt_die_outline,
                          die_layer:      int               = dflt_layers['die'],
                          text:           Union[None, str]  = dflt_text):
    """ Creates etch test structures in integer number of unit cells.
    These tests structures are though to be used by probing on pads (with a
    simple multimeter) that should be isolated one with another if the etching
    is complete.
     
    Parameters:
    die_w (int or float): width of a unit die/cell in the design (the output
    device will be a integer number of unit cells)
    layers_to_etch (list of list of int): etch element of the list correspond to
    one test point, to put on the list of layers specified. e.g.: [[1, 2], 1, 2] or [[1]]
    outline_die (int or float): the width of the die's outline
    die_layer (int)
    text (string) 
    
    Returns:
    DIE_ETCH_TEST (Device): a device (with size n*m of unit cells) with etch
    tests in its center
    
    """
    
    if text is None: text = f'{layers_to_etch}'
    DIE_ETCH_TEST = Device(f'DIE ETCH TEST {text} ')

    TEST = Device()
    
    ## Create the probing areas

    margin = 0.12*die_w
    rect = pg.rectangle((die_w-2*margin, die_w-2*margin))
    for i, layer_to_etch in enumerate(layers_to_etch):
        probe = Device()
        probe.add_array(rect, 2, 1, (die_w, die_w))
        for layer in layer_to_etch:
            TEST << pg.outline(probe, -outline_die, layer=layer).movey(i*die_w)

    ## Create the die
            
    n = math.ceil((TEST.xsize + 2*die_cell_border)/die_w)
    m = math.ceil((TEST.ysize + 2*die_cell_border)/die_w)
    BORDER = die_cell(die_size=(n*die_w, m*die_w),
                    ports = {},
                    ports_gnd = {},
                    text = f"ETCH TEST {text}",
                    isolation = 10,
                    layer = die_layer,
                    invert=True)

    BORDER.move(TEST.center)
    DIE_ETCH_TEST << BORDER.flatten()
    DIE_ETCH_TEST << TEST
    DIE_ETCH_TEST.move(DIE_ETCH_TEST.center, (0, 0))

    return DIE_ETCH_TEST

def create_resolution_test_cell(die_w:               Union[int, float],
                                layer_to_resolve:    int,
                                resolutions_to_test: List[float]       = [0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 1, 1.5, 2.0],
                                outline:             Union[int, float] = dflt_die_outline, 
                                die_layer:           int               = dflt_layers['die'],
                                text:                Union[None, str]  = dflt_text):
    """ Creates a cell containing a resolution test.
    
    Parameters: 
    die_w    (int or float): width of a unit die/cell in the design (the output
    device will be a integer number of unit cells)
    layer_to_resolve (int): the layer to put the resolution test on
    resolutions_to_test (list of float): the resolutions to test in µm
    outline (int or float): the width of the vdp and die's outline
    die_layer    (int or array-like[2])
    text (string): if None, the text is f"RES TEST \n{layer_to_resolve}"
    
    Returns:
    DIE_RES_TEST (Device)
    
    """
    
    if text is None : text = layer_to_resolve
    DIE_RES_TEST = Device(f"DIE RESOLUTION TEST {text} ")

    ## Create the test structure
    TEST_RES = Device(f"RESOLUTION TEST {text} ")
    test_res        = TEST_RES << resolution_test(resolutions = resolutions_to_test, 
                                                  inverted = False,
                                                  layer = layer_to_resolve)
    test_res_invert = TEST_RES << resolution_test(resolutions = resolutions_to_test,
                                                  inverted = resolutions_to_test[-1],
                                                  layer = layer_to_resolve)
    test_res_invert.movey(test_res_invert.ymin, test_res.ymax+5*resolutions_to_test[-1])

    DIE_RES_TEST << TEST_RES.move(TEST_RES.center, (0, 0))

    ## Create the die 
    n = math.ceil((TEST_RES.xsize)/die_w)
    m = math.ceil((TEST_RES.ysize)/die_w)
    BORDER = die_cell(die_size= (n*die_w, m*die_w),
                      ports = {},
                      ports_gnd = [],
                      text = f"RES TEST \n{text} ",
                      isolation = outline,
                      layer = die_layer,
                      invert = True)
    
    DIE_RES_TEST << BORDER.flatten()

    return DIE_RES_TEST

# devices:

def create_nanowires_cell(die_w:              Union[int, float], 
                          pad_size:           Tuple[float], 
                          channels_sources_w: List[Tuple[float, float]],
                          overlap_w:          Union[int, float]           = dflt_ebeam_overlap, 
                          outline_die:        Union[int, float]           = dflt_die_outline, 
                          outline_dev:        Union[int, float]           = dflt_device_outline, 
                          device_layer:       int                         = dflt_layers['device'], 
                          die_layer:          int                         = dflt_layers['die'], 
                          pad_layer:          int                         = dflt_layers['pad'],
                          text:               Union[None, str]            = dflt_text):

    """ Creates a cell that contains several nanowires of given channel and source.
    
    Parameters: 
    die_w    (int or float): width of a unit die/cell in the design (the output
    device will be a integer number of unit cells)
    pad_size (int or float, int or float): dimensions of the die's pads (w, h)
    channels_sources_w (List of (float, float)): the list of (channel_w,
    source_w) of the nanowires to create
    overlap_w   (int or float): extra length of the routes above the die's ports
    to assure alignment with the device (useful for ebeam lithography)
    outline_die (int or float): the width of the pads outline
    outline_dev (int or float): the width of the device's outline
    device_layer (int or array-like[2])
    die_layer    (int or array-like[2])
    pad_layer    (int or array-like[2])
    text (string): if None, the text is "NWIRES"
    
    Returns:
    NANOWIRES_DIE (Device) : a device (of size n*m unit cells) containing the
    nanowires, the border of the die (created with die_cell function), and the
    connections between the nanowires and pads
    
    """
    
    if text is None: text = ''

    NANOWIRES_DIE = Device(f'DIE NWIRES {text} ')
    
    DEVICE = Device(f'NWIRES {text} ')

    ## Create the NANOWIRES

    NANOWIRES = Device()
    nanowires_ref = []
    for i, channel_source_w in enumerate(channels_sources_w):
        nanowire_ref = NANOWIRES << nanowire(channel_source_w[0], channel_source_w[1])
        nanowires_ref.append(nanowire_ref)
    DEVICE << NANOWIRES

    ## Create the DIE
        
    # die parameters, checkup conditions
    n = len(channels_sources_w)
    die_size = (math.ceil((2*(n+1) * pad_size[0])/die_w)*die_w, die_w)
    die_contact_w = NANOWIRES.xsize + overlap_w
    dev_contact_w = NANOWIRES.xsize
    routes_margin = 4*die_contact_w 
    dev_max_size = (2*n*pad_size[0], NANOWIRES.ysize + routes_margin)

    # die, with calculated parameters
    BORDER = die_cell(die_size = die_size, 
                    device_max_size = dev_max_size, 
                    pad_size = pad_size,
                    contact_w = die_contact_w,
                    contact_l = overlap_w,
                    ports = {'N':n, 'S':n}, 
                    ports_gnd = ['S'],
                    isolation = outline_die,
                    text = f'NWIRES {text}',
                    layer = die_layer,
                    pad_layer = pad_layer,
                    invert = True)
    
    ## Place the nanowires

    for i, nanowire_ref in enumerate(nanowires_ref):
        nanowire_ref.movex(BORDER.ports[f'N{i+1}'].x)
        NANOWIRES.add_port(port = nanowire_ref.ports[1], name = f'N{i+1}')
        NANOWIRES.add_port(port = nanowire_ref.ports[2], name = f'S{i+1}')

    ## Route the nanowires and the die

    # hyper tapers
    HT, dev_ports = add_hyptap_to_cell(BORDER.get_ports(),
                                       overlap_w,
                                       dev_contact_w)
    DEVICE.ports = dev_ports.ports
    DEVICE << HT

    # routes from nanowires to hyper tapers
    ROUTES = route_to_dev(HT.get_ports(), NANOWIRES.ports)
    DEVICE << ROUTES

    DEVICE.ports = dev_ports.ports
    DEVICE = pg.outline(DEVICE, outline_dev, open_ports=2*outline_dev)
    DEVICE = pg.union(DEVICE, layer=device_layer)
    DEVICE.name = f'NWIRES {text} '

    NANOWIRES_DIE << DEVICE
    NANOWIRES_DIE << BORDER
    
    NANOWIRES_DIE = pg.union(NANOWIRES_DIE, by_layer = True)
    NANOWIRES_DIE.name = f'DIE NWIRES {text} '
    return NANOWIRES_DIE

def create_ntron_cell(die_w:        Union[int, float],
                      pad_size:     Tuple[float, float],
                      choke_w:      Union[int, float],
                      channel_w:    Union[int, float],
                      gate_w:       Union[None, int, float] = auto_param,
                      source_w:     Union[None, int, float] = auto_param,
                      drain_w:      Union[None, int, float] = auto_param,
                      choke_shift:  Union[None, int, float] = auto_param,
                      overlap_w:    Union[None, int, float] = dflt_ebeam_overlap, 
                      outline_die:  Union[None, int, float] = dflt_die_outline, 
                      outline_dev:  Union[None, int, float] = dflt_device_outline,
                      device_layer: int                     = dflt_layers['device'], 
                      die_layer:    int                     = dflt_layers['die'], 
                      pad_layer:    int                     = dflt_layers['pad'],
                      text:         Union[None, str]        = dflt_text):
    """ Creates a standardized cell specifically for a single ntron.
    Unless specified, scales the ntron parameters as:
     gate_w = drain_w = source_w = 3*channel_w
     choke_shift = -3*channel_w
    
    Parameters: 
    die_w    (int or float): width of a unit die/cell in the design (the output
    device will be a integer number of unit cells)
    pad_size (int or float, int or float): dimensions of the die's pads (w, h)
    choke_w   (int or float): the width of the ntron's choke in µm
    channel_w (int or float): the width of the ntron's channel in µm
    gate_w, source_w, drain_w, choke_shift (int or float): if None, those
    parameters or sized with respect to choke_w and channel_w.
    overlap_w   (int or float): extra length of the routes above the die's ports
    to assure alignment with the device (useful for ebeam lithography)
    outline_die (int or float): the width of the pads outline
    outline_dev (int or float): the width of the device's outline
    device_layer (int or array-like[2])
    die_layer    (int or array-like[2])
    pad_layer    (int or array-like[2])
    text (string): if None, the text is the ntron's choke and channel widths
    
    Returns:
    DIE_NTRON : Device, a device containing the ntron, 
    the border of the die (created with die_cell function), 
    and the connections between the ports
    
    """
    

    ## Create the NTRON
    
    # sizes the ntron parameters that were not given
    if source_w is None and drain_w is None:
        drain_w = source_w = 3*channel_w
    elif source_w is None:
        source_w = drain_w
    else:
        drain_w = source_w
    if gate_w is None:
        gate_w = source_w
    if choke_shift is None:
        choke_shift=-3*channel_w

    NTRON = ntron_compassPorts(choke_w, 
                            gate_w, 
                            channel_w, 
                            source_w, 
                            drain_w, 
                            choke_shift, 
                            device_layer)
    
    if text is None: text = f"chk: {choke_w} \nchnl: {channel_w}"
    DIE_NTRON = Device(f"DIE NTRON {text} ")

    DEVICE = Device(f"NTRON {text} ")
    DEVICE << NTRON

    ## Create the DIE
    
    # die parameters, checkup conditions
    die_contact_w = NTRON.ports['N1'].width + overlap_w
    routes_margin = 2*die_contact_w
    dev_min_w = die_contact_w + 3*outline_die # condition imposed by the die parameters (contacts width)
    device_max_w = max(2*routes_margin+max(NTRON.size), dev_min_w)
    
    # the die with calculated parameters
    BORDER = die_cell(die_size = (die_w, die_w),
                    device_max_size = (device_max_w, device_max_w),
                    pad_size = pad_size,
                    contact_w = die_contact_w,
                    contact_l = overlap_w,
                    ports = {'N':1, 'W':1, 'S':1},
                    ports_gnd = ['S'],
                    text = text,
                    isolation = 10,
                    layer = die_layer,
                    pad_layer = pad_layer,
                    invert = True)

    # place the ntron
    NTRON.movex(NTRON.ports['N1'].midpoint[0], BORDER.ports['N1'].midpoint[0])

    # Route DIE and NTRON
    
    # hyper tapers
    dev_contact_w = NTRON.ports['N1'].width
    HT, device_ports = add_hyptap_to_cell(BORDER.get_ports(), overlap_w, dev_contact_w, device_layer)
    DEVICE << HT
    DEVICE.ports = device_ports.ports
    # routes
    ROUTES = route_to_dev(HT.get_ports(), NTRON.ports, device_layer)
    DEVICE << ROUTES

    DEVICE = pg.outline(DEVICE, outline_dev, precision = 0.000001, open_ports=outline_dev)
    DEVICE = pg.union(DEVICE, layer = device_layer)
    DEVICE.name = f"NTRON {text} "

    DIE_NTRON << DEVICE
    DIE_NTRON << BORDER

    DIE_NTRON = pg.union(DIE_NTRON, by_layer = True)
    DIE_NTRON.name = f"DIE NTRON {text} "
    return DIE_NTRON

def create_snspd_ntron_cell(die_w:        Union[int, float], 
                            pad_size:     Tuple[float, float], 
                            w_choke:      Union[int, float], 
                            w_snspd:      Union[int, float] = auto_param, 
                            overlap_w:    Union[int, float] = dflt_ebeam_overlap, 
                            outline_die:  Union[int, float] = dflt_die_outline, 
                            outline_dev:  Union[int, float] = dflt_device_outline, 
                            device_layer: int               = dflt_layers['device'], 
                            die_layer:    int               = dflt_layers['die'], 
                            pad_layer:    int               = dflt_layers['pad'],
                            text:         Union[None, str]  = dflt_text):
    """ Creates a cell that contains an snspd coupled to ntron. 
    The device's parameters are sized according to the snspd's width and the ntron's choke.
    
    Parameters:
    die_w    (int or float): width of a unit die/cell in the design (the output
    device will be a integer number of unit cells)
    pad_size (int or float, int or float): dimensions of the die's pads (w, h)
    w_choke (int or float): the width of the ntron choke in µm
    w_snspd (int or float): the width of the snspd nanowire in µm (if None,
    scaled to 5*w_choke)
    overlap_w   (int or float): extra length of the routes above the die's ports
    to assure alignment with the device (useful for ebeam lithography)
    outline_die (int or float): the width of the pads outline
    outline_dev (int or float): the width of the device's outline
    device_layer (int or array-like[2])
    die_layer    (int or array-like[2])
    pad_layer    (int or array-like[2])
    text (string): if None, text = f'SNSPD {w_choke}'

    Returns:
    DIE_SNSPD_NTRON (Device): a cell containg a die in die_layer, pads in pad layer 
    and a snspd-ntron properly routed in the device layer.
    """

    # Create SNSPD-NTRON
    if w_snspd is None:
        w_snspd = 5*w_choke
    
    if text is None: text = f'SNSPD \n{w_snspd} {w_choke} '
    DIE_SNSPD_NTRON = Device(f"DIE {text} ")
    DEVICE = Device(f"{text} ")

    SNSPD_NTRON = snspd_ntron(w_snspd = w_snspd, 
                            pitch_snspd = 3*w_snspd,
                            size_snspd =(30*w_snspd, 30*w_snspd),
                            w_inductor = 3*w_snspd,
                            pitch_inductor = 6*w_snspd,
                            k_inductor13 = 20*w_snspd,
                            k_inductor2 = 8*w_snspd,
                            w_choke = w_choke,
                            w_channel = 6*w_choke,
                            w_pad = 10*w_snspd,
                            layer = device_layer)
    DEVICE << SNSPD_NTRON

    # Create DIE

    die_contact_w = min(10*SNSPD_NTRON.ports['N1'].width+overlap_w, 0.5*pad_size[0])
    
    routes_margin = 2*die_contact_w
    margin = 2*(pad_size[1] + outline_die + routes_margin)
    n = max(2, math.ceil((SNSPD_NTRON.xsize+margin)/die_w))
    m = max(1, math.ceil((SNSPD_NTRON.ysize+margin)/die_w))

    dev_min_size = [(die_contact_w+3*outline_die)*x for x in (5, 3)] # condition imposed by the die parameters (contacts width)
    device_max_size = (max(min(n*die_w-margin, 8*routes_margin+SNSPD_NTRON.size[0]), dev_min_size[0]), 
                       max(min(m*die_w-margin, 2*routes_margin+SNSPD_NTRON.size[1]), dev_min_size[1]))

    BORDER = die_cell(die_size=(n*die_w, m*die_w), 
                        device_max_size=device_max_size, 
                        pad_size=pad_size,
                        contact_w=die_contact_w,
                        contact_l=overlap_w,
                        ports={'N':3, 'E':1, 'W':1, 'S':2}, 
                        ports_gnd=['S'],
                        text = text,
                        isolation = outline_die,
                        layer = die_layer,
                        pad_layer = pad_layer,
                        invert = True)

    # Route DIE and SNSPD-NTRON
    
    # hyper tapers
    dev_contact_w = min(4*SNSPD_NTRON.ports['N1'].width, 0.8*die_contact_w)
    HT, device_ports = add_hyptap_to_cell(BORDER.get_ports(), overlap_w, dev_contact_w, device_layer)
    DEVICE << HT
    DEVICE.ports = device_ports.ports

    # routes
    ROUTES = route_to_dev(HT.get_ports(), SNSPD_NTRON.ports, device_layer)
    DEVICE << ROUTES

    DEVICE = pg.outline(DEVICE, outline_dev, precision = 0.000001, open_ports=outline_dev)
    DEVICE = pg.union(DEVICE, layer = device_layer)
    DEVICE.name = f"DIE {text} "

    DIE_SNSPD_NTRON << DEVICE
    DIE_SNSPD_NTRON << BORDER

    DIE_SNSPD_NTRON = pg.union(DIE_SNSPD_NTRON, by_layer = True)
    DIE_SNSPD_NTRON.name = f'SNSPD \n{w_snspd} {w_choke} '

    return DIE_SNSPD_NTRON
