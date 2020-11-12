# -*- coding: utf-8 -*-
"""
Created on Sat Jan 25 14:03:48 2020

@author: omedeiro

Functions created for the design of SNSPD 

import qnngds.omedeiro as om 

"""
from __future__ import division, print_function, absolute_import
import numpy as np
from phidl import Device
import phidl.geometry as pg
import phidl.routing as pr
from phidl import quickplot as qp
# import colang as mc
import string
from datetime import datetime
import os
import sys
from time import sleep
from phidl.device_layout import _parse_layer, DeviceReference

from argparse import Namespace    



sys.path.append(r'Q:\qnnpy')
import qnnpy.functions.functions as qf



def outline(elements, distance = 1, precision = 1e-4, num_divisions = [1, 1],
            join = 'miter', tolerance = 2, join_first = True,
            max_points = 4000, layer = 0, open_ports=-1, rotate_ports=False):
    """ Creates an outline around all the polygons passed in the `elements`
    argument. `elements` may be a Device, Polygon, or list of Devices.
    Parameters
    ----------
    elements : Device(/Reference), list of Device(/Reference), or Polygon
        Polygons to outline or Device containing polygons to outline.
    distance : int or float
        Distance to offset polygons. Positive values expand, negative shrink.
    precision : float
        Desired precision for rounding vertex coordinates.
    num_divisions : array-like[2] of int
        The number of divisions with which the geometry is divided into 
        multiple rectangular regions. This allows for each region to be 
        processed sequentially, which is more computationally efficient.
    join : {'miter', 'bevel', 'round'}
        Type of join used to create the offset polygon.
    tolerance : int or float
        For miter joints, this number must be at least 2 and it represents the 
        maximal distance in multiples of offset between new vertices and their 
        original position before beveling to avoid spikes at acute joints. For 
        round joints, it indicates the curvature resolution in number of 
        points per full circle.
    join_first : bool
        Join all paths before offsetting to avoid unnecessary joins in 
        adjacent polygon sides.
    max_points : int
        The maximum number of vertices within the resulting polygon.
    layer : int, array-like[2], or set
        Specific layer(s) to put polygon geometry on.
  open_ports : int or float
      Trims the outline at each port of the element. The value of open_port
      scales the length of the trim gemoetry (must be positive). 
      Useful for positive tone layouts. 
    Returns
    -------
    D : Device
        A Device containing the outlined polygon(s).
    """
    D = Device('outline')
    if type(elements) is not list: elements = [elements]
    for e in elements:
        if isinstance(e, Device): D.add_ref(e)
        else: D.add(e)
    gds_layer, gds_datatype = _parse_layer(layer)
    D_bloated = pg.offset(D, distance = distance, join_first = join_first,
                       num_divisions = num_divisions, precision = precision,
                       max_points = max_points, join = join,
                       tolerance = tolerance, layer = layer)
    Outline = pg.boolean(A = D_bloated, B = D, operation = 'A-B',
                      num_divisions = num_divisions, max_points = max_points,
                      precision = precision, layer = layer)
    if open_ports>=0:
      for i in e.ports:
          trim = pg.rectangle(size=(distance, e.ports[i].width+open_ports*distance))

          trim.rotate(e.ports[i].orientation)
          trim.move(trim.center, destination=e.ports[i].midpoint)
          if rotate_ports:
              trim.movex(-np.cos(e.ports[i].orientation/180*np.pi)*distance/2)
              trim.movey(-np.sin(e.ports[i].orientation/180*np.pi)*distance/2)
          else:
              trim.movex(np.cos(e.ports[i].orientation/180*np.pi)*distance/2)
              trim.movey(np.sin(e.ports[i].orientation/180*np.pi)*distance/2)

          Outline = pg.boolean(A = Outline, B = trim, operation = 'A-B',
                     num_divisions = num_divisions, max_points = max_points,
                     precision = precision, layer = layer)
      for i in e.ports: Outline.add_port(port=e.ports[i])
    return Outline


def nw_same_side(wire_width = 0.2, wire_pitch=0.6,size=(22,11),layer = 1):
    """
    Create a two port nanowire meander with 1um ports extended 15um.

    Parameters
    ----------
    wire_width : FLOAT, optional
        MEANDER WIDTH. The default is 0.2.
    wire_pitch : FLOAT, optional
        MEANDER PITCH. The default is 0.6.
    size : TUPLE, optional
        (X,Y) MEANDER AREA DIMENSIONS. The default is (22,11).
    layer : INT, optional
        Layer for device to be created on. The default is 1.

    Returns
    -------
    wire : DEVICE
        PHIDL device object is returned.

    Example
    -------
    qp(om.nw_same_side())
    
    """
    
    wire = Device('wire')
    nw = pg.snspd(wire_width = wire_width, wire_pitch=wire_pitch,size=size,terminals_same_side=True,layer = layer)
    NW = wire.add_ref(nw)
    
    extend = pg.straight(size=(1,15))
    EXTEND = wire.add_ref(extend)
    EXTEND.rotate(-90).move(EXTEND.ports[1],destination=NW.ports[1]).movex(-5)
    
    EXTEND1 = wire.add_ref(extend)
    EXTEND1.rotate(-90).move(EXTEND1.ports[1],destination=NW.ports[2]).movex(-5)
    
    bump = pr.route_basic(NW.ports[1],EXTEND.ports[1],path_type='sine',width_type='sine')
    wire.add_ref(bump)
    
    bump = pr.route_basic(NW.ports[2],EXTEND1.ports[1],path_type='sine',width_type='sine')
    wire.add_ref(bump)
    wire.move(origin=NW.center,destination=(0,0))
    wire.flatten(single_layer=layer)
    wire.add_port(name=1,midpoint=(wire.bbox[0][0],wire.bbox[1][1]-1/2),orientation=180)
    wire.add_port(name=2,midpoint=(wire.bbox[0][0],-wire.bbox[1][1]+1/2),orientation=180)
    

    return wire


def nw_same_side_port(wire_width = 0.2, wire_pitch=0.6,size=(22,11),layer = 1):
    """
    Create a nanowire meander section coupled to two macroscopic ports for
    pad connection. 
    
    Future: define destination as an imput. Make connection straight taper

    Parameters
    ----------
    wire_width : FLOAT, optional
        MEANDER WIDTH. The default is 0.2.
    wire_pitch : FLOAT, optional
        MEANDER PITCH. The default is 0.6.
    size : TUPLE, optional
        (X,Y) MEANDER AREA DIMENSIONS. The default is (22,11).
    layer : INT, optional
        Layer for device to be created on. The default is 1.

    Returns
    -------
    nwOut :  DEVICE
        PHIDL device object is returned.

    """
    
    device = Device('nw')
    WIRE = nw_same_side(wire_width = wire_width, wire_pitch=wire_pitch,size=size,layer=layer)
    WIRE.rotate(-90).move(origin=(0,0),destination=(52.5, 52.2))
    wire = device.add_ref(WIRE)
    
    d = pads_adam_quad(layer=1)
    d.move(origin=d.center,destination=(0,0))
    
    hTAPER = hyper_taper(length = 50, wide_section=45, narrow_section=5,layer=0)
    htaper = device.add_ref(hTAPER)
    htaper.rotate(90).move(origin=htaper.ports['wide'],destination=d.ports['21'])
    ROUT = pr.route_basic(wire.ports[1],htaper.ports['narrow'],width_type='straight',path_type='sine')
    rout = device.add_ref(ROUT)
    
    htaper1 = device.add_ref(hTAPER)
    htaper1.rotate(90).move(origin=htaper1.ports['wide'],destination=d.ports['22'])
    ROUT = pr.route_basic(wire.ports[2],htaper1.ports['narrow'],width_type='straight',path_type='sine')
    rout = device.add_ref(ROUT)

    nwOut = pg.outline(device,distance=.1,precision=1e-4,layer=0)
    trim = pg.rectangle(size=(150,.2))
    trim.move(origin=trim.center,destination=(nwOut.center[0],nwOut.bbox[1][1]))
    t = nwOut.add_ref(trim)
    nwOut = pg.boolean(nwOut,t,'A-B',precision=1e-4,layer=layer)
    nwOut.add_port(name = 'wide0', port = htaper.ports['wide'])
    nwOut.add_port(name = 'wide1', port = htaper1.ports['wide'])

    return nwOut



def nw_same_side_port_single(wire_width = 0.2, wire_pitch=0.6,size=(22,11),terminals_same_side=True,layer = 1, portLoc1 = (37.5,131.25), portLoc2 = (-52.5,131.25),nwLoc = (0,0)):
    """ Broken do not use...
    
    """
    device = Device('nw')
    WIRE = nw_same_side(wire_width = wire_width, wire_pitch=wire_pitch,size=size,terminals_same_side=terminals_same_side,layer=layer)
    WIRE.rotate(-90).move(origin=(0,0),destination=nwLoc)
    wire = device.add_ref(WIRE)
    
    d = pads_adam_quad(layer=1)
    d.move(origin=d.center,destination=(0,0))
    
    hTAPER = hyper_taper(length = 50, wide_section=45, narrow_section=5,layer=0)
    htaper = device.add_ref(hTAPER)
    htaper.rotate(90).move(origin=htaper.ports['wide'],destination=d.ports['23'])
    ROUT = pr.route_basic(wire.ports[1],htaper.ports['narrow'],width_type='straight',path_type='sine')
    rout = device.add_ref(ROUT)
    
    hTAPER1 = hyper_taper(length = 15, wide_section=15, narrow_section=5,layer=0)
    htaper1 = device.add_ref(hTAPER1)
    htaper1.rotate(90).move(origin=htaper1.ports['wide'],destination=[nwLoc[0]-95,nwLoc[1]+95])
    ROUT = pr.route_basic(wire.ports[2],htaper1.ports['narrow'],width_type='straight',path_type='sine')
    rout = device.add_ref(ROUT)

    nwOut = pg.outline(device,distance=.1,precision=1e-4,layer=0)
    trim = pg.rectangle(size=(55,.1))
    trim.move(origin=trim.center,destination=(htaper.center[0],htaper.bbox[1][1]+.05))
    trim1 = pg.rectangle(size=(20,.1))
    trim1.move(origin=trim1.center,destination=(htaper1.center[0],htaper1.bbox[1][1]+.05))

    t = nwOut.add_ref(trim)
    t1 = nwOut.add_ref(trim1)
    nwOut = pg.boolean(nwOut,t,'A-B',precision=1e-4,layer=layer)
    nwOut = pg.boolean(nwOut,t1,'A-B',precision=1e-4,layer=layer)
    nwOut.add_port(name = 'wide0', port = htaper.ports['wide'])
    nwOut.add_port(name = 'wide1', port = htaper1.ports['wide'])
    return nwOut


def heat_sameSidePort(wire_width = 0.2, wire_pitch=0.6,size=(22,11),layer = 1, portLoc1 = (37.5,131.25), portLoc2 = (-52.5,131.25),nwLoc=(0,0)):
    """
    Filled nanowire meander with poits on same side. Used as heater for 
    hTron devices 

    Parameters
    ----------
    wire_width : FLOAT, optional
        MEANDER WIDTH. The default is 0.2.
    wire_pitch : FLOAT, optional
        MEANDER PITCH. The default is 0.6.
    size : TUPLE, optional
        (X,Y) MEANDER AREA DIMENSIONS. The default is (22,11).
    layer : INT, optional
        Layer for device to be created on. The default is 1.

    portLoc1 : TUPLE, optional
        Location of port 1. The default is (37.5,131.25).
    portLoc2 : TUPLE, optional
        Location of port 2. The default is (-52.5,131.25).
    nwLoc : TUPLE, optional
        Location of center of nanowire. The default is (0,0).

    Returns
    -------
    device : DEVICE
        PHIDL device object is returned.

    """
    device = Device('nw')
    WIRE = nw_same_side(wire_width = wire_width, wire_pitch=wire_pitch,size=size,layer=layer)
    WIRE.rotate(-90).move(origin=(0,0),destination=nwLoc)
    wire = device.add_ref(WIRE)
    
    PADc = pg.straight(size=(5,5),layer=layer)
    PADc.move(origin=PADc.ports[2],destination=portLoc1)
    padc = device.add_ref(PADc)
    
    PADl = pg.straight(size=(5,5),layer=layer)
    PADl.move(origin=PADl.ports[2],destination=portLoc2)
    padl = device.add_ref(PADl)
    
    

    
    r1 = pr.route_basic(wire.ports[1],PADc.ports[2],width_type='straight',path_type='sine',layer=layer)
    device.add_ref(r1)
    r2 = pr.route_basic(wire.ports[2],PADl.ports[2],width_type='straight',path_type='sine',layer=layer)
    device.add_ref(r2)
    
    return device




def alignment_marks(locations = ((-3500, -3500), (3500, 3500)), layer = 1):
    """
    Create cross-style alignment marks.

    Parameters
    ----------
    locations : TUPLE, optional
        Tuple of (X,Y) locations. The default is ((-3500, -3500), (3500, 3500)).
    layer : INT, optional
        Layer for device to be created on. The default is 1.
        
        
    Returns
    -------
    marks : DEVICE
        PHIDL device object is returned.

    """
    marks = Device('Marks')
    alignMARK=pg.cross(200,5,layer=layer)

    for i in np.arange(0,len(locations),1):
        alignMark = marks.add_ref(alignMARK)
        alignMark.move(origin=alignMark.center,destination=locations[i])
        
    marks.flatten()
    return marks


def hyper_taper (length, wide_section, narrow_section, layer=1):
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
        hyper_taper = HT.add_polygon(pts, layer = 2)
        HT.add_port(name = 'narrow', midpoint = [0, 0],  width = narrow, orientation = 180)
        HT.add_port(name = 'wide', midpoint = [taper_length, 0],  width = wide, orientation = 0)
        HT.flatten(single_layer = layer)
    return HT


def hyper_taper_outline(length=15, wide_section=80, narrow_section=.1, outline=0.5, layer=1):
    """
    Outlined hyper taper for etch process. Derived from colang's hyper taper

    Parameters
    ----------
    length : FLOAT, optional
        Length of taper. The default is 50.
    wide_section : FLOAT, optional
        Wide width dimension. The default is 30.
    narrow_section : FLOAT, optional
        Narrow width dimension. The default is 5.
    outline : FLOAT, optional
        Width of device outline. The default is 0.5.
    layer : INT, optional
        Layer for device to be created on. The default is 1.
        
        
    Returns
    -------
    ht : DEVICE
        PHIDL device object is returned.

    """
    
    ht = Device('ht')
    hyper_import = hyper_taper(length, wide_section, narrow_section)
    hyper_outline = pg.outline(hyper_import,distance=outline,layer=layer)
    ht.add_ref(hyper_outline)
    
    trim_left = pg.rectangle(size=(outline+.001,narrow_section+2*outline))
    ht.add_ref(trim_left)
    trim_left.move(destination=(-outline,-(narrow_section/2+outline)))
    ht = pg.boolean(ht,trim_left,'A-B', precision=1e-6,layer=layer)
    
    max_y_point = ht.bbox[1,1]
    trim_right = pg.rectangle(size=(outline,2*max_y_point))
    ht.add_ref(trim_right)
    trim_right.move(destination=(length, -max_y_point))
    ht = pg.boolean(ht,trim_right,'A-B', precision=1e-6,layer=layer)
    
    ht.add_port(name = 'narrow', midpoint = [0, 0],  width = narrow_section, orientation = 180)
    ht.add_port(name = 'wide', midpoint = [length, 0],  width = wide_section, orientation = 0)
    ht.flatten(single_layer = layer)

    return ht

def straight_taper(width = 2,length = 10,t_length=10, t_width=100, outline = 1, layer =1):
    S = Device('straight')
    
    s = pg.straight(size=(width, length))
    t = hyper_taper(t_length, t_width, width)
    t.rotate(90)
    t.move(origin=t.ports['narrow'],destination=s.ports[1])
    S.add_ref([s,t])

    S.flatten(single_layer=layer)
    S.add_port(port=s.ports[2], name=1)
    return S

def pad_taper(length=40,  pad_width=250, pad_length = 250, narrow_section=.1, w_outline=5, n_outline=0.2, layer=1):
    """
    Create a pad with tapered connection. 

    Parameters
    ----------
    length : TYPE, optional
        DESCRIPTION. The default is 15.
    pad_width : TYPE, optional
        DESCRIPTION. The default is 80.
    narrow_section : TYPE, optional
        DESCRIPTION. The default is .1.
    w_outline : TYPE, optional
        DESCRIPTION. The default is 5.
    n_outline : TYPE, optional
        DESCRIPTION. The default is 0.1.
    layer : TYPE, optional
        DESCRIPTION. The default is 1.

    Returns
    -------
    ht : TYPE
        DESCRIPTION.

    """
    I = Device('ht')
    hyper_wide1 = hyper_taper(length+w_outline, pad_width, narrow_section, layer=layer)
    pI = pg.rectangle(size=(pad_length,pad_width),layer=layer)
    pI.move(destination=(length+w_outline,-pad_width/2))
    I.add_ref([hyper_wide1,pI])
    
    O = Device('ht')
    hyper_wide2 = hyper_taper(length, pad_width+w_outline*2, narrow_section+n_outline*2,layer=layer)
    pO = pg.rectangle(size=(pad_length+w_outline*2,pad_width+w_outline*2))
    pO.move(destination=(length,-(pad_width+w_outline*2)/2))
    O.add_ref([pO,hyper_wide2])
    
    ht = pg.boolean(O,I,'A-B',precision=1e-6, layer=layer)
    ht.add_port(port=hyper_wide1.ports['narrow'], name=1)
    return ht



def pad_U(pad_width=250, pad_length = 250, width=10, layer=1, port_yshift=0, port_width_add=0):

    D=Device('C')
    C = pg.C(size=(pad_length, pad_width), width=width)
    D.add_ref(C)
    D.flatten(single_layer=layer)
    D.add_port(name=1,midpoint=(pad_length+port_yshift,pad_width/2),width=pad_width+port_width_add, orientation=0)
    return D


def pad_basic(base_size=(200,200), port_size =10, taper_length=100, layer=1):
    """
    Creates a filled pad with port at narrow section. 

    Parameters
    ----------
    base_size : TUPLE, optional
        (X,Y) dimensions of pad. The default is (200,200).
    port_size : FLOAT, optional
        Width of port. The default is 10.
    taper_length : FLOAT, optional
        Dimension of tapered section pad to port. The default is 100.
    layer : INT, optional
        Layer for device to be created on. The default is 1.
        
        
    Returns
    -------
    P : DEVICE
        PHIDL device object is returned.


    """
    P = Device('pad')
    
    base = pg.rectangle(size=base_size)
    taper = pg.taper(length=taper_length,width1=base_size[0],width2=port_size)
    taper.rotate(90)
    taper.move(destination=(base_size[0]/2,base_size[1]))
    
    P.add_ref([base,taper])
    P.flatten(single_layer=layer)
    P.add_port(name='narrow',midpoint=(base_size[0]/2,base_size[1]+taper_length),orientation=90,width=port_size)

    return P
    



def pads_adam(trim = [True,True,True],  layer = 1):
    """
    Create three pads using adam's design 
    Trim indicates if the pad should be open (connecting to a device on the
    same layer), or closed (connecting to device on a second layer).
    
    if only 1 pad is required use only one Trim specification
    
    Ports are added at each pad. Name: 1,2,3

    Parameters
    ----------
    trim : LIST, optional
        Trim indicates if the pad should be open (connecting to a device on the
        same layer), or closed (connecting to device on a second layer).
        List should be size 1-3 (for the number of desired pads) of T/F 
        booleans. 
        The default is [True,True,True].
        
    layer : INT, optional
        Layer for device to be created on. The default is 1.

    Returns
    -------
    OUT : DEVICE
        PHIDL device object is returned.
        
    Example
    -------
    qp(om.pads_adam())

    """
    threePad = Device('cell')
    
    base = pg.straight(size = (150,250),layer=layer)
    post = pg.straight(size = (25,25),layer=layer)
    
    b1 = threePad.add_ref(base)
    b2 = threePad.add_ref(base)
    b2.movex(170)
    b3 = threePad.add_ref(base)
    b3.movex(-170)
    
    p1 = threePad.add_ref(post)
    p1.move(origin=p1.center,destination=b1.center).movey(225)
    p2 = threePad.add_ref(post)
    p2.move(origin=p2.center,destination=p1.center).movex(90)
    p3 = threePad.add_ref(post)
    p3.move(origin=p3.center,destination=p1.center).movex(-90)
    
    r1 = pr.route_basic(b1.ports[1],p1.ports[2],path_type='straight',width_type='straight',num_path_pts=50, width1 = 25,layer=layer)
    threePad.add_ref(r1)
    r2 = pr.route_basic(b2.ports[1],p2.ports[2],path_type='straight',width_type='straight',num_path_pts=50, width1 = 25,layer=layer)
    threePad.add_ref(r2)
    r3 = pr.route_basic(b3.ports[1],p3.ports[2],path_type='straight',width_type='straight',num_path_pts=50, width1 = 25,layer=layer)
    threePad.add_ref(r3)

    OUT = pg.outline(threePad,distance = 5,precision=0.0001,layer = layer)

    for i in range(len(trim)):
        if trim[i] == True:
            trimpoly = pg.rectangle(size=(35,5),layer = layer)
            t1 = OUT.add_ref(trimpoly)
            t1.move(origin=t1.center,destination=(-15+90*i,365))
            OUT = pg.boolean(OUT,t1,'A-B',precision=1e-4,layer=layer)
    OUT.add_port(name = 1, midpoint=(-15,340),width=25,orientation=90)    
    OUT.add_port(name = 2, midpoint=(75,340),width=25,orientation=90)
    OUT.add_port(name = 3, midpoint=(165,340),width=25,orientation=90)
    return OUT


def pads_adam_quad(trim = ((True,True,True),(True,True,True),(True,True,True),(True,True,True)), layer = 1):
    """
    pads_adam_quad takes three pads and aranges them in a square. 
    
    Trim is a tuple of 4x3 T/F booleans for deciding what pads should be open 
    or closed.
    
    Ports are added at each pad. Name: 01,02,03,11,12,13,21,...33
    

    Parameters
    ----------
    trim : TUPLE, optional
        Trim indicates if the pad should be open (connecting to a device on the
        same layer), or closed (connecting to device on a second layer).
        List should be size 1-3 (for the number of desired pads) of T/F booleans. 
       The default is ((True,True,True),(True,True,True),(True,True,True),(True,True,True)).
    layer : INT, optional
        Layer for device to be created on. The default is 1.
    
    Returns
    -------
    quadPad : DEVICE
        PHIDL device object is returned.

    """
    
    quadPad = Device('quad')
    for i in range(4):
        quarter = pads_adam(trim[i],layer=layer)
        quarter.move(origin=quarter.center,destination=(0,0))
        quarter.rotate(angle = 90*i, center = (0,345))
        q = quadPad.add_ref(quarter)
        quadPad.add_port(name=str(i)+'1', port = quarter.ports[1])
        quadPad.add_port(name=str(i)+'2', port = quarter.ports[2])
        quadPad.add_port(name=str(i)+'3', port = quarter.ports[3])
    return quadPad
        
    
def pads_adam_fill(style = 'right',layer = 1):
    """
    Filled Adam style pad for lift-off process. 


    Parameters
    ----------
    style : STRING, optional
        'left', 'right', 'center' specification for pad-port direction. 
        The default is 'right'.
    layer : INT, optional
        Layer for device to be created on. The default is 1.

    Returns
    -------
    pad_cover : DEVICE
        PHIDL device object is returned.

    """
    pad_cover = Device('pad_cover')
    base = pg.straight(size = (140,240),layer=layer)
    post = pg.straight(size = (20,50),layer=layer)
    
       
    
    if style =='center':
        b1 = pad_cover.add_ref(base)
            
        p1 = pad_cover.add_ref(post)
        p1.move(origin=p1.center,destination=b1.center).movey(225)
            
        r1 = pr.route_basic(b1.ports[1],p1.ports[2],path_type='straight',width_type='straight',num_path_pts=50, width1 = 20,layer=layer)
        pad_cover.add_ref(r1)
    if style == 'right':    
        b1 = pad_cover.add_ref(base)
        b1.movex(170)
        p1 = pad_cover.add_ref(post)
        p1.move(origin=p1.center,destination=b1.center).movex(90).movey(225)
        r1 = pr.route_basic(b1.ports[1],p1.ports[2],path_type='straight',width_type='straight',num_path_pts=50, width1 = 20,layer=layer)
        pad_cover.add_ref(r1)
    if style =='left':    
        b1 = pad_cover.add_ref(base)
        b1.movex(-170)

        p1 = pad_cover.add_ref(post)
        p1.move(origin=p1.center,destination=b1.center).movex(-90).movey(225)

        r1 = pr.route_basic(b1.ports[1],p1.ports[2],path_type='straight',width_type='straight',num_path_pts=50, width1 = 20,layer=layer)
        pad_cover.add_ref(r1)

#    OUT = pg.outline(pad_cover,distance = 5,precision=0.0001,layer = layer)
    pad_cover.add_port(name=1,port=p1.ports[1])
    return pad_cover

def resistor_pos(size=(6,20), width=20, length=40, overhang=10, pos_outline=.5, layer=1, rlayer=2):
        rwidth=size[0]
        rlength=size[1]
        spacing=rlength-overhang
        res = pg.straight((rwidth,rlength),layer=rlayer)       
        s1 = pg.outline(pg.straight((width, length+spacing)),
                        distance=pos_outline, layer=layer, open_ports=pos_outline)
        
        rout = pg.straight((width+pos_outline*2,
                            rlength-overhang),
                           layer=layer)     
        rout.move(rout.ports[2],s1.ports[1])
        
        res.move(res.center,rout.center)
        
        s2 = pg.outline(pg.straight((width,length+spacing)),
                        distance=pos_outline, layer=layer, open_ports=2)
        
        s2.move(s2.ports[2],rout.ports[1])
        
        D = Device('resistor')
        D.add_ref([res,s1, rout, s2])
        D.flatten()
        D.add_port(s1.ports[2])
        D.add_port(s2.ports[1])
        qp(D)
        return D

def packer(
        D_list,
        text_letter,
        text_pos= None,
        text_layer=1,
        text_height=50,
        spacing = 10,
        aspect_ratio = (1,1),
        max_size = (None,None),
        sort_by_area = True,
        density = 1.1,
        precision = 1e-2,
        verbose = False,
        ):
    """
    Returns Device "p" with references from D_list. Names, or index, of each device is assigned and can be called from p.references[i].parent.name


    Parameters
    ----------
    D_list : TYPE
        DESCRIPTION.
    text_letter : TYPE
        DESCRIPTION.
    text_pos : TYPE, optional
        DESCRIPTION. The default is None.
    text_layer : TYPE, optional
        DESCRIPTION. The default is 1.
    text_height : TYPE, optional
        DESCRIPTION. The default is 50.
    spacing : TYPE, optional
        DESCRIPTION. The default is 10.
    aspect_ratio : TYPE, optional
        DESCRIPTION. The default is (1,1).
    max_size : TYPE, optional
        DESCRIPTION. The default is (None,None).
    sort_by_area : TYPE, optional
        DESCRIPTION. The default is True.
    density : TYPE, optional
        DESCRIPTION. The default is 1.1.
    precision : TYPE, optional
        DESCRIPTION. The default is 1e-2.
    verbose : TYPE, optional
        DESCRIPTION. The default is False.
     : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    p=[]
    p = pg.packer(D_list,
        spacing = spacing,
        aspect_ratio = aspect_ratio,
        max_size = max_size,
        sort_by_area = sort_by_area,
        density = density,
        precision = precision,
        verbose = verbose,
        )
    

    
    for i in range(len(p[0].references)):
        device_text = text_letter+str(i)
        text_object = pg.text(text=device_text, size = text_height, justify='left', layer=text_layer)
        t = p[0].references[i].parent.add_ref(text_object)
        t.move(origin=text_object.bbox[0], destination= (text_pos[0], text_pos[1]))

        p[0].references[i].parent.name = device_text
        
    p = p[0]
    # p.flatten() # do not flatten.
    
    return p

    
def packer_rect(device_list, dimensions, spacing, text_pos=None, text_size = 50, text_layer = 1):
    """
    This function distributes devices from a list onto a rectangular grid. The aspect ratio (dimensions) and spacing must be specified.
    If specified, text can be added automatically in a A1, B2, C3, style. The text will start with A0 in the NW corner.

    Parameters
    ----------
    device_list : LIST
        LIST OF PHIDL DEVICE OBJECTS
    dimensions : TUPLE
        (X,Y) X BY Y GRID POINTS
    spacing : TUPLE
        (dX,dY) SPACING BETWEEN GRID POINTS
    text_pos : TUPLE, optional
        IF SPECIFIED THE GENERATED TEXT IS LOCATED AT (dX,dY) FROM SW CORNER. The default is None.
    text_size : INT, optional
        SIZE OF TEXT LABEL. The default is 50.
    text_layer : INT, optional
        LAYER TO ADD TEXT LABEL TO The default is 1.

    Returns
    -------
    D : DEVICE
        PHIDL device object. List is entered and a single device is returned with labels.
    text_list : LIST
        LIST of strings of device labels.

    """
    
    letters = list(string.ascii_uppercase)

    while len(device_list) < np.product(dimensions):
        device_list.append(None)
    
    new_shape = np.reshape(device_list,dimensions)
    text_list=[]
    D = Device('return')
    for i in range(dimensions[0]):
        for j in range(dimensions[1]):
            if not new_shape[i][j] == None:
                moved_device = new_shape[i][j].move(origin=new_shape[i][j].bbox[0], destination=(i*spacing[0], -j*spacing[1]))
                D.add_ref(moved_device)
                if text_pos:
                    device_text = letters[i]+str(j)
                    text_list.append(device_text)
                    text_object = pg.text(text=device_text, size = text_size, justify='left', layer=text_layer)
                    text_object.move(destination= (i*spacing[0]+text_pos[0], -j*spacing[1]+text_pos[1]))
                    D.add_ref(text_object)

    return D, text_list
    
   
def packer_doc(D_pack_list):
    """
    This function creates a text document to be referenced during meansurement.
    Its primary purpose is to serve as a reference for device specifications on chip.
    For instance, "A2 is a 3um device."
    
    Currently. This function really only works with D_pack_list from packer(). 
    It looks at each reference and grabs the device parameters (which are hard coded).
    'line.append(str(D_pack_list[i].references[j].parent.width))'
    It would be great to have this as a dynamical property that can be expounded for every kind of device/parameter.
    
    'create_device_doc' predated this function and took every np.array parameter in the parameter-dict and wrote it to a .txt file.
    The main problem with this function is that the device name is not associated in the parameter-dict.
    
    Inputs
    ----------
    sample: STRING
        enter a sample name "SPX000". The file path will be generated on the NAS and the .txt file will be saved there. 
    
    Parameters
    ----------
    D_pack_list : LIST
        List containing PHIDL Device objects.

    Returns
    -------
    None.

    """
    
    """ Safety net for writing to the correct location"""
    
    sample = input('enter a sample name: ')
    if sample == '':
        print('Doc not created')
        return
    else:
        path = os.path.join('S:\SC\Measurements',sample)
        os.makedirs(path, exist_ok=True)
    
        path = os.path.join('S:\SC\Measurements',sample, sample+'_device_doc.txt')
        
        file = open(path, "w")
        
        tab = ',\t'    
        string_list=[]
        headers = ['ID', 'WIDTH', 'AREA', 'SQUARES']   
        headers.append('\n----------------------------------\n')
        
        for i in range(len(D_pack_list)):
            for j in range(len(D_pack_list[i].references)):
                line = []
                line.append(str(D_pack_list[i].references[j].parent.name))
                line.append(str(D_pack_list[i].references[j].parent.width))
                line.append(str(D_pack_list[i].references[j].parent.area))
                line.append(str(D_pack_list[i].references[j].parent.squares))
                
                line.append('\n')
                string_list.append(tab.join(line))
                string_list.append('. . . . . . . . . . . . . . . . \n')
            string_list.append('\\-----------------------------------\\ \n')
        
        file.write(tab.join(headers))
        file.writelines(string_list)
        file.close()



def assign_ids(device_list, ids):
    """
    Attach device ID to device list.

    Parameters
    ----------
    device_list : LIST
        List of phidl device objects.
    ids : LIST
        list of identification strings. 
        typically generated from packer_rect/text_labels.

    Returns
    -------
    None.

    """    
    device_list = list(filter(None,device_list))
    for i in range(len(device_list)):
        device_list[i].name = ids[i]
        
   
def text_labels(device_list, adjust_position = (0,0), text_size = 40, layer = 1):
    """ SORTA BROKEN
    This function accepts list of device objects. Each coordinate is extracted 
    from the list and the text is generated automatically.
        
    Labels are generated from SE to NW.
        
            

    Parameters
    ----------
    device_list : TYPE
        DESCRIPTION.
    adjust_position : TYPE, optional
        DESCRIPTION. The default is (0,0).
    text_size : TYPE, optional
        DESCRIPTION. The default is 40.
    layer : TYPE, optional
        DESCRIPTION. The default is 1.

    Returns
    -------
    D : TYPE
        DESCRIPTION.

    """
    
    number_of_devices = np.size(device_list)
    x_locations = []
    y_locations = []
    
    for i in range(number_of_devices):
        if not device_list[i] == None:
            x = device_list[i].bbox[0][0]
            y = device_list[i].bbox[0][1]
            x_locations.append(x)
            y_locations.append(y)
        
    letters = list(string.ascii_uppercase)

    x_reduced = list(set(np.round(x_locations,decimals=0)))
    y_reduced = list(set(np.round(y_locations,decimals=0)))
    x_reduced.sort(); y_reduced.sort()
    count=0
    
    D = Device('return')
    for i in range(len(x_reduced)):
        for j in range(len(y_reduced)):
            print(i, j)
            count += 1
            device_text = letters[i]+str(j)

            text_object = pg.text(text=device_text, size = text_size, justify='left', layer=layer)
            text_object.move(destination= (x_reduced[i]+adjust_position[0], y_reduced[j]+adjust_position[1]))
            
            D.add_ref(text_object)
            
            if count >= number_of_devices-1:
                break
    return D
    
def save_gds(device, prop_dict, filename, path=None):
    """
    This function accepts a device to be converted to GDS and a property 
    dictionary. 

    Parameters
    ----------
    device : TYPE
        DESCRIPTION.
    prop_dict : TYPE
        DESCRIPTION.
    filename : TYPE
        DESCRIPTION.
    path : TYPE, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    None.

    """
    time_str = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    filename = filename+"_"+time_str
    if path:
        os.makedirs(path, exist_ok=True)
        full_path = os.path.join(path,filename)
        print(full_path)
        device.write_gds(full_path)
    else:
        full_path = os.getcwd()
        device.write_gds(filename)
        
    
    qf.output_log(prop_dict, full_path)
    
    
    
    
def outline_invert(device, polygon=None):
    """
    This function takes a outlined device (for positive tone resist and etch
    process) and inverts the device. 
    
    Works with mc.meander

    Parameters
    ----------
    device : DEVICE
        PHIDL device object.
    polygon : INT, optional
        After the boolean operation there are typically three polygons the 
        snspd and two trimmed pieces. Somtimes there is a problem with 
        returning the correct one. 
        This parameter can be used to change the selection. The default is None.

    Returns
    -------
    I : DEVICE
        PHIDL device object.

    """
    device.move(origin=device.bbox[0],destination=(0,0))
    sw = device.bbox[0]
    ne = device.bbox[1]
    
    box = pg.rectangle(size=(ne[0]-sw[0],ne[1]-sw[1]))
    box.move(origin=box.bbox[0], destination=sw)
    
    inverse = pg.boolean(device,box,'B-A', layer=1, precision=1e-7)
    I = Device('inversepoly')
    if polygon:
        for poly in polygon:
            I.add_polygon(inverse.polygons[poly])
    else:
        I.add_polygon(inverse.polygons[1])

    I.move(origin = I.bbox[0], destination=(0,0))

    return I


def create_device_doc(D_pack_list):
    """
    Creates text file containing the parameters related to the device IDs.
    Automatically saved in the corrspoinding sample folder. 
    
    Only parameters that TYPE: np.array are shown in the table. 
    The entire parameter dictionary is saved with the save_gds
    
    Sample name is entered as an imput. This ensures that the file is saved 
    in the correct location.
    
    Parameters
    ----------
    D_pack : LIST 
        list of lists containing phidl device objects with parameters and names attached. 
        


    Returns
    -------
    None.

    """
    
    sample = input('enter a sample name: ')
    
    if sample=='':
        print('Device document not created')
        return
    
    path = os.path.join('S:\SC\Measurements',sample)
    os.makedirs(path, exist_ok=True)
    
    path = os.path.join('S:\SC\Measurements',sample, sample+'_device_doc.txt')
    
    file = open(path, "w")


    tab = '\t'    
    txt_spacing = 20 #there is probably a better method 
    """ Loop through list of sublists """
    for i in range(len(D_pack_list)):
        headers = []   #new headers because each sublist could be a different device. 
        string_list=[]
        
        headers.append('ID'+' '*(txt_spacing-2))
        headers.append('TYPE'+' '*(txt_spacing-4))
        
        """ Loop through references in sublist"""
        for j in range(len(D_pack_list[i].references)):
            line=[]
            name = D_pack_list[i].references[j].parent.name
            line.append(name+ (txt_spacing-len(name))*' ') #append device name
            typE = D_pack_list[i].references[j].parent.type
            line.append(typE+ (txt_spacing-len(typE))*' ') #append device type

            #All references in in D_pack_list will have identical parameters. Hence references[0]
            for key in D_pack_list[i].references[0].parent.parameters: 
                
                # Only save parameters in DOC that are changing. 
                # If the parameter is an array then the array will be the length of the array will be the same as the references length.
                if type(D_pack_list[i].references[0].parent.parameters[key]) == np.ndarray:
                    if j == 0: #If it is the first of the loop append name of columns
                        headers.append(key+(txt_spacing-len(key))*' ')
                    text = str(D_pack_list[i].references[0].parent.parameters[key][j].round(4))
                    line.append(text + (txt_spacing-len(text))*' ')

            line.append('\n')
            string_list.append('.'*len(tab.join(line))+' \n')
            string_list.append(tab.join(line))
            # string_list.append('.'*len(tab.join(line))+' \n')
        string_list.append('\\'+'-'*(len(tab.join(line)))+'\\ \n')
    
        headers.append('\n')
        file.write('\\'+'-'*(len(tab.join(line)))+'\\ \n')
        file.write(tab.join(headers))
        file.writelines(string_list)
    file.close()
    
 
    
def squares_meander_calc(width, area, pitch):
    """
    CALCULATE THE NUMBER OF SQUARES OF A SQUARE SNSPD MEANDER.
    
    Parameters
    ----------
    width : FLOAT
        SNSPD WIDTH.
    area : FLOAT
        SNSPD AREA. ASSUMING A SQUARE DETECTOR
    pitch : FLOAT
        SNSPD PITCH.
        

    Returns
    -------
    squares : FLOAT
        ROUGH CALCULATION OF THE NUMBER OF SQUARES OF A SQUARE SNSPD MEANDER.

    """
    
    number_of_lines = area / (width + pitch)
    squares_per_line = area/width
    
    squares = squares_per_line*number_of_lines
    return round(squares)


def reset_time_calc(width=1, area=10, pitch=2, Ls=80, RL = 50, squares = None):
    """
    CALCULATE SNSPD RESET TIME BASED ON GEOMETRY AND INDUCTANCE. 
    
    Parameters
    ----------
    width : FLOAT
        SNSPD WIDTH.
    area : FLOAT
        SNSPD AREA.
    pitch : FLOAT
        SNSPD PITCH.
    Ls : FLOAT
        SHEET INDUCTANCE.
    RL : FLOAT, optional
        LOAD RESISTANCE. The default is 50.
    squares : FLOAT, optional
        Predetermined number of squares. Input instead of geometry. 

    Returns
    -------
    reset_time : FLOAT
        SNSPD RESET TIME IN (ns).

    """
    if squares != None:
        sq = squares
    else:
        sq = squares_meander_calc(width, area, pitch)
    
    Lk = Ls*sq*1e-3 #Kinetic inductance in nH
    
    reset_time = 3*(Lk/RL)
    print('Squares %0.f, Reset time(ns) %0.f' %(sq,reset_time))
    return reset_time

    
 

def meander(width=0.1, pitch=0.250, area=8, length=None, number_of_paths=1, layer=1, terminals_same_side=False):
    """
    

    Parameters
    ----------
    width : FLOAT, optional
        SNSPD wire width. The default is 0.1.
    pitch : FLOAT, optional
        SNSPD wire pitch. The default is 0.250.
    area : FLOAT, optional
        SNSPD overall Y dimension, and or snspd area if Length is not specified. The default is 8.
    length : FLOAT, optional
        SNSPD overall X dimension. The default is None.
    number_of_paths : INT, optional
        Number of times the SNSPD traverses over the Y dimension. This value is limited by the length of the SNSPD The default is 1.

    Returns
    -------
    X : Device
        PHIDL device object is returned.

    """
    D=Device('x')
    X=Device('big')
    
    n=number_of_paths
    if length==None:
        length = area/number_of_paths
    else:
        length = (length-0.5*(number_of_paths-1))/number_of_paths
        
        
    S=pg.snspd(wire_width = width, wire_pitch = pitch+width, size = (length,area), terminals_same_side = terminals_same_side)
    
    if n==1:
        S=pg.snspd(wire_width = width, wire_pitch = pitch+width, size = (length,area), terminals_same_side = terminals_same_side)
        s=D.add_ref(S)
    
    i=0    
    while i < n:
        s=D.add_ref(S)
        if i==0:
            start=s.ports[1].midpoint
        if np.mod(i,2)!=0:
            s.mirror((0,1),(1,1))
        if i>0:
            s.move(origin=s.ports[1], destination=straight.ports[2])
        if i != n-1:
            straight=D.add_ref(pg.straight(size=(width,0.5),  layer = 0))
            straight.rotate(90)
            straight.move(straight.ports[1], s.ports[2])
        if i == n-1:
            end=s.ports[2].midpoint
        i=i+1
    D.flatten(single_layer=layer)    
    X=pg.deepcopy(D)
    X.add_port(name=1, midpoint = start, width=width, orientation=180)
    X.add_port(name=2, midpoint = end, width=width, orientation=0)
    X.move(origin=X.ports[1], destination=(0,0))
    return X



def snspd_pad_bilayer(parameters=None, sheet_inductance = 300):
    """

    """
    ''' Default parameters for example testing '''
    if parameters == None: 
        parameters = {
                'pad_outline': 7,
                'pad_taper_length': 40,
                'snspd_outline': .2,
                'snspd_width': np.array([1]),
                'snspd_fill': 0.50,
                'snspd_area': np.array([30]),
                'ground_taper_length': 10,
                'pad_width': 200,
                'ground_taper_width': 50,
                'snspd_layer': 1,
                'pad_layer': 2
                }
    
    """ Get length of parameters """ 
    for key in parameters:
            if type(parameters[key]) == np.ndarray:
                parameter_length = len(parameters[key])
                break
            else:
                parameter_length = 0
    
    # """ Convert dictionary keys to local variables """
    # globals().update(parameters) #I love this, but, every variable appears to be undefined. 
    
    """ Convert dictionary keys to namespace """
    n = Namespace(**parameters) #This method of converting dictionary removes "Undefined name" warning
    
    
    """ Generate list of devices from parameters 
        Additionally, this loop will calculate the number of squares of each device. 
    """
    device_list = []
    device_squares_list = []
    for i in range(parameter_length):
        D = Device('snspd')    
        detector = meander(width = n.snspd_width[i],
                              pitch = n.snspd_width[i]/n.snspd_fill-n.snspd_width[i],
                              area = n.snspd_area[i],
                              layer = n.snspd_layer,
                              )
        detector = outline(detector,distance=n.snspd_outline,open_ports=2)
        pad = pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(180)
        
        inductor_squares = squares_meander_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i])
        device_squares = inductor_squares
        reset_time = reset_time_calc(squares = device_squares, Ls=sheet_inductance)

        device_squares_list.append(device_squares)
        
        pad_taper = outline(hyper_taper(40, n.pad_width+n.pad_outline,n.snspd_width[i],n.snspd_layer), distance=n.snspd_outline,open_ports=2)
        pad_taper.move(pad_taper.ports['wide'], pad.ports[1]).movex(10)
        detector.move(origin=detector.ports[2],destination=pad_taper.ports['narrow'])

        
        ground_taper = outline(hyper_taper(n.ground_taper_length,n.ground_taper_width, n.snspd_width[i],n.snspd_layer),distance=n.snspd_outline, open_ports=2)
        ground_taper.rotate(180)
        ground_taper.move(origin=ground_taper.ports['narrow'],destination=detector.ports[1])
                


        D.add_ref([pad_taper,detector, ground_taper])
        D.flatten(single_layer=n.snspd_layer)
        D.add_ref(pad)
        D.rotate(-90)
        D.move(D.bbox[0],destination=(0,0))

        # qp(D)
        # """ Attach dynamical parameters to device object. """
        D.width = n.snspd_width[i]
        D.area = n.snspd_area[i]
        D.squares = device_squares
        D.parameters = parameters
        D.type = 'meander_snspd'
        device_list.append(D)
        
    # """ Attach squares calculation to parameters """
    parameters['snspd_squares']=np.array(device_squares_list)
    return device_list


def straight_snspd_pad_bilayer(parameters=None, sheet_inductance = 300):
    """

    """
    ''' Default parameters for example testing '''
    if parameters == None: 
        parameters = {
                'pad_outline': 7,
                'pad_taper_length': 40,
                'snspd_outline': .2,
                'snspd_width': np.array([1]),
                'snspd_fill': 0.50,
                'snspd_area': np.array([30]),
                'ground_taper_length': 40,
                'pad_width': 200,
                'ground_taper_width': 150,
                'snspd_layer': 1,
                'pad_layer': 2,
                'straight_width':np.array([.1]),
                'straight_length':np.array([50])
                }
    
    """ Get length of parameters """ 
    for key in parameters:
            if type(parameters[key]) == np.ndarray:
                parameter_length = len(parameters[key])
                break
            else:
                parameter_length = 0
    
    # """ Convert dictionary keys to local variables """
    # globals().update(parameters) #I love this, but, every variable appears to be undefined. 
    
    """ Convert dictionary keys to namespace """
    n = Namespace(**parameters) #This method of converting dictionary removes "Undefined name" warning
    
    
    """ Generate list of devices from parameters 
        Additionally, this loop will calculate the number of squares of each device. 
    """
    device_list = []
    device_squares_list = []
    for i in range(parameter_length):
        D = Device('snspd')    
        detector = meander(width = n.snspd_width[i],
                              pitch = n.snspd_width[i]/n.snspd_fill-n.snspd_width[i],
                              area = n.snspd_area[i],
                              layer = n.snspd_layer,
                              )
        detector = outline(detector,distance=n.snspd_outline,open_ports=2)
        pad = pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(180)
        inductor_squares = squares_meander_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i])
        straight_squares = n.straight_length[i]/n.straight_width[i]
        device_squares = inductor_squares + straight_squares
        reset_time = reset_time_calc(squares = device_squares, Ls=sheet_inductance)
        print('- straight squares:%0.f - inductor_squares:%0.f' %(straight_squares, inductor_squares))
        device_squares_list.append(device_squares)
        
        pad_taper = outline(hyper_taper(40, n.pad_width+n.pad_outline,n.snspd_width[i],n.snspd_layer), distance=n.snspd_outline,open_ports=2)
        pad_taper.move(pad_taper.ports['wide'], pad.ports[1]).movex(10)
        detector.move(origin=detector.ports[2],destination=pad_taper.ports['narrow'])
        
        bend1 = outline(pg.optimal_90deg(n.snspd_width[i]), distance=n.snspd_outline, open_ports=2)
        bend1.rotate(-90)
        bend1.move(bend1.ports[1],detector.ports[1])
        
        step1 = outline(pg.optimal_step(n.straight_width[i],n.snspd_width[i], num_pts=100),distance=n.snspd_outline, open_ports=3)
        step1.rotate(90)
        step1.move(step1.ports[2],bend1.ports[2])
        
        STRAIGHT = outline(pg.straight((n.straight_width[i],n.straight_length[i])),distance=n.snspd_outline, open_ports=2)
        STRAIGHT.move(STRAIGHT.ports[1], step1.ports[1])
                
        step2 = outline(pg.optimal_step(n.snspd_width[i],n.straight_width[i], num_pts=100),distance=n.snspd_outline, open_ports=3)
        step2.rotate(90)
        step2.move(step2.ports[2],STRAIGHT.ports[2])
        
        bend2 = outline(pg.optimal_90deg(n.snspd_width[i]), distance=n.snspd_outline, open_ports=3)
        bend2.rotate(90)
        bend2.move(bend2.ports[2],step2.ports[1])

        
        ground_taper = outline(hyper_taper(n.ground_taper_length,n.ground_taper_width, n.snspd_width[i],n.snspd_layer),distance=n.snspd_outline, open_ports=2)
        ground_taper.rotate(180)
        ground_taper.move(origin=ground_taper.ports['narrow'],destination=bend2.ports[1])
        

        D.add_ref([pad_taper,detector,bend1, step1, STRAIGHT, step2, bend2, ground_taper])#,bend1,STRAIGHT, bend2, ground_taper])
        D.flatten(single_layer=n.snspd_layer)
        D.add_ref(pad)
        D.rotate(-90)
        D.move(D.bbox[0],destination=(0,0))

        # """ Attach dynamical parameters to device object. """
        D.width = n.snspd_width[i]
        D.area = n.snspd_area[i]
        D.squares = device_squares
        D.parameters = parameters
        D.type = 'straight_snspd'

        device_list.append(D)
        
    # """ Attach squares calculation to parameters """
    # parameters['snspd_squares']=np.array(device_squares_list)
    return device_list



def straight_wire_pad_bilayer(parameters=None, sheet_inductance = 300):
    """

    """
    ''' Default parameters for example testing '''
    if parameters == None: 
        parameters = {
                'pad_width': 200,
                'pad_outline': 7,
                'pad_taper_length': 40,
                'ground_taper_length': 10,
                'ground_taper_width': 20,
                'straight_outline': 0.2,
                'straight_width':np.array([.1]),
                'straight_length':np.array([40]),
                'straight_layer': 1,
                'pad_layer': 2
                }
    
    """ Get length of parameters """ 
    for key in parameters:
            if type(parameters[key]) == np.ndarray:
                parameter_length = len(parameters[key])
                break
            else:
                parameter_length = 0
    
    # """ Convert dictionary keys to local variables """
    # globals().update(parameters) #I love this, but, every variable appears to be undefined. 
    
    """ Convert dictionary keys to namespace """
    n = Namespace(**parameters) #This method of converting dictionary removes "Undefined name" warning
    
    
    """ Generate list of devices from parameters 
        Additionally, this loop will calculate the number of squares of each device. 
    """
    device_list = []
    device_squares_list = []
    step_scale = 4
    for i in range(parameter_length):
        D = Device('wire')    

        straight_squares = n.straight_length[i]/n.straight_width[i]
        reset_time = reset_time_calc(squares = straight_squares, Ls=sheet_inductance)
        device_squares_list.append(straight_squares)
        
        
        
        ######################################################################

        detector = outline(pg.straight((n.straight_width[i],n.straight_length[i])),distance=n.straight_outline, open_ports=2)
        
        pad = pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(180)

        pad_taper = outline(hyper_taper(40, n.pad_width+n.pad_outline,n.straight_width[i]*step_scale),distance=n.straight_outline, open_ports=2)
        pad_taper.move(pad_taper.ports['wide'], pad.ports[1]).movex(10)
        
        step1 = outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]),distance=n.straight_outline, open_ports=3)
        step1.rotate(180)
        step1.move(step1.ports[1],pad_taper.ports['narrow'])
        
        detector.rotate(90)
        detector.move(origin=detector.ports[2],destination=step1.ports[2])
        
        step2 = outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]),distance=n.straight_outline, open_ports=3)
        step2.move(step2.ports[2],detector.ports[1])
             
        ground_taper = outline(hyper_taper(n.ground_taper_length, n.ground_taper_width, n.straight_width[i]*step_scale), distance= n.straight_outline, open_ports=2)
        ground_taper.rotate(180)
        ground_taper.move(ground_taper.ports['narrow'],step2.ports[1])

        D.add_ref([pad_taper,detector, step1, step2, ground_taper])
        D.flatten(single_layer=n.straight_layer)
        D.add_ref(pad)
        D.rotate(-90)
        D.move(D.bbox[0],destination=(0,0))
        
        
        # """ Attach dynamical parameters to device object. """
        D.width = n.straight_width[i]
        D.squares = straight_squares
        D.parameters = parameters
        D.type = 'straight_wire'

        device_list.append(D)
        
    # """ Attach squares calculation to parameters """
    parameters['snspd_squares']=np.array(device_squares_list)
    return device_list

def resistor_pad_bilayer(parameters=None, sheet_inductance = 300):
    """

    """
    ''' Default parameters for example testing '''
    if parameters == None: 
        parameters = {
                'pad_width': 200,
                'pad_outline': 7,
                'pad_taper_length': 40,
                'ground_taper_length': 20,
                'ground_taper_width': 100,
                'straight_width':3,
                'straight_outline': 0.2,
                'r_width':np.array([1]),
                'r_length':np.array([6]),
                'r_over': 2,
                'straight_layer': 1,
                'pad_layer': 2,
                'r_layer':3
                }
    
    """ Get length of parameters """ 
    for key in parameters:
            if type(parameters[key]) == np.ndarray:
                parameter_length = len(parameters[key])
                break
            else:
                parameter_length = 0

    """ Convert dictionary keys to namespace """
    n = Namespace(**parameters) #This method of converting dictionary removes "Undefined name" warning
    
    
    """ Generate list of devices from parameters 
        Additionally, this loop will calculate the number of squares of each device. 
    """
    device_list = []
    device_squares_list = []
    step_scale = 4
    for i in range(parameter_length):
        D = Device('wire')    

        # straight_squares = n.straight_length[i]/n.straight_width[i]
        # reset_time = reset_time_calc(squares = straight_squares, Ls=sheet_inductance)
        # device_squares_list.append(straight_squares)
        
        
        
        ######################################################################

        r = resistor_pos(size=(n.r_width[i],n.r_length[i]), 
                         width=n.straight_width, 
                         length=n.r_length[i], 
                         overhang=n.r_over, 
                         pos_outline=n.straight_outline, layer=n.straight_layer, rlayer=n.r_layer)
        
        step1 = pg.outline(pg.optimal_step(n.straight_width*step_scale,n.straight_width, symmetric=True),distance=n.straight_outline,layer=n.straight_layer, open_ports=n.straight_outline)
        step1.rotate(-90)
        step1.move(step1.ports[2],r.ports[1])
        
        step2 = pg.outline(pg.optimal_step(n.straight_width*step_scale,n.straight_width, symmetric=True),distance=n.straight_outline,layer=n.straight_layer, open_ports=n.straight_outline)
        step2.rotate(90)
        step2.move(step2.ports[2],r.ports[2])
        
        pad_taper = pg.outline(hyper_taper(40, n.pad_width+n.pad_outline,n.straight_width*step_scale),distance=n.straight_outline,layer=n.straight_layer, open_ports=n.straight_outline)
        pad_taper.rotate(-90)
        pad_taper.move(pad_taper.ports['narrow'], step2.ports[1])
        
        pad = pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(90)
        pad.move(pad.ports[1], pad_taper.ports['wide']).movey(10)
        
        ground_taper = outline(hyper_taper(n.ground_taper_length, n.ground_taper_width, n.straight_width*step_scale), distance= n.straight_outline, open_ports=2)
        ground_taper.rotate(90)
        ground_taper.move(ground_taper.ports['narrow'],step1.ports[1])



        D.add_ref([r, step1, step2, pad_taper, pad, ground_taper])
        D.flatten()
        D.move(D.bbox[0],destination=(0,0))
        
        
        # # """ Attach dynamical parameters to device object. """
        D.squares = (n.r_length[i]-n.r_over)/n.r_width[i]
        D.parameters = parameters
        D.type = 'resistor'

        device_list.append(D)
        qp(D)
    # """ Attach squares calculation to parameters """
    # parameters['snspd_squares']=np.array(device_squares_list)
    return device_list

resistor_pad_bilayer()


def four_point_wire(parameters=None):
    
    ''' Default parameters for example testing '''
    if parameters == None: 
        parameters = {
                'pad_width': 200,   
                'pad_outline': 10,
                'pad_taper_length': 40,
                'ground_taper_length': 10,
                'ground_taper_width': 20,
                'straight_outline': 0.2,
                'straight_width':np.array([.2]),
                'straight_length':np.array([40]),
                'straight_layer': 1,
                'pad_layer': 2
                }
    
    """ Get length of parameters """ 
    for key in parameters:
            if type(parameters[key]) == np.ndarray:
                parameter_length = len(parameters[key])
                break
            else:
                parameter_length = 0
    
    """ Convert dictionary keys to namespace """
    n = Namespace(**parameters) #This method of converting dictionary removes "Undefined name" warning
    
    
    """ Generate list of devices from parameters 
        Additionally, this loop will calculate the number of squares of each device. 
    """
    device_list = []
    device_squares_list = []
    step_scale = 10
    for i in range(parameter_length):
        D = Device('fp')    
        E = Device('wire')

        straight_squares = n.straight_length[i]/n.straight_width[i]
        # reset_time = reset_time_calc(squares = straight_squares, Ls=sheet_inductance)
        # device_squares_list.append(straight_squares)
        
        
        
        ######################################################################
        step_scale=10
        
        for z in range(4): 
            pad = pad_U(pad_width= n.pad_width, width=n.pad_outline, layer=n.pad_layer, port_yshift=-10, port_width_add=n.pad_outline/2)
            pad.rotate(90)
            pad.move(pad.bbox[0], (n.pad_width*z*1.2,0))
            pad_taper = outline(hyper_taper(40, n.pad_width+n.pad_outline,n.straight_width[i]*step_scale, layer=n.straight_layer),distance=n.straight_outline, open_ports=2)
            # pad_taper = outline(hyper_taper(40, n.pad_width+n.pad_outline,step_scale),distance=n.straight_outline, open_ports=2)
            pad_taper.rotate(-90)
            pad_taper.move(pad_taper.ports['wide'], pad.ports[1])
            E.add_ref(pad_taper)
            D.add_ref(pad)
            
        
        straight = outline(pg.straight(size=(n.straight_width[i],n.straight_length[i])),distance=n.straight_outline,open_ports=2)
        straight.rotate(90)
        straight.move(straight.center,D.center)
        straight.movey(n.pad_width*1.25)
        

        pad_taper = outline(hyper_taper(40, n.pad_width+n.pad_outline,n.straight_width[i]*step_scale),distance=n.straight_outline, open_ports=2)
        
        t1 = outline(pg.tee(size=(n.straight_width[i]*4,n.straight_width[i]),stub_size=(n.straight_width[i]*2,n.straight_width[i]*2),taper_type='fillet', layer=n.straight_layer),distance=n.straight_outline, open_ports=2)
        t1.move(t1.ports[1],straight.ports[1])
        
        t2 = outline(pg.tee(size=(n.straight_width[i]*4,n.straight_width[i]),stub_size=(n.straight_width[i]*2,n.straight_width[i]*2),taper_type='fillet', layer=n.straight_layer),distance=n.straight_outline, open_ports=2)
        t2.move(t2.ports[2],straight.ports[2])
        
        s1 = outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]*2),distance=n.straight_outline, open_ports=3)
        s1.rotate(90)
        s1.move(s1.ports[2], t1.ports[3])
        
        s2 = outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]),distance=n.straight_outline, open_ports=3)
        s2.move(s2.ports[2], t1.ports[2])
        
        s3 = outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]*2),distance=n.straight_outline, open_ports=3)
        s3.rotate(90)
        s3.move(s3.ports[2], t2.ports[3])
        
        s4 = outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]),distance=n.straight_outline, open_ports=3)
        s4.rotate(180)
        s4.move(s4.ports[2], t2.ports[1])


        r1 = outline(pr.route_manhattan(port1=E.references[0].ports['narrow'], port2=s2.ports[1]), distance=n.straight_outline,open_ports=3, rotate_ports=True)
        r2 = outline(pr.route_manhattan(port1=E.references[1].ports['narrow'], port2=s1.ports[1]), distance=n.straight_outline,open_ports=3, rotate_ports=True)
        r3 = outline(pr.route_manhattan(port1=E.references[2].ports['narrow'], port2=s3.ports[1]), distance=n.straight_outline,open_ports=3, rotate_ports=True)
        r4 = outline(pr.route_manhattan(port1=E.references[3].ports['narrow'], port2=s4.ports[1]), distance=n.straight_outline,open_ports=3, rotate_ports=True)

        
        E.add_ref([straight, t1, t2, s1, s2, s3, s4, r1, r2, r3, r4])
        E.flatten(single_layer=n.straight_layer)

        D.flatten()
        D.add_ref(E)
        
        """ Attach dynamical parameters to device object. """
        D.width = n.straight_width[i]
        D.squares = straight_squares
        D.parameters = parameters
        D.type='four_point'
        device_list.append(D)
        
    # """ Attach squares calculation to parameters """
    # parameters['snspd_squares']=np.array(device_squares_list)
    return device_list










def save_parameters(parameters, script_name):

    sample = input('enter a sample name: ')
    
    if sample=='':
        print('GDS script document not created')
        return
    
    path = os.path.join('S:\SC\Measurements',sample)
    os.makedirs(path, exist_ok=True)
    
    path = os.path.join('S:\SC\Measurements',sample, sample+'_script_doc.txt')
    
    file = open(path, "w")
    file.write('Script path: '+script_name+'\n')
    
    
    for i in range(len(parameters)):
        file.write(str(parameters[i])+'\n')
        
    file.close()
    print('File Saved: '+ path)   
    
    
    
    
    
    
    
    


def meander_outline(width=0.1, pitch=0.250, area=8, length=None, number_of_paths=1, outline=0.25, layer=1, terminals_same_side=False):
    """
                    width=0.1, pitch=0.250, area=8, length=None, number_of_paths=1, layer=1, terminals_same_side=False):

    Parameters
    ----------
    width : FLOAT, optional
        SNSPD wire width. The default is 0.1.
    pitch : FLOAT, optional
        SNSPD wire pitch. The default is 0.250.
    area : FLOAT, optional
        SNSPD overall Y dimension, and or snspd area if Length is not specified. The default is 8.
    length : FLOAT, optional
        SNSPD overall X dimension. The default is None.
    number_of_paths : INT, optional
        Number of times the SNSPD traverses over the Y dimension. This value is limited by the length of the SNSPD The default is 1.

    Returns
    -------
    X : Device
        PHIDL device object is returned.

    """
    D=Device('x')
    X=Device('big')
    
    n=number_of_paths
    if length==None:
        length = area/number_of_paths
    else:
        length = (length-0.5*(number_of_paths-1))/number_of_paths
        
        
    S=pg.snspd(wire_width = width, wire_pitch = pitch+width, size = (length,area), terminals_same_side = terminals_same_side)
    
    if n==1:
        S=pg.snspd(wire_width = width, wire_pitch = pitch+width, size = (length,area), terminals_same_side = terminals_same_side)
        s=D.add_ref(S)
    
    i=0    
    while i < n:
        s=D.add_ref(S)
        if i==0:
            start=s.ports[1].midpoint
        if np.mod(i,2)!=0:
            s.mirror((0,1),(1,1))
        if i>0:
            s.move(origin=s.ports[1], destination=straight.ports[2])
        if i != n-1:
            straight=D.add_ref(pg.straight(size=(width,0.5),  layer = 0))
            straight.rotate(90)
            straight.move(straight.ports[1], s.ports[2])
        if i == n-1:
            end=s.ports[2].midpoint
        i=i+1
    D.flatten(single_layer=layer)    
    t1 = pg.straight(size=(width,outline))
    t1.rotate(90)
    t1.move(origin=t1.ports[1], destination=end)
    
    t2 = pg.straight(size=(width,outline))
    t2.rotate(90)
    t2.move(origin=t2.ports[2], destination=start)
    
    
    X=pg.deepcopy(D)
    X = pg.outline(X,distance=outline,precision=1e-6,layer=layer)
    X = pg.boolean(X,t1,'A-B',1e-6,layer=layer)
    X = pg.boolean(X,t2,'A-B',1e-6,layer=layer)
    X.add_port(port=t1.ports[2], name=2)
    X.add_port(port=t2.ports[1], name=1)
    X.move(origin=X.ports[1], destination=(0,0))
    
    return X

    
    
def meander_taper(width=0.1, pitch=0.250, area=8, length=None, number_of_paths=1, taper_length=50, taper_narrow=.1, taper_wide=200, layer=1):
    
    X=Device('x')
    m=meander(width=width, pitch=pitch, area=area, length=length, number_of_paths=number_of_paths, layer=layer)
    X.add_ref(m)
    ht = hyper_taper(taper_length, taper_wide, taper_narrow, layer=layer)
    HT1 = X.add_ref(ht)
    HT1.rotate(180)
    HT1.move(origin=HT1.ports['narrow'],destination=X.references[0].ports[1])
    HT2 = X.add_ref(ht)
    HT2.move(origin=HT2.ports['narrow'],destination=X.references[0].ports[2])

    X.add_port(name=1, midpoint = HT1.ports['wide'].midpoint, width=taper_wide, orientation=180)
    X.add_port(name=2, midpoint = HT2.ports['wide'].midpoint, width=taper_wide, orientation=0)
    
    X.move(origin=X.ports[1],destination=(0,0))
    return X

def meander_taper_outline(width=0.1, pitch=0.250, area=8, length=None, number_of_paths=1, taper_length=10, taper_narrow=.1, taper_wide=100, outline=0.5, layer=1):
    
    X=Device('x')
    T=Device('t')
    m=meander_taper(width=width, pitch=pitch, area=area, length=length, 
                    number_of_paths=number_of_paths, taper_length=taper_length, 
                    taper_narrow=taper_narrow, taper_wide=taper_wide, layer=layer)
    X.add_ref(pg.outline(m,distance=outline, precision=1e-4))
    
    SW = (X.bbox[0,0],-X.bbox[1,1])
    SE = (X.bbox[1,0]-outline,X.bbox[0,1])
    ''' Trim edge of outline '''
    t = pg.rectangle(size=(outline, X.bbox[1,1]*2))
    t.move(destination=SE)
    T.add_ref(t)
    t = pg.rectangle(size=(outline, X.bbox[1,1]*2))
    t.move(destination=SW)
    T.add_ref(t)
    X=pg.boolean(X,T,'A-B',precision=1e-6,layer=layer )
    X.add_port(name=1,midpoint=m.ports[1].midpoint,width=taper_wide,orientation=180)
    X.add_port(name=2,midpoint=m.ports[2].midpoint,width=taper_wide,orientation=0)
    return X
