# -*- coding: utf-8 -*-
"""
Created on Thu Mar 23 21:48:10 2023

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
set_quickplot_options(show_ports=True, show_subports=False)



def standard3Port():
    D = pg.gridsweep(om.die_cell, param_y={"text1": [sub for sub in list(string.ascii_uppercase[0:8])]}, param_x={'text2':list(string.digits[1:9])}, param_defaults = {'ports_ground':['S']},  spacing=(0,0))
    D.move(D.center, (0,0))

# INSERT YOUR DEVICE HERE. EXAMPLE BELOW
    # E = Device('')
    # choke_offset = np.tile(np.linspace(0, 3, 8), 8)
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
    # D<<E
    D<<qg.alignment_marks(locations=((-4500, -4500), (-4500, 4500), (4500, -4500), (4500, 4500)), layer=0)
    return D

qp(standard3Port())

#%%
def standard9Port():
    D = pg.gridsweep(om.die_cell_v3, param_y={"text1": [sub for sub in list(string.ascii_uppercase[0:6])]}, param_x={'text2':list(string.digits[1:7])}, param_defaults = {'size':(800, 800), 'size2':(500, 500),'ground_width':300, 'ports':{'N':3, 'E':3, 'W':3, 'S':3}, 'ports_ground':['S']},  spacing=(0,0))
    D.move(D.center, (0,0))

# INSERT YOUR DEVICE HERE. EXAMPLE BELOW
    # E = Device('')
    # choke_offset = np.tile(np.linspace(0, 3, 8), 8)
    # for i, s in zip(D.references, choke_offset):
    #     F = Device('nTron_cell')
    #     nTron = F<<qg.ntron_v2(choke_offset=s)
    #     nTron.move(nTron.center, i.center)
    #     i.ports[1].width = 10
    #     i.ports[2].width = 10
    #     i.ports[3].width = 10
    #     i.ports[4].width = 10

    #     F<<pr.route_smooth(nTron.ports[1], i.ports[1], layer=1)
    #     F<<pr.route_smooth(nTron.ports[2], i.ports[4], layer=1)
    #     F<<pr.route_smooth(nTron.ports[3], i.ports[8], layer=1)
    #     F<<pr.route_smooth(nTron.ports[4], i.ports[10], layer=1)


    #     spacer = F<<pg.rectangle(size=(500,500), layer=3)
    #     spacer.move(spacer.center, i.center)
    #     F.flatten()
    #     E<<F
    # D<<E
    
    D<<qg.alignment_marks(locations=((-4500, -4500), (-4500, 4500), (4500, -4500), (4500, 4500)), layer=0)

    D.name = 'nTronTestDie'
    return D
qp(standard9Port())
