from phidl import quickplot as qp
from phidl import set_quickplot_options
import qnngds.devices as device
from phidl import geometry as pg

set_quickplot_options(blocking=True, show_subports=True)


chip_w = 5000
chip_margin = 50
N_dies = 5

pad_size = (150, 250)
outline_coarse = 10
outline_fine = 0.5
ebeam_overlap = 10

layers = {"annotation": 0, "mgb2_fine": 1, "mgb2_coarse": 2, "pad": 3}

CHIP = pg.Device()
CHIP << device.nanowire.spot()
CHIP << device.ntron.smooth()
CHIP << device.ntron.smooth_compassPorts()
CHIP << device.ntron.sharp()
CHIP << device.resistor.meander()
CHIP << device.resistor.meander_sc_contacts()
CHIP << device.snspd.vertical()

CHIP.write_gds("cleanup_device.gds", max_cellname_length=32000)
