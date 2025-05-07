import gdsfactory as gf
from gdsfactory.typings import Layer


class EbeamLayerMap(gf.LayerEnum):
    layout = gf.constant(gf.kcl.layout)
    EBEAM_FINE: Layer = (1, 0)
    EBEAM_COARSE: Layer = (2, 0)
