from phidl import quickplot as qp
from phidl import set_quickplot_options
set_quickplot_options(blocking=True)

import qnngds.cells as cell
import qnngds.devices as device
import qnngds.design as design


qp(cell.snspd())
# qp(design.Design().snspd_cell())