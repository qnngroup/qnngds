# .. _custom_circuit:
# Tutorial on creating a custom circuit
# =====================================
#
# In this tutorial, we'll demonstrate how to use ``partial``
# to construct a circuit from multiple subdevices.
# First, imports:
import qnngds as qg
from qnngds import Device
from qnngds.typing import DeviceSpec
import phidl.geometry as pg
from phidl import quickplot as qp
from functools import partial


# Now, we can define a function which takes as an argument either
# a device, or a function which returns a device when called.
# Note it is also possible to pass a string that matches the name
# of a device registered with the currently active PDK. However,
# since we haven't specified a PDK or registered any devices with it,
# we will only be able to use ``Device`` instances or ``DeviceFactory``s
# (callable functions that produce a ``Device``).
def ntron_meander(
    ntron_spec: DeviceSpec,
    meander_spec: DeviceSpec,
    output_tee_spec: DeviceSpec,
) -> Device:
    """nTron with meander on drain

    Args:
        ntron_spec (DeviceSpec): device or callable function that returns a device for the nTron
        meander_spec (DeviceSpec): specification for drain meander/inductor
        output_tee_spec (DeviceSpec): specification for tee that connects output, nTron drain, and inductor

    Returns:
        (Device): nTron with connected meander and tee
    """
    D = Device("ntron_meander")

    ntron = D << qg.get_device(ntron_spec)
    meander = D << qg.get_device(meander_spec)
    tee = D << qg.get_device(tee_spec)

    tee.connect(port=tee.ports[2], destination=ntron.ports["d"])
    meander.connect(port=meander.ports[1], destination=tee.ports[1])

    D.add_port(name="g", port=ntron.ports["g"])
    D.add_port(name="s", port=ntron.ports["s"])
    D.add_port(name="d", port=meander.ports[2])
    D.add_port(name="o", port=tee.ports[3])

    return D


# Now we can generate some devices. Here we use
# a few different examples to illustrate how flexible
# the ``DeviceSpec`` type is. For the nTron and meander,
# we will use the default arguments. Note that for ``meander_spec``
# we actually pass an instance of a ``Device`` whereas for both
# ``tee_spec`` and ``ntron_spec``, we pass a ``DeviceFactory``.
ntron_spec = qg.devices.ntron.smooth
meander_spec = qg.devices.snspd.basic()
tee_spec = partial(pg.tee, size=(2, 0.3), stub_size=(0.3, 5), layer=(1, 0))

# Now we generate and plot the device.
D = ntron_meander(ntron_spec, meander_spec, tee_spec)
qp(D)
## IMAGE
## IMAGE_ZOOM
## STOP
from ._save_qp import save_qp  # noqa: E402

save_qp(__file__, D, xlim=(-400, 400), ylim=(-300, 300))
