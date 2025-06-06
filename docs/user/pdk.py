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

    @classmethod
    def outline(cls, layer: Layer) -> int:
        """Used to define desired outline for positive tone layers.

        To make a layer positive tone, return a non-zero value for it.

        E.g. if you want EBEAM_FINE to be positive tone with an outline
        of 100 nm, then you should define this function to return 0.1
        when passed a value of EBEAM_FINE (either as an enum type, a string
        or tuple that is equivalent to the EBEAM_FINE GDS layer).
        """
        if gf.get_layer(layer) == cls.EBEAM_FINE:
            ## uncomment the below line for positive tone
            return 0.1
        elif gf.get_layer(layer) == cls.EBEAM_COARSE:
            ## uncomment the below line for positive tone
            return 10
        # by default, assume a layer is negative tone
        return 0
