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
sys.path.append(r'Q:\qnngds')
import qnnpy.functions.functions as qf
import qnngds.utilities as qu
import qnngds.geometry as qg


    
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
        detector = qg.outline(detector,distance=n.snspd_outline,open_ports=2)
        pad = qg.pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(180)
        
        inductor_squares = squares_meander_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i])
        device_squares = inductor_squares
        reset_time = reset_time_calc(squares = device_squares, Ls=sheet_inductance)

        device_squares_list.append(device_squares)
        
        pad_taper = qg.outline(qg.hyper_taper(40, n.pad_width+n.pad_outline,n.snspd_width[i],n.snspd_layer), distance=n.snspd_outline,open_ports=2)
        pad_taper.move(pad_taper.ports['wide'], pad.ports[1]).movex(10)
        detector.move(origin=detector.ports[2],destination=pad_taper.ports['narrow'])

        
        ground_taper = qg.outline(qg.hyper_taper(n.ground_taper_length,n.ground_taper_width, n.snspd_width[i],n.snspd_layer),distance=n.snspd_outline, open_ports=2)
        ground_taper.rotate(180)
        ground_taper.move(origin=ground_taper.ports['narrow'],destination=detector.ports[1])
                


        D.add_ref([pad_taper,detector, ground_taper])
        D.flatten(single_layer=n.snspd_layer)
        D.add_ref(pad)
        D.rotate(-90)
        D.move(D.bbox[0],destination=(0,0))

        qp(D)
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



def snspd_2pad_bilayer(parameters=None, sheet_inductance = 80):
    """

    """
    ''' Default parameters for example testing '''
    if parameters == None: 
        parameters = {
                'pad_outline': 7,
                'pad_taper_length': 60,
                'snspd_outline': .2,
                'snspd_width': np.array([1]),
                'snspd_fill': 0.50,
                'snspd_area': np.array([30]),
                'pad_width': 200,
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
        detector = qg.outline(detector,distance=n.snspd_outline,open_ports=2)
        pad = qg.pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(180)
        
        inductor_squares = squares_meander_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i])
        device_squares = inductor_squares
        reset_time = reset_time_calc(squares = device_squares, Ls=sheet_inductance)

        device_squares_list.append(device_squares)
        
        pad_taper = qg.outline(qg.hyper_taper(n.pad_taper_length, n.pad_width+n.pad_outline,n.snspd_width[i],n.snspd_layer), distance=n.snspd_outline,open_ports=2)
        pad_taper.move(pad_taper.ports['wide'], pad.ports[1]).movex(10)
        detector.move(origin=detector.ports[2],destination=pad_taper.ports['narrow'])

        
        pad_taper2 = qg.outline(qg.hyper_taper(n.pad_taper_length, n.pad_width+n.pad_outline,n.snspd_width[i],n.snspd_layer), distance=n.snspd_outline,open_ports=2)
        pad_taper2.rotate(180)
        pad_taper2.move(origin=pad_taper2.ports['narrow'],destination=detector.ports[1])
                
        pad2 = qg.pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad2.move(pad2.ports[1],pad_taper2.ports['wide']).movex(10)
    
        D.add_ref([pad_taper,detector, pad_taper2])
        D.flatten(single_layer=n.snspd_layer)
        D.add_ref([pad, pad2])
        D.rotate(-90)
        D.move(D.bbox[0],destination=(0,0))

        # """ Attach dynamical parameters to device object. """
        D.width = n.snspd_width[i]
        D.area = n.snspd_area[i]
        D.squares = device_squares
        D.parameters = parameters
        D.type = 'meander_snspd_diff'
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
        detector = qg.outline(detector,distance=n.snspd_outline,open_ports=2)
        pad = qg.pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(180)
        inductor_squares = squares_meander_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i])
        straight_squares = n.straight_length[i]/n.straight_width[i]
        device_squares = inductor_squares + straight_squares
        reset_time = reset_time_calc(squares = device_squares, Ls=sheet_inductance)
        print('- straight squares:%0.f - inductor_squares:%0.f' %(straight_squares, inductor_squares))
        device_squares_list.append(device_squares)
        
        pad_taper = qg.outline(qg.hyper_taper(40, n.pad_width+n.pad_outline,n.snspd_width[i],n.snspd_layer), distance=n.snspd_outline,open_ports=2)
        pad_taper.move(pad_taper.ports['wide'], pad.ports[1]).movex(10)
        detector.move(origin=detector.ports[2],destination=pad_taper.ports['narrow'])
        
        bend1 = qg.outline(pg.optimal_90deg(n.snspd_width[i]), distance=n.snspd_outline, open_ports=2)
        bend1.rotate(-90)
        bend1.move(bend1.ports[1],detector.ports[1])
        
        step1 = qg.outline(pg.optimal_step(n.straight_width[i],n.snspd_width[i], num_pts=100),distance=n.snspd_outline, open_ports=3)
        step1.rotate(90)
        step1.move(step1.ports[2],bend1.ports[2])
        
        STRAIGHT = qg.outline(pg.straight((n.straight_width[i],n.straight_length[i])),distance=n.snspd_outline, open_ports=2)
        STRAIGHT.move(STRAIGHT.ports[1], step1.ports[1])
                
        step2 = qg.outline(pg.optimal_step(n.snspd_width[i],n.straight_width[i], num_pts=100),distance=n.snspd_outline, open_ports=3)
        step2.rotate(90)
        step2.move(step2.ports[2],STRAIGHT.ports[2])
        
        bend2 = qg.outline(pg.optimal_90deg(n.snspd_width[i]), distance=n.snspd_outline, open_ports=3)
        bend2.rotate(90)
        bend2.move(bend2.ports[2],step2.ports[1])

        
        ground_taper = qg.outline(qg.hyper_taper(n.ground_taper_length,n.ground_taper_width, n.snspd_width[i],n.snspd_layer),distance=n.snspd_outline, open_ports=2)
        ground_taper.rotate(180)
        ground_taper.move(origin=ground_taper.ports['narrow'],destination=bend2.ports[1])
        

        D.add_ref([pad_taper,detector,bend1, step1, STRAIGHT, step2, bend2, ground_taper])
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
    parameters['snspd_squares']=np.array(device_squares_list)
    return device_list

def straight_snspd_2pad_bilayer(parameters=None, sheet_inductance = 300):
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
                'pad_width': 200,
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
        detector = qg.outline(detector,distance=n.snspd_outline,open_ports=2)
        pad = qg.pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(180)
        inductor_squares = squares_meander_calc(n.snspd_width[i], n.snspd_area[i], n.snspd_width[i]/n.snspd_fill-n.snspd_width[i])
        straight_squares = n.straight_length[i]/n.straight_width[i]
        device_squares = inductor_squares + straight_squares
        reset_time = reset_time_calc(squares = device_squares, Ls=sheet_inductance)
        print('- straight squares:%0.f - inductor_squares:%0.f' %(straight_squares, inductor_squares))
        device_squares_list.append(device_squares)
        
        pad_taper = qg.outline(qg.hyper_taper(40, n.pad_width+n.pad_outline,n.snspd_width[i],n.snspd_layer), distance=n.snspd_outline,open_ports=2)
        pad_taper.move(pad_taper.ports['wide'], pad.ports[1]).movex(10)
        detector.move(origin=detector.ports[2],destination=pad_taper.ports['narrow'])
        
        bend1 = qg.outline(pg.optimal_90deg(n.snspd_width[i]), distance=n.snspd_outline, open_ports=2)
        bend1.rotate(-90)
        bend1.move(bend1.ports[1],detector.ports[1])
        
        step1 = qg.outline(pg.optimal_step(n.straight_width[i],n.snspd_width[i], num_pts=100),distance=n.snspd_outline, open_ports=3)
        step1.rotate(90)
        step1.move(step1.ports[2],bend1.ports[2])
        
        STRAIGHT = qg.outline(pg.straight((n.straight_width[i],n.straight_length[i])),distance=n.snspd_outline, open_ports=2)
        STRAIGHT.move(STRAIGHT.ports[1], step1.ports[1])
                
        step2 = qg.outline(pg.optimal_step(n.snspd_width[i],n.straight_width[i], num_pts=100),distance=n.snspd_outline, open_ports=3)
        step2.rotate(90)
        step2.move(step2.ports[2],STRAIGHT.ports[2])
        
        bend2 = qg.outline(pg.optimal_90deg(n.snspd_width[i]), distance=n.snspd_outline, open_ports=3)
        bend2.rotate(90)
        bend2.move(bend2.ports[2],step2.ports[1])

        
        pad_taper2 = qg.outline(qg.hyper_taper(40, n.pad_width+n.pad_outline,n.snspd_width[i],n.snspd_layer), distance=n.snspd_outline,open_ports=2)
        pad_taper2.rotate(180)
        pad_taper2.move(origin=pad_taper2.ports['narrow'],destination=bend2.ports[1])
        
        pad2 = qg.pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad2.move(origin=pad2.ports[1],destination=pad_taper2.ports['wide']).movex(10)
        
        D.add_ref([pad_taper,detector,bend1, step1, STRAIGHT, step2, bend2, pad_taper2])#,bend1,STRAIGHT, bend2, ground_taper])
        D.flatten(single_layer=n.snspd_layer)
        D.add_ref([pad,pad2])
        D.rotate(-90)
        D.move(D.bbox[0],destination=(0,0))

        qp(D)
        # """ Attach dynamical parameters to device object. """
        D.width = n.snspd_width[i]
        D.area = n.snspd_area[i]
        D.squares = device_squares
        D.parameters = parameters
        D.type = 'straight_snspd_diff'

        device_list.append(D)
        
    # """ Attach squares calculation to parameters """
    parameters['snspd_squares']=np.array(device_squares_list)
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

        detector = qg.outline(pg.straight((n.straight_width[i],n.straight_length[i])),distance=n.straight_outline, open_ports=2)
        
        pad = qg.pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(180)

        pad_taper = qg.outline(qg.hyper_taper(40, n.pad_width+n.pad_outline,n.straight_width[i]*step_scale),distance=n.straight_outline, open_ports=2)
        pad_taper.move(pad_taper.ports['wide'], pad.ports[1]).movex(10)
        
        step1 = qg.outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]),distance=n.straight_outline, open_ports=3)
        step1.rotate(180)
        step1.move(step1.ports[1],pad_taper.ports['narrow'])
        
        detector.rotate(90)
        detector.move(origin=detector.ports[2],destination=step1.ports[2])
        
        step2 = qg.outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]),distance=n.straight_outline, open_ports=3)
        step2.move(step2.ports[2],detector.ports[1])
             
        ground_taper = qg.outline(qg.hyper_taper(n.ground_taper_length, n.ground_taper_width, n.straight_width[i]*step_scale), distance= n.straight_outline, open_ports=2)
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

def resistor_pad_bilayer(parameters=None, sheet_resistance=1):
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

        straight_squares = n.r_length[i]/n.r_width[i]
        # reset_time = reset_time_calc(squares = straight_squares, Ls=sheet_inductance)
        device_squares_list.append(straight_squares)
        
        
        
        ######################################################################

        r = qg.resistor_pos(size=(n.r_width[i],n.r_length[i]), 
                         width=n.straight_width, 
                         length=n.r_length[i], 
                         overhang=n.r_over, 
                         pos_outline=n.straight_outline, layer=n.straight_layer, rlayer=n.r_layer)
        
        step1 = qg.outline(pg.optimal_step(n.straight_width*step_scale,n.straight_width, symmetric=True),distance=n.straight_outline,layer=n.straight_layer, open_ports=n.straight_outline)
        step1.rotate(-90)
        step1.move(step1.ports[2],r.ports[1])
        
        step2 = qg.outline(pg.optimal_step(n.straight_width*step_scale,n.straight_width, symmetric=True),distance=n.straight_outline,layer=n.straight_layer, open_ports=n.straight_outline)
        step2.rotate(90)
        step2.move(step2.ports[2],r.ports[2])
        
        pad_taper = qg.outline(qg.hyper_taper(40, n.pad_width+n.pad_outline,n.straight_width*step_scale),distance=n.straight_outline,layer=n.straight_layer, open_ports=n.straight_outline)
        pad_taper.rotate(-90)
        pad_taper.move(pad_taper.ports['narrow'], step2.ports[1])
        
        pad = qg.pad_U(pad_width= n.pad_width, layer=n.pad_layer)
        pad.rotate(90)
        pad.move(pad.ports[1], pad_taper.ports['wide']).movey(10)
        
        ground_taper = qg.outline(qg.hyper_taper(n.ground_taper_length, n.ground_taper_width, n.straight_width*step_scale), distance= n.straight_outline, open_ports=2)
        ground_taper.rotate(90)
        ground_taper.move(ground_taper.ports['narrow'],step1.ports[1])



        D.add_ref([r, step1, step2, pad_taper, pad, ground_taper])
        D.flatten()
        D.move(D.bbox[0],destination=(0,0))
        
        
        # # """ Attach dynamical parameters to device object. """
        D.squares = (n.r_length[i]-n.r_over)/n.r_width[i]
        print("Squares="+str(D.squares)+" Resistance="+str(D.squares*sheet_resistance))
        D.parameters = parameters
        D.type = 'resistor'

        device_list.append(D)
    # """ Attach squares calculation to parameters """
    parameters['snspd_squares']=np.array(device_squares_list)
    return device_list




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
        D = Device('four_point')    
        E = Device('wire')

        straight_squares = n.straight_length[i]/n.straight_width[i]
        # reset_time = reset_time_calc(squares = straight_squares, Ls=sheet_inductance)
        device_squares_list.append(straight_squares)
        
        
        
        ######################################################################
        step_scale=10
        
        for z in range(4): 
            pad = qg.pad_U(pad_width= n.pad_width, width=n.pad_outline, layer=n.pad_layer, port_yshift=-10, port_width_add=n.pad_outline/2)
            pad.rotate(90)
            pad.move(pad.bbox[0], (n.pad_width*z*1.2,0))
            pad_taper = qg.outline(qg.hyper_taper(40, n.pad_width+n.pad_outline,n.straight_width[i]*step_scale, layer=n.straight_layer),distance=n.straight_outline, open_ports=2)
            # pad_taper = outline(hyper_taper(40, n.pad_width+n.pad_outline,step_scale),distance=n.straight_outline, open_ports=2)
            pad_taper.rotate(-90)
            pad_taper.move(pad_taper.ports['wide'], pad.ports[1])
            E.add_ref(pad_taper)
            D.add_ref(pad)
            
        
        straight = qg.outline(pg.straight(size=(n.straight_width[i],n.straight_length[i])),distance=n.straight_outline,open_ports=2)
        straight.rotate(90)
        straight.move(straight.center,D.center)
        straight.movey(n.pad_width*1.25)
        

        pad_taper = qg.outline(qg.hyper_taper(40, n.pad_width+n.pad_outline,n.straight_width[i]*step_scale),distance=n.straight_outline, open_ports=2)
        
        t1 = qg.outline(pg.tee(size=(n.straight_width[i]*4,n.straight_width[i]),stub_size=(n.straight_width[i]*2,n.straight_width[i]*2),taper_type='fillet', layer=n.straight_layer),distance=n.straight_outline, open_ports=2)
        t1.move(t1.ports[1],straight.ports[1])
        
        t2 = qg.outline(pg.tee(size=(n.straight_width[i]*4,n.straight_width[i]),stub_size=(n.straight_width[i]*2,n.straight_width[i]*2),taper_type='fillet', layer=n.straight_layer),distance=n.straight_outline, open_ports=2)
        t2.move(t2.ports[2],straight.ports[2])
        
        s1 = qg.outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]*2),distance=n.straight_outline, open_ports=3)
        s1.rotate(90)
        s1.move(s1.ports[2], t1.ports[3])
        
        s2 = qg.outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]),distance=n.straight_outline, open_ports=3)
        s2.move(s2.ports[2], t1.ports[2])
        
        s3 = qg.outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]*2),distance=n.straight_outline, open_ports=3)
        s3.rotate(90)
        s3.move(s3.ports[2], t2.ports[3])
        
        s4 = qg.outline(pg.optimal_step(n.straight_width[i]*step_scale,n.straight_width[i]),distance=n.straight_outline, open_ports=3)
        s4.rotate(180)
        s4.move(s4.ports[2], t2.ports[1])


        r1 = qg.outline(pr.route_manhattan(port1=E.references[0].ports['narrow'], port2=s2.ports[1]), distance=n.straight_outline,open_ports=3, rotate_ports=True)
        r2 = qg.outline(pr.route_manhattan(port1=E.references[1].ports['narrow'], port2=s1.ports[1]), distance=n.straight_outline,open_ports=3, rotate_ports=True)
        r3 = qg.outline(pr.route_manhattan(port1=E.references[2].ports['narrow'], port2=s3.ports[1]), distance=n.straight_outline,open_ports=3, rotate_ports=True)
        r4 = qg.outline(pr.route_manhattan(port1=E.references[3].ports['narrow'], port2=s4.ports[1]), distance=n.straight_outline,open_ports=3, rotate_ports=True)

        
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
    parameters['snspd_squares']=np.array(device_squares_list)
    return device_list

    
    
def ntron_single(parameters=None):
    
    if parameters == None: 
       parameters = {
               'pad_width': 200,   
               'pad_outline': 10,
               'pad_taper_length': 60,
               'device_layer': 1,
               'pad_layer': 2,
               'choke_w': 0.05, 
               'choke_l': .5,
               'gate_w': 0.2,
               'channel_w': 0.1,
               'source_w': 0.3,
               'drain_w': 0.3,
               'outline': 0.1,
               'routing': 1
               }
        
    n = Namespace(**parameters) #This method of converting dictionary removes "Undefined name" warning
    
    pad = qg.pad_U(pad_width= n.pad_width, width=n.pad_outline, layer=n.pad_layer, port_yshift=-10)
    pad_taper = qg.outline(qg.hyper_taper(n.pad_taper_length, n.pad_width+n.pad_outline,n.routing),distance=n.outline, open_ports=2)
    
    
    D = Device()
    p1 = D<<pad
    p2 = D<<pad
    p3 = D<<pad
    D.distribute(direction='y', spacing=50)
    t1 = D<<pad_taper
    t2 = D<<pad_taper
    t3 = D<<pad_taper

    t1.connect(t1.ports['wide'],p1.ports[1])
    t2.connect(t2.ports['wide'],p2.ports[1])
    t3.connect(t3.ports['wide'],p3.ports[1])


    ntron = qg.outline(qg.ntron_sharp(n.choke_w, n.choke_l, n.gate_w, n.channel_w, n.source_w, n.drain_w), distance=n.outline, open_ports=3, precision=1e-8)
    step = qg.outline(pg.optimal_step(n.routing, n.drain_w, symmetric=True, width_tol=1e-8), distance=n.outline, open_ports=2.1, precision=1e-8)
    step1 = qg.outline(pg.optimal_step(n.routing, n.gate_w, symmetric=True, width_tol=1e-8), distance=n.outline, open_ports=2.1, precision=1e-8)
    
    n1 = D<<ntron
    s1 = D<<step
    s2 = D<<step
    s3 = D<<step1

    n1.move(origin=n1.center,destination=D.center).movex(200)
    s1.connect(s1.ports[2], n1.ports['d'])
    s2.connect(s2.ports[2], n1.ports['s'])
    s3.connect(s3.ports[2], n1.ports['g'])


    D<<qg.outline(pr.route_manhattan(port1=t1.ports['narrow'], port2=s2.ports[1]), distance=n.outline,open_ports=3, rotate_ports=True, precision=1e-8)
    D<<qg.outline(pr.route_basic(port1=t2.ports['narrow'], port2=s3.ports[1]), distance=n.outline,open_ports=3, rotate_ports=False, precision=1e-8)
    D<<qg.outline(pr.route_manhattan(port1=t3.ports['narrow'], port2=s1.ports[1]), distance=n.outline,open_ports=3, rotate_ports=True, precision=1e-8)
    D = pg.union(D, by_layer=True)
    return D


def ntron_gate3(parameters=None):
    
    if parameters == None: 
       parameters = {
               'device_layer': 1,
               'pad_layer': 2,
               'choke_w': 0.05, 
               'choke_l': .3,
               'gate_w': 0.2,
               'gate_p': 0.4,
               'num_gate': 3,
               'channel_w': 0.1,
               'source_w': 0.3,
               'drain_w': 0.3,
               'outline_dis': 0.3,
               'routing': 1
               }
        
    n = Namespace(**parameters) #This method of converting dictionary removes "Undefined name" warning

    D=Device()
        
    pads = D<<qg.pads_adam_quad(layer=n.pad_layer)
    pads.move(origin=pads.center, destination=(0,0))
    

    ntron = qg.ntron_multi_gate_fanout(n.num_gate, n.gate_w, n.gate_p, n.choke_w, 
                            n.choke_l, n.channel_w, n.source_w, n.drain_w, 
                            n.routing, n.outline_dis, n.device_layer)
    # DEVICE 1
    nt1 = D<<ntron
    nt1.rotate(90).movey(-90)

    D<<qg.outline(pr.route_basic(port1=nt1.ports[3], port2=pads.ports[2], width2=n.routing), distance=n.outline_dis,open_ports=3, rotate_ports=False, precision=1e-8, layer=n.device_layer)
    D<<qg.outline(pr.route_manhattan(port1=nt1.ports[2], port2=pads.ports[1], radius=5), distance=n.outline_dis,open_ports=3, rotate_ports=True, precision=1e-8, layer=n.device_layer)
    D<<qg.outline(pr.route_manhattan(port1=nt1.ports[4], port2=pads.ports[3], radius=5), distance=n.outline_dis,open_ports=3, rotate_ports=True, precision=1e-8, layer=n.device_layer)
    D<<qg.outline(pr.route_basic(port1=nt1.ports[5], port2=pads.ports[4], width2=n.routing), distance=n.outline_dis,open_ports=3, rotate_ports=False, precision=1e-8, layer=n.device_layer)
    D<<qg.outline(pr.route_basic(port1=nt1.ports[1], port2=pads.ports[12], width2=n.routing), distance=n.outline_dis,open_ports=3, rotate_ports=False, precision=1e-8, layer=n.device_layer)
    taper = qg.outline(qg.hyper_taper(5, 40, n.routing, layer=n.device_layer),distance=n.outline_dis,open_ports=2, layer=n.device_layer)
    
    for j in [1, 2, 3, 4, 12]:
        t = D<<taper
        t.connect(t.ports['narrow'], pads.ports[j])
        t.rotate(180, center=pads.ports[j].midpoint)
    
    # DEVICE 2
    nt1 = D<<ntron
    nt1.rotate(-90).movey(90)
    
    D<<qg.outline(pr.route_basic(port1=nt1.ports[3], port2=pads.ports[8], width2=n.routing), distance=n.outline_dis,open_ports=3, rotate_ports=False, precision=1e-8, layer=n.device_layer)
    D<<qg.outline(pr.route_manhattan(port1=nt1.ports[2], port2=pads.ports[7], radius=5), distance=n.outline_dis,open_ports=3, rotate_ports=True, precision=1e-8, layer=n.device_layer)
    D<<qg.outline(pr.route_manhattan(port1=nt1.ports[4], port2=pads.ports[9], radius=5), distance=n.outline_dis,open_ports=3, rotate_ports=True, precision=1e-8, layer=n.device_layer)
    D<<qg.outline(pr.route_basic(port1=nt1.ports[5], port2=pads.ports[10], width2=n.routing), distance=n.outline_dis,open_ports=3, rotate_ports=False, precision=1e-8, layer=n.device_layer)
    D<<qg.outline(pr.route_basic(port1=nt1.ports[1], port2=pads.ports[6], width2=n.routing), distance=n.outline_dis,open_ports=3, rotate_ports=False, precision=1e-8, layer=n.device_layer)
   
    taper = qg.outline(qg.hyper_taper(5, 40, n.routing, layer=n.device_layer),distance=n.outline_dis,open_ports=2, layer=n.device_layer) 
    for j in [6, 7, 8, 9, 10]:
        t = D<<taper
        t.connect(t.ports['narrow'], pads.ports[j])
        t.rotate(180, center=pads.ports[j].midpoint)
    
    # DEVICE 3 GATE WIDTH TEST WIRE
    taper=qg.outline(qg.hyper_taper(5, 40, n.gate_w, layer=n.device_layer),distance=n.outline_dis,open_ports=2, layer=n.device_layer)
    t = D<<taper
    t.connect(t.ports['narrow'], pads.ports[5])
    t.rotate(180, center=pads.ports[5].midpoint)
    wire = qg.outline(pg.straight(size=(n.gate_w, 30)), distance=n.outline_dis, open_ports=2, layer=n.device_layer)
    w = D<<wire
    w.connect(w.ports[1], t.ports['narrow'])
    t1=D<<taper
    t1.connect(t1.ports['narrow'], w.ports[2])
    
    # DEVICE 4 CHANNEL WIDTH TEST WIRE
    taper=qg.outline(qg.hyper_taper(5, 40, n.channel_w, layer=n.device_layer),distance=n.outline_dis,open_ports=2, layer=n.device_layer)
    t = D<<taper
    t.connect(t.ports['narrow'], pads.ports[11])
    t.rotate(180, center=pads.ports[11].midpoint)
    wire = qg.outline(pg.straight(size=(n.channel_w, 30)), distance=n.outline_dis, open_ports=2, layer=n.device_layer)
    w = D<<wire
    w.connect(w.ports[1], t.ports['narrow'])
    t1=D<<taper
    t1.connect(t1.ports['narrow'], w.ports[2])

    D = pg.union(D, by_layer=True)
    return D



def ntron_gate1(parameters=None):
    
    if parameters == None: 
       parameters = {
               'device_layer': 1,
               'pad_layer': 2,
               'choke_w': np.array([.05, .05, .05, .05]), 
               'choke_l': np.array([.1, .1, .1, .1]),
               'gate_w': np.array([.2, .2, .2, .2]),
               'gate_p': np.array([.4, .4, .4, .4]),
               'channel_w': np.array([.1, .1, .1, .1]),
               'source_w': 0.3,
               'drain_w': 0.3,
               'outline_dis': 0.15,
               'routing': 1
               }
        
    n = Namespace(**parameters) #This method of converting dictionary removes "Undefined name" warning

    D=Device()
        
    pads = D<<qg.pads_adam_quad(layer=n.pad_layer)
    pads.move(origin=pads.center, destination=(0,0))

    for i in range(4):

        ntron = qg.ntron_multi_gate_fanout(1, n.gate_w[i], n.gate_p[i], n.choke_w[i], 
                                n.choke_l[i], n.channel_w[i], n.source_w, n.drain_w, 
                                n.routing, n.outline_dis, n.device_layer)
        nt1 = D<<ntron
        nt1.rotate(90).movey(-100)
        nt1.rotate(-90*i)
        
        D<<qg.outline(pr.route_basic(port1=nt1.ports[2], port2=pads.ports[i*3+2], width2=n.routing), distance=n.outline_dis,open_ports=3, rotate_ports=False, precision=1e-8, layer=n.device_layer)
        D<<qg.outline(pr.route_manhattan(port1=nt1.ports[1], port2=pads.ports[i*3+1], radius=5), distance=n.outline_dis,open_ports=3, rotate_ports=True, precision=1e-8, layer=n.device_layer)
        D<<qg.outline(pr.route_manhattan(port1=nt1.ports[3], port2=pads.ports[i*3+3], radius=5), distance=n.outline_dis,open_ports=3, rotate_ports=True, precision=1e-8, layer=n.device_layer)
        
        taper = qg.outline(qg.hyper_taper(5, 40, n.routing, layer=n.device_layer),distance=n.outline_dis,open_ports=2, layer=n.device_layer)
        for j in [i*3+1, i*3+2, i*3+3]:
          t = D<<taper
          t.connect(t.ports['narrow'], pads.ports[j])
          t.rotate(180, center=pads.ports[j].midpoint)
        D = pg.union(D, by_layer=True)

    return D


def ntron_amp_single(parameters=None, sheet_resistance=5, sheet_inductance=50):
        
    if parameters == None: 
        parameters = {
                'device_layer': 1,
                'pad_layer': 2,
                'choke_w': 0.05, 
                'choke_l': .3,
                'gate_w': 0.2,
                'gate_p': 0.4,
                'channel_w': 0.2,
                'source_w': .5,
                'drain_w': .5,
                'inductor_w': 0.5,
                'inductor_a1': 20,
                'inductor_a2': 50,
                'outline_dis': 0.1,
                'routing': .5
                }
        n = Namespace(**parameters) #This method of converting dictionary removes "Undefined name" warning
      
        
        D = Device('amplifier_cell')
        pads = D<<qg.pads_adam_quad(layer=n.pad_layer)
        pads.move(origin=pads.center, destination=(0,0))
        
        for i in range(4):
            E = Device('amplifier')
            amp = qg.ntron_amp(n.device_layer,
                               n.pad_layer,
                               n.choke_w,
                               n.choke_l,
                               n.gate_w,
                               n.gate_p,
                               n.channel_w,
                               n.source_w,
                               n.drain_w,
                               n.inductor_w,
                               n.inductor_a1,
                               n.inductor_a2,
                               n.outline_dis,
                               n.routing,
                               sheet_inductance=sheet_inductance,
                               sheet_resistance=sheet_resistance)
            amp.move((55,-100))
            a1 = E<<amp
            
            
            r1 = qg.outline(pr.route_manhattan(a1.ports[1], pads.ports[2], radius = 2 ), distance=n.outline_dis, rotate_ports=True, open_ports=True, layer=n.device_layer)
            r2 = qg.outline(pr.route_manhattan(a1.ports[3], pads.ports[1], radius = 2 ), distance=n.outline_dis, rotate_ports=True, open_ports=True, layer=n.device_layer)
            r3 = qg.outline(pr.route_manhattan(a1.ports[2], pads.ports[12], radius = 10 ), distance=n.outline_dis, rotate_ports=True, open_ports=True, layer=n.device_layer)
            E<<r1
            E<<r2
            E<<r3
            taper = qg.outline(qg.hyper_taper(5, 40, n.routing, layer=n.device_layer),distance=n.outline_dis,open_ports=2, layer=n.device_layer)
            for j in [r1.ports[2], r2.ports[2], r3.ports[2]]:
                t = E<<taper
                t.connect(t.ports['narrow'], j)
                t.rotate(180, center=j.midpoint)
            E.rotate(i*90)
            E = pg.union(E, by_layer=True)
            D<<E
        return D


def encoder(parameters=None):
    
    if parameters == None: 
        parameters = {
                'device_layer': 1,
                'pad_layer': 2,
                'num_gate':10, 
                'gate_w':.15, 
                'gate_p':.2, 
                'choke_w':0.05, 
                'choke_l':.3, 
                'channel_w':0.15, 
                'source_w':0.6, 
                'drain_w':0.6, 
                'routing':1, 
                'outline_dis':.2, 
                'gate_factor':2.5
                }
    n = Namespace(**parameters) #This method of converting dictionary removes "Undefined name" warning
      
    D = Device('encoder')
    pads = D<<qg.pads_adam_quad(layer=n.pad_layer)
    pads.move(origin=pads.center, destination=(0,0))
    
    enc = qg.ntron_multi_gate_dual_fanout(n.num_gate, n.gate_w, n.gate_p, n.choke_w, 
                                          n.choke_l, n.channel_w, n.source_w, n.drain_w, 
                                          n.routing, n.outline_dis, n.device_layer, n.gate_factor)
    
    e1 = D<<enc
    e1.rotate(90)
    
    D<<pg.outline(pr.route_basic(e1.ports[1],pads.ports[11], width2=e1.ports[1].width), distance=n.outline_dis, open_ports=True,layer=n.device_layer)
    D<<pg.outline(pr.route_basic(e1.ports[2],pads.ports[5], width2=e1.ports[2].width), distance=n.outline_dis, open_ports=True,layer=n.device_layer)
    D<<pg.outline(pr.route_basic(e1.ports[5],pads.ports[2], width2=e1.ports[2].width), distance=n.outline_dis, open_ports=True,layer=n.device_layer)
    D<<pg.outline(pr.route_basic(e1.ports[10],pads.ports[8], width2=e1.ports[2].width), distance=n.outline_dis, open_ports=True,layer=n.device_layer)

    D<<qg.outline(pr.route_manhattan(e1.ports[3],pads.ports[12]), distance=n.outline_dis, open_ports=True,layer=n.device_layer, rotate_ports=True)
    D<<qg.outline(pr.route_manhattan(e1.ports[4],pads.ports[1]), distance=n.outline_dis, open_ports=True,layer=n.device_layer, rotate_ports=True)

    D<<qg.outline(pr.route_manhattan(e1.ports[6],pads.ports[3]), distance=n.outline_dis, open_ports=True,layer=n.device_layer, rotate_ports=True)
    D<<qg.outline(pr.route_manhattan(e1.ports[7],pads.ports[4]), distance=n.outline_dis, open_ports=True,layer=n.device_layer, rotate_ports=True)

    D<<qg.outline(pr.route_manhattan(e1.ports[8],pads.ports[6]), distance=n.outline_dis, open_ports=True,layer=n.device_layer, rotate_ports=True)
    D<<qg.outline(pr.route_manhattan(e1.ports[9],pads.ports[7]), distance=n.outline_dis, open_ports=True,layer=n.device_layer, rotate_ports=True)

    D<<qg.outline(pr.route_manhattan(e1.ports[11],pads.ports[9]), distance=n.outline_dis, open_ports=True,layer=n.device_layer, rotate_ports=True)
    D<<qg.outline(pr.route_manhattan(e1.ports[12],pads.ports[10]), distance=n.outline_dis, open_ports=True,layer=n.device_layer, rotate_ports=True)

    taper = qg.outline(qg.hyper_taper(5, 40, n.routing, layer=n.device_layer),distance=n.outline_dis,open_ports=2, layer=n.device_layer)
    for j in range(1, 13):
        t = D<<taper
        t.connect(t.ports['narrow'], pads.ports[j])
        t.rotate(180, center=pads.ports[j].midpoint)
    
    D = pg.union(D, by_layer=True)
    D.flatten()
    return D
qp(encoder())