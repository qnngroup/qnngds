"""Custom types for Layers and Devices"""

import phidl

from functools import partial

from typing import TypeAlias
from collections.abc import Callable, Sequence

LayerSpec: TypeAlias = str | int | tuple[int, int]
LayerSpecs: TypeAlias = Sequence[LayerSpec]
DeviceFactory: TypeAlias = Callable[..., phidl.Device]
DeviceSpec: TypeAlias = str | DeviceFactory | partial[phidl.Device]
DeviceSpecs: TypeAlias = Sequence[DeviceSpec]

__all__ = [
    "LayerSpec",
    "LayerSpecs",
    "DeviceFactory",
    "DeviceSpec",
    "DeviceSpecs",
]
