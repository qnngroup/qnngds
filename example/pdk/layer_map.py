import gdsfactory as gf
from gdsfactory.typings import Layer
from qnngds.utilities import layers_equal


class EbeamLayerMap(gf.LayerEnum):
    layout = gf.constant(gf.kcl.layout)
    EBEAM_FINE: Layer = (1, 0)
    EBEAM_COARSE: Layer = (2, 0)
    DUMMY: Layer = (255, 0)

    @classmethod
    def outline(cls, layer: Layer) -> int:
        if layers_equal(layer, cls.EBEAM_FINE):
            return 0.1
        elif layers_equal(layer, cls.EBEAM_COARSE):
            return 10
        return 0


LAYERS = EbeamLayerMap
