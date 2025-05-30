import phidl.geometry as pg
import numpy as np
import scipy.constants as c


def transmission_line_resonator(
    tl_width,
    tl_length,
    meander_width,
    meander_e_eff,
    res_freq,
    turn_radius,
    meander_gap=1,
    area_length=100,
    layer=0,
    layer_metal=1,
    cpw=False,
    bounding_box=False,
    box_buffer=50,
    box_layer=200,
    overlap=0,
    layer_nb=2,
    meandered=True,
    final_cpw=True,
):
    """Builds a resonator in the middle of two transmission lines, returned as
    pg.Device.

    tl_width: transmission line width [um]
    tl_length: length of each transmission line [um]
    meander_width: width of the resonator [um]
    meander_e_eff: effective permittivity of the resonator at the given width (and gap)
    res_freq: target resonant frequency [Hz]
    turn_radius: turn radius of resonator meander [um]
    tl_gap: gap of the transmission line
    meander_gap: gap of the resonator
    area_length: distance to traverse resonator meander before turning [um]
    layer: GDS layer to write device
    cpw: whether device is CPW architecture or microstrip
    bounding_box: whether to draw a bounding box layer
    """
    print(f"overlap: {overlap} width: {meander_width}")
    tl_device = transmission_line(
        tl_width, meander_width, tl_length, gap=meander_gap, layer=layer
    )
    if meandered:
        res_device, res_area_height = resonator(
            meander_e_eff,
            res_freq,
            meander_width,
            turn_radius,
            area_length,
            layer=layer,
            cpw=cpw,
            gap=meander_gap,
        )

        total_length = tl_length * 2 + res_area_height
        print("Total height of meander: " + str(total_length))
    else:
        res_device = straight_resonator(
            meander_e_eff,
            res_freq,
            meander_width,
            layer=layer,
            cpw=cpw,
            gap=meander_gap,
        )

    device = pg.Device()
    tl_1 = device << tl_device
    tl_1.rotate(180)
    res_ref = device << res_device
    res_ref.connect(res_ref.ports["top"], tl_1.ports["narrow"])
    tl_2 = device << tl_device
    tl_2.rotate(0)
    tl_2.connect(tl_2.ports["narrow"], res_ref.ports["bottom"])

    device.add_port("top", port=tl_1.ports["wide"])
    device.add_port("bottom", port=tl_2.ports["wide"])

    pad_ref = device << pads(
        contact_width=tl_width, layer_sc=layer, layer_metal=layer_metal
    )
    pad_ref.connect(pad_ref.ports["connect"], device.ports["bottom"])

    if final_cpw:
        sc_polys = pg.extract(device, layers=[layer])
        sc_polys.add_port(
            "gnd", midpoint=(0, sc_polys.ymin), width=tl_width, orientation=-90
        )
        sc = pg.kl_outline(sc_polys, distance=meander_gap, open_ports=True, layer=layer)
        other_polys = pg.extract(device, layers=[layer_metal, layer_nb, box_layer])
        device = pg.Device()
        device << sc
        device << other_polys

    if bounding_box:
        # makes lower bound extra high so that it goes to ground
        tl_box = pg.bbox(
            np.add(
                device.bbox, [[-box_buffer / 2, 5], [box_buffer / 2, box_buffer / 2]]
            ),
            layer=box_layer,
        )
        device << tl_box

    label = f"w{meander_width:1.1f}\nf{res_freq/1e9:3.1f}"
    device_label = pg.text(label, size=100, layer=box_layer, justify="center")
    floor_x = device.xmin - 200
    floor_y = device.ymin
    label_ref = device << device_label
    label_ref.xmin = floor_x - 200
    label_ref.ymin = floor_y
    label_ref.move((0, 50))

    return device


def optimal_90deg_as_taper(narrow_width, port_offset=0, layer=0):
    device = pg.Device()
    turn = pg.optimal_90deg(narrow_width / 2, layer=layer)
    turn_left = device << turn
    turn_right = device << turn
    turn_right.mirror()

    device.add_port(
        "wide",
        midpoint=(0, port_offset),
        width=(device.xmax - device.xmin),
        orientation=-90,
    )
    device.add_port(
        "narrow", midpoint=(0, device.ymax), width=narrow_width, orientation=90
    )

    return device


def optimal_step_taper(width1, width2, layer=0):
    device = pg.Device()
    taper_half = pg.optimal_step(width1 / 2, width2 / 2, layer=layer)
    left = device << taper_half
    right = device << taper_half
    right.mirror((1, 0), (0, 0))

    device.add_port(1, (device.xmin, 0), width1, orientation=180)
    device.add_port(2, (device.xmax, 0), width2, orientation=0)

    return device


def ic_device(
    width,
    length,
    gap=0,
    layer=0,
    layer_metal=1,
    cpw=False,
    bounding_box=False,
    box_buffer=50,
    box_layer=200,
    shield=False,
    overlap=None,
    layer_nb=2,
    pad_size=150,
    layer_cover=300,
    final_cpw=True,
    via_layer=105,
    layer_eb=109,
):
    """Builds a short, straight wire for measuring Ic, returned as pg.Device.

    width: wire line width [um]
    length: length of each wire [um]
    gap: gap of the wire
    layer: GDS layer to write device
    cpw: whether device is CPW architecture or microstrip
    bounding_box: whether to draw a bounding box layer
    """
    device_cover = pg.Device()
    device = pg.Device()

    line = pg.rectangle((length, width), layer=layer)
    line.center = [0, 0]
    line.add_port("top", midpoint=(-length / 2, 0), orientation=180, width=width)
    line.add_port("bottom", midpoint=(length / 2, 0), orientation=0, width=width)

    optimal_width = 0.1

    taper_init = optimal_step_taper(width, width * (1 + optimal_width), layer=layer)
    taper = optimal_90deg_as_taper(
        width * (1 + optimal_width),
        port_offset=width * (1 + optimal_width) / 2,
        layer=layer,
    )
    taper_height = (taper.ymax - taper.ymin) + (taper_init.xmax - taper_init.xmin)

    print(
        f"10% taper length: {taper_init.xmax - taper_init.xmin:0.1f} \n wrt width: {(taper_init.xmax - taper_init.xmin)/width:0.1f}"
    )
    # hyper_taper(length=5, wide_section=150, narrow_section=width, layer=layer, cpw=cpw, gap=gap)
    line_ref = device << line
    line_ref.rotate(-90)
    ref_tinit1 = device << taper_init
    ref_tinit1.rotate(-90)
    ref_tinit1.connect(ref_tinit1.ports[1], line_ref.ports["top"])
    ref_t1 = device << taper
    ref_t1.connect(ref_t1.ports["narrow"], ref_tinit1.ports[2])
    ref_tinit2 = device << taper_init
    ref_tinit2.rotate(90)
    ref_tinit2.connect(ref_tinit2.ports[1], line_ref.ports["bottom"])
    ref_t2 = device << taper
    ref_t2.connect(ref_t2.ports["narrow"], ref_tinit2.ports[2])
    pad_ref = device << pads(
        contact_width=150,
        contact_length=150,
        cpw=cpw,
        gap=gap,
        layer_sc=layer,
        layer_metal=layer_metal,
    )
    pad_ref.connect(pad_ref.ports["connect"], ref_t1.ports["wide"])

    if shield:
        cover = pg.rectangle(
            (width - 2 * overlap, length + 2 * taper_height), layer=301
        )
        cover.center = line_ref.center

        optical_carveout = pg.rectangle(cover.size + (2 * width, 0), layer=box_layer)
        op_ref = device << optical_carveout
        op_ref.center = line_ref.center

        ebeam_nb = pg.rectangle(
            (6 * width, length + 2 * taper_height - width), layer=layer_eb
        )
        ebeam_nb.center = line_ref.center
        final_ebeam_nb = pg.kl_boolean(ebeam_nb, cover, "A-B", layer=layer_eb)
        ebeam_ref = device << final_ebeam_nb

        oxide_cover = pg.rectangle(ebeam_ref.size + (10, 10), layer=105)
        ox_ref = device << oxide_cover
        ox_ref.center = line_ref.center

        open_pad = pg.rectangle((250, 210), layer=box_layer)
        open_pad_ref = device << open_pad
        open_pad_ref.center = pad_ref.center
        open_pad_ref.ymin = pad_ref.ymin - 10

    if final_cpw:
        sc_polys = pg.extract(device, layers=[layer])
        sc_polys.add_port(
            "gnd",
            midpoint=(0, sc_polys.ymin),
            width=sc_polys.xmax - sc_polys.xmin,
            orientation=-90,
        )
        shape_fix = pg.rectangle((sc_polys.xmax - sc_polys.xmin, 20))
        shape_fix.center = sc_polys.center
        shape_fix.ymax = sc_polys.ymin + width / 2 + 0.1 * width / 2

        sc = pg.kl_outline(sc_polys, distance=gap, open_ports=True, layer=layer)
        sc = pg.kl_boolean(sc, shape_fix, "A-B", layer=layer)
        other_polys = pg.extract(
            device, layers=[layer_metal, layer_nb, box_layer, via_layer, layer_eb]
        )
        device = pg.Device()
        device << sc

        device << other_polys

    """if bounding_box:
        # makes lower bound extra high so that it goes to ground
        tl_box = pg.bbox(np.add(device.bbox, [[-box_buffer/2, box_buffer/2],[box_buffer/2, box_buffer/2]]), layer=box_layer)
        device << tl_box"""

    if overlap is None:
        label = f"Inf\nw{width:1.0f}"
    elif overlap == width / 2:
        label = f"All\nw{width:1.0f}"
    else:
        label = f"o{overlap/0.04:1.0f}\nw{width:1.0f}"
    device_label = pg.text(label, size=200, layer=box_layer, justify="left")
    floor_x = device.xmin
    floor_y = device.ymin
    label_ref = device << device_label
    label_ref.xmin = floor_x - 550
    label_ref.ymin = floor_y
    label_ref.move((0, 50))

    return device


def tl_only(
    width,
    length,
    layer=0,
    layer_metal=1,
    cpw=False,
    gap=0,
    bounding_box=False,
    box_buffer=50,
    box_layer=200,
):
    line = pg.rectangle((length, width), layer=layer)
    line.center = [0, 0]
    line.add_port("left", midpoint=(-length / 2, 0), orientation=180, width=width)
    line.add_port("right", midpoint=(length / 2, 0), orientation=0, width=width)
    if cpw:
        line = pg.kl_outline(line, distance=gap, open_ports=True, layer=layer)

    device = pg.Device()
    tl = device << line.rotate(90)
    # tl_d.rotate(0)
    pad_ref = device << pads(
        contact_width=width, cpw=cpw, gap=gap, layer_sc=layer, layer_metal=layer_metal
    )
    pad_ref.connect(pad_ref.ports["connect"], tl.ports["right"])

    if bounding_box:
        # makes lower bound extra high so that it goes to ground
        tl_box = pg.bbox(
            np.add(
                device.bbox,
                [[-box_buffer / 2, box_buffer / 2], [box_buffer / 2, box_buffer / 2]],
            ),
            layer=box_layer,
        )
        device << tl_box

    return device


def pads(
    contact_width=300,
    extra_space=0.1,
    layer_sc=0,
    layer_metal=1,
    cpw=False,
    gap=0,
    contact_length=300,
):
    """Builds a bilayer contact pad, returned as pg.Device.

    contact_width: size of top contact layer [um]
    extra_space: subtracted space from upper contact layer to surround contact pad [um]
    layer_sc: GDS layer to write lower layer
    layer_metal: GDS layer to write contact layer
    """
    pad = pg.Device()
    sc_ref = pad << pg.compass(size=(contact_width, contact_length), layer=layer_sc)
    pad.add_port("connect", port=sc_ref.ports["S"])
    pad << pg.compass(
        size=(contact_width - extra_space, contact_length - extra_space),
        layer=layer_metal,
    )

    return pad


def pinhole_test(
    size=400,
    x_overlap=100,
    layer_sc=0,
    layer_metal=1,
    cpw=False,
    gap=0,
    bounding_box=True,
    box_layer=200,
    box_buffer=50,
):
    test = pg.Device()
    sc_pad = pg.compass(size=(size, size), layer=layer_sc)
    if not cpw:
        sc_ref = test << sc_pad
    else:
        sc_ref = test << pg.kl_outline(sc_pad, distance=gap, layer=layer_sc)
    nb_ref = test << pg.compass(size=(size, size), layer=layer_metal)
    sc_ref.center = [0, 0]
    nb_ref.center = [-size + x_overlap, 0]

    text = pg.text(f"o{x_overlap*size} um2", size=100, layer=layer_metal)
    ref = test << text
    ref.ymin = nb_ref.ymax + 20
    ref.xmin = sc_ref.xmin

    if bounding_box:
        tl_box = pg.bbox(
            np.add(
                test.bbox,
                [[-box_buffer / 2, -box_buffer / 2], [box_buffer / 2, box_buffer / 2]],
            ),
            layer=box_layer,
        )
        test << tl_box

    return test


def transmission_line(
    width1, width2, length, layer=0, cpw=False, gap=0, nw_gap=0, taper_gap=0
):
    """Builds a transmission line smoothly tapered to narrower contact,
    returned as pg.Device.

    width1: width of transmission line [um]
    width2: width of narrow contact [um]
    length: length of wide part of transmission line [um]
    layer: GDS layer to write device
    """
    tl = pg.Device()
    line = pg.rectangle((length, width1), layer=layer)
    line.center = [0, 0]
    line.add_port("left", midpoint=(-length / 2, 0), orientation=180, width=width1)
    line.add_port("right", midpoint=(length / 2, 0), orientation=0, width=width1)

    ref = tl << line.rotate(90)
    taper_dev = optimal_90deg_as_taper(width2, port_offset=width2 / 2, layer=layer)
    taper = tl << taper_dev

    taper.connect(ref.ports["left"], taper.ports["wide"])

    tl.add_port("wide", port=ref.ports["right"])
    tl.add_port("narrow", port=taper.ports["narrow"])
    tl.add_port("between", port=taper.ports["wide"])

    return tl


def resonator(
    e_eff, res_freq, width, turn_radius, area_length, layer=0, cpw=False, gap=0
):
    """Builds a resonator at a given resonant frequency, returned as pg.Device
    (meandering)

    e_eff: effective permittivity of resonator at given width (and gap)
    res_freq: target resonant frequency [Hz]
    width: width of resonator [um]
    turn_radius: turn radius of meander [um]
    area_length: distance to traverse before turn [um]
    layer: GDS layer to write device
    cpw: whether cpw or microstrip
    gap: gap of resonator [um]
    """
    res_length = compute_res_wavelength(e_eff, res_freq) / 2
    print("lambda/2: " + str(res_length))
    return meander(res_length, width, turn_radius, area_length, layer, cpw, gap)


def straight_resonator(e_eff, res_freq, width, layer=0, cpw=False, gap=0):
    """Builds a straight resonator at a given resonant frequency, returned as
    pg.Device (not meandered)

    e_eff: effective permittivity of resonator at given width (and gap)
    res_freq: target resonant frequency [Hz]
    width: width of resonator [um]
    turn_radius: turn radius of meander [um]
    area_length: distance to traverse before turn [um]
    layer: GDS layer to write device
    cpw: whether cpw or microstrip
    gap: gap of resonator [um]
    """
    res_length = compute_res_wavelength(e_eff, res_freq) / 2
    print("lambda/2: " + str(res_length))
    device = pg.rectangle((res_length, width), layer=layer)
    device.center = [0, 0]
    device.add_port("top", midpoint=(res_length / 2, 0), width=width, orientation=0)
    device.add_port(
        "bottom", midpoint=(-res_length / 2, 0), width=width, orientation=180
    )
    if not cpw:
        return device
    else:
        return pg.kl_outline(device, distance=gap, open_ports=True, layer=layer)


def compute_veff(e_eff):
    """Computes effective light speed from effective permittivity."""
    return c.c / np.sqrt(e_eff)


def compute_res_wavelength(e_eff, res_freq):
    """Computes resonant wavelength from effective permittivity, resonant
    frequency."""
    v = compute_veff(e_eff)
    return v / res_freq * 1e6


def meander(
    total_length,
    width,
    turn_radius,
    area_length,
    layer=0,
    cpw=False,
    gap=0,
    tolerance=1,
):
    """Defines a uniform-width meander of a given total length that fits into a
    given area width.

    returns PHIDL device and its area length

    total_length: total desired meander length
    width: width of meander
    turn_radius: radius of arcs at 180 degree turns
    area_length: maximum distance for meander to traverse in length
    layer: layer of device
    cpw: whether to make CPW architecture
    gap: gap (if CPW)
    tolerance: maximum allowed difference between desired total_length and actual length
    """
    gap = 0
    odd_turn = pg.arc(
        width=width,
        radius=turn_radius,
        theta=180,
        start_angle=-90,
        layer=layer,
        angle_resolution=0.5,
    )
    even_turn = pg.arc(
        width=width,
        radius=turn_radius,
        theta=180,
        start_angle=90,
        layer=layer,
        angle_resolution=0.5,
    )
    first_attach = pg.arc(
        width=width,
        radius=turn_radius,
        theta=-90,
        start_angle=-90,
        layer=layer,
        angle_resolution=0.5,
    )
    last_attach_odd = pg.arc(
        width=width,
        radius=turn_radius,
        theta=-90,
        start_angle=90,
        layer=layer,
        angle_resolution=0.5,
    )
    last_attach_even = pg.arc(
        width=width,
        radius=turn_radius,
        theta=90,
        start_angle=90,
        layer=layer,
        angle_resolution=0.5,
    )
    """if cpw:
        odd_turn = pg.kl_outline(odd_turn, gap, open_ports=True, layer=layer)
        even_turn = pg.kl_outline(even_turn, gap, open_ports=True, layer=layer)
        first_attach = pg.kl_outline(first_attach, gap, open_ports=True, layer=layer)
        last_attach_odd = pg.kl_outline(last_attach_odd, gap, open_ports=True, layer=layer)
        last_attach_even = pg.kl_outline(last_attach_even, gap, open_ports=True, layer=layer)"""

    num_lines = int(
        (total_length - np.pi * turn_radius) / (area_length + np.pi * turn_radius) - 1
    )
    resulting_length = (num_lines + 1) * (
        area_length + np.pi * turn_radius
    ) + np.pi * turn_radius

    if abs(resulting_length - total_length) > tolerance:
        change_lines = (total_length - resulting_length) / (num_lines + 1)
        area_length += change_lines
        # num_lines = int((total_length - np.pi*turn_radius)/(area_length + np.pi*turn_radius) - 1)
        resulting_length = (num_lines + 1) * (
            area_length + np.pi * turn_radius
        ) + np.pi * turn_radius

    # print('num_lines: '+str(num_lines))
    print("actual length: " + str(resulting_length))

    if abs(resulting_length - total_length) > tolerance:
        print("WARNING: diff from spec is " + str(resulting_length - total_length))

    line = pg.rectangle(size=(area_length, width), layer=layer)
    line.center = [0, 0]
    line.add_port("left", midpoint=(-area_length / 2, 0), orientation=180, width=width)
    line.add_port("right", midpoint=(area_length / 2, 0), orientation=0, width=width)

    half_line = pg.rectangle(size=(area_length / 2, width), layer=layer)
    half_line.center = [0, 0]
    half_line.add_port(
        "left", midpoint=(-area_length / 4, 0), orientation=180, width=width
    )
    half_line.add_port(
        "right", midpoint=(area_length / 4, 0), orientation=0, width=width
    )

    device = pg.Device()
    # first (and last) line is special case -- accounted for in num_lines computation
    attach_1 = device << first_attach
    half_1 = device << half_line
    half_1.connect(half_1.ports["left"], attach_1.ports[1])

    refs = [device << even_turn]
    refs[-1].connect(refs[-1].ports[2], half_1.ports["right"])
    for i in range(num_lines):
        if i % 2 == 0:
            refs.append(device << line)
            refs[-1].connect(refs[-1].ports["right"], refs[-2].ports[1], overlap=-gap)
            refs.append(device << even_turn)
            refs[-1].connect(refs[-1].ports[1], refs[-2].ports["left"], overlap=-gap)
        else:
            refs.append(device << line)
            refs[-1].connect(refs[-1].ports["left"], refs[-2].ports[2], overlap=-gap)
            refs.append(device << odd_turn)
            refs[-1].connect(refs[-1].ports[2], refs[-2].ports["right"], overlap=-gap)
    # last line special case
    half_2 = device << half_line
    if num_lines % 2 == 0:
        half_2.connect(half_2.ports["right"], refs[-1].ports[1], overlap=-gap)
        attach_2 = device << last_attach_even
        attach_2.connect(attach_2.ports[1], half_2.ports["left"], overlap=-gap)
    else:
        half_2.connect(half_2.ports["left"], refs[-1].ports[2])
        attach_2 = device << last_attach_odd
        attach_2.connect(attach_2.ports[1], half_2.ports["right"])

    area_length = num_lines * 2 * turn_radius + 4 * turn_radius

    device.add_port("top", port=attach_1.ports[2])
    device.add_port("bottom", port=attach_2.ports[2])

    return device, area_length


def ground_with_cutouts(width, height, device, cuts_layer=200, layer=0, text_layer=107):
    """Returns full ground cover pattern with cutouts for devices, as
    pg.Device.

    width: width of ground [um]
    height: height of ground [um]
    cutout_coords: center locations for cutouts, list of (x, y) [um]
    cutout_width: width of cutouts [um]
    cutout_height: height of cutouts [um]
    layer: GDS layer to write device
    """
    ground = pg.Device()
    ref = ground << pg.rectangle((width, height), layer=layer)
    ref.center = [0, 0]

    ground = pg.kl_boolean(
        ground, pg.extract(device, layers=[cuts_layer, text_layer]), "A-B", layer=layer
    )

    return ground
