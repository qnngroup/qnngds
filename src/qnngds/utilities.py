"""Utilities for modifying/combining devices into more complex devices or constructing experiments."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

from collections.abc import Sequence

from functools import partial

import numpy as np

from qnngds.typing import LayerSpec, LayerSpecs, DeviceSpec, CrossSectionSpec
from qnngds import Device, LayerSet, Port

import qnngds as qg
import phidl.geometry as pg


def extend_ports(
    device: Device,
    port_names: Sequence[int | str],
    extension: DeviceSpec,
    auto_width: bool = False,
    new_ports: bool = True,
    ext_swap_ports: bool = False,
    ext_mirror: tuple[tuple[float, float], tuple[float, float]] | None = None,
) -> Device:
    """Adds the DeviceSpec extension to the named ports of Device device

    Parameters:
        device (Device): device to add extensions to
        port_names (Sequence[int | str]): names of ports on device which should be extended
        extension (DeviceSpec): specification for extension
        auto_width (bool): if True, uses the kwarg `start_width` when instantiating the `extension`
            `DeviceSpec` to generate the tapers. Determines the `start_width` automatically from
            `device`.
        new_ports (bool): if True, create new ports, using port `2` from `Device` specified by `extension`.
            Also passes any non-extended ports through to the new device that is returned.
        ext_swap_ports (bool): if True, connects port `2` of the extension to the device instead of port `1`.
        ext_mirror (tuple[tuple[float, float], tuple[float,float]] | None): if not None, mirror the extension
            along the vector ext_mirror.

    Returns:
        (Device): the original device with ports extended
    """
    dev_extended = Device()
    dev_i = dev_extended << device

    ext_ports = [1, 2]
    if ext_swap_ports:
        ext_ports.reverse()
    if not new_ports:
        ext_ports.pop()

    def check_ext_ports(ext: Device):
        """Check extension ports for keys 1 and optionally 2"""
        for p in ext_ports:
            if p not in ext.ports:
                raise ValueError(
                    f"port '{p}' not found in extension.ports: {ext.ports.keys()}"
                )

    if not auto_width:
        # all widths are the same
        ext = qg.get_device(extension)
        check_ext_ports(ext)
    for port_name in port_names:
        if auto_width:
            # determine width from dev
            ext = qg.get_device(
                partial(extension, start_width=dev_i.ports[port_name].width)
            )
            check_ext_ports(ext)
        ext_i = dev_extended << ext
        if ext_mirror is not None:
            ext_i.mirror(ext_mirror[0], ext_mirror[1])
        ext_i.connect(
            port=ext_i.ports[ext_ports[0]], destination=dev_i.ports[port_name]
        )
        if new_ports and (ext_ports[1] in ext_i.ports):
            dev_extended.add_port(
                port=ext_i.ports[ext_ports[1]],
                name=port_name,
                layer=dev_i.ports[port_name].layer,
            )
    if new_ports:
        for _, port in dev_i.ports.items():
            if port.name in port_names:
                continue
            dev_extended.add_port(
                port=port,
                name=port.name,
                layer=port.layer,
            )
    dev_extended.name = "ext_port_" + device.name
    return dev_extended


def create_layered_ports(device: Device, layer: LayerSpec):
    """Regenerates new ports for device, assigning them all to a layer

    Parameters:
        device (Device): device to modify
        layer (LayerSpec): GDS layer specification
    """
    for name, port in device.ports.items():
        device.ports[name] = qg.Port(
            name=name,
            midpoint=port.midpoint,
            width=port.width,
            orientation=port.orientation,
            layer=layer,
            parent=port.parent,
        )


def hyper_taper_fn(t: float, start_width: int | float, end_width: int | float) -> float:
    """Used for defining custom cross section widths/offsets

    Args:
        t (float): value on [0,1] mapping to position along length of taper
        start_width (float): starting width (t=0)
        end_width (float): ending width (t=1)

    Returns:
        (float): hyper taper function evaluated at t.
    """
    if start_width > end_width:
        a = np.arccosh(start_width / end_width)
        return np.cosh(a * (1 - t)) * end_width
    else:
        a = np.arccosh(end_width / start_width)
        return np.cosh(a * t) * start_width


def get_outline_layers(layer_set: LayerSet) -> dict[str, float]:
    """Get dictionary maping each layer in a LayerSet to its desired outline amount

    Args:
        layer_set (LayerSet): LayerSet

    Returns:
        (dict[str, float]): mapping of GDS layer name to outline distance. Layers that aren't outlined are omitted.
    """
    # outline
    outline_layers = {}
    for layer in layer_set:
        layer = layer_set[layer]
        ol = layer.outline
        if ol > 0:
            outline_layers[layer.name] = ol
    return outline_layers


def get_keepout_layers(layer_set: LayerSet) -> dict[str, str]:
    """Get dictionary maping a layer to a second layer which it should serve as a keepout for

    Args:
        layer_set (LayerSet): LayerSet

    Returns:
        (dict[str, str]): mapping of GDS layer name to GDS layer name.
    """
    # keepout
    keepout_layers = {}
    for layer in layer_set:
        layer = layer_set[layer]
        keepout = layer.keepout
        if keepout is not None:
            keepout_layers[layer.name] = keepout
    return keepout_layers


def outline(
    device: Device,
    outline_layers: dict[str, float] | None = None,
    kl_tile_size: int | None = None,
    kl_precision: float = 1e-4,
) -> Device:
    """Outline polygons within device by layer.

    Args:
        device (Device): device to outline
        outline_layers (dict[str, float]): map of desired outline amount per layer. If a layer is omitted, it will not be outlined
        kl_tile_size (int | None): if not None, size of tile to divide geometry into for multithreaded execution
        kl_precision (int | None): precision for KLayout operation (equivalently, sets dbu for KLayout)

    Returns:
        (Device): the outlined device
    """
    tile_size = None if kl_tile_size is None else (kl_tile_size, kl_tile_size)
    dev_outlined = Device()
    # extend ports
    dev_extended = Device()
    dev = dev_extended.add_ref(device)
    if outline_layers is None:
        outline_layers = {}
    for k, v in outline_layers.items():
        if v <= 0:
            raise ValueError(f"outline must be greater than zero, got {outline_layers}")
    outline_layers = {qg.get_layer(k).tuple: v for k, v in outline_layers.items()}
    new_ports = []
    processed_ports = []
    for layer in outline_layers.keys():
        for port in dev.ports:
            port = dev.ports[port]
            if qg.get_layer(port.layer).tuple != layer:
                continue
            ext = dev_extended.add_ref(
                pg.straight(
                    size=(port.width, outline_layers[layer] + 2e-4),
                    layer=qg.get_layer(port.layer).tuple,
                )
            )
            create_layered_ports(ext, layer)
            ext.connect(port=ext.ports[1], destination=port)
            # translate slightly to make sure there's no gap
            ext.move(1e-4 * np.diff(ext.ports[1].normal, axis=0)[0])
            p = ext.ports[2]
            p.name = port.name
            new_ports.append(p)
            processed_ports.append(port)
    new_ports += [
        dev.ports[p] for p in dev.ports if dev.ports[p] not in processed_ports
    ]
    polygons = device.get_polygons(by_spec=True)
    extended_polygons = dev_extended.get_polygons(by_spec=True)
    for layer, poly in polygons.items():
        layer = qg.get_layer(layer).tuple
        if layer not in outline_layers:
            dev_outlined.add_polygon(poly, layer=layer)
        else:
            dummy = Device()
            dummy.add_polygon(poly, layer=layer)
            bloated = pg.kl_offset(
                dummy,
                distance=outline_layers[layer],
                precision=kl_precision,
                tile_size=tile_size,
                layer=layer,
            )
            dummy = Device()
            dummy.add_polygon(extended_polygons[layer], layer=layer)
            outlined = pg.kl_boolean(
                A=bloated,
                B=dummy,
                operation="A-B",
                precision=kl_precision,
                tile_size=tile_size,
                layer=layer,
            )
            dev_outlined << outlined
    # add ports
    dev_outlined.flatten()
    for port in new_ports:
        port.midpoint = np.array(port.midpoint) - 1e-4 * np.diff(port.normal, axis=0)[0]
        dev_outlined.add_port(port=port)
    dev_outlined.name = "ol_" + device.name
    return dev_outlined


def invert(
    device: Device,
    ext_bbox_distance: dict[LayerSpec, float] = {},
    kl_tile_size: int | None = None,
    kl_precision: float = 1e-4,
) -> Device:
    """Outline polygons within device by layer.

    Args:
        device (Device): device to invert
        ext_bbox_distance (dict[LayerSpec, float]): amount to expand bounding box for each layer. If a layer is omitted, it will not be inverted.
        kl_tile_size (int | None): if not None, size of tile to divide geometry into for multithreaded execution
        kl_precision (int | None): precision for KLayout operation (equivalently, sets dbu for KLayout)

    Returns:
        (Device): the inverted device
    """
    tile_size = None if kl_tile_size is None else (kl_tile_size, kl_tile_size)
    dev_inverted = Device()
    ext_bbox_distance = {qg.get_layer(k).tuple: v for k, v in ext_bbox_distance.items()}
    polygons = device.get_polygons(by_spec=True)
    for layer, poly in polygons.items():
        layer = qg.get_layer(layer).tuple
        if layer not in ext_bbox_distance:
            dev_inverted.add_polygon(poly, layer=layer)
        else:
            dummy = Device()
            dummy.add_polygon(poly, layer=layer)
            bbox = dummy.bbox
            ext = ext_bbox_distance[layer]
            bbox[0] -= [ext, ext]
            bbox[1] += [ext, ext]
            bloated = pg.bbox(bbox, layer=layer)
            dummy = Device()
            dummy.add_polygon(polygons[layer], layer=layer)
            inverted = pg.kl_boolean(
                A=bloated,
                B=dummy,
                operation="A-B",
                precision=kl_precision,
                tile_size=tile_size,
                layer=layer,
            )
            dev_inverted << inverted
    dev_inverted.flatten()
    dev_inverted.name = "inv_" + device.name
    return dev_inverted


def keepout(
    device: Device,
    outline_layers: dict[LayerSpec, float] | None = None,
    keepout_layers: dict[LayerSpec, LayerSpecs] | None = None,
    kl_tile_size: int | None = None,
    kl_precision: float = 1e-4,
) -> Device:
    """Apply keepout layers

    Args:
        device (Device): device to outline
        outline_layers (dict[LayerSpec, float]): map of desired outline amount per layer.
            If a layer is omitted, it will not be outlined
        keepout_layers (dict[LayerSpec, LayerSpecs]): map of desired layer(s) to keepout. If a keepout
            layer applies to a positive-tone layer (i.e. layer in outline_layers with non-zero outline),
            then the keepout regions will be unioned. If keepout layer applies to negative-tone
            (i.e. layer not in outline_layers), then the keepout region will be subtracted.
        kl_tile_size (int | None): if not None, size of tile to divide geometry into for multithreaded execution
        kl_precision (int | None): precision for KLayout operation (equivalently, sets dbu for KLayout)

    Returns:
        (Device): device with keepout applied
    """
    tile_size = None if kl_tile_size is None else (kl_tile_size, kl_tile_size)
    dev_keepout = Device()
    if keepout_layers is None:
        return device
    if outline_layers is None:
        outline_layers = {}

    outline_layers = {qg.get_layer(k).tuple: v for k, v in outline_layers.items()}
    keepout_layers = {qg.get_layer(k).tuple: v for k, v in keepout_layers.items()}
    processed_layers = set([])

    polygons = device.get_polygons(by_spec=True)
    for keepout_layer, mapped_layers in keepout_layers.items():
        if keepout_layer not in polygons:
            continue
        keepout_poly = polygons[keepout_layer]
        for mapped_layer in mapped_layers:
            mapped_layer = qg.get_layer(mapped_layer).tuple
            neg_tone = mapped_layer not in outline_layers
            d_keepout = Device()
            d_keepout.add_polygon(keepout_poly, layer=mapped_layer)
            if mapped_layer not in polygons:
                if neg_tone:
                    continue
                else:
                    # pos-tone, add/union
                    # since mapped_layer not in polygons,
                    # union mapped+keepout is just keepout
                    dev_keepout << d_keepout
                    processed_layers.add(mapped_layer)
                    continue
            mapped_poly = polygons[mapped_layer]
            d_mapped = Device()
            d_mapped.add_polygon(mapped_poly, layer=mapped_layer)
            if neg_tone:
                # neg-tone, subtract
                dev_keepout << pg.kl_boolean(
                    A=d_mapped,
                    B=d_keepout,
                    operation="A-B",
                    precision=kl_precision,
                    tile_size=tile_size,
                    layer=mapped_layer,
                )
            else:
                # pos-tone, add/union
                dev_keepout << pg.kl_boolean(
                    A=d_mapped,
                    B=d_keepout,
                    operation="A+B",
                    precision=kl_precision,
                    tile_size=tile_size,
                    layer=mapped_layer,
                )
            processed_layers.add(mapped_layer)
    # add remaining layers
    for layer in device.layers:
        layer = qg.get_layer(layer).tuple
        if layer in processed_layers:
            continue
        if layer in keepout_layers:
            continue
        dev_keepout.add_polygon(polygons[layer], layer=layer)
    # add ports
    dev_keepout.flatten()
    dev_keepout.add_ports(device.ports)
    return dev_keepout


def get_cross_section_with_layer(
    layer: LayerSpec = "PHOTO1", default: CrossSectionSpec | None = None
) -> CrossSectionSpec | None:
    """Find the cross section associated with the given layer, or default

    Args:
        layer (LayerSpec): layer specification to find cross section for
        default (CrossSectionSpec | None): default return value if cross section
            is not found

    Returns:
        (CrossSectionSpec | None): found cross section or default
    """
    for xc in qg.get_active_pdk().cross_sections:
        xc = qg.get_cross_section(xc)
        if qg.get_layer(xc.sections[0]["layer"]) == qg.get_layer(layer):
            return xc


def get_device_port_direction(component: Device) -> dict[str, Sequence[Port]]:
    """Returns ports of a component organized by direction.

    Args:
        component (Device): component to get ports from

    Returns:
        (dict[str, Ports]): list of ports for each direction
    """
    ports = {x: [] for x in ["E", "N", "W", "S"]}
    # group by direction
    for p in component.ports.values():
        ports[_get_port_direction(p)].append(p)
    return ports


def _get_port_direction(port: Port, warn_not_90: bool = False) -> str:
    """Gets string port direction ("N", "S", "E" or "W") of a port

    Args:
        port (Port): port
        warn_not_90 (bool): warn if orientation is not multiple of 90 deg. default False

    Returns:
        (str): string of port orientation
    """
    angle = port.orientation % 360
    if (angle % 90 != 0) and warn_not_90:
        raise Warning("non-manhattan port orientation detected")
    if angle <= 45 or angle >= 315:
        return "E"
    elif angle <= 135 and angle >= 45:
        return "N"
    elif angle <= 225 and angle >= 135:
        return "W"
    else:
        return "S"
