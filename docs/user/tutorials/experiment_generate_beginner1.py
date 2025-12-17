import qnngds as qg
from phidl import quickplot as qp
from functools import partial

ls = qg.LayerSet()
ls.add_layer(qg.Layer(name="PHOTO", gds_layer=1))

cross_sections = dict(
    photo=partial(qg.geometries.default_cross_section, layer="PHOTO"),
)

layer_transitions = qg.layer_auto_transitions(ls)

PDK = qg.Pdk(
    "single_layer_pdk",
    layers=ls,
    cross_sections=cross_sections,
    layer_transitions=layer_transitions,
)
PDK.activate()

dut = partial(qg.devices.ntron.sharp, layer="PHOTO")
pad_array = qg.pads.array(
    pad_specs=(qg.pads.stack(size=(200, 200), layers=("PHOTO",)),),
    columns=1,
    rows=3,
    pitch=250,
)
route_groups = (
    qg.experiment.RouteGroup(qg.get_cross_section("photo"), {"g": 2, "s": 1, "d": 3}),
)

c = qg.experiment.generate(
    dut=dut,
    pad_array=pad_array,
    label=None,
    route_groups=route_groups,
    dut_offset=(350, 250),
    pad_offset=(0, 0),
    label_offset=(0, 0),
    retries=1,
)

qp(c)

from ._save_qp import save_qp  # noqa: E402

save_qp(__file__, c, xlim=(320, 380), ylim=(240, 260))
