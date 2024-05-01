from phidl import Device
from phidl import quickplot as qp
from phidl import set_quickplot_options

set_quickplot_options(blocking=True)

import qnngds

DEV = qnngds.cells.ntron()

GDS = Device()
GDS << DEV
GDS.write_gds("single_dev.gds", max_cellname_length=32000)

qp(DEV)
