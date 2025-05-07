import gdsfactory as gf
from gdsfactory.cross_section import CrossSection, cross_section, xsection
from gdsfactory.typings import LayerSpec


@xsection
def ebeam(
    width: float = 25,
    layer: LayerSpec = "EBEAM_COARSE",
    radius: float = 30.0,
    radius_min: float = 10,
    **kwargs,
) -> CrossSection:
    """Return Strip cross_section."""
    return cross_section(
        width=width,
        layer=layer,
        radius=radius,
        radius_min=radius_min,
        **kwargs,
    )


strip = gf.cross_section.strip
cross_sections = dict(ebeam=ebeam, strip=strip)
