""" 
Circuits module contains a library of QNN's circuits (e.g. snspd coupled to ntron, logic gates etc.)
"""

from __future__ import division, print_function, absolute_import
from phidl import Device
from phidl import quickplot as qp
from phidl import set_quickplot_options
import phidl.geometry as pg
from typing import Tuple, Union
import math

import qnngds.devices as qd

set_quickplot_options(blocking=True)

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
                layer:          int                      = 0
                ) -> Device:
    """
    Creates a SNSPD coupled to an NTRON, with 3 inductors in the circuit as:

    >>> |        |
    >>> L1       L3
    >>> |        |
    >>> |__L2__NTRON
    >>> |        |
    >>> SNSPD
    >>> |
    
    The length of L1, L2, and L3 (long nanowires) where scaled against the SNSPD:
    L1 = L3 = k13 * L and L2 = k2 * L where L is the SNSPD kinetic inductance.

    Parameters:
        w_snspd (float): Width of the SNSPD.
        pitch_snspd (float): Pitch of the SNSPD.
        size_snspd (Tuple[Union[int, float]]): Size of the SNSPD.
        w_inductor (float): Width of the inductors.
        pitch_inductor (float): Pitch of the inductors.
        k_inductor13 (Union[int, float]): The factor for scaling L1 and L3 relative to the SNSPD kinetic inductance.
        k_inductor2 (Union[int, float]): The factor for scaling L2 relative to the SNSPD kinetic inductance.
        w_choke (float): Width of the choke in the NTRON.
        w_channel (float): Width of the channel in the NTRON.
        w_pad (Union[int, float]): Width of the external connections to the cell.
        layer (int): Layer of the device.

    Returns:
        Device: The created device.
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
        NTRON = SNSPD_NTRON << qd.ntron(choke_w = w_choke, 
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

