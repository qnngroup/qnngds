import numpy as np
from scipy.special import factorial
from scipy.integrate import quad
from scipy import constants

from qnngds.qnngds.taper_helpers.spherical_bessel_zeros import Jn_zeros

'''
taper design based on "Variational theory of the tapered impedance
transformer" by R. Erickson
'''

# Erickson polynomial helper functions
def I_integrand(u, N):
    ''' integrated component of regularized incomplete beta 
    function to be numerically solved with scipy.quad; N is 
    order of the Erickson taper polynomial
    '''
    return (u - u**2)**N

def I(z, N):
    '''regularized incomplete beta function used in the 
    Erickson taper polynomial
    '''
    integrated = quad(I_integrand, 0, z, args=(N))
    return factorial((2*N + 1))/factorial(N)**2*integrated[0]

# compute Erickson polynomial
def erickson_polynomial_z(x_norm, N, Z1=1000, Z2=50):
    '''x_norm: x-value normalized to total length of taper (between 0-1)
    N: order of Erickson polynomial (typically between 2-10, increasing
       N increases length but decreases reflections)
    Z1: impedance at start of taper
    Z2: load impedance to match

    the Erickson polynomial taper minimizes reflections, but is longer
    than the Klopfenstein

    returns design value for taper impedance at location x_norm
    '''
    return Z2*np.exp(np.log(Z1/Z2)*I(1-x_norm, N))

def length(lambdafs, epsilon2, N):
    '''lambdafs: free-space design wavelength [any length units]
    epsilon2: permittivity at load
    N: order of Erickson polynomial

    returns: total required length of Erickson taper 
             at design wavelength and order N in same
             units as lambdafs
    '''
    # get the zeros of Nth order spherical bessel function
    zn = Jn_zeros(N, 1)[N][0]
    return 2*zn*lambdafs/(np.pi*constants.c*np.sqrt(constants.mu_0*epsilon2))