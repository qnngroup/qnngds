"""Functions for interfacing with py-tdgl"""

import numpy as np
import qnngds as qg
from qnngds.typing import LayerSpec

try:
    import tdgl
except ImportError:
    raise ImportError("qnngds.analysis.tdgl requires tdgl to be installed")


def make_tdgl_device(
    device: qg.Device,
    coherence_length: float,
    london_lambda: float,
    thickness: float,
    gamma: float,
    layer: LayerSpec,
) -> tdgl.Device:
    """Make a tdgl.Device that can be used for simulation from a qnngds Device.

    Cannot currently model structures with holes in them.

    Args:
        device (qnngds.Device): input device. Only one layer will be used, supports multiple ports,
            but regions must be contiguous(?)
        layer (LayerSpec): layer of device to use.
        coherence_length (float): coherence length of superconducting film in microns
        london_lambda (float): london magnetic penetration depth in microns
        thickness (float): thickness of the film in microns
        gamma (float): material constant describing ratio of scattering time for electrons and phonons

    Returns:
        (tdgl.Device): a tdgl.Device instance that can be used with tdgl.solve() to model evolution of
            order parameter and phase under application of bias current.
    """
    tdgl_layer = tdgl.Layer(
        coherence_length=coherence_length,
        london_lambda=london_lambda,
        thickness=thickness,
        gamma=gamma,
    )
    length_units = "um"
    resample_points = int(max(device.xsize, device.ysize) / coherence_length * 10)
    pp = device.get_polygons(by_spec=qg.get_layer(layer).tuple)[0]
    film = tdgl.Polygon("film", points=pp).resample(resample_points).buffer(0)
    terminals = []
    probe_points = []
    for port_name in device.ports:
        port = device.ports[port_name]
        theta = port.orientation * np.pi / 180
        p1 = port.midpoint + port.width / 2 * np.array([np.sin(theta), -np.cos(theta)])
        p2 = port.midpoint + port.width / 2 * np.array([-np.sin(theta), np.cos(theta)])
        tangent = p2 - p1
        normal = np.array([np.cos(theta), np.sin(theta)])
        terminals.append(
            tdgl.Polygon(
                str(port.name),
                points=[
                    p1 - 0.1 * tangent + coherence_length * normal,
                    p2 + 0.1 * tangent + coherence_length * normal,
                    p2 + 0.1 * tangent - coherence_length * normal,
                    p1 - 0.1 * tangent - coherence_length * normal,
                ],
            )
        )
        probe_points.append(port.midpoint - 5 * coherence_length * normal)
    return tdgl.Device(
        device.name,
        layer=tdgl_layer,
        film=film,
        terminals=terminals,
        probe_points=probe_points,
        length_units=length_units,
    )
