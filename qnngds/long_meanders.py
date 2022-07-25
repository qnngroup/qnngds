import numpy as np
import scipy.io as sio
import matplotlib.pyplot as plt
from scipy import constants
from scipy.interpolate import interp1d

from qnngds.qnngds.taper_helpers.erickson_taper import length, erickson_polynomial_z
from qnngds.qnngds.taper_helpers.klopfenstein_taper import klop_length, klopfenstein_z
from qnngds.qnngds.taper_helpers.taper_library import *

from qnngds.qnngds.meander_geometry import CPW_to_phidl, cpw_pad, microstrip_taper_c, solid_pad
from qnngds.qnngds.long_meander_helpers.generator_scripts import generate_taper, generate_meander
from qnngds.qnngds.long_meander_helpers.coords import Coords, quarter12to3, quarter12to9

'''
Functions that put all the pieces together to output specific long meanders as PHIDL devices

* make_snspi_meander - returns a PHIDL device of an SNSPI meander
    - Requires:
        * design parameters in um (see docstring)
* make_taper - returns a PHIDL device taper and a matching pad device in the appropriate size
    - Requires: 
        * Sonnet simulation of Z, eps_eff and the output csv filepaths
         (default format: filename \n output value type \n parameter, output \n) 
         -- or analytical calculation from taper_helpers/analytical.py
        * other design parameters in um/MHz/dB
'''

def make_snspi_meander(w, g, array_length, array_height, min_conductor, 
    line_height, meander_architecture=ARCHITECTURE.CPW, gds_name=None, plot=False):
    '''
    Generates a meander array for an SNSPI
    
    w = width of central conductor [um]
    g = gap to ground [um]
    array_length = total x-length of array [um]
    array_height = total y-height of array [um]
    min_conductor = minimum amount of ground conductor spacer when turning [um]
    line_height = height of one pixel in a single line [um]
    meander_architecture = CPW vs Microstrip [taper_library.ARCHITECTURE]
    gds_name (optional) = name of gds file to write array to [string]
    plot (optional) = (Boolean) whether to plot meander Coords 
    '''

    coords = Coords()
    coords.initialize_horizontal(w, g)

    dl = 0.1
    coords = generate_meander(coords, w, g, array_length, array_height, min_conductor, line_height, dl)

    if meander_architecture == ARCHITECTURE.CPW:
        meander = CPW_to_phidl(coords, port1='top', port2='bottom')
    elif meander_architecture == ARCHITECTURE.Microstrip:
        meander = microstrip_taper_c(coords, port1='top', port2='bottom')

    meander.flatten()
    if gds_name:
        meander.write_gds(gds_name)

    if plot:
        plt.plot(np.multiply(coords.x0, 1E-3), np.multiply(coords.y0, 1E-3), marker=',')
        plt.plot(np.multiply(coords.x1, 1E-3), np.multiply(coords.y1, 1E-3), marker=',', color='orange')
        plt.plot(np.multiply(coords.x2, 1E-3), np.multiply(coords.y2, 1E-3), marker=',', color='green')
        plt.plot(np.multiply(coords.x3, 1E-3), np.multiply(coords.y3, 1E-3), marker=',', color='green')
        plt.plot(np.multiply(coords.x4, 1E-3), np.multiply(coords.y4, 1E-3), marker=',', color='orange')

        plt.xlabel('x [mm]')
        plt.ylabel('y [mm]')

        plt.axis('square')

        plt.show()

    return meander

def make_taper(z_file, eps_file, gap, w0, lmax, Fc, F1=50, F2=20000, num_freq_points=1000,
  taper_geometry=TAPER_GEOM.Klopfenstein, taper_architecture = ARCHITECTURE.CPW, 
  epsilon2=constants.epsilon_0*10, Zmatch=50, RdB=-20, N=2, sections=6000, offset=0,
  bending_radius_factor=3, pigtail=True, plot=False):
    '''
    z_file: path to file of calculated impedances as function of width/gap
    eps_file: path to file of calculated epsilons as function of width/gap
    gap = initial gap [um]
    w0 = initial width [um]
    lmax = maximum lengthwise dimension to meander taper [um]
    Fc = lower cut-off frequency [MHz]
    F1 = start frequency for response plot [MHz]
    F2 = stop frequency for response plot [MHz]
    num_freq_points = number of frequencies between F1 and F2 to compute
    taper_geometry = Klopfenstein vs Erickson
    taper_architecture = CPW vs microstrip
    epsilon2 = final epsilon to match to
    Zmatch = final impedance to match to
    RdB = operating band ripple [dB] (needed for Klopfenstein)
    N = polynomial order (needed for Erickson)
    sections = number of subdivisions of polygons to create
    offset = offset for centering taper
    bending_radius_factor = geometric constant for determining bend radius
    plot = Boolean, whether to plot resulting taper

    returns: d [Taper Device], pad [matching Pad Device], final_width [last width value used, [um]]
    '''
    # compute derived parameters
    f = Fc*1e6 # design frequency [Hz]
    lambdafs = constants.c/f # design free space wavelength [m]

    freqs = np.arange(F1*1e6, F2*1e6, (F2-F1)*1e6/num_freq_points)

    # read Z(w), eps(w) directly from Sonnet CSVs
    wsim, Zsim = read_other_csv(z_file, 2)
    wsim, epssim = read_other_csv(eps_file, 2)

    # compute simulated Zload based on width
    Zsim_interp = interp1d(wsim, Zsim)
    wsim_interp = interp1d(Zsim, wsim)
    nsim_interp = interp1d(Zsim, np.sqrt(epssim))
    Zload = Zsim_interp(w0)

    # compute desired Z(l), n(l), w(l)
    if taper_geometry == TAPER_GEOM.Erickson:
        # compute Erickson taper Zs and total length
        Z_target = np.asarray([erickson_polynomial_z(xi, N, Z1=Zmatch, Z2=Zload) for xi in np.arange(0, 1+1/sections, 1/sections)])
        total_length = length(lambdafs, epsilon2, N) # [m]
    elif taper_geometry == TAPER_GEOM.Klopfenstein:
        # compute Klopfenstein taper Zs and total length
        Z_target = np.asarray([klopfenstein_z(xi, RdB, Z1=Zmatch, Z2=Zload) for xi in np.arange(0, 1+1/sections, 1/sections)])
        total_length = klop_length(lambdafs, Zload, Zmatch, RdB)



    dlmd0 = total_length/sections # length per section [m]

    Z_target = np.flip(Z_target)

    n_target = nsim_interp(Z_target)
    w_design = wsim_interp(Z_target)

    # divide up length of taper into sections of size dlmd0/n(i) in um
    dlmd0_um = dlmd0*1E6 # [um]
    l = [0] # [um]
    for i in range(1, len(n_target)):
        l.append(l[i-1] + dlmd0_um/n_target[i-1])

    num_squares = np.sum(np.divide(dlmd0_um, np.multiply(n_target, w_design)))
    print(num_squares)

    w_l = interp1d(l, w_design)
    n_w = interp1d(w_design, n_target)

    ''' 3: Taper calculation: compute x and y coordinates of taper
    '''

    coords, row = generate_taper(l, w_design, w_l, n_w, gap, dlmd0_um, lmax=lmax, offset=offset)
    #top_pigtail_coords = generate_pigtail(coords, 0, gap)
    final_width = np.abs(coords.y3[-1] - coords.y2[-1])
    r = bending_radius_factor*(final_width + 2*gap)

    if pigtail:
        # check if row even or odd for pigtail geometry calculation
        if row % 2 == 1:
            i = quarter12to3(coords, final_width, gap, r, 0)
        else:
            i = quarter12to9(coords, final_width, gap, r, 0)

    if taper_architecture == ARCHITECTURE.CPW:
        d = CPW_to_phidl(coords)
        pad = cpw_pad(final_width, gap, False, final_width/3, final_width, gap)
    elif taper_architecture == ARCHITECTURE.Microstrip:
        d = microstrip_taper_c(coords)
        pad = solid_pad(final_width)
    #d.write_gds(gds_name)

    if plot:

        plt.plot(np.multiply(coords.x0, 1E-3), np.multiply(coords.y0, 1E-3), marker=',')
        plt.plot(np.multiply(coords.x1, 1E-3), np.multiply(coords.y1, 1E-3), marker=',', color='orange')
        plt.plot(np.multiply(coords.x2, 1E-3), np.multiply(coords.y2, 1E-3), marker=',', color='green')
        plt.plot(np.multiply(coords.x3, 1E-3), np.multiply(coords.y3, 1E-3), marker=',', color='green')
        plt.plot(np.multiply(coords.x4, 1E-3), np.multiply(coords.y4, 1E-3), marker=',', color='orange')

        plt.xlabel('x [mm]')
        plt.ylabel('y [mm]')

        plt.axis('square')

        plt.show()
    return d, pad, final_width

# save to .mat for generating coordinates from MATLAB script if desired
# sio.savemat('erickson_nbn.mat', {'erickson_Z': Z_target, 'erickson_l': total_length, 'epssim': epssim, 'wsim': wsim, 'Zsim': Zsim})