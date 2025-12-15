"""Custom types for Layers and Devices"""

import phidl

from functools import partial

from typing import TypeAlias
from collections.abc import Callable, Sequence

LayerSpec: TypeAlias = str | int | tuple[int, int]
LayerSpecs: TypeAlias = Sequence[LayerSpec]
DeviceFactory: TypeAlias = Callable[..., phidl.Device]
DeviceSpec: TypeAlias = str | DeviceFactory | phidl.Device | partial[DeviceFactory]
DeviceSpecs: TypeAlias = Sequence[DeviceSpec]
CrossSectionFactory: TypeAlias = Callable[..., phidl.CrossSection]
CrossSectionSpec: TypeAlias = (
    str | CrossSectionFactory | phidl.CrossSection | partial[CrossSectionFactory]
)

__all__ = [
    "LayerSpec",
    "LayerSpecs",
    "DeviceFactory",
    "DeviceSpec",
    "DeviceSpecs",
    "CrossSectionFactory",
    "CrossSectionSpec",
]
