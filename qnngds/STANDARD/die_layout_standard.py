# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 10:30:07 2023

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
import time
import phidl.path as ppz

from phidl.device_layout import _parse_layer, DeviceReference

from argparse import Namespace    



sys.path.append(r'Q:\qnnpy')
sys.path.append(r'Q:\qnngds')
import qnngds.omedeiro_v3 as om
import qnnpy.functions.functions as qf
import qnngds.utilities as qu
import qnngds.geometry as qg
from phidl import set_quickplot_options
set_quickplot_options(show_ports=True, show_subports=True)



def nTronTestDie():
    D = Device()
    rec = D<<pg.rectangle((10000,10000), layer=99)
    dut = D<<pg.gridsweep(om.die_cell, param_y={"text1": [sub for sub in list(string.ascii_uppercase[0:8])]}, param_x={'text2':list(string.digits[1:9])}, param_defaults = {'ports_ground':['S']},  spacing=(0,0))
    dut.move(dut.center, rec.center)
    # E = Device('nTron')
    # choke_offset = np.tile(np.linspace(0, 3, 7), 7)
    # for i, s in zip(D.references, choke_offset):
    #     F = Device('nTron_cell')
    #     nTron = F<<qg.ntron_v2(choke_offset=s)
    #     nTron.movex(nTron.ports[1].midpoint[0], i.ports[1].midpoint[0])
    #     nTron.movey(nTron.ports[3].midpoint[1], i.ports[3].midpoint[1])
    #     i.ports[1].width = 10
    #     i.ports[2].width = 10
    #     i.ports[3].width = 10
    #     i.ports[4].width = 10

    #     F<<pr.route_smooth(nTron.ports[1], i.ports[1], layer=1)
    #     F<<pr.route_smooth(nTron.ports[2], i.ports[2], layer=1)
    #     F<<pr.route_smooth(nTron.ports[3], i.ports[4], layer=1)
    #     F<<pr.route_smooth(nTron.ports[4], i.ports[3], layer=1)


    #     spacer = F<<pg.rectangle(size=(500,500), layer=3)
    #     spacer.move(spacer.center, i.center)
    #     F.flatten()
    #     E<<F
    marks = D<<qg.alignment_marks(locations=((-4500, -4500), (-4500, 4500), (4500, -4500), (4500, 4500)), layer=0)
    marks.move(marks.center, rec.center)
    # D<<E
    # D.flatten()
    D.remove(rec)
    D.name = 'nTronTestDie'
    return D

def nTronTestDie2():
    D = Device()
    rec = D<<pg.rectangle((10000,10000), layer=99)
    dut = D<<pg.gridsweep(om.die_cell_v3, param_y={"text1": [sub for sub in list(string.ascii_uppercase[0:6])]}, param_x={'text2':list(string.digits[1:7])}, param_defaults = {'size':(800, 800), 'size2':(500, 500),'ground_width':300, 'ports':{'N':3, 'E':3, 'W':3, 'S':3}, 'ports_ground':['S']},  spacing=(0,0))
    dut.move(dut.center, rec.center)
    # E = Device('nTron')
    # choke_offset = np.tile(np.linspace(0, 3, 7), 7)
    # for i, s in zip(D.references, choke_offset):
    #     F = Device('nTron_cell')
    #     nTron = F<<qg.ntron_v2(choke_offset=s)
    #     nTron.movex(nTron.ports[1].midpoint[0], i.ports[1].midpoint[0])
    #     nTron.movey(nTron.ports[3].midpoint[1], i.ports[3].midpoint[1])
    #     i.ports[1].width = 10
    #     i.ports[2].width = 10
    #     i.ports[3].width = 10
    #     i.ports[4].width = 10

    #     F<<pr.route_smooth(nTron.ports[1], i.ports[1], layer=1)
    #     F<<pr.route_smooth(nTron.ports[2], i.ports[2], layer=1)
    #     F<<pr.route_smooth(nTron.ports[3], i.ports[4], layer=1)
    #     F<<pr.route_smooth(nTron.ports[4], i.ports[3], layer=1)


    #     spacer = F<<pg.rectangle(size=(500,500), layer=3)
    #     spacer.move(spacer.center, i.center)
    #     F.flatten()
    #     E<<F
    marks = D<<qg.alignment_marks(locations=((-4500, -4500), (-4500, 4500), (4500, -4500), (4500, 4500)), layer=0)
    marks.move(marks.center, rec.center)
    # D<<E
    # D.flatten()
    D.remove(rec)
    D.name = 'nTronTestDie'
    return D


def snspdTestDie():
    
    D = pg.gridsweep(om.die_cell, param_y={"text1": [sub for sub in list(string.ascii_uppercase[0:7])]}, param_x={'text2':list(string.digits[1:8])}, param_defaults = {'ports_ground':['S']},  spacing=(0,0))
    E = Device('SNSPD')
    snspd_area = np.tile(np.linspace(10, 250, 7), 7)
    for i, s in zip(D.references, snspd_area):
        F = Device('snspd_cell')
        spd = F<<pg.snspd_expanded(wire_width=0.1, wire_pitch=0.4, size=(s,s), layer=1)
        spd.rotate(-90)
        spd.move(spd.center, i.center)

        F<<pr.route_smooth(spd.ports[1], i.ports[1], layer=1)
        F<<pr.route_smooth(spd.ports[2], i.ports[2], layer=1)

        spacer = F<<pg.rectangle(size=(500,500), layer=3)
        spacer.move(spacer.center, i.center)
        F.flatten()
        E<<F
    D.flatten()
    D<<E
    D.name = 'snspdTestDie'
    return D

def blankArray(n=8, text1='A', text2='B'):
    D = om.die_cell_v3(ports = {'N':n, 'E':n, 'W':3, 'S':n},ports_ground=['S'], size=(100*n,100*n), size2=(500,500), pad_size=(50,250), text1=text1, text2=text2)
    F = Device('nmem_array_cell')
    # nmem = F<<om.memory_array(n,n)
    # nmem.move(nmem.center, D.center)

    # layers = np.append(np.tile(1, 2*n), np.tile(2, 2*n))

    # for i in range(1,2*n+1):
    #     F<<pr.route_smooth(nmem.ports[i], D.ports[i], path_type='Z', length1=50, length2=20, layer=1, radius=1)
        
    # heaterIntsizeX = abs(D.ports[1].midpoint[0]-D.ports[2*n].midpoint[0])-80
    # heaterIntsizeY = abs(D.ports[2*n].midpoint[1])+100
    # heaterIntsize = np.array([heaterIntsizeX, heaterIntsizeY])
    # heaterInt = F<<pg.compass_multi(heaterIntsize, ports={"W":n, 'E':n})
    # heaterInt_ports = list(heaterInt.ports.values())
    # heaterInt_ports.sort(key=port_norm, reverse=True)
    
    # nmem_portlist = list(nmem.ports.values())
    # nmem_portlist2 = nmem_portlist[2*n:4*n]
    # nmem_portlist2 = port_nearest(heaterInt_ports, nmem_portlist2)

    # for i in range(0,2*n):
    #     F<<pr.route_sharp(nmem_portlist2[i], heaterInt_ports[i].rotate(180), length1=10, length2=30, width=(nmem_portlist2[i].width, 10), path_type='Z', layer=2)
    #     extension = F<<pg.straight(size=(10,20), layer=2)
    #     extension.connect(extension.ports[1], heaterInt_ports[i].rotate(180))
    # padPorts = list(D.ports.values())
    # padPorts = padPorts[2*n:4*n]
    # padPorts.sort(key=port_norm, reverse=True)
    # heaterInt_ports = port_nearest(padPorts, heaterInt_ports)
    # for i in range(0,2*n):
    #     F<<pr.route_sharp(padPorts[i], heaterInt_ports[i], length1=30, length2=30, width=padPorts[i].width, path_type='Z', layer=4)
            
    # F.remove(heaterInt)
    # spacerLoc1 = D.ports[1].midpoint+np.array([-20,10])
    # spacerLoc2 = D.ports[2*n].midpoint+np.array([20,-10])
    # spacer = F<<pg.rectangle(size=spacerLoc1-spacerLoc2, layer=3)
    # spacer.move(spacer.center, D.center)
    F<<D
    return F

def blankArray2():
    D = Device()
    rec = D<<pg.rectangle((10000,10000), layer=99)
    marks = D<<qg.alignment_marks(locations=((-4500, -4500), (-4500, 4500), (4500, -4500), (4500, 4500)), layer=0)
    marks.move(marks.center, rec.center)
    N=4
    dut = D<<pg.gridsweep(blankArray, spacing=(0,0), param_x={'text1': list(string.ascii_uppercase[0:N])}, param_y={'text2': list(string.digits[1:N+1])}, param_defaults={'n':8})
    dut.move(dut.center, rec.center)
    D.remove(rec)
    return D


B = Device('wafer')

B<<pg.ring(radius=100e3/2, layer=99)

Ndie = 45
 # param_x={'text2':list(string.digits[1:8])}, param_defaults = {'ports_ground':['S']},  spacing=(0,0))
# die = pg.basic_die(size=(10e3, 10e3), die_name=)
# die_list = np.tile(die, 36)

die_array = pg.gridsweep(om.basic_die, param_x={'text1': list(string.ascii_uppercase[0:7])}, param_y={'text2': list(string.digits[1:8])}, param_defaults={'size': (10e3, 10e3), 'text_size': 400, 'text_location':'S'}, spacing=(0,0))
die_array.move(die_array.center, (0,0))
B<<die_array


# for i in range(0,49):#49
#     a = B<<nTronTestDie()
#     a.move(a.center, die_array.references[i].center)
    
for i in range(0,49):#49
    a = B<<nTronTestDie2()
    a.move(a.center, die_array.references[i].center)

# for i in [2]:#range(0,21):
#     a = B<<blankArray2()
#     a.move(a.center, die_array.references[i].center)
# qp(B)


B.write_gds('test')



