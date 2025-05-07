from pdk import PDK
from pdk.components import pad_tri
from functools import partial

import gdsfactory as gf
import qnngds as qg

PDK.activate()

smooth_ntron = partial(
    qg.devices.ntron.smooth,
    choke_w=0.02,
    gate_w=1,
    channel_w=19,
    source_w=19,
    drain_w=19,
    choke_shift=-0.3,
    layer="EBEAM_FINE",
)

slotted_ntron = qg.devices.ntron.slotted(
    base_spec=smooth_ntron,
    slot_width=1,
    slot_length=40.0,
    slot_pitch=2,
    n_slot=9,
)

pad_array = partial(pad_tri, size=(200, 200), yspace=200, layer="EBEAM_COARSE")

c = qg.utilities.generate_experiment(
    dut=slotted_ntron,
    pad_array=pad_array,
    label=gf.components.texts.text(
        "nTron\nwg/wc/Nch\n0.01/1/10", size=25, layer="EBEAM_COARSE", justify="right"
    ),
    port_groupings=(("g", "s", "d"),),
    route_cross_section=(PDK.get_cross_section("ebeam"),),
    route_tapers=None,
    dut_offset=(0, 0),
    pad_offset=(0, 0),
    label_offset=(-120, -200),
    retries=1,
)

c.show()
