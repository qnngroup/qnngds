import gdsfactory as gf
from gdsfactory.typings import Layer


class EbeamLayerMap(gf.LayerEnum):
    layout = gf.constant(gf.kcl.layout)
    EBEAM_FINE: Layer = (1, 0)
    EBEAM_COARSE: Layer = (2, 0)

    @classmethod
    def outline(cls, layer: Layer) -> int:
        if layer == cls.EBEAM_FINE:
            return 0.1
        elif layer == cls.EBEAM_COARSE:
            return 10
        return 0
