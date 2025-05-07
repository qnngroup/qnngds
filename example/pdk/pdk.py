from functools import partial

import gdsfactory as gf
from gdsfactory.get_factories import get_cells

from pdk import components
from pdk.cross_section import cross_sections
from pdk.layer_map import EbeamLayerMap

layer_transitions = {
    (EbeamLayerMap.EBEAM_FINE, EbeamLayerMap.EBEAM_COARSE): partial(
        components.ebeam_fine_to_coarse,
        layer1=EbeamLayerMap.EBEAM_FINE,
        layer2=EbeamLayerMap.EBEAM_COARSE,
    ),
    (EbeamLayerMap.EBEAM_COARSE, EbeamLayerMap.EBEAM_FINE): partial(
        components.ebeam_fine_to_coarse,
        layer2=EbeamLayerMap.EBEAM_FINE,
        layer1=EbeamLayerMap.EBEAM_COARSE,
    ),
    EbeamLayerMap.EBEAM_FINE: partial(
        components.hyper_taper,
        layer1=EbeamLayerMap.EBEAM_FINE,
        layer2=EbeamLayerMap.EBEAM_FINE,
    ),
    EbeamLayerMap.EBEAM_COARSE: partial(
        components.hyper_taper,
        layer1=EbeamLayerMap.EBEAM_COARSE,
        layer2=EbeamLayerMap.EBEAM_COARSE,
    ),
}

PDK = gf.Pdk(
    name="test_pdk",
    layers=EbeamLayerMap,
    cross_sections=cross_sections,
    layer_transitions=layer_transitions,
    cells=get_cells(components),
)
