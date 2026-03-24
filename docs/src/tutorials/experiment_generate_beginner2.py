# .. _experiment_generate_beginner2:
# Creation of positive-tone ebeam layouts with ``experiment.generate``
# ====================================================================
#
# Now, we will demonstrate how to generate a layout with ``experiment.generate`` for a positive-tone
# ebeam lithography process using two layers for different beam currents.
#
# Imports are the same as in :ref:`experiment_generate_beginner1`:
import qnngds as qg
import phidl.geometry as pg
from phidl import quickplot as qp
from functools import partial

# When setting up the PDK, we define two layers this time, as well as a new interlayer transition between
# them using ``geometries.fine_to_coarse``.
# Note the ``outline`` argument being passed to the ``Layer`` constructor.
ls = qg.LayerSet()
ls.add_layer(qg.Layer(name="EBEAM_FINE", gds_layer=1, outline=0.1))
ls.add_layer(qg.Layer(name="EBEAM_COARSE", gds_layer=2, outline=10))
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
    "single_layer_postone_ebeam_pdk",
    layers=ls,
    cross_sections=cross_sections,
    layer_transitions=layer_transitions,
)
PDK.activate()
# The rest of the code is almost the same as in :ref:`experiment_generate_beginner1`:
ntron = qg.devices.ntron.sharp(layer="EBEAM_FINE")
ext = partial(
    pg.optimal_step, end_width=1, symmetric=True, layer=qg.get_layer("EBEAM_FINE")
)
dut = qg.utilities.extend_ports(
    device=ntron, port_names=["g", "s", "d"], extension=ext, auto_width=True
)
pad_array = qg.pads.array(
    pad_specs=(qg.pads.stack(size=(200, 200), layers=("EBEAM_COARSE",)),),
    columns=1,
    rows=3,
    pitch=250,
)
route_groups = (
    qg.experiment.RouteGroup(qg.get_cross_section("ebeam"), {"g": 2, "s": 1, "d": 3}),
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
## SKIPSTART
from ._save_qp import save_qp  # noqa: E402

save_qp(__file__, c, xlim=(345, 355), ylim=(245, 255))
## SKIPSTOP
## IMAGE
# Zooming in on the nTron:
## IMAGE_ZOOM
## STOP
