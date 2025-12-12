from phidl import set_quickplot_options
from phidl import quickplot as qp

import qnngds as qg

ls = qg.LayerSet()
ls.add_layer(qg.Layer(name="NTRON", gds_layer=1, gds_datatype=0, outline=0))
ls.add_layer(qg.Layer(name="VIA", gds_layer=10, gds_datatype=0, outline=0))
ls.add_layer(qg.Layer(name="ROUTING", gds_layer=20, gds_datatype=0, outline=0))
ls.add_layer(qg.Layer(name="EBEAM_FINE", gds_layer=30, gds_datatype=0, outline=0.1))
ls.add_layer(qg.Layer(name="EBEAM_COARSE", gds_layer=31, gds_datatype=0, outline=10))
PDK = qg.Pdk("test_pdk", layers=ls)
PDK.activate()

set_quickplot_options(blocking=True)

dev_list = [
    qg.geometries.taper(),
    qg.geometries.hyper_taper(),
    qg.geometries.euler_taper(),
    qg.geometries.angled_taper(),
    qg.geometries.tee(),
    qg.geometries.via(),
    qg.test_structures.alignment_mark([l for l in PDK.layers]),
    qg.test_structures.resolution_test(),
    qg.test_structures.litho_checkerboard(),
    qg.test_structures.vdp(),
    qg.test_structures.rect_tlm(),
    qg.test_structures.circ_tlm(),
    qg.test_structures.via_chain(),
    qg.test_structures.etch_test(),
]
for dev in dev_list:
    qp(dev)
