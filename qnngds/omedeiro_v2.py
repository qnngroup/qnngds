# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 10:17:33 2021

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



sys.path.append(r'Q:\qnnpy')
sys.path.append(r'Q:\qnngds')
import qnnpy.functions.functions as qf
import qnngds.utilities as qu
import qnngds.geometry as qg
   
def ntron_single(
               device_layer=1,
               pad_layer=2,
               choke_w=0.05, 
               choke_l=.5,
               gate_w=0.2,
               channel_w=0.1,
               source_w=0.3,
               drain_w=0.3,
               outline=0.1,
               routing=1,
               pad_width=200,   
               pad_outline=10,
               pad_taper_length=60,
               ):
    D = Device('ntron_single')
    input_dict = locals()

    pad = qg.pad_U(pad_width= pad_width, width=pad_outline, layer=pad_layer, port_yshift=-10)
    pad_taper = qg.outline(qg.hyper_taper(pad_taper_length, pad_width+pad_outline,routing),distance=outline, open_ports=2)
    
    
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


    ntron = qg.outline(qg.ntron_sharp(choke_w, choke_l, gate_w, channel_w, source_w, drain_w), distance=outline, open_ports=3, precision=1e-8)
    step = qg.outline(pg.optimal_step(routing, drain_w, symmetric=True, width_tol=1e-8), distance=outline, open_ports=2.1, precision=1e-8)
    step1 = qg.outline(pg.optimal_step(routing, gate_w, symmetric=True, width_tol=1e-8), distance=outline, open_ports=2.1, precision=1e-8)
    
    n1 = D<<ntron
    s1 = D<<step
    s2 = D<<step
    s3 = D<<step1

    n1.move(origin=n1.center,destination=D.center).movex(200)
    s1.connect(s1.ports[2], n1.ports['d'])
    s2.connect(s2.ports[2], n1.ports['s'])
    s3.connect(s3.ports[2], n1.ports['g'])


    D<<qg.outline(pr.route_manhattan(port1=t1.ports['narrow'], port2=s2.ports[1]), distance=outline,open_ports=3, rotate_ports=True, precision=1e-8)
    D<<qg.outline(pr.route_basic(port1=t2.ports['narrow'], port2=s3.ports[1]), distance=outline,open_ports=3, rotate_ports=False, precision=1e-8)
    D<<qg.outline(pr.route_manhattan(port1=t3.ports['narrow'], port2=s1.ports[1]), distance=outline,open_ports=3, rotate_ports=True, precision=1e-8)
    D = pg.union(D, by_layer=True)
    D.info = input_dict
    return D


def ntron_ind(choke_w = 0.05, 
              choke_l = .3,
              gate_w = 0.2,
              channel_w = 0.1,
              source_w = .4,
              drain_w = .3,
              inductor_a1 = 15,
              inductor_a2 = 5,
              outline_dis = 0.2,
              sheet_inductance=50,
              routing=1,
              pad_width=200,   
              pad_outline=10,
              pad_taper_length=60,
              device_layer = 1,
              pad_layer = 2,
              ):
    
    D = Device('ntron_ind')
    D.info = locals()
    
    pad = qg.pad_U(pad_width= pad_width, width=pad_outline, layer=pad_layer, port_yshift=-10)
    pad_taper = qg.outline(qg.hyper_taper(pad_taper_length, pad_width+pad_outline,routing),distance=outline_dis, open_ports=2)
    
    pad = qg.pad_U(pad_width= pad_width, width=pad_outline, layer=pad_layer, port_yshift=-10)
    pad_taper = qg.outline(qg.hyper_taper(pad_taper_length, pad_width+pad_outline,routing),distance=outline_dis, open_ports=2)
    
    
    p1 = D<<pad
    p2 = D<<pad
    p3 = D<<pad
    p4 = D<<pad
    D.distribute(direction='y', spacing=40)
    t1 = D<<pad_taper
    t2 = D<<pad_taper
    t3 = D<<pad_taper
    t4 = D<<pad_taper


    t1.connect(t1.ports['wide'],p1.ports[1])
    t2.connect(t2.ports['wide'],p2.ports[1])
    t3.connect(t3.ports['wide'],p3.ports[1])
    t4.connect(t4.ports['wide'],p4.ports[1])



    ntron = qg.ntron_four_port(choke_w,
                                choke_l,
                                gate_w,
                                channel_w,
                                source_w,
                                drain_w,
                                inductor_a1,
                                inductor_a2,
                                routing,
                                device_layer)
    n1 = D<<qg.outline(ntron, distance=outline_dis, open_ports=2.1)
    n1.rotate(-90)
    n1.move(origin=n1.center,destination=D.center).movex(220)

    D<<qg.outline(pr.route_manhattan(port1=t4.ports['narrow'], port2=n1.ports[1], radius=10), distance=outline_dis,open_ports=0, rotate_ports=True, precision=1e-8)
    D<<qg.outline(pr.route_manhattan(port1=t3.ports['narrow'], port2=n1.ports[4], radius=10), distance=outline_dis,open_ports=0, rotate_ports=True, precision=1e-8)
    D<<qg.outline(pr.route_manhattan(port1=t2.ports['narrow'], port2=n1.ports[2], radius=10), distance=outline_dis,open_ports=0, rotate_ports=True, precision=1e-8)
    D<<qg.outline(pr.route_manhattan(port1=t1.ports['narrow'], port2=n1.ports[3], radius=10), distance=outline_dis,open_ports=0, rotate_ports=True, precision=1e-8)
    
    D = pg.union(D, by_layer=True)
    
    return D

