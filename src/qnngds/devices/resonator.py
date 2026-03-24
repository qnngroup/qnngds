"""Layout for various superconducting resonators."""

# can be removed in python 3.14, see https://peps.python.org/pep-0749/
from __future__ import annotations

import qnngds as qg

import numpy as np
import scipy.constants
from functools import partial

from qnngds.typing import (
    LayerSpec,
    LayerSpecs,
    DeviceSpec,
    DeviceFactory,
    CrossSectionSpec,
)
from qnngds import Device, CrossSection

import phidl.path as pp
import phidl.geometry as pg
from phidl import Path


def compute_veff(n_eff: float) -> float:
    """Computes effective light speed from effective index

    Args:
        n_eff: effective index of refraction

    Returns:
        (float): effective phase velocity in m/s
    """
    return scipy.constants.c / n_eff


def compute_res_wavelength(n_eff: float, res_freq: float) -> float:
    """Computes resonant wavelength from effective index, resonant
    frequency.

    Args:
        n_eff: effective index of refraction
        res_freq: resonant frequency in Hz

    Returns:
        (float): resonant wavelength in microns
    """
    v = compute_veff(n_eff)
    return v / res_freq * 1e6


def cpw(
    width: float = 10,
    gap: float = 5,
    radius: float = 50,
    layer: LayerSpec = "PHOTO1",
) -> CrossSection:
    """Creates a coplanar waveguide (CPW) cross section.

    NB resulting cross section is inverted: gaps will be filled and
    conductor will be empty.

    Args:
        width (float): width of center conductor
        gap (float): width of gaps on either side of conductor
        radius (float): bend radius
        layer (LayerSpec): GDS layer specification

    Returns:
        (CrossSection): CPW cross section
    """
    CPW = CrossSection(radius=radius)
    CPW.add(
        width=width,
        offset=0,
        layer=qg.get_layer(layer),
        hidden=True,
        ports=(1, 2),
        name="center",
    )
    for i in range(2):
        CPW.add(
            width=gap,
            layer=qg.get_layer(layer),
            offset=(-1) ** i * (width + gap) / 2,
            name="gap_" + ("u" if i == 0 else "l"),
        )
    return CPW


def microstrip(
    width: float = 5,
    radius: float = 50,
    layer: LayerSpec = "PHOTO1",
) -> CrossSection:
    """Creates a microstrip cross section

    NB unlike :py:func:`cpw`, conductor is filled

    Args:
        width (float): width of center conductor
        radius (float): bend radius
        layer (LayerSpec): GDS layer specification

    Returns:
        (CrossSection): microstrip cross section
    """
    USTRIP = CrossSection(radius=radius)
    USTRIP.add(
        width=width,
        offset=0,
        layer=qg.get_layer(layer),
        ports=(1, 2),
        name="center",
    )
    return USTRIP


@qg.device
def transmission_line(
    cross_section: CrossSectionSpec = cpw,
    length: float = 100,
) -> Device:
    """Construct a straight transmission line by extruding a cross section

    Args:
        length (float): length of transmission line
        cross_section (CrossSectionSpec): cross section to extrude

    Returns:
        (Device): straight transmission line
    """
    xc = qg.get_cross_section(cross_section)
    return xc.extrude(pp.straight(length=length))


@qg.device
def meandered(
    cross_section: CrossSectionSpec = cpw,
    n_eff: float = 10,
    resonant_freq: float = 5e9,
    meander_width: float = 500,
) -> Device:
    """Construct meandered half-wave resonator

    Args:
        n_eff (float): effective index of refraction
        resonant_freq (float): resonant frequeny in Hz
        meander_width (float): width of meander structure
        cross_section (CrossSectionSpec): cross section to use (e.g. CPW)

    Returns:
        (Device): meandered half-wave resonator
    """
    xc = qg.get_cross_section(cross_section)
    desired_length = compute_res_wavelength(n_eff=n_eff, res_freq=resonant_freq) / 2
    left_bend = pp.euler(radius=xc.radius, angle=90, use_eff=False, p=1)
    right_bend = pp.euler(radius=xc.radius, angle=-90, use_eff=False, p=1)
    L_bend = left_bend.length()
    x_bend = left_bend.xsize
    # compute number of lines
    L_straight = meander_width - 2 * x_bend
    L_half = L_straight / 2 - x_bend
    n_rows = int(
        np.ceil(
            (desired_length - 2 * (L_half + 2 * L_bend)) / (L_straight + 2 * L_bend)
        )
    )
    # correct straight length
    L_straight = (desired_length - 2 * L_bend * n_rows - 4 * L_bend + 2 * x_bend) / (
        1 + n_rows
    )
    L_half = L_straight / 2 - x_bend
    half = pp.straight(length=L_half)
    straight = pp.straight(length=L_straight)
    # start, left, right, and end segments
    start = [left_bend, half, right_bend]
    right = [right_bend, straight, left_bend]
    left = [left_bend, straight, right_bend]
    if n_rows % 2 == 0:
        end = [right_bend, half, left_bend]
    else:
        end = [left_bend, half, right_bend]
    # construct the path
    P = Path()
    P.append(start)
    rows = 0
    for _ in range(int(np.ceil(n_rows / 2))):
        P.append(right)
        rows += 1
        if rows < n_rows:
            P.append(left)
            rows += 1
    P.append(end)
    return xc.extrude(P)


@qg.device
def straight(
    cross_section: CrossSectionSpec = cpw,
    n_eff: float = 100,
    resonant_freq: float = 1e9,
) -> Device:
    """Construct straight half-wave resonator

    Args:
        cross_section (CrossSectionSpec): cross section to use (e.g. CPW)
        n_eff (float): effective index of refraction
        resonant_freq (float): resonant frequeny in Hz

    Returns:
        (Device): meandered half-wave resonator
    """
    desired_length = compute_res_wavelength(n_eff=n_eff, res_freq=resonant_freq) / 2
    xc = qg.get_cross_section(cross_section)
    return xc.extrude(pp.straight(length=desired_length))


@qg.device
def pad(
    width: float = 100,
    length: float = 200,
    edge_exclusion: float = 10,
    sc_layer: LayerSpec = "PHOTO1",
    metal_layers: LayerSpecs = ("PHOTO2",),
) -> Device:
    """Construct a pad for resonator with a metal layer for bonding on top of superconductor.

    Args:
        width (float): Desired width of superconductor layer
        edge_exclusion (float): Amount on each side to decrease width of top metal bonding pad.
        sc_layer (LayerSpec): layer specification for superconductor
        metal_layers (LayerSpecs): layer(s) for metal

    Returns:
        (Device): pad
    """
    PAD = Device()
    sc = PAD << pg.straight(size=(width, length), layer=qg.get_layer(sc_layer))
    sc.move(sc.center, (0, 0))
    for metal_layer in metal_layers:
        metal = PAD << pg.rectangle(
            size=(width - 2 * edge_exclusion, length - 2 * edge_exclusion),
            layer=qg.get_layer(metal_layer),
        )
        metal.move(metal.center, (0, 0))
    PAD.add_port(name=1, port=sc.ports[2], layer=sc_layer)
    return PAD


@qg.device
def transmission_line_resonator(
    transmission_line_specs: tuple[DeviceSpec | None, DeviceSpec | None] = (
        transmission_line,
        None,
    ),
    resonator_spec: DeviceSpec = meandered,
    tl_cross_section: CrossSectionSpec = partial(cpw, width=75, gap=24),
    res_cross_section: CrossSectionSpec = cpw,
    taper: DeviceFactory = qg.geometries.hyper_taper,
    pads: tuple[DeviceSpec | None, DeviceSpec | None] = (pad, None),
    bbox_extension: float = 500,
) -> Device:
    """Construct a resonator embedded between two transmission lines

    Inverts final design based on layer choice and PDK Layer class's outline function

    Args:
        transmission_line_specs (tuple[DeviceSpec | None, DeviceSpec | None]): Desired DeviceSpec for
            transmission line on either end of resonator. If DeviceSpec, take a single argument
            ``cross_section``. If None, no transmission line will be created (although the resonator will
            taper out to the width of the ``tl_cross_section``.
        resonator_spec (DeviceSpec): Desired DeviceSpec for embedded resonator.
            Must take a single argument ``cross_section``.
        tl_cross_section (CrossSectionSpec): CPW or microstrip cross section for transmission line.
        res_cross_section (CrossSectionSpec): CPW or microstrip cross section for resonator.
        taper (DeviceFactory): Callable which produces a Device, used to generate a filled taper
            between resonator and transmission line. Port widths must match. Should be solid (i.e. not outlined);
            will be automatically outlined for CPW.
        pads (tuple[DeviceSpec | None, DeviceSpec | None]): DeviceSpec or None for each pad.
            If DeviceSpec, must take a single argument ``width``. If None, no pad will be created
        bbox_extension (float): amount to extend ground plane for negative tone layout CPW, or positive
            tone microstrip

    Returns:
        (Device): resonator embedded between transmission lines

    Example:

    >>> from functools import partial
    >>> tl_spec = partial(
    >>>     qg.devices.resonator.transmission_line,
    >>>     length=100,
    >>> )
    >>> res_spec = partial(
    >>>     qg.devices.resonator.meandered,
    >>>     n_eff=100,
    >>>     resonant_freq=1e9,
    >>>     meander_width=300,
    >>> )
    >>> tl_xc_spec = partial(
    >>>     qg.devices.resonator.cpw,
    >>>     width=20,
    >>>     gap=4,
    >>>     layer="PHOTO1",
    >>> )
    >>> res_xc_spec = partial(
    >>>     qg.devices.resonator.cpw,
    >>>     width=10,
    >>>     radius=30,
    >>>     gap=2,
    >>>     layer="PHOTO1",
    >>> )
    >>> c = qg.devices.resonator.transmission_line_resonator(
    >>>     transmission_line_specs=(tl_spec, None),
    >>>     resonator_spec=res_spec,
    >>>     tl_cross_section=tl_xc_spec,
    >>>     res_cross_section=res_xc_spec,
    >>>     taper=qg.geometries.hyper_taper,
    >>>     pads=(qg.devices.resonator.pad, None),
    >>>     bbox_extension=200,
    >>> )

    """
    res_xc = qg.get_cross_section(res_cross_section)
    tl_xc = qg.get_cross_section(tl_cross_section)
    # if section[0] (the main section) is hidden, then assume we're using a CPW
    res_cpw = res_xc.sections[0]["hidden"]
    tl_cpw = tl_xc.sections[0]["hidden"]
    res_layers = set(section["layer"] for section in res_xc.sections)
    tl_layers = set(section["layer"] for section in tl_xc.sections)
    # check inputs
    if res_cpw ^ tl_cpw:
        raise ValueError(
            "Detected mismatch between resonator and transmission "
            f"line cross-section types. {res_cpw=} and {tl_cpw=}."
        )
    if res_layers != tl_layers:
        raise ValueError(
            "Detected mismatch between resonator and transmission "
            f"line layers. {res_layers=} and {tl_layers=}."
        )
    if len(res_layers) > 1:
        raise Warning(
            "WARNING: detected more than 1 layer in cross section "
            "spec, tapers may not work correctly"
        )

    is_cpw = res_cpw
    layers = res_layers

    R = Device()
    res = resonator_spec(res_xc)
    R << res
    R.add_ports(res.ports)
    # create new cross-section for taper using transitions
    T = Device()
    trans_length = sum(section["width"] for section in tl_xc.sections)
    trans_layer = res_xc.sections[0]["layer"]
    transition = taper(
        start_width=res_xc.sections[0]["width"],
        end_width=tl_xc.sections[0]["width"],
        length=trans_length,
        layer=trans_layer,
    )
    if is_cpw:
        # outline transition
        start_w = sum(section["width"] for section in res_xc.sections)
        end_w = sum(section["width"] for section in tl_xc.sections)
        wide_transition = taper(
            start_width=start_w, end_width=end_w, length=trans_length, layer=trans_layer
        )
        T << pg.kl_boolean(
            A=wide_transition,
            B=transition,
            operation="A-B",
            layer=res_xc.sections[1]["layer"],
        )
    else:
        T << transition
    T.add_ports(transition.ports)
    # add tapers
    R = qg.utilities.extend_ports(
        device=R,
        port_names=[1, 2],
        extension=T,
    )
    for n, tl_spec in enumerate(transmission_line_specs):
        if tl_spec is None:
            continue
        # attach tl to device
        R = qg.utilities.extend_ports(
            device=R,
            port_names=[n + 1],
            extension=tl_spec(tl_xc),
        )
    for n, pad in enumerate(pads):
        if pad is None:
            continue
        # create the pad
        pad_i = pad(tl_xc.sections[0]["width"])
        if is_cpw:
            # outline the pad
            pad_i = qg.utilities.outline(
                device=pad_i,
                outline_layers={tl_xc.sections[1]["layer"]: tl_xc.sections[1]["width"]},
            )
        # attach pad to device
        # new_ports is False, since we're not really extending the ports, just capping them with pads.
        # there is not a second port on the pad to propagate to the newly-created device.
        R = qg.utilities.extend_ports(
            device=R, port_names=[n + 1], extension=pad_i, new_ports=False
        )
    # invert if needed
    outline_layers = qg.utilities.get_outline_layers(qg.get_active_pdk().layers)
    # if not CPW and layer is positive-tone, invert
    ext_bbox_distance = {
        layer: bbox_extension for layer in outline_layers if not is_cpw
    }
    # if CPW and layer is negative-tone, invert
    ext_bbox_distance |= {
        layer: bbox_extension
        for layer in layers
        if is_cpw and layer not in outline_layers
    }
    inverted = qg.utilities.invert(R, ext_bbox_distance=ext_bbox_distance)
    R = Device("resonator")
    R << inverted
    R.add_ports(inverted.ports)
    return R
