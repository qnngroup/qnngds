import gdsfactory as gf
from gdsfactory.cross_section import CrossSection, cross_section, xsection
from gdsfactory.typings import LayerSpec
from pdk.layer_map import LAYERS


@xsection
def ebeam(
    width: float = 25,
    layer: LayerSpec = (2, 0),
    radius: float = 30.0,
    radius_min: float = 10,
    **kwargs,
) -> CrossSection:
    """Return Strip cross_section."""
    ol = LAYERS.outline(layer)
    if ol > 0:
        ct = gf.Section(width=ol, offset=(width + ol) / 2, layer=layer)
        cb = gf.Section(width=ol, offset=-(width + ol) / 2, layer=layer)
        c0 = gf.Section(
            width=width, offset=0, layer=layer, hidden=True, port_names=("o1", "o2")
        )
        section = gf.CrossSection(
            sections=(c0, ct, cb),
            radius=radius,
            radius_min=radius_min,
            **kwargs,
        )
        return section
    else:
        return cross_section(
            width=width,
            layer=layer,
            radius=radius,
            radius_min=radius_min,
            **kwargs,
        )


cross_sections = dict(ebeam=ebeam, strip=ebeam)
