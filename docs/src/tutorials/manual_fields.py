## ruff: noqa: E402
# .. _manual_fields:
# Manual field placement
# ======================================
#
# In this tutorial, we will cover manual
# field placement. This is important when writing large
# devices, since fracturing in beamer will tend to put
# field boundaries in the middle of large devices.

# First, we can set up our PDK:
import qnngds as qg
from qnngds import Device

import phidl.geometry as pg
from phidl import quickplot as qp

from functools import partial

ls = qg.LayerSet()
ls.add_layer(qg.Layer(name="ebeam", gds_layer=1, color="black"))
ls.add_layer(qg.Layer(name="field", gds_layer=1000, color="yellow", alpha=0.6))

cross_sections = {}
layer_transitions = qg.layer_auto_transitions(ls)

PDK = qg.Pdk(
    "ebeam_with_fields",
    layers=ls,
    cross_sections=cross_sections,
    layer_transitions=layer_transitions,
)
PDK.activate()
# Now lets create a large device. We'll make it a bit smaller than the field size.
D = Device("ebeam_field_example")
meander = qg.devices.snspd.basic(
    wire_width=0.2,
    wire_pitch=0.6,
    size=(990, 990),
    layer="ebeam",
    terminals_same_side=True,
)
taper = partial(
    pg.optimal_step,
    end_width=1,
    anticrowding_factor=4,
    num_pts=100,
    symmetric=False,
    layer=qg.get_layer("ebeam"),
)
snspd = D << qg.utilities.extend_ports(
    device=qg.utilities.extend_ports(
        device=meander,
        port_names=(1,),
        extension=taper,
        auto_width=True,
    ),
    port_names=(2,),
    extension=taper,
    ext_mirror=((0, 0), (0, 1)),
    auto_width=True,
)
# Now we can place a square millimeter field around the SNSPD
field = D << pg.rectangle(size=(1e3, 1e3), layer=qg.get_layer("field"))
field.move((snspd.xmax + 0.3 - field.xmax, snspd.y - field.y))

# Lets place a bunch of them on a single 10x10 chip.
sample = qg.sample.Sample(
    cell_size=2e3, sample=qg.sample.piece10mm, edge_exclusion=1e3, allow_cell_span=False
)
sample.place_multiple_on_sample(
    devices=[D] * 16,
    cell_coordinate_bbox=((0, 0), (8, 8)),
)
qp(sample.devices)
## SKIPSTART
from ._save_qp import save_qp  # noqa: E402

save_qp(
    __file__, sample.devices, plot_name="snspds", xlim=(-1600, -400), ylim=(400, 1600)
)
## SKIPSTOP
## IMAGE_snspds
## IMAGE_snspds_ZOOM

# We can export the fields to a file named fields.txt:
sample.export_manual_fields(field_layer="field", save_path="fields.txt")
## TEXT_fields

# We can also visualize the writing fields:
fields = sample.visualize_fields(field_layer="field")
qp(fields)
## SKIPSTART
save_qp(__file__, sample.devices, plot_name="fields")
## SKIPSTOP
## IMAGE_fields
