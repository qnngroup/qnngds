# -*- coding: utf-8 -*-
"""
Created on Sun Mar  7 19:27:05 2021

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
               routing=2,
               pad_width=200,   
               pad_outline=10,
               pad_taper_length=60,
               ):
    D = Device('ntron_single')
    input_dict = locals()

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

    D = pg.union(D, by_layer=True)
    D.add_port(1, port=s1.ports[1])
    D.add_port(2, port=s2.ports[1])
    D.add_port(3, port=s3.ports[1])

    D.info = input_dict
    return D


def ntron_ind(choke_w = 0.015, 
              choke_l = .4,
              gate_w = 0.2,
              channel_w = 0.1,
              source_w = .4,
              drain_w = .4,
              inductor_a1 = 15,
              inductor_a2 = 5,
              outline_dis = 0.2,
              sheet_inductance=50,
              routing=1,
              layer = 1,
              ):
    
    D = Device('ntron_ind')
    info = locals()


    ntron = qg.ntron_four_port(choke_w,
                                choke_l,
                                gate_w,
                                channel_w,
                                source_w,
                                drain_w,
                                inductor_a1,
                                inductor_a2,
                                routing,
                                layer)
    for i in [(-100,100), (100,100), (100,-100), (-100, -100)]:
        n1 = D<<qg.outline(ntron, distance=outline_dis, open_ports=2.1)
        n1.move(destination=i)
        
    port_list = D.get_ports()
    for p in port_list:
        if p.name == 5:
            port_list.remove(p)

    ports_num = len(port_list)
    a, b = divmod(ports_num, 4)
    conn_side = np.tile(a, 4)
    for i in range(b):
        conn_side[i] = conn_side[i]+1
    conn_side.sort()
    conn_dict = {'W': conn_side[0],
                 'E': conn_side[1],
                 'S': conn_side[2],
                 'N': conn_side[3]}
    field_x=400
    
    field = pg.compass_multi(size=(field_x,field_x), ports = conn_dict, flip_ports=True, layer = 10)
    
    f_ports = field.get_ports()
    def getmidy(p):
        return p.midpoint[1]

    f_ports.sort(key=getmidy, reverse=True)
    
    route_list = [5, 1, 0, 7, 2, 4, 3, 6, 14, 10, 8, 15, 11, 13, 9, 12]
    
    for i in range(len(route_list)):
        t = D<<pg.outline(qg.hyper_taper(15, f_ports[0].width*.75, routing), distance=outline_dis, open_ports=True)
        t.connect(t.ports['wide'], f_ports[route_list[i]])
        r = D<<qg.outline(pr.route_manhattan(port1=port_list[i], port2=t.ports['narrow'], radius=10), distance=outline_dis,open_ports=0, rotate_ports=True)

    D = pg.union(D)
    D.flatten(single_layer=layer)

    D.info = info
    return D



def tesla(width=0.2, pitch=0.6,length=3.5, angle=15, num=5, pad_width=220, outline=1):
    D = Device('tesla_valve')
    
    val = D<<qg.tesla_valve(width, pitch, length, angle, num)
    tap = D<<qg.hyper_taper(40, pad_width+10, width)
    tap.connect(tap.ports['narrow'], val.ports[1])
    tap_g = D<<qg.hyper_taper(40, pad_width, width)
    tap_g.connect(tap_g.ports['narrow'], val.ports[2])
    
    D = pg.union(D, precision=1e-6)
    D.add_port(name=1, port=tap.ports['wide'])
    D.add_port(name=2, port=tap_g.ports['wide'])
    D = pg.outline(D, distance=outline, open_ports=True, precision=1e-6, layer=1)
    
    pad = D<<qg.pad_U(pad_width=pad_width, pad_length=pad_width, width=15, layer=2)
    pad.connect(pad.ports[1], D.ports[1])
    pad.movex(15)
    D.flatten()
    return D

    
def straight_wire_pad_bilayer(width=0.2, length=30, outline=0.5, layer=1):
    D = Device('straight_wire')    
    info = locals()
    
    ground_taper_length = 20
    pad_outline = 15
    pad_width = 250
    step_scale = 3
    ######################################################################
    detector = qg.outline(pg.straight((width,length)),distance=outline, open_ports=2)
    
    pad = qg.pad_U(pad_width= pad_width, layer=layer+1)
    pad.rotate(180)

    pad_taper = qg.outline(qg.hyper_taper(40, pad_width+pad_outline,width*step_scale),distance=outline, open_ports=2)
    pad_taper.move(pad_taper.ports['wide'], pad.ports[1]).movex(10)
    
    step1 = qg.outline(pg.optimal_step(width*step_scale,width),distance=outline, open_ports=3)
    step1.rotate(180)
    step1.move(step1.ports[1],pad_taper.ports['narrow'])
    
    detector.rotate(90)
    detector.move(origin=detector.ports[2],destination=step1.ports[2])
    
    step2 = qg.outline(pg.optimal_step(width*step_scale,width),distance=outline, open_ports=3)
    step2.move(step2.ports[2],detector.ports[1])
         
    ground_taper = qg.outline(qg.hyper_taper(ground_taper_length, pad_width+10, width*step_scale), distance= outline, open_ports=2)
    ground_taper.rotate(180)
    ground_taper.move(ground_taper.ports['narrow'],step2.ports[1])

    D.add_ref([pad_taper,detector, step1, step2, ground_taper])
    D = pg.union(D, by_layer=True)
    D.flatten(single_layer=layer)
    D.add_ref(pad)
    D.rotate(-90)
    D.move(D.bbox[0],destination=(0,0))
    
    D.info = info
    D.info['squares'] = length/width

    return D

# D = straight_wire_pad_bilayer()