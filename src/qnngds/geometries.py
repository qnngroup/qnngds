""" Geometries contains common devices from test structures to proper circuits.
"""

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

# Basics

def alignement_mark(layers: List[int] = [1, 2, 3, 4]
                    ) -> Device:
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
                    layer:       int                = 0
                    ) -> Device:
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

# Tapers, tools 

def hyper_taper(length = 10, wide_section = 50, narrow_section = 5, layer=0):
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
     
def optimal_taper(width = 100.0, num_pts = 15, length_adjust = 3, layer = 0):
    
    D = Device('optimal_taper')
    
    t1 = D<<pg.optimal_90deg(width, num_pts, length_adjust)
    t2 = D<<pg.optimal_90deg(width, num_pts, length_adjust)
    t2.mirror()
    t2.move(t2.ports[1], t1.ports[1])
    
    D.movex(-t1.ports[1].midpoint[0])
    D.movey(-width)
    D = pg.union(D, layer=layer)

    #wide port trim
    trim = pg.straight(size=(width,-2.5*D.bbox[0][0]))
    trim.rotate(90)
    trim.move(trim.bbox[0],D.bbox[0])
    trim.movex(-.005)
    trim.movey(-.0001)
    A = pg.boolean(t1,trim, 'A-B', layer=layer, precision=1e-9)
    B = pg.boolean(t2,trim, 'A-B', layer=layer, precision=1e-9)

    # #top length trim
    trim2 = D<<pg.straight(size=(width*2, t1.ports[1].midpoint[1]-width*4))
    trim2.connect(trim2.ports[1], t1.ports[1].rotate(180))
    A = pg.boolean(A,trim2, 'A-B', layer=layer, precision=1e-9)
    B = pg.boolean(B,trim2, 'A-B', layer=layer, precision=1e-9)
    
    # # width trim 1
    trim3 = A<<pg.straight(size=(width/2, t1.ports[1].midpoint[1]+.1))
    trim3.connect(trim3.ports[1], t1.ports[1].rotate(180))
    trim3.movex(-width/2)
    A = pg.boolean(A,trim3, 'A-B', layer=layer, precision=1e-9)

    # # width trim 2
    trim3 = B<<pg.straight(size=(width/2, t1.ports[1].midpoint[1]+.1))
    trim3.connect(trim3.ports[1], t1.ports[1].rotate(180))
    trim3.movex(width/2)
    B = pg.boolean(B,trim3, 'A-B', layer=layer, precision=1e-9)
    
    p = B.get_polygons()
    x1 = p[0][0,0]
 
    A.movex(width/2+x1)
    B.movex(-width/2-x1)
    D = A
    D<<B
    D = pg.union(D, layer=layer)

    D.add_port(name=1,midpoint=(0, width*4), width=width,orientation=90)
    D.add_port(name=2, midpoint=(0,0), width=D.bbox[0][0]*-2, orientation=-90)
    
    return D 
