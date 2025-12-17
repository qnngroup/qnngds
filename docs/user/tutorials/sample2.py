import qnngds as qg
from phidl import quickplot as qp
import phidl.geometry as pg

ls = qg.LayerSet()
ls.add_layer(qg.Layer(name="PHOTO", gds_layer=1))

PDK = qg.Pdk(
    "single_layer_pdk",
    layers=ls,
)
PDK.activate()

piece = qg.sample.Sample(cell_size=1e3, sample=qg.sample.piece10mm, edge_exclusion=500)

piece.place_on_sample(
    device=pg.rectangle(size=(1, 1), layer=qg.get_layer("PHOTO")),
    cell_coordinate_bbox=(4, 4),
)

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

wafer.write_cell_corners(width=100, layer="PHOTO")
wafer.write_cell_labels(size=400, layer="PHOTO", inset_dist=200, location=2)

wafer.write_alignment_marks(
    marker_spec=pg.cross(length=100, width=3, layer=qg.get_layer("PHOTO")),
    location=(20e3, 30e3),
)

qp(wafer.devices)

from ._save_qp import save_qp  # noqa: E402

save_qp(__file__, wafer.devices, xlim=(-7.5e3, 7.5e3), ylim=(-7.5e3, 7.5e3))
