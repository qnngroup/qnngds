# -*- coding: utf-8 -*-
"""
Created on Wed Nov 18 20:40:59 2020

@author: omedeiro
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
    p.name = text_letter
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
    
def save_gds(device, filename, prop_dict=None, path=None):
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
        
    if prop_dict:
        qf.output_log(prop_dict, full_path)
    
    

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
    
    
    