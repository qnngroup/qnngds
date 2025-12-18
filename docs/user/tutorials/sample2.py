# .. _sample2:
# Nested sample generation
# =======================
#
# The following example will illustrate filling a wafer with
# multiple 10 x 10 mm pieces, as well as addition of
# dicing marks and labels for the 10 x 10s.
#
# For the purpose of this tutorial, the 10 x 10 pieces will be empty.
#
# First, imports
import qnngds as qg
from phidl import quickplot as qp
import phidl.geometry as pg

# Now, basic single layer PDK setup. This is only really necessary to
# get the nice layername to tuple translation, since we're not doing
# any routing here.
ls = qg.LayerSet()
ls.add_layer(qg.Layer(name="PHOTO", gds_layer=1))
PDK = qg.Pdk("single_layer_pdk", layers=ls)
PDK.activate()
# Next, we'll define the 10 x 10 piece and place a dummy rectangle on it.
# In practice, one would fill this up with experiments generated
# from devices and circuits.
piece = qg.sample.Sample(cell_size=1e3, sample=qg.sample.piece10mm, edge_exclusion=500)
piece.place_on_sample(
    device=pg.rectangle(size=(1, 1), layer=qg.get_layer("PHOTO")),
    cell_coordinate_bbox=(4, 4),
)
# Now, we generate the wafer sample and place a bunch of identical copies
# of the 10 x 10. Again, in practice, one would have several different 10 x 10s.
wafer = qg.sample.Sample(
    cell_size=10e3,
    sample=qg.sample.wafer100mm,
    edge_exclusion=10e3,
    allow_cell_span=False,
)
wafer.place_multiple_on_sample(
    devices=[piece.devices] * wafer.num_open_cells(),
    cell_coordinate_bbox=((0, 0), (10, 10)),
)
# Now we can write corners for all the occupied cells on the wafer as well as text
# labels so we can keep track of which piece is which after dicing.
wafer.write_cell_corners(width=100, layer="PHOTO")
wafer.write_cell_labels(size=400, layer="PHOTO", inset_dist=200, location=2)
# Finally, we can write alignment marks and plot the device.
wafer.write_alignment_marks(
    marker_spec=pg.cross(length=100, width=3, layer=qg.get_layer("PHOTO")),
    location=(20e3, 30e3),
)
qp(wafer.devices)
## IMAGE
## IMAGE_ZOOM
## STOP
from ._save_qp import save_qp  # noqa: E402

save_qp(__file__, wafer.devices, xlim=(-7.5e3, 7.5e3), ylim=(-7.5e3, 7.5e3))
