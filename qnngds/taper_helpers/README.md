This folder contains helper functions for calculating tapers.

* analytical.py - script to analytically approximate impedance and 
phase velocity of a metallic CPW on a multilayer stack, saves as
npy archives
* erickson_taper.py - helper functions for calculating Erickson taper, 
used by long_meanders.make_taper()
* klopfenstein_taper.py - helper functions for calculating Klopfenstein
taper, used by long_meanders.make_taper()
* spherical_bessel_zeros.py - SciPy cookbook math required by Erickson taper
* taper_library.py - helper functions specific to taper geometries,
used by long_meanders.make_taper()