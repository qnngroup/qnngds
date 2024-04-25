from phidl import quickplot as qp
from phidl import set_quickplot_options

set_quickplot_options(blocking=True)

import qnngds.cells as cell
import qnngds.devices as device
import qnngds.design as design
import qnngds.utilities as utility


# qp(cell.snspd())
# # qp(design.Design().snspd_cell())
# qp(utility.die_cell(isolation = 20))

print(utility.calculate_dev_max_size())
