"""Layout for various superconducting resonators."""

import numpy as np
import scipy.constants

import gdsfactory as gf
import qnngds as qg

from gdsfactory.typings import (
    ComponentSpec,
    CrossSectionSpec,
    LayerSpec,
    ComponentFactory,
)

from functools import partial


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
    width: float = 15,
    radius: float = 20,
    gap: float = 4,
    layer: LayerSpec = "PHOTO1",
) -> gf.CrossSection:
    """Creates a coplanar waveguide (CPW) cross section.

    NB resulting cross section is inverted: gaps will be filled and
    conductor will be empty.

    Args:
        width (float): width of center conductor
        gap (float): width of gaps on either side of conductor

    Returns:
        gf.CrossSection: CPW cross section
    """
    inner = gf.Section(
        width=width,
        offset=0,
        layer=layer,
        hidden=True,
        port_names=("e1", "e2"),
        port_types=("electrical", "electrical"),
        name="center",
    )
    gaps = partial(
        gf.Section,
        width=gap,
        layer=layer,
    )
    return gf.CrossSection(
        sections=(
            inner,
            gaps(offset=-(width + gap) / 2, name="gap_l"),
            gaps(offset=(width + gap) / 2, name="gap_u"),
        ),
        radius=radius,
        radius_min=radius,
    )


def microstrip(
    width: float = 15,
    radius: float = 20,
    layer: LayerSpec = "PHOTO1",
) -> gf.CrossSection:
    """Creates a microstrip cross section

    NB unlike :py:func:`cpw`, conductor is filled

    Args:
        width (float): width of center conductor

    Returns:
        gf.CrossSection: microstrip cross section
    """
    inner = gf.Section(
        width=width,
        offset=0,
        layer=layer,
        port_names=("e1", "e2"),
        port_types=("electrical", "electrical"),
        name="center",
    )
    return gf.CrossSection(
        sections=(inner,),
        radius=radius,
        radius_min=radius,
    )


@gf.cell
def transmission_line(
    cross_section: CrossSectionSpec,
    length: float = 50,
) -> gf.Component:
    """Construct a straight transmission line by extruding a cross section

    Args:
        length (float): length of transmission line
        cross_section (CrossSectionSpec): cross section to extrude

    Returns:
        gf.Component: straight transmission line
    """
    return gf.path.extrude(
        gf.path.straight(length=length, npoints=2),
        cross_section=gf.get_cross_section(cross_section),
    )


@gf.cell
def resonator_meandered(
    cross_section: CrossSectionSpec,
    n_eff: float = 100,
    resonant_freq: float = 1e9,
    meander_width: float = 300,
) -> gf.Component:
    """Construct meandered half-wave resonator

    Args:
        n_eff (float): effective index of refraction
        resonant_freq (float): resonant frequeny in Hz
        meander_width (float): width of meander structure
        cross_section (CrossSectionSpec): cross section to use (e.g. CPW)

    Returns:
        gf.Component: meandered half-wave resonator
    """
    xc = gf.get_cross_section(cross_section)
    desired_length = compute_res_wavelength(n_eff=n_eff, res_freq=resonant_freq) / 2
    left_bend = gf.path.euler(radius=xc.radius, angle=90, use_eff=False)
    right_bend = gf.path.euler(radius=xc.radius, angle=-90, use_eff=False)
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
    half = gf.path.straight(length=L_half)
    straight = gf.path.straight(length=L_straight)
    # start, left, right, and end segments
    start = [left_bend, half, right_bend]
    right = [right_bend, straight, left_bend]
    left = [left_bend, straight, right_bend]
    if n_rows % 2 == 0:
        end = [right_bend, half, left_bend]
    else:
        end = [left_bend, half, right_bend]
    # construct the path
    P = gf.Path()
    P.append(start)
    rows = 0
    for _ in range(int(np.ceil(n_rows / 2))):
        P.append(right)
        rows += 1
        if rows < n_rows:
            P.append(left)
            rows += 1
    P.append(end)
    return gf.path.extrude(P, xc)


@gf.cell
def resonator_straight(
    n_eff: float = 100,
    resonant_freq: float = 1e9,
    cross_section: CrossSectionSpec = cpw,
):
    """Construct straight half-wave resonator

    Args:
        n_eff (float): effective index of refraction
        resonant_freq (float): resonant frequeny in Hz
        cross_section (CrossSectionSpec): cross section to use (e.g. CPW)

    Returns:
        gf.Component: meandered half-wave resonator
    """
    desired_length = compute_res_wavelength(n_eff=n_eff, res_freq=resonant_freq) / 2
    return gf.path.extrude(
        gf.path.straight(length=desired_length), gf.get_cross_section(cross_section)
    )


@gf.cell
def pad(
    width: float = 100,
    length: float = 200,
    edge_exclusion: float = 10,
    sc_layer: LayerSpec = "PHOTO1",
    metal_layer: LayerSpec = "PHOTO2",
) -> gf.Component:
    """Construct a pad for resonator with a metal layer for bonding on top of superconductor.

    Args:
        width (float): Desired width of superconductor layer
        edge_exclusion (float): Amount on each side to decrease width of top metal bonding pad.
        sc_layer (LayerSpec): layer for superconductor
        metal_layer (LayerSpec): layer for metal

    Returns:
        gf.Component: pad
    """
    PAD = gf.Component()
    sc = PAD << gf.components.compass(size=(width, length), layer=sc_layer)
    sc.move(sc.center, (0, 0))
    metal = PAD << gf.components.compass(
        size=(width - 2 * edge_exclusion, length - 2 * edge_exclusion),
        layer=metal_layer,
    )
    metal.move(metal.center, (0, 0))
    PAD.add_port(name="e1", port=sc.ports["e4"])
    return PAD


@gf.cell
def transmission_line_resonator(
    transmission_line_spec: ComponentSpec = transmission_line,
    resonator_spec: ComponentSpec = resonator_meandered,
    tl_cross_section: CrossSectionSpec = partial(cpw, width=75, gap=24),
    res_cross_section: CrossSectionSpec = cpw,
    taper: ComponentFactory = qg.geometries.hyper_taper,
    pads: tuple[ComponentSpec | None, ComponentSpec | None] = (pad, None),
) -> gf.Component:
    """Construct a resonator embedded between two transmission lines

    Inverts final design based on layer choice and PDK Layer class's outline function

    Args:
        transmission_line (ComponentSpec): Desired component spec for transmission line.
            Must take a single argument ``cross_section``.
        resonator (ComponentSpec): Desired component spec for embedded resonator.
            Must take a single argument ``cross_section``.
        tl_cross_section (CrossSectionSpec): CPW or microstrip cross section for transmission line.
        res_cross_section (CrossSectionSpec): CPW or microstrip cross section for resonator.
        taper (ComponentFactory): Callable which produces a Component, used to generate a filled taper
            between resonator and transmission line. Port widths must match. Should be solid (i.e. not outlined);
            will be automatically outlined for CPW.
        pad (tuple[ComponentSpec | None, ComponentSpec | None]): Component spec or None for each pad.
            If ComponentSpec, must take a single argument ``width``. If None, no pad will be created

    Returns:
        gf.Component: resonator embedded between transmission lines

    Example:

    >>> from functools import partial
    >>> tl_spec = partial(
    >>>     qg.devices.resonator.transmission_line,
    >>>     length=100,
    >>> )
    >>> res_spec = partial(
    >>>     qg.devices.resonator.resonator_meandered,
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
    >>>     transmission_line=tl_spec,
    >>>     resonator=res_spec,
    >>>     tl_cross_section=tl_xc_spec,
    >>>     res_cross_section=res_xc_spec,
    >>>     taper=qg.geometries.hyper_taper,
    >>>     pad=qg.devices.resonator.pad,
    >>> )

    """
    res_xc = gf.get_cross_section(res_cross_section)
    tl_xc = gf.get_cross_section(tl_cross_section)
    # if section[0] (the main section) is hidden, then assume we're using a CPW
    res_cpw = res_xc.sections[0].hidden
    tl_cpw = tl_xc.sections[0].hidden
    res_layers = set(sect.layer for sect in res_xc.sections)
    tl_layers = set(sect.layer for sect in tl_xc.sections)
    # check inputs
    if res_cpw ^ tl_cpw:
        error_msg = "Detected mismatch between resonator and transmission line cross-section types."
        error_msg += f" {res_cpw=} and {tl_cpw=}."
        raise ValueError(error_msg)
    if res_layers != tl_layers:
        error_msg = "Detected mismatch between resonator and transmission line layers."
        error_msg += f" {res_layers=} and {tl_layers=}."
        raise ValueError(error_msg)

    if len(res_layers) > 1:
        raise Warning(
            "WARNING: detected more than 1 layer in cross section spec, tapers may not work correctly"
        )

    is_cpw = res_cpw
    layers = res_layers

    R = gf.Component()
    res = resonator_spec(res_xc)
    R << res
    R.add_ports(res.ports)
    # create new cross-section for taper using transitions
    T = gf.Component()
    trans_length = tl_xc.sections[0].width
    trans_layer = res_xc.sections[0].layer
    transition = taper(
        start_width=res_xc.sections[0].width,
        end_width=tl_xc.sections[0].width,
        length=trans_length,
        layer=trans_layer,
    )
    if is_cpw:
        # outline transition
        start_w = sum(section.width for section in res_xc.sections)
        end_w = sum(section.width for section in tl_xc.sections)
        wide_transition = taper(
            start_width=start_w, end_width=end_w, length=trans_length, layer=trans_layer
        )
        T << gf.boolean(
            A=wide_transition,
            B=transition,
            operation="A-B",
            layer1=trans_layer,
            layer2=trans_layer,
            layer=res_xc.sections[1].layer,
        )
    else:
        T << transition
    T.add_ports(transition.ports)
    R_ext = gf.components.extend_ports(
        component=R,
        port_names=["e1", "e2"],
        extension=T,
    )
    R_ext_tl = gf.components.extend_ports(
        component=R_ext,
        port_names=["e1", "e2"],
        extension=transmission_line_spec(tl_xc),
    )
    for n, pad in enumerate(pads):
        if pad is None:
            continue
        pad_i = pad(tl_xc.sections[0].width)
        if is_cpw:
            pad_i = qg.utilities.outline(
                component=pad_i,
                outline_layers={str(tl_xc.sections[1].layer): tl_xc.sections[1].width},
            )
        R_ext_tl = gf.components.extend_ports(
            component=R_ext_tl, port_names=[f"e{n + 1}"], extension=pad_i
        )
    # invert if needed
    outline_layers = qg.utilities.get_outline_layers(gf.get_active_pdk().layers)
    # if not CPW and layer is positive-tone, invert
    ext_bbox_layers = {str(layer): 50 for layer in outline_layers if not is_cpw}
    # if CPW and layer is negative-tone, invert
    ext_bbox_layers |= {
        str(layer): 50 for layer in layers if is_cpw and layer not in outline_layers
    }
    inverted = qg.utilities.invert(R_ext_tl, ext_bbox_layers=ext_bbox_layers)
    R = gf.Component()
    R << inverted
    R.add_ports(inverted.ports)
    return R
