from phidl import set_quickplot_options
from phidl import quickplot as qp

import qnngds as qg

ls = qg.LayerSet()
ls.add_layer(qg.Layer(name="PHOTO1", gds_layer=10, gds_datatype=0, outline=0))
ls.add_layer(qg.Layer(name="PHOTO2", gds_layer=20, gds_datatype=0, outline=0))
ls.add_layer(qg.Layer(name="PHOTO3", gds_layer=30, gds_datatype=0, outline=0))
ls.add_layer(qg.Layer(name="PHOTO4", gds_layer=40, gds_datatype=0, outline=0))
ls.add_layer(qg.Layer(name="EBEAM_FINE", gds_layer=1, gds_datatype=0, outline=0.1))
ls.add_layer(qg.Layer(name="EBEAM_COARSE", gds_layer=2, gds_datatype=0, outline=10))
ls.add_layer(
    qg.Layer(
        name="EBEAM_KEEPOUT",
        gds_layer=3,
        gds_datatype=0,
        keepout=["EBEAM_FINE", "EBEAM_COARSE"],
    )
)
PDK = qg.Pdk("test_pdk", layers=ls)
PDK.activate()

set_quickplot_options(blocking=True)

dev_list = [
    # qg.geometries.taper(),
    # qg.geometries.hyper_taper(),
    # qg.geometries.euler_taper(),
    # qg.geometries.angled_taper(),
    # qg.geometries.tee(),
    # qg.geometries.via(),
    # qg.geometries.optimal_hairpin(),
    # qg.test_structures.alignment_mark([l for l in PDK.layers]),
    # qg.test_structures.resolution_test(),
    # qg.test_structures.litho_checkerboard(),
    # qg.test_structures.vdp(),
    # qg.test_structures.rect_tlm(),
    # qg.test_structures.circ_tlm(),
    # qg.test_structures.via_chain(),
    # qg.test_structures.etch_test(),
    # qg.devices.diode.basic(),
    # qg.devices.diode.gated(),
    # qg.devices.nanowire.variable_length(),
    # qg.devices.nanowire.sharp(),
    # qg.devices.htron.planar(),
    # qg.devices.htron.heater(),
    # qg.devices.htron.multilayer(),
    # qg.devices.ntron.smooth(),
    # qg.devices.ntron.sharp(),
    # qg.devices.ntron.slotted(),
    # qg.devices.resistor.meander(),
    # qg.devices.resistor.meander_sc_contacts(),
    qg.devices.snspd.basic(),
    qg.devices.snspd.vertical(),
]
for dev in dev_list:
    qp(dev)
