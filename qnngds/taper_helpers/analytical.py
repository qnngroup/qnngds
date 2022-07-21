import numpy as np
import scipy.constants
from mpmath import mp
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

'''
Note: requires mpmath library for extra floating point precision (https://mpmath.org/)

Script to analytically calculate properties of a thin metal CPW on top 
of a multilayer stack (e.g. thin NbN on STO/Si stack). 

Saves desired s and g values as well as corresponding impedances and phase
velocities, plus s50+g50 files that are s/g combinations resulting in 50 ohms
to assist with creating constant-impedance tapers

Based on "50 Ohm Transmission Line with Extreme Wavelength 
Compression Based on Superconducting Nanowire on High-Permittivity
Substrates," Santavicca, D. et al.
'''

s_samples = np.concatenate((np.arange(0.1, 1, 0.01), np.arange(1, 10, 0.1), np.arange(10, 100, 1), np.arange(100, 1000, 100)))
g_samples = np.concatenate((np.arange(0.001, 0.01, 0.001), np.arange(0.01, 0.1, 0.01), s_samples))

print(s_samples)

# set number of decimal points of precision 
mp.dps = 300

# data folder
DATA_FOLDER = '../data/CPW_STO_Lk=80pH_eps=1100_analytical'

# sample parameters used in paper
NBN_THICKNESS = 15E-9 # [nm]
NBN_RSH = 187 # [ohms]
NBN_LKSH = 80E-12 # [pH]
#NBN_LKSH = 21.5E-12 # [pH]
NBN_LONDON_DEPTH = 507E-9 # [nm]
NBN_PEARL_LENGTH = 34.2E-6 # [um]
STO_EPS2 = 1100
STO_H2 = 100E-9 # [nm]
SI_EPS1 = 11.7
SI_H1_MINUS_H2 = 390E-6 # [um]

def impedance(C, L):
    return mp.sqrt(L/C)

def vp(C, L):
    return 1/mp.sqrt(L*C)

def gap(Tc):
    return 1.76*scipy.constants.k*Tc 

def Lk_per_square(Rs, Tc):
    return scipy.constants.hbar*Rs/(np.pi*gap(Tc))


class CPW:
    '''
    class to assist with analytical computations of important design values
    for a CPW line
    '''
    def __init__(self, eps1, eps2, h1, h2, s, g, pearl_length=NBN_PEARL_LENGTH):
        '''
        eps1: relative permittivity of lower material in stack
        eps2: relative permittivity of upper material in stack
        h1: height of full stack
        h2: height of upper material in stack
        s: half width of central CPW conductor
        g: width of CPW gap
        '''
        self.eps1 = eps1
        self.eps2 = eps2
        self.h1 = h1
        self.h2 = h2
        self.s = s
        self.g = g
        self.pearl_length = pearl_length

        self.k = self.calc_k(s, g)
        self.k1 = self.calc_k1(s, g, h1)
        self.k2 = self.calc_k2(s, g, h2)
        self.p = self.calc_p(pearl_length)

        self.q1 = self.calc_q(self.k, self.k1)
        self.q2 = self.calc_q(self.k, self.k2)
        self.epsr = self.calc_epsr(self.q1, eps1, self.q2, eps2)

    def capacitance(self):
        '''
        returns: capacitance per unit length of CPW
        '''
        return 4*scipy.constants.epsilon_0*self.epsr*mp.ellipk(self.k**2)/mp.ellipk(self.prime(self.k)**2)

    def magnetic_inductance(self):
        '''
        returns: magnetic inductance per unit length of CPW
        '''
        return self.epsr/(self.capacitance()*scipy.constants.c**2)

    def kinetic_inductance(self):
        '''
        returns: kinetic inductance per unit length of CPW
        '''
        return scipy.constants.mu_0*self.pearl_length*self.f(self.k, self.p)/(4*self.s)

    def z0(self):
        return 30*mp.pi/mp.sqrt(self.epsr)*mp.ellipk(self.prime(self.k)**2)/mp.ellipk(self.k**2)

    def calc_epsr(self, q1, eps1, q2, eps2):
        '''
        q1: geometric parameter q1
        eps1: relative permittivity of lower material in stack
        q2: geometric parameter q2
        eps2: relative permittivity of upper material in stack
        returns: effective permittivity of stack
        '''
        return 1 + q1*(eps1 - 1) + q2*(eps2 - eps1)

    def f(self, k, p):
        numerator = (k+p**2)*mp.atanh(p) - (1+k*p**2)*mp.atanh(k*p)
        denominator = p*(1-k**2)*(mp.atanh(p))**2
        return numerator/denominator

    def calc_q(self, k, kx):
        '''
        k: geometric constant
        kx: modified geometric constant
        returns: qx
        '''
        return 1/2*mp.ellipk(kx**2)*mp.ellipk(self.prime(k)**2)/(mp.ellipk(self.prime(kx)**2)*mp.ellipk(k**2))

    def prime(self, k):
        '''
        k: one of several geometric constants
        returns: k'
        '''
        return mp.sqrt(1 - k**2)

    def calc_k(self, s, g):
        '''
        s: half width of central conductor
        g: gap width of CPW
        returns: geometric parameter k
        '''
        return s/(s+g)

    def calc_p(self, pearl_length):
        '''
        pearl_length = Pearl length of CPW material

        assumes Pearl length >> width of central conductor

        returns: geometric parameter p
        '''
        return 0.63/np.sqrt(pearl_length/self.s)

    def calc_k1(self, s, g, h1):
        '''
        s: half width of central conductor
        g: gap width of CPW
        h1: height of whole stack
        returns: geometric parameter k1
        '''
        return mp.tanh(mp.pi*s/(2*h1))/mp.tanh(mp.pi*(s+g)/(2*h1))

    def calc_k2(self, s, g, h2):
        '''
        s: half width of central conductor
        g: gap width of CPW
        h2: height of top layer of stack
        returns: geometric parameter k2
        '''
        return mp.sinh(mp.pi*s/(2*h2))/mp.sinh(mp.pi*(s+g)/(2*h2))

h1 = SI_H1_MINUS_H2 + STO_H2

# just generate, like, an absolute metric ton of data
valid_s = []
valid_g = []
valid_z = []
valid_vph = []

s50 = []
g50 = []
# iterate over widths
for s2 in s_samples:
    z_g = []
    g_s = []
    # iterate over gaps
    for g in g_samples:
        # initialize CPW with a given s and g
        cpw = CPW(SI_EPS1, STO_EPS2, h1, STO_H2, s2/2*1E-6, g*1E-6)

        # extract & save computed impedance, phase velocity
        c = cpw.capacitance()
        l = cpw.magnetic_inductance() + NBN_LKSH/(s2*1E-6)

        z = impedance(c, l)
        vph = vp(c, l)
        
        if mp.isnormal(z):
            z = float(z)
            vph = float(vph)

            valid_s.append(s2)
            valid_g.append(g)
            g_s.append(g)
            valid_z.append(z)
            z_g.append(z)
            valid_vph.append(vph)

    # try to find the gap value resulting in 50 ohm for a given s
    try:
        g = np.interp(50, z_g, g_s)
        print(g)
        g50.append(g)
        s50.append(s2)
    except ValueError:
        print(str(s2) + ' has no reasonable 50 ohm gap value')

np.save(DATA_FOLDER+'/s.npy', valid_s)
np.save(DATA_FOLDER+'/g.npy', valid_g)
np.save(DATA_FOLDER+'/z.npy', valid_z)
np.save(DATA_FOLDER+'/vph.npy', valid_vph)
np.save(DATA_FOLDER+'/s50.npy', s50)
np.save(DATA_FOLDER+'/g50.npy', g50)


# relatively quickly find & plot the constant 50-ohm line for g vs s
'''
s50 = []
g50 = []
for s2 in np.logspace(-1, 3, 1000):
    print(s2)
    z_g = []
    valid_g = []
    for g in np.logspace(-3, 3, 1000):
        cpw = CPW(SI_EPS1, STO_EPS2, h1, STO_H2, s2/2*1E-6, g*1E-6, NBN_PEARL_LENGTH)
        c = cpw.capacitance()
        l = cpw.magnetic_inductance() + NBN_LKSH/(s2*1E-6) # cpw.kinetic_inductance()
        z = impedance(c, l)
        if mp.isnormal(z):
            z = float(z)
            if z > 50:
                break
            z_g.append(z)
            valid_g.append(g)
    try:
        g = np.interp(50, z_g, valid_g)
        print(g)
        g50.append(g)
        s50.append(s2)
    except ValueError:
        print(str(s2) + ' has no reasonable 50 ohm gap value')
            
plt.loglog(s50, g50)
plt.show()'''