from . import typing as typing
from .layout import (
    Port,  # noqa: F401
    Device,  # noqa: F401
    DeviceArray,  # noqa: F401
    Layer,  # noqa: F401
    LayerSet,  # noqa: F401
    CrossSection,  # noqa: F401
)
from . import geometries as geometries
from . import utilities as utilities
from . import test_structures as test_structures
from .pdk import (
    Pdk,  # noqa: F401
    get_active_pdk,  # noqa: F401
    get_layer,  # noqa: F401
    get_device,  # noqa: F401
    get_cross_section,  # noqa: F401
)
from . import devices as devices

# from . import sample as sample
# from . import pads as pads


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
