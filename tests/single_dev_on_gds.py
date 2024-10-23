"""This module is designed to generate a GDS file named "single_dev.gds". In
the simplest possible way, it writes a gds file containing the result (a Device
object) of the function to be tested.

Run this test from its parent directory (qnngds/tests).

This test is helpfull to check what is the hierarchy and the name in the
Device developped.

For eg., a phidl.geometry.union() will return an entirely flattened
Device named "union". Although very useful, union looses in some way the
hierachy information and it is important to determine whether or not
this information is to be kept. The same reflexion goes for
phidl.geometry.boolean().
"""

from phidl import Device
from phidl import quickplot as qp
from phidl import set_quickplot_options

set_quickplot_options(blocking=True)

import qnngds


def test_qnngds_device(DEV: Device):

    GDS = Device()
    GDS << DEV
    # GDS.write_gds("single_dev.gds", max_cellname_length=32000)

    qp(DEV)


if __name__ == "__main__":

    # Modify below the device to be tested, eg: DEV = qnngds.circuits.snspd_ntron()
    DEV = qnngds.cells.snspd_ntron()

    test_qnngds_device(DEV)
