"""Pdk functions for layer and device management, mostly taken from gdsfactory"""

from __future__ import annotations

from qnngds import Layer, LayerSet
from phidl import CrossSection
import phidl
from qnngds.typing import LayerSpec, LayerSpecs, DeviceSpec, DeviceSpecs

_ACTIVE_PDK: Pdk | None = None


class Pdk:
    """PDK class, stores layer information, cross sections, layer transistions, and devices"""

    def __init__(
        self,
        name: str,
        layers: LayerSet,
        cross_sections: dict[str, CrossSection] = {},
        layer_transitions: dict[LayerSpec | LayerSpecs, DeviceSpec] = {},
        devices: DeviceSpecs = [],
    ):
        """Constructor

        Parameters
            name (str): name of PDK
            layers (LayerSet): LayerSet to use for PDK
            cross_sections (dict[str, CrossSection]): map of named cross sections to their instances
            layer_transitions (dict[LayerSpec, DeviceSpec]): map of LayerSpec (or pair of LayerSpecs)
                to a DeviceSpec which will transition between layers
            devices (DeviceSpecs): devices to register with PDK
        """
        self.name = name
        self.layers = layers
        self.cross_sections = cross_sections
        self.layer_transitions = layer_transitions
        self.devices = devices

    def activate(self):
        """Enable the PDK and allow it to be accessed globally"""
        _set_active_pdk(self)

    def get_layer(self, layer: LayerSpec) -> Layer:
        """Get a specific layer within the PDK

        Parameters
            layer (LayerSpec): string, int, or tuple that identifies the desired layer

        Returns
            Layer: instance of layer matching the queried LayerSpec
        """
        if isinstance(layer, str):
            if layer not in self.layers:
                raise ValueError(
                    f"[qnngds] Pdk.get_layer(): could not find layer {layer} in Pdk {self.name}"
                )
            return self.layers[layer]
        if isinstance(layer, int):
            layer = (layer, 0)
        if isinstance(layer, tuple):
            for layer in self.layers:
                layer = self.layers[layer]
                if layer == (layer.gds_layer, layer.gds_datatype):
                    return layer
        raise ValueError(
            f"[qnngds] Pdk.get_layer(): could not find layer {layer} in Pdk {self.name}"
        )

    def get_device(self, spec: DeviceSpec) -> phidl.Device:
        """Get a specific layer within the PDK

        Parameters
            device (DeviceSpec): device instance, name (string), or callable function that identifies desired device

        Returns
            Device: instance of device matching the queried DeviceSpec
        """
        if callable(spec):
            d = spec()
            if not isinstance(d, phidl.Device):
                # allow both phidl and qnngds Devices
                # (qnngds device has layer-assigned ports)
                raise ValueError(
                    "[qnngds] get_device() error: Callable argument `spec` did not return a phidl.Device or Device."
                )
            return d
        if isinstance(spec, phidl.Device):
            return spec
        if isinstance(spec, str):
            if spec not in self.devices:
                approx_match = [d for d in self.devices if spec in d]
                raise ValueError(
                    f"{spec} from PDK {self.name} not in self.devices: did you mean {approx_match}"
                )
            return self.devices[spec]
        raise ValueError(
            "[qnngds] get_device() error: Argument `spec` is invalid, must be a device, function that returns a device, or string name for device registered with active PDK"
        )


def get_active_pdk():
    """Get the globally-activated PDK"""
    global _ACTIVE_PDK

    if _ACTIVE_PDK is None:
        return get_generic_pdk()

    return _ACTIVE_PDK


def get_generic_pdk():
    """Get a generic PDK"""
    layers = LayerSet()
    layers.add_layer(Layer(name="default", gds_layer=1, gds_datatype=0))
    return Pdk(
        name="generic",
        layers=layers,
        cross_sections={},
        layer_transitions={},
        devices=[],
    )


def _set_active_pdk(pdk: Pdk):
    """Helper method for PDK activation"""
    global _ACTIVE_PDK
    _ACTIVE_PDK = pdk


def get_layer(layer: LayerSpec):
    """Get a specific layer within the globally-activated PDK

    Parameters
        layer (LayerSpec): string, int, or tuple that identifies the desired layer

    Returns
        Layer: instance of layer matching the queried LayerSpec
    """
    return get_active_pdk().get_layer(layer)


def get_device(device: DeviceSpec):
    """Get a specific layer within the globally-activated PDK

    Parameters
        device (DeviceSpec): device instance, name (string), or callable function that identifies desired device

    Returns
        Device: instance of device matching the queried DeviceSpec
    """
    return get_active_pdk().get_device(device)
