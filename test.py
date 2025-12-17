"""Basic test code"""

import phidl

import qnngds as qg

from functools import partial

phidl.set_quickplot_options(blocking=True)

ls = qg.LayerSet()
ls.add_layer(qg.Layer(name="EBEAM_FINE", gds_layer=1, gds_datatype=0, outline=0.1))
ls.add_layer(qg.Layer(name="EBEAM_COARSE", gds_layer=2, gds_datatype=0, outline=10))
ls.add_layer(qg.Layer(name="PHOTO1", gds_layer=10, gds_datatype=0, outline=0))
ls.add_layer(qg.Layer(name="PHOTO2", gds_layer=20, gds_datatype=0, outline=0))
ls.add_layer(qg.Layer(name="PHOTO3", gds_layer=30, gds_datatype=0, outline=0))
ls.add_layer(qg.Layer(name="PHOTO4", gds_layer=40, gds_datatype=0, outline=0))
ls.add_layer(
    qg.Layer(
        name="EBEAM_KEEPOUT",
        gds_layer=3,
        gds_datatype=0,
        keepout=["EBEAM_FINE", "EBEAM_COARSE"],
    )
)

cross_sections = dict(
    photo1=partial(qg.geometries.default_cross_section, layer="PHOTO1"),
    photo2=partial(qg.geometries.default_cross_section, layer="PHOTO2"),
    photo3=partial(qg.geometries.default_cross_section, layer="PHOTO3"),
    photo4=partial(qg.geometries.default_cross_section, layer="PHOTO4"),
    ebeam=partial(qg.geometries.default_cross_section, radius=40, layer="EBEAM_COARSE"),
)

layer_transitions = {
    ("EBEAM_FINE", "EBEAM_COARSE"): partial(
        qg.geometries.fine_to_coarse,
        layer1="EBEAM_FINE",
        layer2="EBEAM_COARSE",
    )
}
layer_transitions |= qg.layer_auto_transitions(ls)

PDK = qg.Pdk(
    "test_pdk",
    layers=ls,
    cross_sections=cross_sections,
    layer_transitions=layer_transitions,
)
PDK.activate()

c = qg.experiment.generate(
    dut=partial(qg.devices.ntron.sharp, layer="PHOTO1"),
    pad_array=qg.pads.array(
        pad_specs=(qg.pads.stack(size=(200, 200), layers=("PHOTO1",)),),
        columns=1,
        rows=3,
        pitch=250,
    ),
    label=None,
    route_groups=(
        qg.experiment.RouteGroup(
            qg.get_cross_section("photo1"), {"g": 2, "s": 1, "d": 3}
        ),
    ),
    dut_offset=(350, 250),
    pad_offset=(0, 0),
    label_offset=(0, 0),
    retries=1,
)

phidl.quickplot(c)


# sample = qg.sample.Sample(cell_size=10e3, sample=qg.sample.wafer100mm, edge_exclusion=500, allow_cell_span=True)
# sample.visualize_open_cells()

dev_list = [
    # qg.geometries.taper(),
    # qg.geometries.hyper_taper(),
    # qg.geometries.euler_taper(),
    # qg.geometries.angled_taper(),
    # qg.geometries.tee(),
    # qg.geometries.via(),
    # qg.geometries.optimal_hairpin(),
    # qg.geometries.fine_to_coarse(),
    # qg.geometries.fine_to_coarse(layer1="PHOTO1", layer2="PHOTO2"),
    # qg.test_structures.alignment_mark(["PHOTO1", "PHOTO2"]),
    # qg.test_structures.resolution_test(),
    # qg.test_structures.litho_checkerboard(),
    # qg.test_structures.vdp(),
    # qg.test_structures.rect_tlm(),
    # qg.test_structures.circ_tlm(),
    # qg.test_structures.via_chain(),
    # qg.test_structures.etch_test(),
    # qg.test_structures.cross_bridge_kelvin_resistor(),
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
    # qg.devices.snspd.basic(),
    # qg.devices.snspd.vertical(),
    # qg.devices.resonator.transmission_line(),
    # qg.devices.resonator.meandered(),
    # qg.devices.resonator.straight(),
    # qg.devices.resonator.pad(),
    # qg.devices.resonator.transmission_line_resonator(),
    # qg.pads.stack(),
    # qg.pads.array(),
    # qg.pads.vdp(),
    # qg.pads.quad_line(),
]
for dev in dev_list:
    phidl.quickplot(dev)
