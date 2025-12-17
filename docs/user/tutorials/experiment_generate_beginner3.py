import qnngds as qg
from phidl import quickplot as qp
from functools import partial

ls = qg.LayerSet()
ls.add_layer(qg.Layer(name="EBEAM_FINE", gds_layer=1, outline=0.1))
ls.add_layer(qg.Layer(name="EBEAM_COARSE", gds_layer=2, outline=10))
ls.add_layer(qg.Layer(name="EBEAM_KEEPOUT", gds_layer=3, keepout=("EBEAM_FINE",)))
ls.add_layer(qg.Layer(name="PHOTO", gds_layer=10))

cross_sections = dict(
    ebeam=partial(qg.geometries.default_cross_section, layer="EBEAM_COARSE"),
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
    "dual_layer_postone_ebeam_pdk",
    layers=ls,
    cross_sections=cross_sections,
    layer_transitions=layer_transitions,
)
PDK.activate()

dut = partial(
    qg.devices.resistor.meander_sc_contacts,
    layer_res="PHOTO",
    layer_contacts=("EBEAM_FINE",),
    layer_keepout=("EBEAM_KEEPOUT",),
)
pad_array = qg.pads.array(
    pad_specs=(qg.pads.stack(size=(200, 200), layers=("EBEAM_COARSE",)),),
    columns=1,
    rows=2,
    pitch=250,
)
route_groups = (qg.experiment.RouteGroup(qg.get_cross_section("ebeam"), {1: 2, 2: 1}),)

c = qg.experiment.generate(
    dut=dut,
    pad_array=pad_array,
    label=None,
    route_groups=route_groups,
    dut_offset=(350, 125),
    pad_offset=(0, 0),
    label_offset=(0, 0),
    retries=1,
)

qp(c)

from ._save_qp import save_qp  # noqa: E402

save_qp(__file__, c, xlim=(300, 380), ylim=(100, 150))
