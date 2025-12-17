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

import matplotlib.pyplot as plt  # noqa: E402
import os  # noqa: E402
from phidl import set_quickplot_options  # noqa: E402

set_quickplot_options(show_subports=False)
qp(c)
dirname = os.path.dirname(__file__)
basename = os.path.basename(__file__).split(".")[0]
save_path = os.path.join(dirname, ".".join((basename, "png")))
plt.savefig(save_path)
# zoom
plt.xlim((320, 380))
plt.ylim((240, 260))
save_path = os.path.join(dirname, ".".join((basename + "_zoom", "png")))
plt.savefig(save_path)
plt.close()
