import numpy as np
from scipy import special
from scipy.integrate import quad

'''
taper design based on "A Transmission Line Taper of 
Improved Design" by R. W. Klopfenstein
'''

def integrand(y, A):
    return special.i1(A*np.sqrt(1 - y**2))/(A*np.sqrt(1 - y**2)) 

def phi(z, A):
    integrated = quad(integrand, 0, z, args=(A))
    return integrated[0]

def klopfenstein_z(x_norm, RdB, Z1=1000, Z2=50):
    '''x_norm: x-value normalized to total length of taper (between 0-1)
    Z1: impedance at start of taper
    Z2: load impedance to match

    returns design value for Klopfenstein taper impedance at location x_norm
    '''
    if x_norm == 1:
        return Z2 
    else:
        T_load = np.log(Z2/Z1)*0.5
        T_ripple = 10**(RdB/20)
        A = np.arccosh(T_load/T_ripple)

        if x_norm <= 1/2:
            logZ = 0.5*np.log(Z1*Z2) - T_load/np.cosh(A)*(A**2*phi(np.abs(2*x_norm - 1), A))
        else:
            logZ = 0.5*np.log(Z1*Z2) + T_load/np.cosh(A)*(A**2*phi(np.abs(2*x_norm - 1), A))
        Z = np.exp(logZ)

        return Z

def klop_length(lambdafs, Zload, Z0, RdB):
    '''lambdafs: free-space design wavelength [any length units]
    Zload: load impedance
    Z0: impedance at start of taper
    RdB: operating band ripple [dB]

    returns: total required length of Klopfenstein taper
    '''
    T_load = np.log(Zload/Z0)*0.5
    T_ripple = 10**(RdB/20)
    A = np.arccosh(T_load/T_ripple)

    return A*lambdafs/(2*np.pi)