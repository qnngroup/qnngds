from pdk import PDK
from pdk.components import pad_tri
from functools import partial

import qnngds as qg

PDK.activate()

smooth_ntron = partial(
    qg.devices.ntron.smooth,
    choke_w=0.01,
    gate_w=1,
    channel_w=19,
    source_w=19,
    drain_w=19,
    # channel_w=15,
    # source_w=15.1,
    # drain_w=15.1,
    choke_shift=-0.3,
    layer="EBEAM_FINE",
)

slotted_ntron = qg.devices.ntron.slotted(
    base_spec=smooth_ntron,
    slot_width=1,
    slot_length=40.0,
    slot_pitch=2,
    n_slot=9,
    # base_spec=smooth_ntron, slot_width=5, slot_length=110.0, slot_pitch=20, n_slot=1
)

# slotted_ntron.show()


pad_array = partial(pad_tri, size=(200, 200), yspace=200, layer="EBEAM_COARSE")


c = qg.utilities.generate_experiment(
    dut=slotted_ntron,
    pad_array=pad_array,
    port_groupings=(("g", "s", "d"),),
    route_cross_section=(PDK.get_cross_section("ebeam"),),
    route_tapers=None,
    dut_offset=(0, 0),
    pad_offset=(0, 0),
    retries=1,
)

# c.show()

b = qg.geometries.resolution_test(outline=1)
b.show()
