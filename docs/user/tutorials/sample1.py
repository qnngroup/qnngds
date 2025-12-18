# .. _sample1:
# Basic sample generation
# =======================
#
# Let's generate a 10 x 10 mm sample with an array of nTrons with different dimensions.
# First, imports:
import qnngds as qg
from phidl import quickplot as qp
from functools import partial
import phidl.geometry as pg
import numpy as np

# We'll just use a single layer, so we can define the PDK as so:
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
# Now we'll set up an array of devices that we want to place on the sample:
ntrons = []
channel_w = 2.0
pad_array = qg.pads.array(
    pad_specs=(qg.pads.stack(size=(200, 100), layers=("PHOTO",)),),
    columns=1,
    rows=3,
    pitch=300,
)
route_groups = (
    qg.experiment.RouteGroup(qg.get_cross_section("photo"), {"g": 2, "s": 1, "d": 3}),
)
for choke_w in np.linspace(0.2, 1.0, 9):
    label_text = f"wg/wc {round(choke_w, 2)}/{round(channel_w, 2)}"
    label = pg.text(
        label_text, size=25, layer=qg.get_layer("PHOTO").tuple, justify="center"
    ).rotate(-90)
    dut = partial(
        qg.devices.ntron.sharp,
        choke_w=choke_w,
        gate_w=2 * channel_w,
        channel_w=channel_w,
        drain_w=2 * channel_w,
        source_w=2 * channel_w,
        layer="PHOTO",
    )
    ntron = qg.experiment.generate(
        dut=dut,
        pad_array=pad_array,
        label=label,
        route_groups=route_groups,
        dut_offset=(100, 0),
        pad_offset=(-pad_array.xsize, -300),
        label_offset=(150, 0),
        retries=1,
    )
    ntron.rotate(90)
    ntrons.append(ntron)
# We can set up the sample and place the devices on it:
sample = qg.sample.Sample(
    cell_size=1e3, sample=qg.sample.piece10mm, edge_exclusion=500, allow_cell_span=False
)
sample.place_multiple_on_sample(
    devices=ntrons * 9,
    cell_coordinate_bbox=((0, 0), (8, 8)),
)
qp(sample.devices)
## IMAGE
## IMAGE_ZOOM
## STOP
from ._save_qp import save_qp  # noqa: E402

save_qp(__file__, sample.devices, xlim=(-400, 400), ylim=(-300, 300))
