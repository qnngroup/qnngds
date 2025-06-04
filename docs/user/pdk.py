"""Dummy PDK with some example layers"""

import gdsfactory as gf
from gdsfactory.typings import Layer


class ApiGenLayers(gf.LayerEnum):
    """Fine, coarse e-beam layer and two photolithography layers"""

    layout = gf.constant(gf.kcl.layout)

    EBEAM_FINE: Layer = (1, 0)
    EBEAM_COARSE: Layer = (2, 0)
    PHOTO1: Layer = (3, 0)
    PHOTO2: Layer = (4, 0)
