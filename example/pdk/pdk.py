from functools import partial

import gdsfactory as gf
from gdsfactory.get_factories import get_cells

from pdk import components
from pdk.cross_section import cross_sections
from pdk.layer_map import LAYERS

layer_transitions = {
    (LAYERS.EBEAM_FINE, LAYERS.EBEAM_COARSE): partial(
        components.ebeam_fine_to_coarse,
        layer1=LAYERS.EBEAM_FINE,
        layer2=LAYERS.EBEAM_COARSE,
    ),
    (LAYERS.EBEAM_COARSE, LAYERS.EBEAM_FINE): partial(
        components.ebeam_fine_to_coarse,
        layer2=LAYERS.EBEAM_FINE,
        layer1=LAYERS.EBEAM_COARSE,
    ),
    LAYERS.EBEAM_FINE: partial(
        components.hyper_taper,
        layer1=LAYERS.EBEAM_FINE,
        layer2=LAYERS.EBEAM_FINE,
    ),
    LAYERS.EBEAM_COARSE: partial(
        components.hyper_taper,
        layer1=LAYERS.EBEAM_COARSE,
        layer2=LAYERS.EBEAM_COARSE,
    ),
}

PDK = gf.Pdk(
    name="test_pdk",
    layers=LAYERS,
    cross_sections=cross_sections,
    layer_transitions=layer_transitions,
    cells=get_cells(components),
)
