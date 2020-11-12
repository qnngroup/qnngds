# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 19:27:28 2020

@author: omedeiro
"""

# omedeiro archive
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


def optimal_90deg_outline(width=10.0, num_pts=15, length_adjust=1, layer=0, outline = 0.2):
    b = pg.optimal_90deg(width, num_pts, length_adjust, layer)
    o = pg.outline(b,distance=outline)
    trim1 = pg.rectangle(size=(outline,width+3*outline))
    trim1.move(trim1.center,b.ports[2]).movex(outline/2)
    trim2 = pg.rectangle(size=(width+3*outline,outline))
    trim2.move(trim2.center,b.ports[1]).movey(outline/2)
    I=Device('bend')
    I.add_ref([trim1,trim2])
    d = pg.boolean(o,I,'A-B')
    d.add_port(b.ports[1])
    d.add_port(b.ports[2])
    return d



def optimal_step_outline(width1=1, width2=3, outline=.5, layer=1):
    s = pg.optimal_step(start_width=width1, end_width=width2,num_pts=200 )
    o = pg.outline(s,distance=outline)
    trim1 = pg.rectangle(size=(outline,width1+outline*3))
    trim2 = pg.rectangle(size=(outline,width2+outline*3))
    trim1.move(origin=trim1.center,destination=s.ports[1]).movex(-outline/2)
    trim2.move(origin=trim2.center,destination=s.ports[2]).movex(outline/2)
    T = Device('trims')
    T.add_ref([trim1, trim2])
    b = pg.boolean(o,T,'A-B')
    b.flatten(single_layer=layer)
    b.add_port(s.ports[1])
    b.add_port(s.ports[2])
    return b



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

def straight_outline(width = 2,length = 10, outline = 1, layer =1):
    S = Device('straight')
    
    s = pg.straight(size=(width, length))
    o = pg.outline(s, distance=outline)

    trim = pg.rectangle(size=(width+2*outline, outline))
    a = S.add_ref(trim)
    a.move(trim.center,s.ports[1]).movey(outline/2)
    b = S.add_ref(trim)
    b.move(trim.center,s.ports[2]).movey(-outline/2)
    
    S = pg.boolean(o,S,'A-B')
    S.flatten(single_layer=layer)
    S.add_port(s.ports[1])
    S.add_port(s.ports[2])
    return S




def straight_taper_outline(width = 2,length = 10,t_length=10, t_width=100, outline = 1, layer =1):
    S = Device('straight')
    
    s = pg.straight(size=(width, length))
    t = hyper_taper(t_length, t_width, width)
    t.rotate(90)
    t.move(origin=t.ports['narrow'],destination=s.ports[1])
    S.add_ref([s,t])
    o = pg.outline(S, distance=outline)

    S = Device('straight')
    trim = pg.rectangle(size=(t_width+2*outline, outline))
    a = S.add_ref(trim)
    a.move(trim.center,t.ports['wide']).movey(outline/2)
    b = S.add_ref(trim)
    b.move(trim.center,s.ports[2]).movey(-outline/2)
    
    S = pg.boolean(o,S,'A-B')
    S.flatten(single_layer=layer)
    S.add_port(port=s.ports[2], name=1)
    return S



def pad_basic_outline(base_size=(200,200), port_size =(25,5), taper_length=150, outline = 5, trim = True, layer=1):
    """
    
    
    Create an outline port for etch process.         
    Unlike pad_basic, "port_size" is a tuple.
    Outline cannot be > 2*port_size[1]
    port name is 'narrow'
    
    Parameters
    ----------
    base_size : TUPLE, optional
        (X,Y) Dimensions of pad. The default is (200,200).
    port_size : TUPLE, optional
        (X,Y) Dimensions of port. The default is (25,5).
    taper_length : FLOAT, optional
        Dimension of tapered section pad to port. The default is 150.
    outline : FLOAT, optional
        Width of pad outline. The default is 5.
    trim : BOOLEAN, optional
        Boolean for open or closed pad. The default is True.
    layer :  INT, optional
        Layer for device to be created on. The default is 1.
        
        
    Returns
    -------
    P : DEVICE
        PHIDL device object is returned.

    """
    
    P = Device('pad')
    
    base = pg.rectangle(size=base_size)
    
    taper = pg.taper(length=taper_length,width1=base_size[0],width2=port_size[0])
    taper.rotate(90)
    taper.move(destination=(base_size[0]/2,base_size[1]))
    
    port = pg.rectangle(size=port_size)
    top_center_point = (base_size[0]/2-port_size[0]/2,base_size[1]+taper_length)
    port.move(destination=top_center_point)
    
    
    P.add_ref([base,taper,port])
    P = pg.outline(P,distance=outline,precision=0.0001)
    
    if trim:
        port1 = port.movey(outline)
        P.add_ref(port1)
        P = pg.boolean(P,port1,'A-B',precision=0.0001)
        
    P.add_port(name='narrow',midpoint=(base_size[0]/2,base_size[1]+taper_length),orientation=90,width=port_size[0])
    P.flatten(single_layer=layer)
    
    return P


   
    
def snspd_pad_bilayer(parameters=None, sheet_inductance = 300):
    """
    Create a list of square snspd meanders with pads on a second layer. This design overlaps with >10um tolerance for stage misalignment. 
    
    
    snspd_width and snspd_area must be arrays.

    Parameters
    ----------
    parameters : DICT
        Dictionary of device properties. Multiple devices can be generatred by
        entering an array.
    
        EXAMPLE:
        parameters = {
                        'pad_dim': (200,200),
                        'pad_outline': 10,
                        'pad_taper_length': 80,
                        'pad_port_size': (40,10),
                        'pad_layer': 3,
                        'snspd_outline': 1,
                        'snspd_width': np.array([.5,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5]),
                        'snspd_fill': 0.25,
                        'snspd_area': np.array([50,60,70,80,90,100,100,100,100,100,100,100]),
                        'snspd_taper_length': 40,
                        'snspd_port': 150,
                        'snspd_layer': 1,
                        }
        
    sheet_inductance : FLOAT, optional 
        Film sheet inductance, in pH/sq, for reset time calculation. The default is 80.

    Returns
    -------
    parameters : DICT
        Calculated number of squares is appended to the dictionary.
    device_list : LIST
        List of PHIDL device objects.

    """
    
    ''' Default parameters for example testing '''
    if parameters == None: 
        parameters = {
                'pad_dim': (200,200),
                'pad_outline': 10,
                'pad_taper_length': 80,
                'pad_port_size': (40,10),
                'pad_layer': 2,
                'snspd_outline': 1,
                'snspd_width': np.array([.1]),
                'snspd_fill': 0.25,
                'snspd_area': np.array([10]),
                'snspd_taper_length': 40,
                'snspd_port': 150,
                'snspd_layer': 1,
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
        detector = meander(
                              width = n.snspd_width[i],
                              pitch = n.snspd_width[i]/n.snspd_fill-n.snspd_width[i],
                              area = n.snspd_area[i],
                              layer = n.snspd_layer,
                              )
        detector = outline(detector,distance=n.snspd_outline, open_ports=n.snspd_width[i]/n.snspd_outline)
        pad = pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(180)
        device_squares = squares_meander_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i])
        reset_time = reset_time_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i],Ls=sheet_inductance)

        device_squares_list.append(device_squares)
        
        pad_taper = hyper_taper_outline(40, n.pad_width+30,n.snspd_width[i], n.snspd_outline,n.snspd_layer)
        pad_taper.move(pad_taper.ports['wide'], pad.ports[1]).movex(10)
        detector.move(origin=detector.ports[2],destination=pad_taper.ports['narrow'])
        

        ground_taper = hyper_taper_outline(n.ground_taper_length,n.ground_taper_width, n.snspd_width[i],n.snspd_outline,n.snspd_layer)
        ground_taper.rotate(180)
        ground_taper.move(origin=ground_taper.ports['narrow'],destination=detector.ports[1])
        
        D.add_ref([pad_taper,detector, ground_taper])
        D.flatten(single_layer=n.snspd_layer)
        D.add_ref(pad)
        D.rotate(-90)
        D.move(D.bbox[0],destination=(0,0))
        
        """ Attach dynamical parameters to device object. """
        D.width = n.snspd_width[i]
        D.area = n.snspd_area[i]
        D.squares = device_squares
        D.parameters = parameters
        device_list.append(D)
        
    # """ Attach squares calculation to parameters """
    # parameters['snspd_squares']=np.array(device_squares_list)
    return device_list

    
def snspd_pad_monolayer(parameters=None, sheet_inductance = 300):
    """
    Create a list of square snspd meanders on the same layer. Pad and snspd can have different outline sizes. 
    The pad size is a snspd_port by snspd_port square. 
    
    
    snspd_width and snspd_area must be arrays.

    Parameters
    ----------
    parameters : DICT
        Dictionary of device properties. Multiple devices can be generatred by
        entering an array.
    
        EXAMPLE:
        parameters = {
                'pad_outline': 3,
                'snspd_outline': 1,
                'snspd_width': np.array([.1]),
                'snspd_fill': 0.25,
                'snspd_area': np.array([10]),
                'snspd_taper_length': 40,
                'snspd_port': 200,
                'snspd_layer': 1,
                }
    n = Namespace(**parameters) 
    
    sheet_inductance : FLOAT, optional 
        Film sheet inductance, in pH/sq, for reset time calculation. The default is 80.

    Returns
    -------
    parameters : DICT
        Calculated number of squares is appended to the dictionary.
    device_list : LIST
        List of PHIDL device objects.

    """
    ''' Default parameters for example testing '''
    if parameters == None: 
        parameters = {
                'pad_outline': 10,
                'snspd_outline': .5,
                'snspd_width': np.array([.1]),
                'snspd_fill': 0.25,
                'snspd_area': np.array([10]),
                'snspd_taper_length': 40,
                'snspd_port': 200,
                'snspd_layer': 1,
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
        detector = meander_outline(
                              width = n.snspd_width[i],
                              pitch = n.snspd_width[i]/n.snspd_fill-n.snspd_width[i],
                              area = n.snspd_area[i],
                              layer = n.snspd_layer,
                              outline=n.snspd_outline
                              )
        pad = pad_taper(length=n.snspd_taper_length,
                        pad_width= n.snspd_port,
                        narrow_section=n.snspd_width[i],
                        w_outline=n.pad_outline,
                        n_outline=n.snspd_outline,
                        layer=n.snspd_layer)
        
        device_squares = squares_meander_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i])
        reset_time = reset_time_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i],Ls=sheet_inductance)

        device_squares_list.append(device_squares)
        
        detector.move(origin=detector.ports[2],destination=pad.ports[1])
        
        ground_taper = hyper_taper_outline(n.snspd_taper_length,n.snspd_port, n.snspd_width[i],n.snspd_outline,n.snspd_layer)
        ground_taper.rotate(180)
        ground_taper.move(origin=ground_taper.ports['narrow'],destination=detector.ports[1])
        
        D.add_ref(detector)
        D.add_ref(pad)
        D.add_ref(ground_taper)
        
        D.flatten()
        D.rotate(-90)
        D.move(D.bbox[0],destination=(0,0))
        
        """ Attach dynamical parameters to device object. """
        D.width = n.snspd_width[i]
        D.area = n.snspd_area[i]
        D.squares = device_squares
        D.parameters = parameters
        device_list.append(D)
        
    # """ Attach squares calculation to parameters """
    # parameters['snspd_squares']=np.array(device_squares_list)
    return device_list



def straight_snspd_pad_monolayer(parameters=None, sheet_inductance = 300):
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
                'layer': 1,
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
        detector = meander_outline(
                              width = n.snspd_width[i],
                              pitch = n.snspd_width[i]/n.snspd_fill-n.snspd_width[i],
                              area = n.snspd_area[i],
                              layer = n.layer,
                              outline=n.snspd_outline
                              )
        pad = pad_taper(length=n.pad_taper_length,
                        pad_width= n.pad_width,
                        narrow_section=n.snspd_width[i],
                        w_outline=n.pad_outline,
                        n_outline=n.snspd_outline,
                        layer=n.layer)
        
        device_squares = squares_meander_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i])
        reset_time = reset_time_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i],Ls=sheet_inductance)

        device_squares_list.append(device_squares)
        
        detector.move(origin=detector.ports[2],destination=pad.ports[1])
        step1 = optimal_step_outline(n.snspd_width[i],n.straight_width[i],outline=n.snspd_outline)
        step1.rotate(180)
        step1.move(step1.ports[1],detector.ports[1])
        
        bend1 = optimal_90deg_outline(n.straight_width[i])
        bend1.rotate(-90)
        bend1.move(bend1.ports[1],step1.ports[2])
        
        STRAIGHT = straight_outline(n.straight_width[i],n.straight_length[i],outline=n.snspd_outline)
        STRAIGHT.move(STRAIGHT.ports[1], bend1.ports[2])
        
        bend2 = optimal_90deg_outline(n.straight_width[i])
        bend2.rotate(90)
        bend2.move(bend2.ports[2],STRAIGHT.ports[2])

        step2 = optimal_step_outline(n.snspd_width[i],n.straight_width[i],outline=n.snspd_outline)
        step2.move(step2.ports[2],STRAIGHT.ports[1])
        
        
        ground_taper = hyper_taper_outline(n.ground_taper_length,n.ground_taper_width, n.straight_width[i],n.snspd_outline,n.layer)
        ground_taper.rotate(180)
        ground_taper.move(origin=ground_taper.ports['narrow'],destination=bend2.ports[1])
        
        D.add_ref([detector,pad,step1,bend1,STRAIGHT, bend2, ground_taper])

        
        D.flatten()
        D.rotate(-90)
        D.move(D.bbox[0],destination=(0,0))
        
        """ Attach dynamical parameters to device object. """
        D.width = n.snspd_width[i]
        D.area = n.snspd_area[i]
        D.squares = device_squares
        D.parameters = parameters
        device_list.append(D)
        
    # """ Attach squares calculation to parameters """
    # parameters['snspd_squares']=np.array(device_squares_list)
    return device_list