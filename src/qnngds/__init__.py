from .decorator import device as device
from . import typing as typing
from .layout import (
    Port as Port,
    Device as Device,
    DeviceArray as DeviceArray,
    Layer as Layer,
    LayerSet as LayerSet,
    CrossSection as CrossSection,
    to_qg_device as to_qg_device,
)
from . import geometries as geometries
from . import utilities as utilities
from . import test_structures as test_structures
from .pdk import (
    Pdk as Pdk,
    get_active_pdk as get_active_pdk,
    get_layer as get_layer,
    get_device as get_device,
    get_cross_section as get_cross_section,
    layer_auto_transitions as layer_auto_transitions,
)
from . import devices as devices
from . import sample as sample
from . import pads as pads
from . import experiment as experiment


def help():
    """Provides links to documentation."""

    print(
        "Need help? Check qnngds documentation: https://qnngds.readthedocs.io/en/latest/ \n"
    )
    print(" - Tutorials: https://qnngds.readthedocs.io/en/latest/tutorials.html \n")
    print(" - API: https://qnngds.readthedocs.io/en/latest/api.html \n\n")

    print(
        "You are a contributor? Check this documentation: https://qnngds.readthedocs.io/projects/qnngds-dev/en/latest/"
    )
