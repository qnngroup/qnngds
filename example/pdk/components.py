import gdsfactory as gf

from gdsfactory.typings import LayerSpec
import qnngds as qg


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
    return taper


@gf.cell
def ebeam_fine_to_coarse(
    width1: float = 1.0,
    width2: float = 2.0,
    layer1: LayerSpec = (1, 0),
    layer2: LayerSpec = (2, 0),
) -> gf.Component:
    taper = gf.Component()
    ot = gf.components.superconductors.optimal_step(
        start_width=0.7 * width1,
        end_width=width2,
        num_pts=100,
        anticrowding_factor=0.5,
        symmetric=True,
        layer=layer2,
    )
    ot_i = taper.add_ref(ot)
    ht = qg.geometries.hyper_taper(
        length=ot.xsize / 2,
        wide_section=(width2 + width1) / 2,
        narrow_section=width1,
        layer=layer1,
    )
    ht_i = taper.add_ref(ht)
    ht_i.move(ht_i.ports["e1"].center, ot_i.ports["e1"].center)

    for n, port in enumerate([ht_i.ports["e1"], ot_i.ports["e2"]]):
        taper.add_port(
            name=f"e{n}",
            center=port.center,
            orientation=port.orientation,
            width=port.width,
            layer=layer1 if n == 0 else layer2,
            port_type="optical",
        )
    return taper


bend_euler = gf.components.bends.bend_euler
straight = gf.components.straight
