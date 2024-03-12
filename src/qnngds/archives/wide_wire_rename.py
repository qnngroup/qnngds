# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 16:17:54 2021

@author: omedeiro
"""


import sys
import os 
sys.path.append(r'G:\My Drive\layout\functions')
import colang as mc
from phidl import Device
from phidl import quickplot as qp
import phidl.geometry as pg
import numpy as np
from argparse import Namespace    


sys.path.append(r'Q:\qnngds')
import qnngds.omedeiro_v3 as om
import qnngds.omedeiro as om1

import qnngds.utilities as qu
import qnngds.archives.geometry as qg

#%%

width = [0.5, 1, 2, 3, 4, 5]
a1 = [45, 190, 300, 600, 400, 1000] # x
a2 = [100, 100, 200, 300, 400, 500] # y

D_list = []
for (w, aw, al) in zip(width, a1, a2):
    D = Device('straight_snspd')
    d = D<<om.snspd_straight_ind_symdiff2(w, 30,  aw, al)
    D.info = d.info
    D_list.append(D)    
    print(D.info['inductor_squares'])
X = pg.grid(D_list, spacing=(200, 200))
qp(X)

X.write_gds('test_multipass')