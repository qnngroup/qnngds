""" Utilies is used for building cells in design. Cells are made of devices
(found in utilities) and a die_cell border, wich contains pads, text etc... The
device and its die are linked thanks to functions present in this file. """

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
