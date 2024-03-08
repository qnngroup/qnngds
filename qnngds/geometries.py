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

### Useful common nanowire-based devices

""" copied and adjusted from qnngds geometries"""
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

""" copied and adjusted from qnngds geometries"""
def ntron_compassPorts(choke_w     = 0.03, 
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
    D.add_port(name='N1', port=d.ports[1])
    D.add_port(name='S1', port=s.ports[2])
    D.add_port(name='W1', port=k.ports[1])
    D.name = f"NTRON {choke_w} {channel_w} "
    D.info = locals()

    return D

def nanowire(channel_w: float = 0.1, 
             source_w:  float = 0.3, 
             layer:     int   = 0, 
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

