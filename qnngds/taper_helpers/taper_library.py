import numpy as np
import csv
import matplotlib.pyplot as plt
from enum import Enum

#from electronics_geometry.general_geometries.cpw_coords import Coords

'''
Helper functions for computing impedance matching taper coordinates
in Python. Works for any taper geometry for which width as a function
of length has been calculated.

implemented in Python by Emma Batson
'''

class TAPER_GEOM(Enum):
    Erickson = 0
    Klopfenstein = 1

class ARCHITECTURE(Enum):
    CPW = 0
    Microstrip = 1

def read_sonnet_csv(filename):
    ''' 
    filename: path to Sonnet CSV file

    read out some y value as a function of width
    from Sonnet output CSV with rows of form:
    0 - filepath DE_EMBEDDED w=val g=val
    1 - FREQUENCY (GHz) MAG[y]
    2 - freq, y

    returns: list[widths], list[ys]
    '''
    widths = []
    gs = []
    ys = []
    with open(filename) as csvfile:
        read = csv.reader(csvfile)
        for i, row in enumerate(read):
            # read width from 0th row
            if i % 3 == 0:
                startindex = row[0].find('w=')
                stopindex = row[0][startindex:].find('g=')
                width = float(row[0][startindex+2:startindex+stopindex-1])
                widths.append(width)
                g = float(row[0][startindex+stopindex+2:-1])
                gs.append(g)
            # read y value from 2nd row
            elif i % 3 == 2:
                ys.append(float(row[1]))
    return widths, ys, gs

def read_other_csv(filename, skiprows=0):
    '''
    filename: path to CSV file
    skiprows: number of rows at beginning to skip

    assumes each data row of CSV has form [X, Y]

    returns: list[xs], list[ys]
    '''
    xs = []
    ys = []
    with open(filename) as csvfile:
        read = csv.reader(csvfile)
        for i, row in enumerate(read):
            if i < skiprows:
                pass 
            else:
                xs.append(float(row[0]))
                ys.append(float(row[1]))
    return xs, ys

def slice_by_gap(widths, gs, Zs, eEffs, gap_val):
    '''
    used for slicing a multidimensional dataset
    to take only widths and ys at a given gap value

    widths = arraylike of width values
    gs = arraylike of gap values, in same order
    Zs = arraylike of Z vals in same order
    eEffs = arraylike of eEffs in same order
    gap_val = desired gap value

    returns widths and ys at gap value
    '''
    gaps = np.array(gs)
    indices = np.where(gaps == gap_val)[0]
    new_widths = []
    new_Zs = []
    new_eEffs = []
    for i in indices:
        new_widths.append(widths[i])
        new_Zs.append(Zs[i])
        new_eEffs.append(eEffs[i])

    # sort based on widths
    zipped = zip(new_widths, new_Zs, new_eEffs)
    sorted_lists = sorted(zipped)
    tuples = zip(*sorted_lists)

    return [list(t) for t in tuples]

def sonnet_plot(filename, xvar='w', ylabel='Z'):
    width, y, g = read_sonnet_csv(filename)
    if xvar == 'w':
        plt.plot(width, y)
        plt.xlabel('Width [um]')
    elif xvar == 'g':
        plt.plot(g, y)
        plt.xlabel('Gap [um]')
    plt.ylabel(ylabel)
    plt.show()