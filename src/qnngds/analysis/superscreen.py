"""Functions for interfacing with superscreen"""

import numpy as np
import qnngds as qg
from qnngds.typing import LayerSpec
import phidl.geometry as pg

try:
    import superscreen as sc
except ImportError:
    raise ImportError(
        "qnngds.analysis.superscreen requires superscreen to be installed"
    )


def make_superscreen_device(
    device: qg.Device,
    london_lambda: dict[LayerSpec, float] | float,
    thickness: dict[LayerSpec, float] | float,
    z0: dict[LayerSpec, float] | None = None,
) -> sc.Device:
    """Make a superscreen.Device that can be used for simulation from a qnngds Device.

    Makes a best-effort attempt to autoassign ports to different polygons in the geometry.
    Cannot currently model structures with holes in them.

    Args:
        device (qnngds.Device): input device. Supports multiple layers and ports, although
            self-intersecting layers with ports may not be processed correctly.
        london_lambda (dict[LayerSpec, float] | float): per-layer london magnetic penetration depth in microns
            (if dict), or same penetration depth for all layers (if float)
        thickness (dict[LayerSpec, float] | float): per-layer thickness of the film in microns
            (if dict), or same thickness for all layers
        z0 (dict[LayerSpec, float] | None): optional, z height of each layer. Required for multiple layer device.
            Default None.

    Returns:
        (superscreen.Device): a superscreen.Device instance that can be used with the superscreen modeling
            kit to simulate flux trapping, fluxoids, mutual inductance, and other screening effects.
    """
    layers = [qg.get_layer(layer) for layer in device.get_layers()]
    if len(layers) > 1 and z0 is None:
        raise ValueError("must specify z0 layer heights for multilayer device")
    if isinstance(london_lambda, float):
        london_lambda = {layer: london_lambda for layer in layers}
    if isinstance(thickness, float):
        thickness = {layer: thickness for layer in layers}

    def get_layer_attr(attrs: dict, layer: LayerSpec):
        """Helper method for getting the values from a dict that maps layer to a float, since
        the type of the key may vary"""
        try:
            return attrs[layer]
        except KeyError:
            next_key = next(iter(attrs.keys()))
            if isinstance(next_key, tuple):
                return attrs[qg.get_layer(layer).tuple]
            elif isinstance(next_key, str):
                return attrs[qg.get_layer(layer).name]
            else:
                raise

    sc_layers = {}
    polygons = []
    ports = {}
    for layer in layers:
        sc_layers[layer] = sc.Layer(
            layer.tuple,
            london_lambda=get_layer_attr(london_lambda, layer),
            thickness=get_layer_attr(thickness, layer),
            z0=get_layer_attr(z0, layer),
        )
        # create the polygons
        new_polygons = []
        for n, pp in enumerate(
            pg.union(device, by_layer=True).get_polygons(
                by_spec=qg.get_layer(layer).tuple
            )
        ):
            poly = sc.Polygon(f"{layer.tuple}_{n}", layer=layer.tuple, points=pp)
            resample_points = int(
                np.max(poly.extents) / get_layer_attr(london_lambda, layer) * 10
            )
            new_polygons.append(poly.resample(resample_points).buffer(0))
        polygons += new_polygons
        # add ports
        for port_name in device.ports:
            if qg.get_layer(device.ports[port_name].layer) == qg.get_layer(layer):
                # add port
                port = (
                    sc.Polygon(
                        f"port_{layer.tuple}_{port_name}",
                        points=sc.geometry.box(
                            get_layer_attr(london_lambda, layer),
                            device.ports[port_name].width,
                        ),
                        layer=layer.tuple,
                    )
                    .rotate(device.ports[port_name].orientation)
                    .translate(
                        dx=device.ports[port_name].x, dy=device.ports[port_name].y
                    )
                )
                # check if the port intersects any of the new polygons
                # this makes a best effort guess of which polygon has which ports
                # if there are multiple intersecting polygons on the same layer that have ports, then
                # this will almost definitely fail and produce an error
                for n, polygon in enumerate(new_polygons):
                    pmain = qg.Device()
                    pport = qg.Device()
                    pmain.add_polygon(polygon.points, layer=0)
                    pport.add_polygon(port.points, layer=0)
                    intersection = pg.kl_boolean(pmain, pport, "and").get_polygons()
                    if len(intersection) > 0:
                        key = f"{layer.tuple}_{n}"
                        if key not in ports:
                            ports[key] = []
                        ports[key].append(port)
    return sc.Device(
        device.name,
        layers=sc_layers,
        films=polygons,
        terminals=ports,
        length_units="um",
    )
