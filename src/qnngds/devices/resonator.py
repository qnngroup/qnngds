"""Layout for various superconducting resonators."""

import numpy as np
import scipy.constants

import gdsfactory as gf
import qnngds as qg

from gdsfactory.typings import ComponentSpec, CrossSectionSpec, LayerSpec

from functools import partial
from collections.abc import Callable


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
def transmission_line_resonator(
    transmission_line_spec: ComponentSpec = transmission_line,
    resonator_spec: ComponentSpec = resonator_meandered,
    tl_cross_section: CrossSectionSpec = partial(cpw, width=75, gap=24),
    res_cross_section: CrossSectionSpec = cpw,
    taper_fn: Callable = qg.utilities.hyper_taper_fn,
) -> gf.Component:
    """Construct a resonator embedded between two transmission lines

    Inverts final design based on layer choice and PDK Layer class's outline function

    Args:
        transmission_line (ComponentSpec): desired component spec for transmission line.
            Must take a single argument ``cross_section``.
        resonator (ComponentSpec): desired component spec for embedded resonator
            Must take a single argument ``cross_section``.
        tl_cross_section (CrossSectionSpec): cpw or microstrip cross section for transmission line
        res_cross_section (CrossSectionSpec): cpw or microstrip cross section for resonator
        taper_fn (Callable): function for taper width. See :py:func:`qnngds.utilities.hyper_taper_fn`
            for an example.

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
    >>>     taper_fn=qg.utilities.hyper_taper_fn,
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
    res_xc_center = gf.CrossSection(sections=(res_xc.sections[0],))
    tl_xc_center = gf.CrossSection(sections=(tl_xc.sections[0],))
    x_trans = gf.path.transition(
        cross_section1=res_xc_center, cross_section2=tl_xc_center, width_type=taper_fn
    )
    transition = gf.path.extrude_transition(
        p=gf.path.straight(length=tl_xc.sections[0].width, npoints=200),
        transition=x_trans,
    )
    # if is_cpw:
    #    # outline transition
    #    #outline_layers = {str(layer): layers
    #    transition = qg.utilities.outline(transition, outline_layers)
    # if is_cpw:
    #    res_xc = gf.CrossSection(sections=res_xc.sections[1:])
    #    tl_xc = gf.CrossSection(sections=tl_xc.sections[1:])
    inner_width_fn = lambda t: np.where(
        t <= 1,
        taper_fn(t, res_xc.sections[0].width, tl_xc.sections[0].width),
        tl_xc.sections[0].width,
    )
    taper_s0 = gf.Section(
        width=res_xc.sections[0].width,
        # width_function=inner_width_fn,
        offset=0,
        layer=res_xc.sections[0].layer,
        hidden=is_cpw,
        port_names=("e1", "e2"),
        port_types=("electrical", "electrical"),
    )
    if is_cpw:
        outer_width_fn = lambda t: np.where(
            t <= 1,
            taper_fn(t, res_xc.sections[1].width, tl_xc.sections[1].width),
            tl_xc.sections[1].width,
        )
        taper_s12 = partial(
            gf.Section,
            width=res_xc.sections[1].width,
            # width_function=outer_width_fn,
            offset=0,
            layer=res_xc.sections[1].layer,
            port_names=("e1", "e2"),
        )
        taper_s1 = taper_s12(
            offset_function=lambda t: -(inner_width_fn(t) + outer_width_fn(t)) / 2
        )
        taper_s2 = taper_s12(
            offset_function=lambda t: (inner_width_fn(t) + outer_width_fn(t)) / 2
        )
        section = gf.CrossSection(sections=(taper_s0, taper_s1, taper_s2))
    else:
        section = gf.CrossSection(sections=(taper_s0,))
    # ext_taper = gf.path.extrude_transition(p=gf.path.straight(length=tl_xc.sections[0].width, npoints=200), transition=Xtrans)#cross_section=section)
    ext_taper = gf.path.extrude(
        p=gf.path.straight(length=tl_xc.sections[0].width, npoints=2000),
        cross_section=section,
    )

    R_ext = gf.components.extend_ports(
        component=R,
        port_names=["e1", "e2"],
        extension=ext_taper,
    )
    R_ext.show()
    input("press enter to continue")
    R_ext_tl = gf.components.extend_ports(
        component=R,
        port_names=["e1", "e2"],
        extension=transmission_line_spec(tl_xc),
    )
    # invert if needed
    outline_layers = qg.utilities.get_outline_layers(gf.get_active_pdk().layers)
    # if not CPW and layer is positive-tone, invert
    ext_bbox_layers = {str(layer): 50 for layer in outline_layers if not is_cpw}
    # if CPW and layer is negative-tone, invert
    ext_bbox_layers |= {
        str(layer): 50 for layer in layers if is_cpw and layer not in outline_layers
    }
    # TODO add pad
    inverted = qg.utilities.invert(R_ext_tl, ext_bbox_layers=ext_bbox_layers)
    R = gf.Component()
    R << inverted
    R.add_ports(inverted.ports)
    return R
