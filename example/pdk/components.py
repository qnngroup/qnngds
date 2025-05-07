import gdsfactory as gf

from gdsfactory.typings import LayerSpec
import qnngds as qg

from pdk.cross_section import cross_sections
from pdk.layer_map import LAYERS
from functools import partial


@gf.cell
def pad_tri(
    size: tuple[float, float] = (200, 200),
    yspace: float = 100,
    layer: LayerSpec = (1, 0),
) -> gf.Component:
    pads = gf.Component()
    pad = gf.components.pad(
        size=size,
        layer=layer,
        port_inclusion=0,
        port_orientation=None,
        port_orientations=(90,),
    )
    ports = []
    for i in range(2):
        p_i = pads.add_ref(pad)
        if i == 1:
            p_i.rotate(180)
        p_i.move(p_i.ports[0].center, (0, 0))
        p_i.movey(-yspace / 2 * (-1) ** i)
        ports += p_i.ports
    p_i = pads.add_ref(pad)
    p_i.rotate(-90)
    p_i.move(p_i.ports[0].center, (-size[0] / 2 - 50, 0))
    ports += p_i.ports
    for n, port in enumerate(ports):
        pads.add_port(
            name=f"e{n + 1}",
            center=port.center,
            orientation=port.orientation,
            port_type="optical",
            width=size[0],
            layer=layer,
        )
    return pads


@gf.cell
def hyper_taper(
    width1: float = 1.0,
    width2: float = 2.0,
    layer1: LayerSpec = (1, 0),
    layer2: LayerSpec = (2, 0),
) -> gf.Component:
    taper = gf.Component()
    ht = qg.geometries.hyper_taper(
        length=width2, wide_section=width2, narrow_section=width1, layer=layer2
    )
    taper.add_ref(ht)
    for n, port in enumerate(ht.ports):
        taper.add_port(
            name=f"e{n}",
            center=port.center,
            orientation=port.orientation,
            width=port.width,
            layer=layer1 if n == 0 else layer2,
            port_type="optical",
        )

    outline_layers = qg.utilities.get_outline_layers(LAYERS)
    return qg.utilities.outline(taper, outline_layers)


@gf.cell
def ebeam_fine_to_coarse(
    width1: float = 5.0,
    width2: float = 10.0,
    layer1: LayerSpec = (1, 0),
    layer2: LayerSpec = (2, 0),
) -> gf.Component:
    taper = gf.Component()
    outline_layers = qg.utilities.get_outline_layers(LAYERS)
    pos_tone = False
    for layer in outline_layers.keys():
        if qg.utilities.layers_equal(layer, layer1) or qg.utilities.layers_equal(
            layer, layer2
        ):
            pos_tone = True
            break
    if pos_tone:
        # positive tone
        t2 = gf.components.straight(
            length=outline_layers[tuple(layer2)],
            npoints=2,
            cross_section=cross_sections["ebeam"],
            width=None,
        )
        t1 = qg.geometries.hyper_taper(
            length=outline_layers[tuple(layer2)],
            wide_section=outline_layers[tuple(layer2)] * 2 + width2,
            narrow_section=width1,
            layer=layer1,
        )
        t1 = qg.utilities.outline(t1, outline_layers)
        t2_i = taper.add_ref(t2)
        t1_i = taper.add_ref(t1)
        t1_i.move(t1_i.ports["e2"].center, t2_i.ports["o1"].center)
        t1_i.movex(outline_layers[tuple(layer2)] / 2)
    else:
        t2 = gf.components.superconductors.optimal_step(
            start_width=0.7 * width1,
            end_width=width2,
            num_pts=100,
            anticrowding_factor=0.5,
            symmetric=True,
            layer=layer2,
        )
        t1 = qg.geometries.hyper_taper(
            length=t2.xsize / 2,
            wide_section=(width2 + width1) / 2,
            narrow_section=width1,
            layer=layer1,
        )
        t2_i = taper.add_ref(t2)
        t1_i = taper.add_ref(t1)
        t1_i.move(t1_i.ports["e1"].center, t2_i.ports["e1"].center)

    for n, port in enumerate(
        [t1_i.ports["e1"], t2_i.ports["o2" if pos_tone else "e2"]]
    ):
        taper.add_port(
            name=f"e{n}",
            center=port.center,
            orientation=port.orientation,
            width=port.width,
            layer=layer1 if n == 0 else layer2,
            port_type="optical",
        )
    return taper


bend_euler = partial(
    gf.components.bends.bend_euler, cross_section=cross_sections["ebeam"]
)
straight = partial(gf.components.straight, cross_section=cross_sections["ebeam"])
