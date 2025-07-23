"""Dummy PDK with some example layers"""

import gdsfactory as gf
from gdsfactory.typings import Layer, LayerSpec
from gdsfactory.cross_section import CrossSection, cross_section, xsection

from functools import partial


class ApiGenLayers(gf.LayerEnum):
    """Fine, coarse e-beam layer and two photolithography layers"""

    layout = gf.constant(gf.kcl.layout)

    EBEAM_FINE: Layer = (1, 0)
    EBEAM_COARSE: Layer = (2, 0)
    EBEAM_KEEPOUT: Layer = (3, 0)
    PHOTO1: Layer = (4, 0)
    PHOTO2: Layer = (5, 0)

    @classmethod
    def outline(cls, layer: Layer) -> int:
        """Used to define desired outline for positive tone layers.

        To make a layer positive tone, return a non-zero value for it.

        E.g. if you want EBEAM_FINE to be positive tone with an outline
        of 100 nm, then you should define this function to return 0.1
        when passed a value of EBEAM_FINE (either as an enum type, a string
        or tuple that is equivalent to the EBEAM_FINE GDS layer).
        """
        if gf.get_layer(layer) == cls.EBEAM_FINE:
            ## uncomment the below line for positive tone
            return 0.1
        elif gf.get_layer(layer) == cls.EBEAM_COARSE:
            ## uncomment the below line for positive tone
            return 10
        # by default, assume a layer is negative tone
        return 0

    @classmethod
    def keepout(cls, layer: Layer) -> Layer:
        """Used to define keepout regions

        For example, if ``layer`` is a keepout layer
        for ``EBEAM_FINE``, then return ``EBEAM_FINE``.
        If ``layer`` is not a keepout layer, return ``None``.

        """
        if gf.get_layer(layer) == cls.EBEAM_KEEPOUT:
            return cls.EBEAM_FINE
        return None


LAYERS = ApiGenLayers


@xsection
def default(
    width: float = 25,
    layer: LayerSpec = LAYERS.EBEAM_FINE,
    radius: float = 30.0,
    radius_min: float = 30.0,
    force_no_outline: bool = False,
    **kwargs,
) -> CrossSection:
    """Return Strip cross_section.

    Args:
        width (float): width of cross section
        layer (LayerSpec): desired layer for cross section
        radius (float): bend radius
        radius_min (float): minimum bend radius
        force_no_outline (bool): if True, ignores if layer is positive tone.
        kwargs: keyword args for gf.CrossSection

    Returns:
        CrossSection
    """
    outline = LAYERS.outline(layer)
    if (outline > 0) and not (force_no_outline):
        # if outline is greater than zero, then do a positive tone cross section
        # with the center of the cross section missing (hidden=True)
        top = gf.Section(width=outline, offset=(width + outline) / 2, layer=layer)
        bot = gf.Section(width=outline, offset=-(width + outline) / 2, layer=layer)
        mid = gf.Section(
            width=width,
            offset=0,
            layer=layer,
            hidden=True,
            port_names=("e1", "e2"),
            port_types=("electrical", "electrical"),
        )
        section = gf.CrossSection(
            sections=(mid, top, bot),
            radius=radius,
            radius_min=radius_min,
            **kwargs,
        )
        return section
    else:
        # just do a normal cross section
        return cross_section(
            width=width,
            layer=layer,
            radius=radius,
            radius_min=radius_min,
            port_names=("e1", "e2"),
            port_types=("electrical", "electrical"),
            **kwargs,
        )


cross_sections = dict(
    ebeam_coarse=partial(default, layer="EBEAM_COARSE"),
    ebeam_fine=partial(default, layer="EBEAM_FINE"),
    default=default,
)
