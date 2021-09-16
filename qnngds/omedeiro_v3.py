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
   


def ntron_single(choke_w = 0.015, 
              choke_l = .3,
              gate_w = 0.2,
              channel_w = 0.120,
              source_w = .4,
              drain_w = .4,
              routing = 1,
              layer=1,
              sheet_inductance=50,
              outline_dis=0.2,
              ):
    
    D = Device('ntron_ind')
    info = locals()


    
    j=-90
    for i in [(-0,150), (150,0), (0,-150), (-150, 0)]:
        ntron = qg.ntron_sharp(choke_w,
                                choke_l,
                                gate_w,
                                channel_w,
                                source_w,
                                drain_w,
                                layer)
        ntron.rotate(j)
        n1 = D<<ntron
        n1.move(destination=i)
        j+=-90
        
    port_list = D.get_ports()
    for p in port_list:
        if p.name == 4:
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

    route_list = [1, 2, 0, 5, 7, 3, 10, 9, 11, 6, 4, 8]
    # D<<field
    new_port_list=[]
    for i in range(len(route_list)):
        step = pg.optimal_step(port_list[i].width, routing, symmetric=True)
        s = D<<step
        s.connect(s.ports[1], port_list[i])
        t = D<<qg.hyper_taper(15, f_ports[0].width*.75, routing)
        t.connect(t.ports[2], f_ports[route_list[i]])
        if round(s.ports[2].midpoint[0], 6)==round(t.ports[1].midpoint[0], 6) or round(s.ports[2].midpoint[1], 6)==round(t.ports[1].midpoint[1], 6):
           r = D<<pr.route_basic(port1=s.ports[2], port2=t.ports[1])
        else:
           r = D<<pr.route_manhattan(port1=s.ports[2], port2=t.ports[1], radius=10)
        new_port_list.append(t.ports[2])
    
    new_port_list.sort(key=getmidy, reverse=True)

    D = pg.union(D)
    D.flatten(single_layer=layer)
    [D.add_port(name=n, port=new_port_list[n]) for n in range(len(new_port_list))]
    D = pg.outline(D, distance=outline_dis, open_ports=2, layer=layer)
    D.info = info
    return D


def ntron_ind3(choke_w = 0.02, 
              choke_l = .3,
              gate_w = 0.2,
              channel_w = 0.120,
              source_w = .4,
              drain_w = .4,
              inductor_a1 = 30,
              inductor_a2 = 10,
              routing = 3,
              layer=1,
              sheet_inductance=50,
              outline_dis=0.2,
              ):
    
    D = Device('ntron_ind3')
    info = locals()


    x=65
    y=65
    j=0
    for i in [(-x,y), (x,y), (x,-y), (-x, -y)]:
        ntron = qg.ntron_three_port(choke_w,
                                choke_l,
                                gate_w,
                                channel_w,
                                source_w,
                                drain_w,
                                inductor_a1,
                                inductor_a2,
                                routing,
                                layer)
        ntron.rotate(j)
        n1 = D<<qg.outline(ntron, distance=outline_dis, open_ports=2.1)
        n1.move(destination=i)
        j+=-90
        
    port_list = D.get_ports()
    for p in port_list:
        if p.name == 4:
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

    route_list = [4, 0, 1, 2, 3, 5, 7, 11, 10, 9, 8, 6 ]
    
    for i in range(len(route_list)):
        t = D<<pg.outline(qg.hyper_taper(30, f_ports[0].width*.75, routing), distance=outline_dis, open_ports=True)
        t.connect(t.ports[2], f_ports[route_list[i]])
        r = D<<qg.outline(pr.route_manhattan(port1=port_list[i], port2=t.ports[1], radius=15), distance=outline_dis,open_ports=0, rotate_ports=True)

    D = pg.union(D)
    D.flatten(single_layer=layer)

    D.info = info
    return D


def ntron_ind_gnd(choke_w = 0.02, 
              choke_l = .3,
              gate_w = 0.2,
              channel_w = 0.120,
              source_w = .4,
              drain_w = .4,
              inductor_a1 = 30,
              inductor_a2 = 10,
              routing = 3,
              layer=1,
              sheet_inductance=50,
              outline_dis=0.2,
              ):
    
    D = Device('ntron_ind3')
    info = locals()


    x=75
    y=75
    j=-90
    for i in [(-x,y), (x,y), (x,-y), (-x, -y)]:
        ntron = qg.ntron_three_port1(choke_w,
                                choke_l,
                                gate_w,
                                channel_w,
                                source_w,
                                drain_w,
                                inductor_a1,
                                inductor_a2,
                                routing,
                                layer)
        ntron.rotate(j)
        n1 = D<<qg.outline(ntron, distance=outline_dis, open_ports=2.1)
        n1.move(destination=i)
        j+=-90
        
    port_list = D.get_ports()
    for p in port_list:
        if p.name == 4:
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

    route_list = [4, 0, 1, 2, 3, 5, 7, 11, 10, 9, 8, 6 ]
    
    for i in range(len(route_list)):
        t = D<<pg.outline(qg.hyper_taper(30, f_ports[0].width*.75, routing), distance=outline_dis, open_ports=True)
        t.connect(t.ports[2], f_ports[route_list[i]])
        r = D<<qg.outline(pr.route_manhattan(port1=port_list[i], port2=t.ports[1], radius=15), distance=outline_dis,open_ports=0, rotate_ports=True)

    D = pg.union(D)
    D.flatten(single_layer=layer)

    D.info = info
    return D



def ntron_ind3_gnd(choke_w = 0.02, 
              choke_l = .3,
              gate_w = 0.2,
              channel_w = 0.120,
              source_w = .4,
              drain_w = .4,
              inductor_a1 = 40,
              inductor_a2 = 15,
              routing = 3,
              layer=1,
              sheet_inductance=50,
              outline_dis=0.2,
              ):
    
    D = Device('ntron_ind3_gnd')
    info = locals()


    x=120
    y=x
    j=180
    for i in [(x, y), (x,-y), (-x,-y), (-x, y)]:
        ntron = qg.ntron_three_port_gnd(choke_w,
                                choke_l,
                                gate_w,
                                channel_w,
                                source_w,
                                drain_w,
                                inductor_a1,
                                inductor_a2,
                                routing,
                                layer)
        ntron.rotate(j)
        n1 = D<<qg.outline(ntron, distance=outline_dis, open_ports=2.1)
        n1.move(destination=i)
        j+=-90
        
    port_list = D.get_ports()


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

    route_list = [4, 3, 2, 6, 15, 10, 8, 14, 11, 12, 13, 9, 0, 5, 7, 1]
    # route_list = [4, 0, 1, 2, 3, 5, 7, 11, 10, 9, 8, 6 ]
    
    for i in range(len(route_list)):
        t = D<<pg.outline(qg.hyper_taper(30, f_ports[0].width*.75, routing), distance=outline_dis, open_ports=True)
        t.connect(t.ports[2], f_ports[route_list[i]])
        r = D<<qg.outline(pr.route_manhattan(port1=port_list[i], port2=t.ports[1], radius=5), distance=outline_dis,open_ports=0, rotate_ports=True)

    D = pg.union(D)
    D.flatten(single_layer=layer)

    D.info = info
    return D



def ntron_ind4(choke_w = 0.02, 
              choke_l = .4,
              gate_w = 0.2,
              channel_w = 0.120,
              source_w = .4,
              drain_w = .4,
              inductor_a1 = 15,
              inductor_a2 = 5,
              outline_dis = 0.2,
              sheet_inductance=50,
              routing=1,
              layer = 1,
              ):
    
    D = Device('ntron_ind4')
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
        t = D<<pg.outline(qg.hyper_taper(30, f_ports[0].width*.75, routing), distance=outline_dis, open_ports=True)
        t.connect(t.ports[2], f_ports[route_list[i]])
        r = D<<qg.outline(pr.route_manhattan(port1=port_list[i], port2=t.ports[1], radius=15), distance=outline_dis,open_ports=0, rotate_ports=True)

    D = pg.union(D)
    D.flatten(single_layer=layer)

    D.info = info
    return D



def ntron_10g(num_gate=10, 
              gate_w=.15, 
              gate_p=.30, 
              choke_w=0.02, 
              choke_l=.3, 
              channel_w=0.120, 
              source_w=0.6, 
              drain_w=0.6, 
              routing=1, 
              outline_dis=.2, 
              layer=1, 
              gate_factor=2.5):
    
    D = Device('ntron_10g')
    info = locals()
    
    conn_dict = {'N': 3,
                 'W': 3,
                 'S': 3,
                 'E': 3}
    enc = qg.ntron_multi_gate_dual_fanout(num_gate, 
              gate_w, 
              gate_p, 
              choke_w, 
              choke_l, 
              channel_w, 
              source_w, 
              drain_w, 
              routing, 
              outline_dis, 
              layer, 
              gate_factor)
    e = D<<enc
    
    field_x=400

    field = pg.compass_multi(size=(field_x,field_x), ports = conn_dict, flip_ports=True, layer = 10)
    f_ports = field.get_ports()

    def getmidy(p):
        return p.midpoint[1]

    f_ports.sort(key=getmidy, reverse=True)
    
    port_list = enc.get_ports()    
    route_list = [10, 1, 9, 8, 6, 4, 0, 2, 3, 5, 7, 11]
    
    for i in range(len(route_list)):
        t = D<<pg.outline(qg.hyper_taper(30, f_ports[0].width*.75, routing), distance=outline_dis, open_ports=True)
        t.connect(t.ports[2], f_ports[route_list[i]])
        if round(port_list[i].midpoint[0], 6)==round(t.ports[1].midpoint[0], 6) or round(port_list[i].midpoint[1], 6)==round(t.ports[1].midpoint[1], 6):
            r = D<<qg.outline(pr.route_basic(port1=port_list[i], port2=t.ports[1]), distance=outline_dis,open_ports=0, rotate_ports=False)
        else:
            r = D<<qg.outline(pr.route_manhattan(port1=port_list[i], port2=t.ports[1], radius=10), distance=outline_dis,open_ports=0, rotate_ports=True)

    D = pg.union(D)
    D.flatten(single_layer=layer)

    D.info = info
    return D



def ntron_10g_ind(num_gate=10, 
              gate_w=.2, 
              gate_p=.30, 
              choke_w=0.050, 
              choke_l=.3, 
              channel_w=0.120, 
              source_w=0.3, 
              drain_w=0.3,
              inductor_a1=30, 
              inductor_a2=5,
              routing=1, 
              outline_dis=.2, 
              layer=1, 
              gate_factor=50):
    
    
    D = Device('ntron_10g')
    info = locals()
    
    conn_dict = {'N': 4,
                 'W': 3,
                 'S': 3,
                 'E': 3}
    enc = qg.ntron_multi_gate_dual_fanout_ind(num_gate, 
              gate_w, 
              gate_p, 
              choke_w, 
              choke_l, 
              channel_w, 
              source_w, 
              drain_w, 
              inductor_a1,
              inductor_a2,
              routing, 
              outline_dis, 
              layer, 
              gate_factor)
    e = D<<enc
    
    field_x=400

    field = pg.compass_multi(size=(field_x,field_x), ports = conn_dict, flip_ports=True, layer = 10)
    f_ports = field.get_ports()

    def getmidy(p):
        return p.midpoint[1]

    f_ports.sort(key=getmidy, reverse=True)
    
    port_list = enc.get_ports()    
    # route_list = [10, 1, 9, 8, 6, 4, 0, 2, 3, 5, 7, 11]
    route_list = [10, 9, 7, 5, 0, 3, 4, 6, 8, 12, 11, 1, 2]

    
    for i in range(len(route_list)):
        t = D<<pg.outline(qg.hyper_taper(30, f_ports[0].width*.75, routing), distance=outline_dis, open_ports=True)
        t.connect(t.ports[2], f_ports[route_list[i]])
        if round(port_list[i].midpoint[0], 6)==round(t.ports[1].midpoint[0], 6) or round(port_list[i].midpoint[1], 6)==round(t.ports[1].midpoint[1], 6):
            r = D<<qg.outline(pr.route_basic(port1=port_list[i], port2=t.ports[1]), distance=outline_dis,open_ports=0, rotate_ports=False)
        else:
            r = D<<qg.outline(pr.route_manhattan(port1=port_list[i], port2=t.ports[1], radius=20), distance=outline_dis,open_ports=0, rotate_ports=True)

    D = pg.union(D)
    D.flatten(single_layer=layer)

    D.info = info
    return D

def ntron_snspd():
    det_width=.1
    inductor_width = .3
    D = Device('ntron_snspd')
    
    det= pg.snspd(wire_width=det_width, wire_pitch=.3, size = (3, 3))
    det.rotate(90)
    
    print(det.info)
    d = D<<det
    
    s1 = D<<pg.optimal_step(det_width, inductor_width, symmetric=True, anticrowding_factor=4)
    s1.connect(s1.ports[1], d.ports[2])
    s2 = D<<pg.optimal_step(det_width, inductor_width, symmetric=True, anticrowding_factor=4)
    s2.connect(s2.ports[1], d.ports[1])
    
    tee1 = D<<pg.tee(size=(1, inductor_width), stub_size=(inductor_width, 1), taper_type = 'fillet')
    tee1.connect(tee1.ports[2], s1.ports[2])
    
    L1 = D<<qg.snspd_vert(wire_width=inductor_width, size=(20, 10))
    L1.connect(L1.ports[1], tee1.ports[3])
    print(L1.info)
    ntron = D<<qg.ntron_sharp(layer=0, gate_w=inductor_width)
    ntron.connect(ntron.ports['g'], L1.ports[2])

    L2 = D<<pg.snspd(wire_width=inductor_width, wire_pitch=inductor_width*3, size=(36, 12))
    L2.mirror()
    print(L2.info)
    L2.connect(L2.ports[1], tee1.ports[1])
    
    L3 = D<<pg.snspd(wire_width=inductor_width, wire_pitch=inductor_width*3, size=(36, 12))
    L3.connect(L3.ports[1], ntron.ports['d'])
    
    D.move(D.bbox[0], (0,5))
    
    ht1 = D<<qg.hyper_taper(1, 5, inductor_width)
    ht1.connect(ht1.ports[1], s2.ports[2])
    
    st1 = D<<pg.straight(size=(inductor_width, 9.5))
    st1.connect(st1.ports[1], ntron.ports['s'])
    
    ht2 = D<<qg.hyper_taper(1, 5, inductor_width)
    ht2.connect(ht2.ports[1], st1.ports[2])
    
    
    qp(D)
    
ntron_snspd()

def tesla(width=0.2, pitch=0.6,length=3.5, angle=15, num=5, pad_width=220, outline=1):
    D = Device('tesla_valve')
    
    val = D<<qg.tesla_valve(width, pitch, length, angle, num)
    tap = D<<qg.hyper_taper(40, pad_width+10, width)
    tap.connect(tap.ports[1], val.ports[1])
    tap_g = D<<qg.hyper_taper(40, pad_width, width)
    tap_g.connect(tap_g.ports[1], val.ports[2])
    
    D = pg.union(D, precision=1e-6)
    D.add_port(name=1, port=tap.ports[2])
    D.add_port(name=2, port=tap_g.ports[2])
    D = pg.outline(D, distance=outline, open_ports=True, precision=1e-6, layer=1)
    
    pad = D<<qg.pad_U(pad_width=pad_width, pad_length=pad_width, width=15, layer=2)
    pad.connect(pad.ports[1], D.ports[1])
    pad.movex(15)
    D.flatten()
    return D

    
def straight_wire_pad_bilayer(width=0.2, length=30, outline=0.5, layer=1, pad_layer=None, two_pads=False, step_scale = 3, pad_shift=10, anticrowding_factor=1.2):
    D = Device('straight_wire')    
    info = locals()
    
    if pad_layer is None:
        pad_layer=layer+1
    ground_taper_length = 20
    pad_outline = 15
    pad_width = 250
    # step_scale = 3 #how big the optimal step is from the straight width. 
    ######################################################################
    detector = qg.outline(pg.straight((width,length)),distance=outline, open_ports=2, layer=layer)
    
    pad = qg.pad_U(pad_width= pad_width, layer=pad_layer)
    pad.rotate(180)

    pad_taper = qg.outline(qg.hyper_taper(40, pad_width+4*pad_outline,width*step_scale),distance=outline, open_ports=2, layer=layer)
    pad_taper.move(pad_taper.ports[2], pad.ports[1]).movex(pad_shift)
    
    step1 = qg.outline(pg.optimal_step(width*step_scale,width, symmetric=True, anticrowding_factor=anticrowding_factor),distance=outline, open_ports=3, layer=layer)
    step1.rotate(180)
    step1.move(step1.ports[1],pad_taper.ports[1])
    
    detector.rotate(90)
    detector.move(origin=detector.ports[2],destination=step1.ports[2])
    
    step2 = qg.outline(pg.optimal_step(width*step_scale,width, symmetric=True, anticrowding_factor=anticrowding_factor),distance=outline, open_ports=3, layer=layer)
    step2.move(step2.ports[2],detector.ports[1])
         
    ground_taper = qg.outline(qg.hyper_taper(ground_taper_length, pad_width+4*pad_outline, width*step_scale), distance= outline, open_ports=2, layer=layer)
    ground_taper.rotate(180)
    ground_taper.move(ground_taper.ports[1],step2.ports[1])

    if two_pads:
        pad2 = qg.pad_U(pad_width= pad_width, layer=layer+1)
        pad2.move(pad2.ports[1], ground_taper.ports[2])
        pad2.movex(pad_shift)
        D<<pad2
        D<<pad
    else:
        D<<pad
        
    D.add_ref([pad_taper,detector, step1, step2, ground_taper])
    D = pg.union(D, by_layer=True)
    D.rotate(-90)
    D.move(D.bbox[0],destination=(0,0))
    D.flatten()
    D.info = info
    D.info['squares'] = length/width

    return D

def snspd_straight_ind_symdiff(width=1, length=30, a1=300, a2=100, inductor_width_factor=2, layer=1):
    
    D = Device('snspd_straight_sym_ind')
    info = locals()
    
    detector = pg.straight(size=(width, length))
    d = D<<detector
    
    iwf = inductor_width_factor
    
    step = pg.optimal_step(width, width*iwf, symmetric=True)
    s1 = D<<step
    s1.connect(s1.ports[1], d.ports[1])
    s2 = D<<step
    s2.connect(s2.ports[1], d.ports[2])
    
    turn = pg.optimal_90deg(width*iwf)
    t1 = D<<turn
    t1.connect(t1.ports[1], s1.ports[2])
    t2 = D<<turn
    t2.connect(t2.ports[2], s2.ports[2])
    
    inductor1 = pg.snspd(wire_width=width*iwf, wire_pitch=width*iwf*3, size=(a1, a2))
    L1 = D<<inductor1
    L1.connect(L1.ports[1], t1.ports[2])
    inductor2 = pg.snspd(wire_width=width*iwf, wire_pitch=width*iwf*3, size=(a1, a2))
    inductor2.mirror()
    L2 = D<<inductor2
    L2.move(L2.ports[1], t2.ports[1])
    
    ground_taper = qg.hyper_taper(30, 200, width*iwf)
    
    g1 = D<<ground_taper
    g1.connect(g1.ports[1], L1.ports[2])
    g2 = D<<ground_taper
    g2.connect(g2.ports[1], L2.ports[2])
    
    D.flatten(single_layer=layer)
    D = pg.union(D)
    D.info = info
    D.info['inductor_squares'] = inductor1.info['num_squares']+inductor2.info['num_squares']
    D.add_port(name=1, port=g1.ports[2])
    D.add_port(name=2, port=g2.ports[2])
    
    return D

def snspd_straight_ind_symdiff2(width=1, length=30, a1=300, a2=100, inductor_width_factor=3, layer=1):
    
    D = Device('snspd_straight_sym_ind')
    info = locals()
    
    detector = pg.straight(size=(width, length))
    d = D<<detector

    iwf = inductor_width_factor
    
    step = pg.optimal_step(width, width*iwf, symmetric=True)
    step_d = step.ports[2].midpoint[0] - step.ports[1].midpoint[0]
    s1 = D<<step
    s1.connect(s1.ports[1], d.ports[1])
    s2 = D<<step
    s2.connect(s2.ports[1], d.ports[2])
    
    hp = pg.optimal_hairpin(width*iwf, width*iwf*3, length=a2/2)
    h1 = D<<hp
    h1.connect(h1.ports[1], s1.ports[2])
    h2 = D<<hp
    h2.connect(h2.ports[2], s2.ports[2])
    
    turn = pg.optimal_90deg(width*iwf)
    turn_d = turn.ports[2].midpoint[0]
    
    distance = turn_d - step_d
    t1 = D<<turn
    t1.connect(t1.ports[1], h1.ports[2])
    t1.movey(distance)
    t2 = D<<turn
    t2.connect(t2.ports[2], h2.ports[1])
    t2.movey(-distance)
    
    inductor1 = pg.snspd(wire_width=width*iwf, wire_pitch=width*iwf*3, size=(a1, a2))
    L1 = D<<inductor1
    L1.connect(L1.ports[1], t2.ports[1])
    inductor2 = pg.snspd(wire_width=width*iwf, wire_pitch=width*iwf*3, size=(a1, a2))
    inductor2.mirror()
    L2 = D<<inductor2
    L2.move(L2.ports[2], t1.ports[2])
    
    ground_taper = qg.hyper_taper(30, 200, width*3)
    
    g1 = D<<ground_taper
    g1.connect(g1.ports[1], L1.ports[2])
    g2 = D<<ground_taper
    g2.connect(g2.ports[1], L2.ports[1])
    
    D.flatten(single_layer=layer)
    D = pg.union(D)
    D.info = info
    D.info['inductor_squares'] = inductor1.info['num_squares']+inductor2.info['num_squares']
    D.add_port(name=1, port=g1.ports[2])
    D.add_port(name=2, port=g2.ports[2])
    
    return D


def snspd_straight_ind_symdiff3(width=1, length=30, a1=300, a2=100, inductor_width_factor=3, layer=1):
    
    D = Device('snspd_straight_sym_ind')
    info = locals()
    
    detector = pg.straight(size=(width, length))
    detector.rotate(90)
    detector.move(detector.center, destination=(0,0))
    d = D<<detector

    iwf = inductor_width_factor
    
    step = pg.optimal_step(width, width*iwf, symmetric=True)
    step_length = step.bbox[1][0]-step.bbox[0][0]
    step_d = step.ports[2].midpoint[0] - step.ports[1].midpoint[0]
    s1 = D<<step
    s1.connect(s1.ports[1], d.ports[1])
    s2 = D<<step
    s2.connect(s2.ports[1], d.ports[2])
    
    testhp = pg.optimal_hairpin(width*iwf, width*iwf*3, length=0)
    zeroLdim = testhp.bbox[1][0]-testhp.bbox[0][0]
    Ldim=a1/2-length/2-step_length

    hp = pg.optimal_hairpin(width*iwf, width*iwf*3, length=Ldim)
    
    h1 = D<<hp
    h1.connect(h1.ports[1], s1.ports[2])
    h2 = D<<hp
    h2.connect(h2.ports[1], s2.ports[2])
  
    
    inductor1 = pg.snspd(wire_width=width*iwf, wire_pitch=width*iwf*3, size=(a1, a2))
    inductor1.mirror()
    L1 = D<<inductor1
    L1.connect(L1.ports[1], h2.ports[2])
    L1.movex(Ldim)

    inductor2 = pg.snspd(wire_width=width*iwf, wire_pitch=width*iwf*3, size=(a1, a2))
    inductor2.mirror()
    L2 = D<<inductor2
    L2.connect(L2.ports[2], h1.ports[2])
    L2.movex(-Ldim)
    
    hp2 = pg.optimal_hairpin(width*iwf, width*iwf*3, length=a1/2)
    h3 = D<<hp2
    h3.connect(h3.ports[2], L1.ports[2])
    h3.movex(a1/2)
    
    h4 = D<<hp2
    h4.connect(h4.ports[2], L2.ports[1])
    h4.movex(-a1/2)
    
    turn = pg.optimal_90deg(width=width*iwf)
    Tdim = turn.ports[2].midpoint[0]
    t1 = D<<turn
    t1.connect(t1.ports[2], h3.ports[1])
    t1.movex(-Tdim+width*iwf/2)
    
    t2 = D<<turn
    t2.connect(t2.ports[2], h4.ports[1])
    t2.movex(Tdim-width*iwf/2)

    ground_taper = qg.hyper_taper(10, 200, width*iwf)
    
    g1 = D<<ground_taper
    g1.connect(g1.ports[1], t1.ports[1])
    g2 = D<<ground_taper
    g2.connect(g2.ports[1], t2.ports[1])
    
    D.flatten(single_layer=layer)
    D = pg.union(D)
    D.info = info
    D.info['inductor_squares'] = inductor1.info['num_squares']+inductor2.info['num_squares']
    D.info['total_squares'] = length/width + inductor1.info['num_squares']+inductor2.info['num_squares']
    D.add_port(name=1, port=g1.ports[2])
    D.add_port(name=2, port=g2.ports[2])
   
    return D





def snspd_hairpin_ind_symdiff(width=1, length=30, a1=300, a2=100, layer=1):
    
    D = Device('snspd_straight_sym_ind')
    info = locals()
    
    # detector = pg.straight(size=(width, length))
    # d = D<<detector
    detector = pg.optimal_hairpin(width=width, pitch=width*3, length=length)
    d = D<<detector
    
    step = pg.optimal_step(width, width*3)
    s1 = D<<step
    s1.connect(s1.ports[1], d.ports[2])
    step1 = pg.optimal_step(width*3, width)
    s2 = D<<step1
    s2.connect(s2.ports[2], d.ports[1])
    
    turn = pg.optimal_hairpin(width=width*3, pitch=width*9, length=width*25)
    t1 = D<<turn
    t1.connect(t1.ports[2], s1.ports[2])
    t2 = D<<turn
    t2.connect(t2.ports[1], s2.ports[1])
    
    inductor1 = pg.snspd(wire_width=width*3, wire_pitch=width*9, size=(a1, a2))
    L1 = D<<inductor1
    L1.connect(L1.ports[1], t1.ports[1])
    inductor2 = pg.snspd(wire_width=width*3, wire_pitch=width*9, size=(a1, a2))
    inductor2.mirror()
    L2 = D<<inductor2
    L2.move(L2.ports[2], t2.ports[2])
    
    ground_taper = qg.hyper_taper(30, 200, width*3)
    
    g1 = D<<ground_taper
    g1.connect(g1.ports[1], L1.ports[2])
    g2 = D<<ground_taper
    g2.connect(g2.ports[1], L2.ports[1])
    
    D.flatten(single_layer=layer)
    D = pg.union(D)
    D.info = info
    D.info['inductor_squares'] = inductor1.info['num_squares']+inductor2.info['num_squares']
    
    return D

def snspd_extended(wire_width=1, wire_pitch=4, a1=100, layer=1):
    D = Device('snspd_dogbone')
    info = locals()
    
    detector = pg.snspd(wire_width, wire_pitch, size = (a1, a1))
    d = D<<detector
    
    htaper = qg.hyper_taper(50, 200, wire_width)
    ht1 = D<<htaper
    ht1.connect(ht1.ports[1], d.ports[1])
    
    ht2 = D<<htaper
    ht2.connect(ht2.ports[1], d.ports[2])

    
    D.flatten(single_layer=layer)
    D = pg.union(D)
    D.add_port(port=ht1.ports[2], name=1)
    D.add_port(port=ht2.ports[2], name=2)
    D.info = info
    D.info['num_squares'] = detector.info['num_squares']
    print(detector.info['num_squares'])
    return D


def snspd_single_end(wire_width=1, wire_pitch=4, a1=100, layer=1):
    D = Device('snspd_dogbone')
    info = locals()
    
    detector = pg.snspd(wire_width, wire_pitch, size = (a1, a1))
    d = D<<detector
    
    htaper = qg.hyper_taper(50, 200, wire_width)
    ht1 = D<<htaper
    ht1.connect(ht1.ports[1], d.ports[1])
    
    ht2 = D<<htaper
    ht2.connect(ht2.ports[1], d.ports[2])
    
    pad = pg.straight(size=(200, 250))
    p1 = D<<pad
    p1.connect(p1.ports[1], ht1.ports[2])
    
    D.flatten(single_layer=layer)
    D = pg.union(D)
    D.add_port(port=ht2.ports[2])
    D.info = info
    D.info['num_squares'] = detector.info['num_squares']
    print(detector.info['num_squares'])
    return D


def snspd_dogbone(wire_width=1, wire_pitch=4, a1=100, layer=1):
    D = Device('snspd_dogbone')
    info = locals()
    
    detector = pg.snspd(wire_width, wire_pitch, size = (a1, a1))
    d = D<<detector
    
    htaper = qg.hyper_taper(100, 200, wire_width)
    ht1 = D<<htaper
    ht1.connect(ht1.ports[1], d.ports[1])
    
    ht2 = D<<htaper
    ht2.connect(ht2.ports[1], d.ports[2])
    
    pad = pg.straight(size=(200, 250))
    p1 = D<<pad
    p1.connect(p1.ports[1], ht1.ports[2])
    p2 = D<<pad
    p2.connect(p2.ports[1], ht2.ports[2])
    
    D.flatten(single_layer=layer)
    D = pg.union(D)
    D.info = info
    print(detector.info['num_squares'])
    return D

def snspd_straight_dogbone(wire_width=1, a1=100, layer=1):
    D = Device('snspd_dogbone')
    info = locals()
    
    detector = pg.straight(size = (wire_width, a1))
    d = D<<detector
    detector.info['num_squares'] = a1/wire_width
    htaper = qg.hyper_taper(60, 200, wire_width)
    ht1 = D<<htaper
    ht1.connect(ht1.ports[1], d.ports[1])
    
    ht2 = D<<htaper
    ht2.connect(ht2.ports[1], d.ports[2])
    
    pad = pg.straight(size=(200, 250))
    p1 = D<<pad
    p1.connect(p1.ports[1], ht1.ports[2])
    p2 = D<<pad
    p2.connect(p2.ports[1], ht2.ports[2])
    
    D.flatten(single_layer=layer)
    D = pg.union(D)
    D.info = info
    print(detector.info['num_squares'])
    return D


def memory_array(N, M, spacing=(8, 5), layer1=1, layer2=2):
    D = Device('memory_array')
    info = locals()
    
    D_list = []
    d_list = []

    port_list = []
    Dsub = Device('column')

    for i in range(0,N):
        memory = qg.nMem()
        d = Dsub<<memory
        d.movey(i*spacing[1])


    sub_port_list = Dsub.get_ports()
    sub_port_list = np.reshape(sub_port_list, (N,4))
    port_list = []
    for i in range(1, N):
        con = Dsub<<pr.route_basic(sub_port_list[i-1][0], sub_port_list[i][1], layer=layer1)
        # port_list.extend(Dsub.get_ports())
        # port_list = port_list[:len(port_list)-2]
    
    for i in range(0, M):
        d = D<<Dsub
        d.movex(i*spacing[0])
        
    port_list = D.get_ports()
    heaterL=[]
    heaterR=[]
    colT = []
    colB = []
    for p in port_list:
        if p.name==1:
            colT.append(p)
        if p.name==2:
            colB.append(p)
        if p.name==3:
            heaterL.append(p)
        if p.name==4:
            heaterR.append(p)
        

    for i in range(0, N*(M-1)):
        D<<pr.route_basic(heaterR[i], heaterL[i+N], layer=layer2)
        
    D.flatten()
    
    if N==1:
        n=1
    else:
        n=2*N-1
        
    # CREATE OUTLINE (EITHER HERE OR AFTER ADDING ROUTING TO PADS)
    E = pg.extract(D, layers=[layer1])
    colT = np.reshape(colT, (M,n)).T
    for p, i in zip(colT[N-1], range(0, M)):
        E.add_port(port=p, name=i+1)
    colB = np.reshape(colB, (M, n)).T
    for p, i in zip(colB[0], range(0, M)):
        E.add_port(port=p, name=M+i+1)
        
    # E = pg.outline(E, distance=.1, open_ports=True)
    # D<<E
    D = pg.union(D, by_layer=True)

    # ADD PORTS
    for p, i in zip(colT[N-1], range(0, M)):
        D.add_port(port=p, name=i+1)
    for p, i in zip(colB[0], range(0, M)):
        D.add_port(port=p, name=M+i+1)
    for p, i in zip(heaterL[0:N], range(0, N)):
        D.add_port(port=p, name=M*2+i+1)
    for p, i in zip(heaterR[len(heaterR)-N:len(heaterR)], range(0, N)):
        D.add_port(port=p, name=M*2+i+1+N)
    return D

# D, d = memory_array(4,2, spacing=(10,10))
# qp(D)