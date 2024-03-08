""" Geometries contains common devices from test structures to proper circuits.
"""

from __future__ import division, print_function, absolute_import
from phidl import Device, Port
# from phidl import quickplot as qp
# from phidl import set_quickplot_options
import phidl.geometry as pg
import phidl.routing as pr
from typing import Tuple, List, Union, Dict, Set
import numpy as np
import math
import os


# Basics

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
                    layer:       int                = 0):
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


# Common nanowire-based devices

def ntron(choke_w     = 0.03, 
          gate_w      = 0.2, 
          channel_w   = 0.1, 
          source_w    = 0.3, 
          drain_w     = 0.3, 
          choke_shift = -0.3, 
          layer       = 0):
    
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

def ntron_compassPorts(choke_w     = 0.03, 
                       gate_w      = 0.2, 
                       channel_w   = 0.1, 
                       source_w    = 0.3, 
                       drain_w     = 0.3, 
                       choke_shift = -0.3, 
                       layer       = 0):
    """ A basic ntron with ports named as in compass multi (N1, W1, S1 for
    drain, gate, source) """

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

def ntron_sharp(choke_w=0.03, choke_l=.5, gate_w=0.2, channel_w=0.1, source_w=0.3, drain_w=0.3, layer=0):
    
    D = Device('nTron')
    
    choke = pg.taper(choke_l, gate_w, choke_w)
    k = D<<choke
    
    channel = pg.compass(size=(channel_w, choke_w/10))
    c = D<<channel
    c.connect(channel.ports['W'],choke.ports[2])
    
    drain = pg.taper(channel_w*6, drain_w, channel_w)
    d = D<<drain
    d.connect(drain.ports[2], c.ports['N'])
    
    source = pg.taper(channel_w*6, channel_w, source_w)
    s = D<<source
    s.connect(source.ports[1], c.ports['S'])
    
    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(name='g', port=k.ports[1])
    D.add_port(name='d', port=d.ports[1])
    D.add_port(name='s', port=s.ports[2])
    D.name = 'nTron'
    D.info = locals()
    return D 

def nanowire(channel_w: float = 0.1, 
             source_w:  float = 0.3, 
             layer:     int   = 0, 
             num_pts:   int   = 100):
    """ Creates a single wire, of same appearance as a ntron but without the
    gate.
    
    Parameters:
    channel_w (int or float): the width of the channel (at the hot-spot location)
    source_w  (int or float): the width of the nanowire's "source"
    layer (int): the layer where to put the device
    num_pts (int): the number of points comprising the optimal_steps geometries

    Returns:
    NANOWIRE (Device): a device containing 2 optimal steps joined at their
    channel_w end

    """
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

def snspd_vert(wire_width = 0.2, wire_pitch = 0.6, size = (6,10),
        num_squares = None, terminals_same_side = False, extend=None, layer = 0):
    
    D = Device('snspd_vert')
    S = pg.snspd(wire_width = wire_width, wire_pitch = wire_pitch, size = size,
        num_squares = num_squares, terminals_same_side = terminals_same_side, layer = layer)
    s1 = D<<S
    
    HP = pg.optimal_hairpin(width = wire_width, pitch=wire_pitch, length=size[0]/2, layer=layer)
    h1 = D<<HP
    h1.connect(h1.ports[1], S.references[0].ports['E'])
    h1.rotate(180, h1.ports[1])
    
    h2 = D<<HP
    h2.connect(h2.ports[1], S.references[-1].ports['E'])
    h2.rotate(180, h2.ports[1])
    
    T = pg.optimal_90deg(width=wire_width, layer=layer)
    t1 = D<<T
    T_width = t1.ports[2].midpoint[0]
    t1.connect(t1.ports[1],h1.ports[2])
    t1.movex(-T_width+wire_width/2)
    
    t2 = D<<T
    t2.connect(t2.ports[1],h2.ports[2])
    t2.movex(T_width-wire_width/2)
    
    D = pg.union(D, layer=layer)
    D.flatten()
    if extend:
        E = pg.straight(size=(wire_width, extend), layer=layer)
        e1 = D<<E
        e1.connect(e1.ports[1],t1.ports[2])
        e2 = D<<E
        e2.connect(e2.ports[1],t2.ports[2])
        D = pg.union(D, layer=layer)
        D.add_port(name=1, port=e1.ports[2])
        D.add_port(name=2, port=e2.ports[2])
    else:
        D.add_port(name=1, port=t1.ports[2])
        D.add_port(name=2, port=t2.ports[2])
        
    D.info = S.info
    return D

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
                layer:          int                      = 0):
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

def tesla_valve(width=0.2, pitch=0.6, length=4, angle=15, num=5):
    D = Device('tesla_valve')

    hp = pg.optimal_hairpin(width, pitch, length)
    hp.move(hp.bbox[0], destination=(0,0))
    hp.rotate(-angle, center=(hp.ports[1].midpoint))
    
    ramp = pg.straight(size=(length, width+pitch))
    r = D<<ramp
    r.movex(-pitch)
    h = D<<hp
    
    d = pg.boolean(h, r, 'A-B')
    d.movex(d.bbox[0][0], destination=0)
    d.rotate(angle/2)
    D.remove([h, r])
    
    d.add_port(name=1, midpoint=(0,width/2), width=width, orientation=180)
    d.add_port(name=2, midpoint=(length*np.cos(angle/2*np.pi/180),width/2 + length*np.sin(angle/2*np.pi/180)), width=width, orientation=0)
    d<<pr.route_basic(d.ports[1], d.ports[2], path_type='straight')
    
    dd = pg.union(d, precision=1e-8)
    dd.add_port(name=1, port=d.ports[1])
    dd.add_port(name=2, port=d.ports[2])
    
    D_list = np.tile(dd, num)
    
    for i in range(num):
        
        vert = D<<D_list[i]

        if i%2 == 0:
            vert.mirror(p1=(1,0))
        if i == 0:
            next_port = vert.ports[2]
        if i > 0:
            vert.connect(vert.ports[1], next_port)
            next_port = vert.ports[2]
    
    port_list = D.get_ports()
    D = pg.union(D, precision=1e-10)
    D.add_port(name=1, port=port_list[0])
    D.add_port(name=2, port=port_list[-1])
    return D

def via_square(width=3, inset=2, layers=[0, 1, 2], outline=False):
    D = Device('via')    
    via0 = pg.compass(size=(width+2*inset, width+2*inset), layer=layers[0])
    v0 = D<<via0
    
    via1 = pg.compass(size=(width, width), layer=layers[1])
    v1 = D<<via1
    v1.move(v1.center, v0.center)
    
    via2 = pg.compass(size=(width+2*inset, width+2*inset), layer=layers[2])
    v2 = D<<via2
    v2.move(v2.center, v1.center)
    
    D.flatten()
    
    if outline:
        E = pg.copy_layer(D, layer=0, new_layer=0)
        D.remove_layers(layers=[0])
        E = pg.outline(E, distance=outline, layer=0)
        D<<E
        
        F = pg.copy_layer(D, layer=2, new_layer=2)
        D.remove_layers(layers=[2])
        F = pg.outline(F, distance=outline, layer=2)
        D<<F
    
    port_list = [v0.ports['N'], v0.ports['S'], v0.ports['E'], v0.ports['W']]
    [D.add_port(name=n+1, port=port_list[n]) for n in range(len(port_list))]
    
    return D

def via_round(width=3, inset=2, layers=[0, 1, 2], outline=False):
    D = Device('via')    
    via0 = pg.compass(size=(width+2*inset, width+2*inset), layer=layers[0])
    v0 = D<<via0
    
    via1 = pg.circle(radius=width/2, layer=layers[1])
    v1 = D<<via1
    v1.move(v1.center, v0.center)
    
    via2 = pg.compass(size=(width+2*inset, width+2*inset), layer=layers[2])
    v2 = D<<via2
    v2.move(v2.center, v1.center)
    
    D.flatten()
    
    if outline:
        E = pg.copy_layer(D, layer=0, new_layer=0)
        D.remove_layers(layers=[0])
        E = pg.outline(E, distance=outline, layer=0)
        D<<E
        
        F = pg.copy_layer(D, layer=2, new_layer=2)
        D.remove_layers(layers=[2])
        F = pg.outline(F, distance=outline, layer=2)
        D<<F
    
    port_list = [v0.ports['N'], v0.ports['S'], v0.ports['E'], v0.ports['W']]
    [D.add_port(name=n+1, port=port_list[n]) for n in range(len(port_list))]
    
    return D

""" Other geonetries like htron, plannar htron, logic gates etc could be added.
One good standard to remember could be to name the devices ports with compass
multi names (i.e. N1, N2, W1, S1 etc...) for the utilities functions to properly
work.
"""