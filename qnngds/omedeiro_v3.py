# -*- coding: utf-8 -*-
"""
Created on Sun Mar  7 19:27:05 2021

@author: omedeiro
"""

from __future__ import division, print_function, absolute_import
import numpy as np
from phidl import Device, CrossSection, Path
import phidl.geometry as pg
import phidl.routing as pr
from phidl import quickplot as qp
# import colang as mc
import string
from datetime import datetime
import os
import sys
from time import sleep
import phidl.path as pp

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
    
    field = pg.compass_multi(size=(field_x,field_x), ports = conn_dict, layer = 10)
    
    f_ports = field.get_ports()
    def getmidy(p):
        return p.midpoint[1]

    f_ports.sort(key=getmidy, reverse=True)

    route_list = [4, 0, 1, 2, 3, 5, 7, 11, 10, 9, 8, 6 ]
    
    for i in range(len(route_list)):
        t = D<<pg.outline(qg.hyper_taper(30, f_ports[0].width*.75, routing), distance=outline_dis, open_ports=True)
        t.connect(t.ports[2], f_ports[route_list[i]].rotate(180))
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

    field = pg.compass_multi(size=(field_x,field_x), ports = conn_dict, layer = 10)
    f_ports = field.get_ports()

    def getmidy(p):
        return p.midpoint[1]

    f_ports.sort(key=getmidy, reverse=True)
    
    port_list = enc.get_ports()    
    route_list = [10, 1, 9, 8, 6, 4, 0, 2, 3, 5, 7, 11]
    
    for i in range(len(route_list)):
        t = D<<pg.outline(qg.hyper_taper(30, f_ports[0].width*.75, routing), distance=outline_dis, open_ports=True)
        t.connect(t.ports[2], f_ports[route_list[i]].rotate(180))
        if round(port_list[i].midpoint[0], 6)==round(t.ports[1].midpoint[0], 6) or round(port_list[i].midpoint[1], 6)==round(t.ports[1].midpoint[1], 6):
            r = pr.route_basic(port1=port_list[i], port2=t.ports[1])
            D<<pg.outline(r, distance=outline_dis, open_ports=True)
        else:
            r = pr.route_manhattan(port1=port_list[i], port2=t.ports[1], radius=10)
            r.ports[1].rotate(180)
            r.ports[2].rotate(180)
            D<<pg.outline(r, distance=outline_dis,open_ports=True)

    D = pg.union(D)
    D.flatten(single_layer=layer)

    D.info = info
    return D



def ntron_10g_ind(num_gate=10, 
                  gate_w=.2, 
                  gate_p=.450, 
                  choke_w=0.03, 
                  choke_l=.3, 
                  channel_w=0.12, 
                  source_w=0.3, 
                  drain_w=0.3, 
                  inductor_a1=7, 
                  inductor_a2=30, 
                  routing=1, 
                  outline_dis=.2, 
                  layer=1, 
                  gate_factor=15, 
                  choke_taper='straight', 
                  sheet_inductance=50):
    
    D = Device('ntron_10g')
    info = locals()
    
    conn_dict = {'N': 3,
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

    field = pg.compass_multi(size=(field_x,field_x), ports = conn_dict, layer = 10)
    f_ports = field.get_ports()

    def getmidy(p):
        return p.midpoint[1]

    f_ports.sort(key=getmidy, reverse=True)
    
    port_list = enc.get_ports()    
    # route_list = [10, 9, 7, 5, 0, 3, 4, 6, 8, 11, 1, 2]
    route_list = [9, 8, 6, 4, 0, 2, 3, 5, 7, 11, 10, 1]
    
    for i in range(len(route_list)):
        t = D<<pg.outline(qg.hyper_taper(30, f_ports[0].width*.75, routing), distance=outline_dis, open_ports=True)
        t.connect(t.ports[2], f_ports[route_list[i]].rotate(180))
        if round(port_list[i].midpoint[0], 6)==round(t.ports[1].midpoint[0], 6) or round(port_list[i].midpoint[1], 6)==round(t.ports[1].midpoint[1], 6):
            r = pr.route_basic(port1=port_list[i], port2=t.ports[1])
            D<<pg.outline(r, distance=outline_dis, open_ports=True)
        else:
            r = pr.route_manhattan(port1=port_list[i], port2=t.ports[1], radius=10)
            r.ports[1].rotate(180)
            r.ports[2].rotate(180)
            D<<pg.outline(r, distance=outline_dis,open_ports=True)

    D = pg.union(D)
    D.flatten(single_layer=layer)

    D.info = info
    return D



def ntron_snspd(det_width=.1, inductor_width = .3, choke_w=0.02, channel_w=0.12, layer=1):
    info = locals()

    
    routing=3
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
    
    L1 = D<<qg.snspd_vert(wire_width=inductor_width, size=(20, 25))
    L1.connect(L1.ports[1], tee1.ports[3])
    print(L1.info)
    ntron = D<<qg.ntron_sharp(choke_w=choke_w, channel_w=channel_w, gate_w=inductor_width, layer=0,)
    ntron.connect(ntron.ports['g'], L1.ports[2])

    L2 = D<<pg.snspd(wire_width=inductor_width, wire_pitch=inductor_width*2, size=(36, 18))
    L2.mirror()
    print(L2.info)
    L2.connect(L2.ports[1], tee1.ports[1])
    
    L3 = D<<pg.snspd(wire_width=inductor_width, wire_pitch=inductor_width*3, size=(36, 18))
    L3.connect(L3.ports[1], ntron.ports['d'])
    
    D.move(D.bbox[0], (0,5))
    
    ht1 = D<<qg.hyper_taper(1, 5, inductor_width)
    ht1.connect(ht1.ports[1], s2.ports[2])
    
    st1 = D<<pg.straight(size=(inductor_width, 9.5))
    st1.connect(st1.ports[1], ntron.ports['s'])
    
    ht2 = D<<qg.hyper_taper(1, 5, inductor_width)
    ht2.connect(ht2.ports[1], st1.ports[2])
    
    routs1 = D<<pg.optimal_step(inductor_width, routing, symmetric=True, anticrowding_factor=4)
    routs1.connect(routs1.ports[1], L2.ports[2])
    routs2 = D<<pg.optimal_step(inductor_width, routing, symmetric=True, anticrowding_factor=4)
    routs2.connect(routs2.ports[1], L3.ports[2])
    
    D.move(D.center, (0,0))

    port_list = [routs1.ports[2], routs2.ports[2], ht1.ports[2], ht2.ports[2]]
    D = pg.union(D)
    D.add_port(port=port_list[0], name=1)
    D.add_port(port=port_list[1], name=2)
    D.add_port(port=port_list[2], name=3)
    D.add_port(port=port_list[3], name=4)

    E = Device('4ntron_snspds')
    pads = qg.pad_array(8, outline=10, size1=(250, 250), size2=(250, 250))
    pads.remove(pads.polygons[2:8])
    pads.remove([pads.ports[2],pads.ports[3],pads.ports[4],pads.ports[5],pads.ports[6],pads.ports[7]])
    E<<pads
    E<<D
    
    port_list=[]
    for i in range(0,2):
        ht = E<<qg.hyper_taper(10, 100, routing, layer=0)
        ht.connect(ht.ports[2], pads.ports[i])
        port_list.append(ht.ports[2])
        E<<pr.route_basic(ht.ports[1], D.ports[i+1])
        
    port_list.extend([ht1.ports[2], ht2.ports[2]])
    F = pg.copy_layer(E, layer=0)
    F = pg.union(F)
    F.add_port(port=port_list[0], name=1)
    F.add_port(port=port_list[1], name=2)
    F.add_port(port=port_list[2], name=3)
    F.add_port(port=port_list[3], name=4)

    F = pg.outline(F, distance=0.20, open_ports=3, layer=layer)
    E.remove_layers(layers=[0])
    E.flatten(single_layer=layer+1)
    E<<F
    E.flatten()
    E.info = info
    return E
    

def ntron_andor(choke_w=0.02, channel_w=0.12, inductor_width = .3, layer=1):
    D = Device('ntron_andor')
    info=locals()
    routing=3
    
    ntron1 = D<<qg.ntron_sharp(choke_w=choke_w, channel_w=channel_w, gate_w=inductor_width, layer=0)
    ntron2 = D<<qg.ntron_sharp(choke_w=choke_w, channel_w=channel_w, gate_w=inductor_width, layer=0)
    ntron2.mirror()
    ntron2.movex(15)
    
    L1 = D<<pg.snspd(wire_width=inductor_width, wire_pitch=inductor_width*2, size=(9, 5))
    print(L1.info)
    L1.connect(L1.ports[1], ntron1.ports['d'])
    
    L2 = D<<pg.snspd(wire_width=inductor_width, wire_pitch=inductor_width*2, size=(9, 5))
    L2.mirror()
    L2.connect(L2.ports[1], ntron2.ports['d'])
    cen = D.center
    tee1 = D<<pg.tee(size=(1, inductor_width), stub_size=(inductor_width, 1), taper_type = 'fillet')
    tee1.move(tee1.center, cen)
    tee1.rotate(180, center=cen).movey(8)
    D<<pr.route_manhattan(tee1.ports[1], L1.ports[2], radius=1)
    D<<pr.route_manhattan(tee1.ports[2], L2.ports[2], radius=1)

    L3 = D<<qg.snspd_vert(wire_width=inductor_width, wire_pitch=inductor_width*2, size=(15, 15))
    print(L3.info)
    L3.connect(L3.ports[1], tee1.ports[3])
    
    routs1 = D<<pg.optimal_step(inductor_width, routing, symmetric=True, anticrowding_factor=1.5)
    routs1.connect(routs1.ports[1], ntron1.ports['g'])
    routs2 = D<<pg.optimal_step(inductor_width, routing, symmetric=True, anticrowding_factor=1.5)
    routs2.connect(routs2.ports[1], ntron2.ports['g'])
    routs3 = D<<pg.optimal_step(inductor_width, routing, symmetric=True, anticrowding_factor=1.5)
    routs3.connect(routs3.ports[1], L3.ports[2])
    
    st1 = D<<pg.straight(size=(inductor_width, 5))
    st1.connect(st1.ports[1], ntron1.ports['s'])
    st2 = D<<pg.straight(size=(inductor_width, 5))
    st2.connect(st2.ports[1], ntron2.ports['s'])
    
    ht1 = D<<qg.hyper_taper(1, 5, inductor_width)
    ht1.connect(ht1.ports[1], st1.ports[2])
    ht2 = D<<qg.hyper_taper(1, 5, inductor_width)
    ht2.connect(ht2.ports[1], st2.ports[2])
    D.move(D.center, (0,18))

    port_list = [routs1.ports[2], routs2.ports[2], routs3.ports[2], ht1.ports[2], ht2.ports[2]]
    D = pg.union(D)
    for p, i in zip(port_list, range(0,5)):
        D.add_port(port=p, name=i)
    pads = qg.pad_array(5, size1=(200,200), size2=(300,300), outline=10)
    pads.remove(pads.polygons[0])
    pads.remove(pads.polygons[0])
    pads.rotate(180)
    p=D<<pads
    
    port_list=[]
    for i, n in zip([2, 3, 4], [2, 0, 1]):
        port_taper=D<<qg.hyper_taper(10, 150, routing)
        port_taper.connect(port_taper.ports[2], p.ports[i])
        port_list.append(port_taper.ports[2])
        D<<pr.route_basic(port_taper.ports[1], D.ports[n])
    port_list.append(D.ports[3])
    port_list.append(D.ports[4])
    
    E = pg.copy_layer(D, layer=0)
    for p, n in zip(port_list, range(0,5)):
        E.add_port(port=p, name=n)
    E = pg.outline(E, distance=0.2, open_ports=3, layer=layer)
    D.remove_layers(layers=[0])
    D.flatten(single_layer=layer+1)
    D<<E
    D = pg.union(D, by_layer=True)
    D.flatten()
    D.info = info
    return D
    
def ntron_not(choke_w=0.02, channel_w=0.12, inductor_width=.3, gate_w = 0.3, nw_w = .1, nw_area=(3,2), layer=1):
    
    D = Device('ntron_not')
    info=locals()

    routing=3
    
    ntron1 = D<<qg.ntron_sharp(choke_w=choke_w, channel_w=channel_w, gate_w=gate_w, drain_w=inductor_width, source_w=inductor_width, layer=0)
    
    tee1 = D<<pg.tee(size=(3, inductor_width), stub_size=(inductor_width, 1), taper_type = 'fillet')
    tee1.connect(tee1.ports[1], ntron1.ports['s'])
    
    step1 = D<<pg.optimal_step(inductor_width, nw_w, symmetric=True, anticrowding_factor=1.5)
    step1.connect(step1.ports[1], tee1.ports[2])
    
    L1 = D<<pg.snspd(wire_width=nw_w, wire_pitch=.2, size=nw_area)
    print(L1.info)
    L1.connect(L1.ports[1], step1.ports[2])
    
    st1 = D<<pg.straight(size=(.1, .5))
    st1.connect(st1.ports[1], L1.ports[2])
    
    ht1 = D<<qg.hyper_taper(1, 5, .1)
    ht1.connect(ht1.ports[1], st1.ports[2])
    

    
    L2 = D<<pg.snspd(wire_width=inductor_width, wire_pitch=inductor_width*2, size=(inductor_width*30, inductor_width*20))
    print(L2.info)
    L2.connect(L2.ports[1], ntron1.ports['d'])
    
    tee2 = D<<pg.tee(size=(5, inductor_width), stub_size=(inductor_width, 1), taper_type = 'fillet')
    tee2.connect(tee2.ports[2], L2.ports[2])
    
    routs1 = D<<pg.optimal_step(inductor_width, routing, symmetric=True, anticrowding_factor=1.5)
    routs1.connect(routs1.ports[1], tee1.ports[3])
    
    routs2 = D<<pg.optimal_step(inductor_width, routing, symmetric=True, anticrowding_factor=1.5)
    routs2.connect(routs2.ports[1], tee2.ports[3])
    
    routs3 = D<<pg.optimal_step(inductor_width, routing, symmetric=True, anticrowding_factor=1.5)
    routs3.connect(routs3.ports[1], tee2.ports[1])
    
    routs4 = D<<pg.optimal_step(gate_w, routing, symmetric=True, anticrowding_factor=1.5)
    routs4.connect(routs4.ports[1], ntron1.ports['g'])
    
    port_list=[routs4.ports[2], routs3.ports[2], routs1.ports[2], routs2.ports[2]]
    

    
    pads = qg.pad_array(6, size1=(200,200), size2=(300,300), outline=10)
    pads.remove(pads.polygons[2])
    pads.remove(pads.polygons[2])
    pads.rotate(90)
    D<<pads
    port_list2=[]
    for p, i in zip(port_list, range(0,4)):
        port_taper=D<<qg.hyper_taper(10, 80, routing)
        port_taper.connect(port_taper.ports[2], pads.ports[i])
        port_list2.append(port_taper.ports[2])
        D<<pr.route_manhattan(port_taper.ports[1], p, radius=3)
    port_list2.append(ht1.ports[2])
    
    E = pg.copy_layer(D, layer=0)

    for p, n in zip(port_list2, range(0,5)):
        E.add_port(port=p, name=n)
    E = pg.outline(E, distance=.2, open_ports=3, layer=layer)
    D.remove_layers(layers=[0])
    D.flatten(single_layer=layer+1)
    D<<E
    D = pg.union(D, by_layer=True)
    # qp(D)
    D.info = info
    return D
    


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

    
def straight_wire_pad_bilayer(width=0.2, length=30, outline=0.5, layer=1, pad_layer=None, two_pads=False, pad_iso=None, step_scale = 3, pad_shift=10, anticrowding_factor=1.2, de_etch=None):
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
        pad2 = qg.pad_U(pad_width= pad_width, layer=pad_layer)
        pad2.move(pad2.ports[1], ground_taper.ports[2])
        pad2.movex(pad_shift)
        D<<pad2
        D<<pad
    else:
        D<<pad
        

        
    if de_etch:
        pad_etch = D<<pg.rectangle(size=(pad_width-40, pad_width-40), layer=de_etch)
        pad_etch.move(pad_etch.center, pad.center)
        if two_pads:
            pad_etch = D<<pg.rectangle(size=(pad_width-40, pad_width-40), layer=de_etch)
            pad_etch.move(pad_etch.center, pad2.center)
            
            
    if pad_iso is not None:
        pad_etch = D<<pg.rectangle(size=(pad_width-40, pad_width-40), layer=0)
        pad_etch.move(pad_etch.center, pad2.center)
        iso = D<<pg.outline(pad_etch, distance=10, layer=pad_iso)
        iso1 = D<<pg.outline(pad_etch, distance=10, layer=pad_iso)
        iso1.move(iso1.center, pad.center)
        D.remove(pad_etch)

        
        
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

def snspd_extended(wire_width=1, wire_pitch=4, a1=100, a2=None, layer=1):
    D = Device('snspd_dogbone')
    info = locals()
    
    if a2 is None:
        a2=a1
    detector = pg.snspd(wire_width, wire_pitch, size = (a1, a2))
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


def snspd_single_end(wire_width=1, wire_pitch=4, a1=100, a2=None, layer=1):
    D = Device('snspd_dogbone')
    info = locals()
    
    if a2 is None:
        a2=a1
        
    detector = pg.snspd(wire_width, wire_pitch, size = (a1, a2))
    d = D<<detector
    
    htaper = qg.hyper_taper(50, 200, wire_width)
    ht1 = D<<htaper
    ht1.connect(ht1.ports[1], d.ports[1])
    
    ht2 = D<<htaper
    ht2.connect(ht2.ports[1], d.ports[2])
    
    pad = pg.straight(size=(250, 250))
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


 
    
def single_cell(device_layer = 1, heater_layer=2, loop_adjust=0):
    D = Device('cell')
    
    det = D<<qg.snspd_vert(wire_width = 0.1, wire_pitch = 0.6, size = (10,10), layer = device_layer)
    
    taper = pg.optimal_step(0.1, 2, symmetric=True, anticrowding_factor = 1, layer = device_layer)
    
    t1 = D<<taper
    t1.connect(t1.ports[1], det.ports[1])
    
    t2 = D<<taper
    t2.connect(t2.ports[1], det.ports[2])
    
    tee = pg.tee(size = (2, 2), stub_size = (1, 2+loop_adjust), taper_type = 'fillet', layer = device_layer)
    
    tee1 = D<<tee
    tee1.connect(tee1.ports[2], t1.ports[2])
    
    tee2 = D<<tee
    tee2.connect(tee2.ports[1], t2.ports[2])
    
    rs1 = D<<pr.route_smooth(tee1.ports[3], tee2.ports[3], path_type='U', length1=10, layer=device_layer)
    port1 = tee1.ports[1]
    port2 = tee2.ports[2]
    
    
    
    ht1 = D<<pg.C(width=0.8, size=(6, 3.5), layer=heater_layer)
    ht1.rotate(0)
    ht1.move(origin=ht1.center, destination=(15.5+loop_adjust, -5))
    
    D.add_port(name=3, midpoint=(0,-20), orientation=0, width=2)
    D.add_port(name=4, midpoint=(35+loop_adjust,-20), orientation=180, width=2)

    D<<pr.route_smooth(ht1.ports[2], D.ports[3], layer=heater_layer, width = 2)
    D<<pr.route_smooth(D.ports[4], ht1.ports[1], layer=heater_layer, width = 2)
    
    D = pg.union(D, by_layer=True)
    D.add_port(name=1, port=port1)
    D.add_port(name=2, port=port2)
    D.add_port(name=3, midpoint=(0,-20), orientation=0, width=2)
    D.add_port(name=4, midpoint=(35+loop_adjust,-20), orientation=180, width=2)

    return D
# qp(single_cell(loop_adjust=1))

def single_bit_array(N, M, spacing=(40, 30), device_layer=1, heater_layer=2):
    D = Device('1bit_array')
    info = locals()
    
    D_list = []
    d_list = []

    port_list = []
    Dsub = Device('column')

    for i in range(0,N):
        memory = single_cell(device_layer=device_layer, heater_layer=heater_layer)
        d = Dsub<<memory
        d.movey(i*spacing[1])


    sub_port_list = Dsub.get_ports()
    sub_port_list = np.reshape(sub_port_list, (N,4))
    port_list = []
    for i in range(1, N):
        con = Dsub<<pr.route_basic(sub_port_list[i-1][0], sub_port_list[i][1], layer=device_layer)
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
        D<<pr.route_basic(heaterR[i], heaterL[i+N], layer=heater_layer)
        
    D.flatten()
    
    if N==1:
        n=1
    else:
        n=2*N-1
        
    # CREATE OUTLINE (EITHER HERE OR AFTER ADDING ROUTING TO PADS)
    E = pg.extract(D, layers=[device_layer])
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


# qp(single_bit_array(2,2))


def memory_array(N, M, spacing=(8, 5), layer1=1, layer2=2):
    D = Device('memory_array')
    info = locals()
    
    D_list = []
    d_list = []

    port_list = []
    Dsub = Device('column')

    for i in range(0,N):
        memory = qg.memory_v4()
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
# D = memory_array(8,8, spacing=(7,6))
# qp(D)




def tap_array(n, width=1, tap_spacing=100, pad_extension=10, alternate=False, layer=1):
    D = Device('tap_array')
    
    tee = pg.tee(size=(tap_spacing, width), stub_size=(width*4,pad_extension), taper_type='fillet')
    t_list=[]
    port_list=[]
    for i in range(0,n):
        t = D<<tee
        t_list.append(t)
        if i==0:
            port_list.append(t.ports[2])
            port_list.append(t.ports[3])
            
        if i>0:
            if alternate:
                t.connect(t.ports[2-(i%2)], t_list[i-1].ports[2-(i%2)])
                port_list.append(t.ports[3])
            else:
                t.connect(t.ports[2], t_list[i-1].ports[1])
                port_list.append(t.ports[3])
        if i==n-1:
            if alternate:
                port_list.append(t.ports[1+(i%2)])
            else:
                port_list.append(t.ports[1])
                
    D.flatten(single_layer=layer)
    for p, i in zip(port_list, range(0,len(port_list))):
        D.add_port(name=i, port=p)
    # qp(D)
    return D

def via_array(n, via_size=3, via_inset=1, spacing=150, pad_size=(250,250), outline_dis=5, layers=[0,1,2]):
    D = Device('via_array')
    
    # pad1 = D<<pg.straight(size=pad_size, layer=layers[1])
    
    offset = 15
    p = 3
    
    via = qg.via_square(width=via_size, inset=via_inset, layers=layers)
    via_list=[]
    for i in range(0,n):
        conn = pg.straight(size=(via_size+via_inset*2, spacing-via_size-2*via_inset), layer=layers[1+(-1)**(i+1)])

        v = D<<via
        v.movey(i*spacing)
        via_list.append(v)
        if i < n-1:
            c = D<<conn
            c.connect(c.ports[1], v.ports[1])
        
    # v = D<<via
    # v.movey(i*spacing)
    # v.connect(v.ports[2], c.ports[2])
    # via_list.append(v)
    connT = pg.straight(size=(via_size+via_inset*2, spacing-via_size-2*via_inset), layer=layers[2])

    cstart = D<<pg.straight(size=(via_size+via_inset*2, spacing-via_size-2*via_inset), layer=layers[2])
    cstart.connect(cstart.ports[1], via_list[0].ports[2])
    

    
    pstart = D<<qg.pad_basic(base_size=pad_size, port_size=via_size+via_inset*2, taper_length=60, layer=layers[2])
    pstart.connect(pstart.ports[1], cstart.ports[2])
    
    pstart_etch = D<<pg.rectangle(size=(pad_size[0]+offset, pad_size[1]+offset), layer=layers[0])
    pstart_etch.move(pstart_etch.center, pstart.ports['center'])


    for via, i in zip(via_list, range(1,len(via_list))):
        cint = D<<pg.straight(size=(via_size+via_inset*2, spacing-via_size-2*via_inset), layer=layers[1+(-1)**i])
        cint.connect(cint.ports[1], via.ports[p])
        cint.movey(spacing/2)
        cint.movex(-cint.ports[1].midpoint[0])
        
        if p==3:
            p=4
        else:
            p=3
        pint = D<<qg.pad_basic(base_size=pad_size, port_size=via_size+via_inset*2, taper_length=60, layer=layers[1+(-1)**i])
        pint.connect(pint.ports[1], cint.ports[2])
        
        pint_etch = D<<pg.rectangle(size=(pad_size[0]+offset, pad_size[1]+offset), layer=layers[1+(-1)**(i+1)])
        pint_etch.move(pint_etch.center, pint.ports['center'])
        
        if p==4:
            pint_etch1 = D<<pg.rectangle(size=(pad_size[0]-offset, pad_size[1]-offset), layer=layers[1])
            pint_etch1.move(pint_etch1.center, pint.ports['center'])

    cend = D<<pg.straight(size=(via_size+via_inset*2, spacing-via_size-2*via_inset), layer=layers[1+(-1)**(i+1)])
    cend.connect(cend.ports[1], via_list[-1].ports[1])
    
    pend = D<<qg.pad_basic(base_size=pad_size, port_size=via_size+via_inset*2, taper_length=60, layer=layers[1+(-1)**(i+1)])
    pend.connect(pend.ports[1], cend.ports[2])
    
    if n%2==0:
        pend_etch = D<<pg.rectangle(size=(pad_size[0]+offset, pad_size[1]+offset), layer=layers[0])
        pend_etch.move(pend_etch.center, pend.ports['center'])
    else:
        pend_etch = D<<pg.rectangle(size=(pad_size[0]+offset, pad_size[1]+offset), layer=layers[2])
        pend_etch.move(pend_etch.center, pend.ports['center'])
        pend_etch1 = D<<pg.rectangle(size=(pad_size[0]-offset, pad_size[1]-offset), layer=layers[1])
        pend_etch1.move(pend_etch1.center, pend.ports['center'])
            
    E = pg.extract(D, layers=[layers[0]])
    E = pg.outline(E, distance=outline_dis, layer=layers[0])
    D.remove_layers(layers=[layers[0]])
    D<<E
    
    E = pg.extract(D, layers=[layers[2]])
    E = pg.outline(E, distance=outline_dis, layer=layers[2])
    D.remove_layers(layers=[layers[2]])
    D<<E
    
    return D
# qp(via_array(3))





def htron(width1=0.5, length1=4, length2=2, hwidth1=0.15, hwidth2=1, size=(3,1), terminals_same_side=False, expanded=True, rout1=2, rout2=2, dl=3, hl=1):
    D = Device('htron')
    

    wire1 = D<<pg.straight(size=(width1,length1), layer=dl)
    
    if terminals_same_side:
        heater1 = D<<pg.snspd(hwidth1, hwidth1*2, size=size, terminals_same_side=terminals_same_side, layer=hl)
        heater1.move(heater1.center, wire1.center)
        D.info['heater_info'] = heater1.info
    else:
        heater1 = D<<pg.straight(size=(hwidth1,2), layer=hl)
        heater1.rotate(90)
        heater1.move(heater1.center, wire1.center)

    if expanded:
        
        hstep1 = D<<pg.optimal_step(hwidth1, hwidth2, layer=hl, symmetric=True)
        hstep2 = D<<pg.optimal_step(hwidth2, hwidth1, layer=hl, symmetric=True)
    
        hstep1.connect(hstep1.ports[1], heater1.ports[2])
        hstep2.connect(hstep2.ports[2], heater1.ports[1])
        
        step1 = D<<pg.optimal_step(width1, rout1, symmetric=True, layer=dl)
        step1.connect(step1.ports[1], wire1.ports[1])
        
        step2 = D<<pg.optimal_step(width1, rout1, symmetric=True, layer=dl)
        step2.connect(step2.ports[1], wire1.ports[2])

        port1 = hstep2.ports[1]
        port1.midpoint = port1.midpoint+(1,0)
        port2 = hstep1.ports[2]
        port2.midpoint = port2.midpoint-(1,0)
        port_list = [step1.ports[2], step2.ports[2], port1,  port2]
    else:
        port_list = [wire1.ports[1], wire1.ports[2], heater1.ports[1], heater1.ports[2]]

    info = D.info
    D = pg.union(D, by_layer=True)
    D.flatten()
    D.info = info
    
    for p,i in zip(port_list, range(0,len(port_list))):
        D.add_port(name=i, port=p)
        
    return D       

def htron_alt(heater_size=(0.2, 4), channel_size=(1,4), route_width=4, h_layer=1, c_layer=2):
    D = Device('htron')
    
    
    channel = D<<pg.straight(size=channel_size, layer=c_layer)
    
    channel.move(channel.center, (0,0))

    channel_taper = D<<pg.optimal_step(channel_size[0], route_width, anticrowding_factor=0.2, symmetric='True', layer=c_layer)
    channel_taper.connect(channel_taper.ports[1], channel.ports[1])
    channel_taper1 = D<<pg.optimal_step(channel_size[0], route_width, anticrowding_factor=0.2, symmetric='True', layer=c_layer)
    channel_taper1.connect(channel_taper1.ports[1], channel.ports[2])
    ### FLAG POLE CONNECTORS ###
    flagpole1 = D<<pg.flagpole(size=(route_width*2, route_width), stub_size=(heater_size[0],channel_size[1]), shape='p', taper_type='fillet', layer=h_layer)
    flagpole2 = D<<pg.flagpole(size=(route_width*2, route_width), stub_size=(heater_size[0],channel_size[1]), shape='d', taper_type='fillet', layer=h_layer)

    flagpole1.move(flagpole1.ports[1].midpoint, (0,0))
    flagpole2.move(flagpole2.ports[1].midpoint, (0,0))

    compass1 = D<<pg.compass(size=(route_width, route_width), layer=h_layer)
    compass2 = D<<pg.compass(size=(route_width, route_width), layer=h_layer)
    
    compass1.connect(compass1.ports['N'], flagpole1.ports[2].rotate(180))
    compass2.connect(compass2.ports['N'], flagpole2.ports[2].rotate(180))
    
    
    port_list = [channel_taper.ports[2], channel_taper1.ports[2], compass2.ports['E'], compass1.ports['E']]

    info = D.info
    D = pg.union(D, by_layer=True)
    D.flatten()
    D.info = info
    
    for p,i in zip(port_list, range(0,len(port_list))):
        D.add_port(name=i, port=p)

    return D        
# qp(htron_alt())

def htron_not(width1=0.5, width2=0.15, length1=8, length2=2, hwidth1=0.15, size=(3,3), route_width=1, dl=3, hl=1):
    D = Device('htron_not')
    

    wire1 = D<<pg.straight(size=(width1,length1), layer=dl)
    

    heater1 = D<<pg.snspd(hwidth1, hwidth1*2, size=size, terminals_same_side=True, layer=hl)
    heater1.move(heater1.center, wire1.center)

    D.info['heater_info'] = heater1.info

    hstep1 = D<<pg.optimal_step(hwidth1, route_width, layer=hl)
    hstep2 = D<<pg.optimal_step(route_width, hwidth1, layer=hl)

    hstep1.connect(hstep1.ports[1], heater1.ports[2])
    hstep2.connect(hstep2.ports[2], heater1.ports[1])
    
    wire2 = D<<pg.straight(size=(width1,length2), layer=dl)
    wire2.connect(wire2.ports[1], wire1.ports[2])
    
    tee1 = D<<pg.tee(size=(route_width*2,width1), stub_size=(route_width,width1*2),taper_type ='fillet', layer=dl)
    tee2 = D<<pg.tee(size=(route_width*2,width1), stub_size=(route_width,width1*2),taper_type ='fillet', layer=dl)

    tee1.connect(tee1.ports[1], wire2.ports[2])
    tee2.connect(tee2.ports[2], wire2.ports[2])
    
    
    step1 = D<<pg.optimal_step(width1, width2, anticrowding_factor = 1.5, num_pts=100, symmetric=True,  layer=dl)
    step1.connect(step1.ports[1], tee1.ports[2])
    
    wire3 = D<<pg.straight(size=(width2, 2), layer=dl)
    wire3.connect(wire3.ports[1], step1.ports[2])
    
    step2 = D<<pg.optimal_step(route_width, width2, anticrowding_factor = 1.5, num_pts=100, symmetric=True, layer=dl)
    step2.connect(step2.ports[2], wire3.ports[2])
    
    
    tee3 = D<<pg.tee(size=(route_width*5,width1), stub_size=(width1,width1*10),taper_type ='fillet', layer=dl)
    tee3.connect(tee3.ports[2], wire1.ports[1])
    
    induct1 = D<<pg.snspd(wire_width=width1, wire_pitch=width1*2, size=(20,10), layer=dl)
    induct1.connect(induct1.ports[1], tee3.ports[3])
    
    D.info['induct_info'] = induct1.info

    step3 = D<<pg.optimal_step(width1, route_width, anticrowding_factor = 1.5, symmetric=True, layer=dl)
    step3.connect(step3.ports[1], tee3.ports[1])

    step4 = D<<pg.optimal_step(width1, route_width, anticrowding_factor = 1.5, symmetric=True, layer=dl)
    step4.connect(step4.ports[1], induct1.ports[2])
    
    taper=0
    if taper==1:  
        taper1 = D<<qg.optimal_taper(width1, layer=dl)
        taper1.connect(taper1.ports[1], step2.ports[1])
        port_list = [step3.ports[2], step4.ports[2], tee1.ports[3], tee2.ports[3], taper1.ports[2], hstep1.ports[2], hstep2.ports[1]]
    else:
        port_list = [step3.ports[2], step4.ports[2], tee1.ports[3], tee2.ports[3], step2.ports[1], hstep1.ports[2], hstep2.ports[1]]
    info=D.info
    D = pg.union(D, by_layer=True)
    D.flatten()
    D.info = info
    
    for p,i in zip(port_list, range(0,len(port_list))):
        D.add_port(name=i, port=p)
        
    return D


def htron_notR(width1=0.5, width2=0.15, rlength1=5, rlength2=2, length1=4, length2=2, hwidth1=0.2, size=(3,1), route_width=1, dl1=2, dl2=4, hl=1):
    D = Device('htron_not')
    

    wire1 = D<<pg.straight(size=(width1,length1), layer=dl1)
    

    heater1 = D<<pg.snspd(hwidth1, hwidth1*2, size=size, terminals_same_side=True, layer=dl2)
    heater1.move(heater1.center, wire1.center)

    D.info['heater_info'] = heater1.info

    hstep1 = D<<pg.optimal_step(hwidth1, route_width, layer=dl2)
    hstep2 = D<<pg.optimal_step(route_width, hwidth1, layer=dl2)

    hstep1.connect(hstep1.ports[1], heater1.ports[2])
    hstep2.connect(hstep2.ports[2], heater1.ports[1])
    
    step3 = D<<pg.optimal_step(width1, route_width, anticrowding_factor = 1.0, symmetric=True, layer=dl1)
    step3.connect(step3.ports[1], wire1.ports[1])
    step4 = D<<pg.optimal_step(width1, route_width, anticrowding_factor = 1.0, symmetric=True, layer=dl1)
    step4.connect(step4.ports[1], wire1.ports[2])

    
    tee = pg.tee(size=(route_width*2,route_width), stub_size=(route_width,route_width*2),taper_type ='fillet', layer=dl1)

    tee1 = D<<tee
    tee1.connect(tee1.ports[2], step3.ports[2])
    
    r1 = D<<qg.resistor_neg(size=(0.25,rlength1), width=1, length=-3, overhang=1, pos_outline=.1, layer=dl1, rlayer=hl)
    r1.connect(r1.ports[1], tee1.ports[3])
    
    arc1 = D<<pg.arc(radius=1, width=1, theta=90, layer=dl1)
    arc1.connect(arc1.ports[1], step4.ports[2])
    r2 = D<<qg.resistor_neg(size=(0.25,rlength2), width=1, length=2, overhang=1, pos_outline=.1, layer=dl1, rlayer=hl)
    r2.connect(r2.ports[1], arc1.ports[2])

    
    port_list = [tee1.ports[1], r1.ports[2], r2.ports[2], hstep1.ports[2], hstep2.ports[1]]
    info=D.info
    D = pg.union(D, by_layer=True)
    D.flatten()
    D.info = info
    
    for p,i in zip(port_list, range(0,len(port_list))):
        D.add_port(name=i, port=p)
        
    return D



def htron_notR_alt(heater_size=(0.2, 4), channel_size=(1,4), res1_size=(0.25, 4), route_width=4, h_layer=1, c_layer=2, r_layer=1):
    D = Device('htron')
    
    
    channel = D<<pg.straight(size=channel_size, layer=c_layer)
    
    channel.move(channel.center, (0,0))

    channel_taper = D<<pg.optimal_step(channel_size[0], route_width, anticrowding_factor=0.2, symmetric='True', layer=c_layer)
    channel_taper.connect(channel_taper.ports[1], channel.ports[1])
    channel_taper1 = D<<pg.optimal_step(channel_size[0], route_width, anticrowding_factor=0.2, symmetric='True', layer=c_layer)
    channel_taper1.connect(channel_taper1.ports[1], channel.ports[2])
    ### FLAG POLE CONNECTORS ###
    flagpole1 = D<<pg.flagpole(size=(route_width*2, route_width), stub_size=(heater_size[0],channel_size[1]), shape='p', taper_type='fillet', layer=h_layer)
    flagpole2 = D<<pg.flagpole(size=(route_width*2, route_width), stub_size=(heater_size[0],channel_size[1]), shape='b', taper_type='fillet', layer=h_layer)

    flagpole1.move(flagpole1.ports[1].midpoint, (0,0))
    flagpole2.move(flagpole2.ports[1].midpoint, (0,0))

    flagpole1.mirror()
    flagpole2.mirror()
    compass1 = D<<pg.compass(size=(route_width, route_width), layer=h_layer)
    compass2 = D<<pg.compass(size=(route_width, route_width), layer=h_layer)
    
    compass1.connect(compass1.ports['N'], flagpole1.ports[2].rotate(180))
    compass2.connect(compass2.ports['N'], flagpole2.ports[2].rotate(180))
    
    
    
    tee = pg.tee(size=(route_width*2,route_width), stub_size=(route_width,route_width*2),taper_type ='fillet', layer=c_layer)

    tee1 = D<<tee
    tee1.connect(tee1.ports[2], channel_taper.ports[2])
    
    r1 = D<<pg.straight(size=res1_size, layer=r_layer)
    r1.connect(r1.ports[1], tee1.ports[3])
    r1pad = pg.straight(size=(route_width,2), layer=r_layer)
    r1p = D<<r1pad
    r1p.connect(r1p.ports[1], r1.ports[1])
    r2p = D<<r1pad
    r2p.connect(r2p.ports[1], r1.ports[2])

    # flagpole1 = pg.flagpole(size = (route_width*2, route_width), stub_size=(route_width, route_width),taper_type ='fillet', layer=c_layer)
    # fp1 = D<<flagpole1
    # fp1.connect(fp1.ports[1], channel_taper1.ports[2])
    # fp1.mirror()
    
    # compass3 = D<<pg.compass(size=(route_width*2, route_width), layer=c_layer)
    # compass3.connect(compass3.ports['N'], fp1.ports[2].rotate(180))


    arc1 = D<<pg.arc(radius=4, width=route_width, theta=90, layer=c_layer)
    arc1.connect(arc1.ports[1], channel_taper1.ports[2])



    port_list = [tee1.ports[1], r2p.ports[1].rotate(180), arc1.ports[2], compass2.ports['E'], compass1.ports['W']]

    info = D.info
    D = pg.union(D, by_layer=True)
    D.flatten()
    D.info = info
    
    for p,i in zip(port_list, range(0,len(port_list))):
        D.add_port(name=i, port=p)

    return D        




def htron_andor(width1=0.3, pitch1=0.8, width2=0.15, length1=8, length2=2, hwidth1=0.3, hwidth2=0.5, dl=3, hl=1):
    D = Device('htron_andor')
    


    wire1 = D<<pg.straight(size=(width1,length1), layer=dl)
    
    wire2 = D<<pg.straight(size=(width1,length2), layer=dl)
    wire2.connect(wire2.ports[1], wire1.ports[2])
    
    wire3 = D<<pg.straight(size=(width1, length1), layer=dl)
    wire3.connect(wire3.ports[1],wire1.ports[1])
    
    #first heater
    heater1 = D<<pg.snspd(hwidth1, pitch1, size=(width1*6,hwidth1*10), terminals_same_side=True, layer=hl)
    heater1.move(heater1.center, wire1.center)

    D.info['heater_info'] = heater1.info
    
    hstep1 = D<<pg.optimal_step(hwidth1, hwidth2, layer=hl)
    hstep2 = D<<pg.optimal_step(hwidth2, hwidth1, layer=hl)

    hstep1.connect(hstep1.ports[1], heater1.ports[2])
    hstep2.connect(hstep2.ports[2], heater1.ports[1])
    
    #second heater
    heater2 = D<<pg.snspd(hwidth1, pitch1, size=(width1*6,hwidth1*10), terminals_same_side=True, layer=hl)
    heater2.mirror()
    heater2.move(heater2.center, wire3.center)


    hstep21 = D<<pg.optimal_step(hwidth1, hwidth2, layer=hl)
    hstep22 = D<<pg.optimal_step(hwidth2, hwidth1, layer=hl)

    hstep21.connect(hstep21.ports[1], heater2.ports[1])
    hstep22.connect(hstep22.ports[2], heater2.ports[2])

    # tee1 = D<<pg.tee(size=(length1,width1), stub_size=(width1,width1*2),taper_type ='fillet', layer=dl)
    # tee1.connect(tee1.ports[2], wire3.ports[2])
    
    
    taper=0
    if taper==1:
        taper1 = D<<qg.optimal_taper(width1, layer=dl)
        taper1.connect(taper1.ports[1], wire2.ports[2])

        port_list = [wire3.ports[2], taper1.ports[2], hstep1.ports[2], hstep2.ports[1], hstep21.ports[2], hstep22.ports[1]]
        
    else:
        port_list = [wire3.ports[2], wire2.ports[2], hstep1.ports[2], hstep2.ports[1], hstep21.ports[2], hstep22.ports[1]]
    
    # D = pg.union(D, by_layer=True)
    D.flatten()
    
    for p,i in zip(port_list, range(0,len(port_list))):
        D.add_port(name=i, port=p)
        
    return D



def htron_andor_snspd(width1=0.5, width2=0.1, length1=4, length2=4, hwidth1=0.15, hwidth2=0.5, dl=3, hl=1):
    D = Device('htron_andor_snspd')
    
    wire1 = D<<pg.straight(size=(width1,length1), layer=dl)
    
    heater1 = D<<pg.snspd(hwidth1, hwidth1*2, size=(hwidth1*30,hwidth1*15), terminals_same_side=True, layer=hl)
    heater1.move(heater1.center, wire1.center)

    hstep1 = D<<pg.optimal_step(hwidth1, hwidth2, layer=hl)
    hstep2 = D<<pg.optimal_step(hwidth2, hwidth1, layer=hl)

    hstep1.connect(hstep1.ports[1], heater1.ports[2])
    hstep2.connect(hstep2.ports[2], heater1.ports[1])
    
    wire2 = D<<pg.straight(size=(width1,length2), layer=dl)
    wire2.connect(wire2.ports[1], wire1.ports[2])
    
   
    induct1 = D<<pg.snspd(wire_width=width1, wire_pitch=width1*2, size=(12,10), layer=dl)
    induct1.connect(induct1.ports[1], wire1.ports[1])
    
    print(induct1.info)
    
    tee1 = D<<pg.tee(size=(length1,width1), stub_size=(width1,width1*2),taper_type ='fillet', layer=dl)
    tee1.connect(tee1.ports[2], induct1.ports[2])
    
    # taper1 = D<<qg.hyper_taper(1, 10, width1, layer=dl)
    # taper1.connect(taper1.ports[1], wire2.ports[2])
    
    tee2 = D<<pg.tee(size=(length1*3,width1), stub_size=(width1,width1*4),taper_type ='fillet', layer=dl)
    tee2.connect(tee2.ports[2], tee1.ports[3])
    

    snspd1 = D<<pg.snspd_expanded(wire_width=width2, wire_pitch=width2*3, size=(10,10), connector_width=width1, layer=dl)
    snspd1.mirror()
    snspd1.connect(snspd1.ports[1], tee2.ports[3])
    print(snspd1.info)

    wire3 = D<<pg.straight(size=(width1,snspd1.ports[2].midpoint[1]-wire2.ports[2].midpoint[1]), layer=dl)
    wire3.connect(wire3.ports[1], snspd1.ports[2])
    
    taper=0
    if taper==1:
        taper1 = D<<qg.optimal_taper(width1, layer=dl)
        taper1.connect(taper1.ports[1], wire2.ports[2])
        
        taper2 = D<<qg.optimal_taper(width1, layer=dl)
        taper2.connect(taper2.ports[1], wire3.ports[2])
        port_list = [tee1.ports[1], tee2.ports[1], taper2.ports[2], taper1.ports[2], hstep1.ports[2], hstep2.ports[1]]
        
    else:    
        port_list = [tee1.ports[1], tee2.ports[1], wire3.ports[2], wire2.ports[2], hstep1.ports[2], hstep2.ports[1]]
    
    D = pg.union(D, by_layer=True)
    D.flatten()
    
    for p,i in zip(port_list, range(0,len(port_list))):
        D.add_port(name=i, port=p)
        
    return D



def meander_smooth(wire_width=0.1, meander_length=30, desired_length=5, desired_width=None, pitch=None, layer=1):
    P = Path()
    
    if pitch is None:
        pitch = wire_width*4
        
    if desired_length is None:
        desired_length = meander_length/2
        
        
    r = pitch
    arc_length = 2*np.pi*r/4
    
    target_length = desired_length
    
    
    n = int(target_length/(2*r)) # number of verts in target length
    # print("Number of verts = " + str(n))
    nlength = (meander_length-2*n*arc_length-2*r)/(n-1) # meander straight length
    # print("nlength=" + str(nlength))
    # nturns = int(np.floor(meander_length/meander_width)-1)
    # print(nturns)
    sarc = pp.arc(r, -90)
    P.append(sarc)
    straight = pp.straight(nlength/2-r)
    P.append(straight)
    i=1
    for i in range(1,n):
    # while P.length() < meander_length-nlength:
        if i>1:
            straight = pp.straight(nlength)
            P.append(straight)
        if np.mod(i,2) > 0:
            turn = pp.arc(radius=pitch, angle=180)
            P.append(turn)
        else:
            turn = pp.arc(radius=pitch, angle=-180)
            P.append(turn)
        i=i+1
        j=i
    straight = pp.straight(nlength/2-r)
    P.append(straight)
    # print("j = "+str(j))
    if np.mod(j,2)!=0:
        sarc = pp.arc(r, 90)
        P.append(sarc)
    else:
        sarc = pp.arc(r, -90)
        P.append(sarc)

    tail_length = meander_length-P.length()
    # print("Path_length="+str(P.length()))
    # print("tail_length="+str(tail_length))

    if tail_length < 0:
        raise 'error'

    D = P.extrude(wire_width, layer=layer)    
    D.add_port(0, midpoint=P.points[0], orientation=180, width = wire_width)
    D.add_port(1, midpoint=P.points[-1], orientation=0, width = wire_width)
    t1 = D<<pg.straight(size=(wire_width, tail_length/2), layer=layer)
    t1.connect(t1.ports[1], D.ports[0])
    t2 = D<<pg.straight(size=(wire_width, tail_length/2), layer=layer)
    t2.connect(t2.ports[1], D.ports[1])
    D = pg.union(D, layer=layer)
    D.add_port(1, port=t1.ports[2])
    D.add_port(2, port=t2.ports[2])
    D.move(D.ports[1], (0,0))
    
    # print("sum="+str(P.length()+tail_length))
    return D
# D=Device()
# D<<meander_smooth(meander_length=120, desired_length=5) 
# D<<meander_smooth(meander_length=120, desired_length=10) 
# D<<meander_smooth(meander_length=120, desired_length=25) 
# D.distribute(direction='y', spacing=1)
# D.align(alignment='x')
# qp(D)

# E = Device()
# E<<meander_smooth(meander_length=120, desired_length=5) 
# E<<meander_smooth(meander_length=60, desired_length=5) 
# E<<meander_smooth(meander_length=30, desired_length=5) 
# E.distribute(direction='y', spacing=1)

# F = Device()
# F<<D
# F<<E
# F.distribute(direction='x', spacing=10)
# qp(F)



def die_edge(size0=300, size1 = (7500,7500), layer=0):
    D = Device()
    
    n = int(size1[0]/size0)
    ploc = pg.compass_multi(size=size1, ports={'N': n, 'E': n, 'W': n, 'S': n})
    for p in ploc.ports:
        pad = pg.straight(size=(150,300), layer=2)
        pp = D<<pad
        pp.connect(pp.ports[1], ploc.ports[p])
    
    D<<qg.alignment_marks(locations = ((-4000, -4000), (4000, 4000), (-4000, 4000), (4000, -4000)))
        
    print(len(ploc.ports))
    D.flatten(single_layer=layer)
    return D

def die_row(size0=(150,300), size1 = (7500,300), layer=0):
    D = Device()
    
    n = int(size1[0]/size0[1])
    ploc = pg.compass_multi(size=size1, ports={'N': n, 'S': n})
    for p in ploc.ports:
        pad = pg.straight(size=size0)
        pp = D<<pad
        pp.connect(pp.ports[1], ploc.ports[p])
    
    E = Device()
    for i in range(0,int(0.5*size1[0]/(size0[0]*2+size1[1]))+2):
        E<<D
    E.distribute(direction='y')
    E.move(E.center, (0,0))
    E<<qg.alignment_marks(locations = ((-4000, -4000), (4000, 4000), (-4000, 4000), (4000, -4000)))
        
    print(len(ploc.ports)*i)
    E.flatten(single_layer=layer)
    return E


def die_field(size0=(450,600), size1 = (7500,7500), layer=0):
    
    D = Device()
    n = int(size1[0]/size0[1])
    ploc = pg.compass_multi(size=size0, ports={'N': 3, 'W':6, 'S': 3})
    for p in ploc.ports:
        if ploc.ports[p].orientation == 0 or ploc.ports[p].orientation == 180:
            pad = pg.straight(size=(75,300))
            pp = D<<pad
            pp.connect(pp.ports[1], ploc.ports[p])
        else:
            pad = pg.straight(size=(100,300))
            pp = D<<pad
            pp.connect(pp.ports[1], ploc.ports[p])
    

    x = int(size1[0]/(D.bbox[1][0]-D.bbox[0][0]))-2
    y = int(size1[1]/(D.bbox[1][1]*2))

    E=Device()
    D_list = np.tile(D, x*y)
    E << pg.grid(D_list, spacing=(200,100), shape=(x,y))
    E.move(E.center, (0,0))
    E<<qg.alignment_marks(locations = ((-4000, -4000), (4000, 4000), (-4000, 4000), (4000, -4000)))

    print(x*y)
    return E


def die_cell(size=(500,500), pad_size=(150,200), ground_width=250, ports = {'N':1, 'E':1, 'W':1, 'S':1}, ports_ground=['E','S'], text1='A', text2='1'):

    D = Device()
    
    
    cell = pg.rectangle(size=size)
    ground = D<<pg.outline(cell, distance=ground_width)
    
    padloc = D<<pg.compass_multi(size=size, ports=ports)
    padloc.move(padloc.center, ground.center)
    padloc_list = list(padloc.ports.keys())
    D.remove(ground)
    E = Device()
    
    port_list=[]
    for p in padloc_list:
        pad = E<<qg.pad_basic(base_size=pad_size, port_size=10, taper_length=100)
        pad.connect(pad.ports['base'], padloc.ports[p])
        port_list.append(pad.ports['base'])
        
        cardstr = p[0]
        # if any(cardstr != g for g in ports_ground):
        boolcheck = any(p[0] == g for g in ports_ground)
        if not boolcheck:
            padOut = pg.outline(pad, distance=10)
            ground = pg.boolean(ground, padOut, 'A-B')

    D<<E
    D<<ground
    D.remove(padloc)
    
    E=Device()
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, D.bbox[0]+ground_width/2)
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, D.bbox[1]-ground_width/2)
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, (D.bbox[0][0]+ground_width/2, D.bbox[1][1]-ground_width/2))
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, (D.bbox[1][0]-ground_width/2, D.bbox[0][0]+ground_width/2))
    
    labelOpen = E<<pg.rectangle(size=(300, 50))
    labelOpen.move(labelOpen.center, (D.center[0], D.bbox[0][0]+30))
    D = pg.boolean(D,E,'A-B')

    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center, D.bbox[0]+ground_width/2)
    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center, D.bbox[1]-ground_width/2)
    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center,(D.bbox[0][0]+ground_width/2, D.bbox[1][1]-ground_width/2))
    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center, (D.bbox[1][0]-ground_width/2, D.bbox[0][0]+ground_width/2))

    label = D<<pg.text(text1+text2, size=40, justify="center")
    label.move(label.center, labelOpen.center)
    
    
    
    D = pg.union(D)
    for p, i in zip(port_list, range(1,len(port_list)+1)):
        D.add_port(i, port=p)

    D.move(D.center, (0,0))
    D.flatten()
    return D


def die_cell_v2(size=(2500,2500), size2=(500,500), pad_size=(150,200), ground_width=250, ports = {'N':1, 'E':1, 'W':1, 'S':1}, ports_ground=['E','S'], text1='A', text2='1'):

    D = Device()
    
    
    cell = pg.rectangle(size=size)
    ground = D<<pg.outline(cell, distance=ground_width)
    
    padloc = D<<pg.compass_multi(size=size, ports=ports)
    padloc.move(padloc.center, ground.center)
    padloc_list = list(padloc.ports.keys())
    
    fieldloc = pg.compass_multi(size=size2, ports=ports)
    fieldloc.move(fieldloc.center, ground.center)
    fieldloc_ports = list(fieldloc.ports.values())
    D.remove(fieldloc)
    D.remove(ground)
    E = Device()
    
    port_list=[]
    for p, i in zip(padloc_list, range(0,len(fieldloc_ports))):
        fieldloc_ports[i].width = 10
        pad = E<<pg.straight(size=pad_size)
        pad.connect(pad.ports[1], padloc.ports[p])
        
        pad2 = E<<pg.straight(size=(20,30))
        pad2.connect(pad2.ports[1], fieldloc_ports[i])
        E<<pr.route_sharp(pad.ports[1], pad2.ports[2], path_type='Z', length1=30, length2=10)
        pad2.ports[2].width=20
        port_list.append(pad2.ports[2].rotate(180))
        
        cardstr = p[0]
        # if any(cardstr != g for g in ports_ground):
        boolcheck = any(p[0] == g for g in ports_ground)
        if not boolcheck:
            padOut = pg.outline(pad, distance=10)
            ground = pg.boolean(ground, padOut, 'A-B')

    D<<E
    D<<ground
    D.remove(padloc)
    
    E=Device()
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, D.bbox[0]+ground_width/2)
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, D.bbox[1]-ground_width/2)
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, (D.bbox[0][0]+ground_width/2, D.bbox[1][1]-ground_width/2))
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, (D.bbox[1][0]-ground_width/2, D.bbox[0][0]+ground_width/2))
    
    labelOpen = E<<pg.rectangle(size=(300, 50))
    labelOpen.move(labelOpen.center, (D.center[0], D.bbox[0][0]+30))
    D = pg.boolean(D,E,'A-B')

    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center, D.bbox[0]+ground_width/2)
    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center, D.bbox[1]-ground_width/2)
    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center,(D.bbox[0][0]+ground_width/2, D.bbox[1][1]-ground_width/2))
    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center, (D.bbox[1][0]-ground_width/2, D.bbox[0][0]+ground_width/2))

    label = D<<pg.text(text1+text2, size=40, justify="center")
    label.move(label.center, labelOpen.center)
    
    
    
    D = pg.union(D)
    for p, i in zip(port_list, range(1,len(port_list)+1)):
        D.add_port(i, port=p)

    D.move(D.center, (0,0))
    D.flatten()
    return D

def die_cell_v3(size=(1500,1500), size2=(500,500), pad_size=(150,250), ground_width=500, ports = {'N':1, 'E':1, 'W':1, 'S':1}, ports_ground=['E','S'], text1='A', text2='1'):

    D = Device()
    
    
    cell = pg.rectangle(size=size)
    ground = D<<pg.outline(cell, distance=ground_width)
    
    padloc = D<<pg.compass_multi(size=size, ports=ports)
    padloc.move(padloc.center, ground.center)
    padloc_list = list(padloc.ports.keys())
    # print(padloc.ports)
    fieldloc = pg.compass_multi(size=size2, ports=ports)
    fieldloc.move(fieldloc.center, ground.center)
    fieldloc_ports = list(fieldloc.ports.values())
    D.remove(fieldloc)
    D.remove(ground)
    E = Device()

    
    port_list=[]
    for p, i in zip(padloc_list, range(0,len(fieldloc_ports))):
        fieldloc_ports[i].width = 10
        pad = E<<pg.straight(size=pad_size)
        pad.connect(pad.ports[1], padloc.ports[p])
        
        pad2 = E<<pg.straight(size=(20,30))
        pad2.connect(pad2.ports[1], fieldloc_ports[i])
        E<<pr.route_quad(pad.ports[1], pad2.ports[2])
        pad2.ports[2].width=20
        port_list.append(pad2.ports[2].rotate(180))
        
        cardstr = p[0]
        # if any(cardstr != g for g in ports_ground):
        boolcheck = any(p[0] == g for g in ports_ground)
        if not boolcheck:
            padOut = pg.outline(pad, distance=10)
            ground = pg.boolean(ground, padOut, 'A-B')

    D<<E
    D<<ground
    D.remove(padloc)
    
    E=Device()
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, D.bbox[0]+ground_width/2)
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, D.bbox[1]-ground_width/2)
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, (D.bbox[0][0]+ground_width/2, D.bbox[1][1]-ground_width/2))
    markerOpen = E<<pg.rectangle(size=(150,150))
    markerOpen.move(markerOpen.center, (D.bbox[1][0]-ground_width/2, D.bbox[0][0]+ground_width/2))
    
    labelOpen = E<<pg.rectangle(size=(300, 50))
    labelOpen.move(labelOpen.center, (D.center[0], D.bbox[0][0]+30))
    D = pg.boolean(D,E,'A-B')

    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center, D.bbox[0]+ground_width/2)
    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center, D.bbox[1]-ground_width/2)
    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center,(D.bbox[0][0]+ground_width/2, D.bbox[1][1]-ground_width/2))
    marker = D<<pg.cross(length=150, width=5)
    marker.move(marker.center, (D.bbox[1][0]-ground_width/2, D.bbox[0][0]+ground_width/2))

    label = D<<pg.text(text1+text2, size=40, justify="center")
    label.move(label.center, labelOpen.center)
    
    nPorts = []
    ePorts = []
    wPorts = []
    sPorts = []
    
    for p in port_list:
        if p.orientation == 270:
            nPorts.append(p)
        if p.orientation == 0:
            ePorts.append(p)
        if p.orientation == 180:
            wPorts.append(p)
        if p.orientation == 90:
            sPorts.append(p)

    port_list2=[]
    port_list2.extend(nPorts)
    port_list2.extend(sPorts)
    port_list2.extend(ePorts)
    port_list2.extend(wPorts)

    # print(port_list[[0]])
    D = pg.union(D)
    for p, i in zip(port_list2, range(1,len(port_list2)+1)):
        D.add_port(i, port=p)

    D.move(D.center, (0,0))
    D.flatten()
    # qp(D)
    return D

# a = die_cell_v3(ports={'N':3, 'E':3, 'W':3, 'S':3})

# qp(die_cell_v2(size=(2500,2500), ports={'N':8, 'E':8, 'W':8, 'S':8}))



def basic_die(text1='A', text2='1', **kwargs):
    return pg.basic_die(die_name=text1+text2, **kwargs)