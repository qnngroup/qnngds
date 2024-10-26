"""Tests contains common test structures for following/characterizing a
fabrication process and its effect on the materials."""

from phidl import Device
import phidl.geometry as pg
from typing import List, Union


def alignment_mark(layers: List[int] = [1, 2, 3, 4]) -> Device:
    """Creates an alignment mark for each photolithography.

    Args:
        layers (List[int]): An array of layers.

    Returns:
        Device: A device containing the alignment marks on each layer.
    """

    def create_marker(layer1, layer2):

        MARK = Device()

        # central part with cross

        CROSS = Device("CROSS")
        cross = CROSS << pg.union(pg.cross(length=190, width=20), layer=layer1)
        rect = pg.rectangle((65, 65), layer=layer2)
        window = CROSS.add_array(rect, 2, 2, (125, 125))
        window.move(window.center, cross.center)
        MARK << CROSS.flatten()

        # combs
        def create_comb(pitch1=500, pitch2=100, layer1=1, layer2=2):

            COMB = Device()

            # middle comb (made of layer1), pitch = 10
            rect1 = pg.rectangle((5, 30), layer=layer1)
            middle_comb = COMB.add_array(rect1, 21, 1, spacing=(10, 0))
            middle_comb.move(COMB.center, (0, 0))

            # top and bottom combs (made of layer2), pitchs = 10+pitch1, 10+pitch2
            rect2 = pg.rectangle((5, 30), layer=layer2)
            top_comb = COMB.add_array(rect2, 21, 1, spacing=(10 + pitch1 / 1000, 0))
            top_comb.move(
                top_comb.center, (middle_comb.center[0], middle_comb.center[1] + 30)
            )
            top_text = COMB.add_ref(pg.text(f"{pitch1}NM", size=10, layer=layer2))
            top_text.move(top_text.center, (140, 30))

            bottom_comb = COMB.add_array(rect2, 21, 1, spacing=(10 + pitch2 / 1000, 0))
            bottom_comb.move(
                bottom_comb.center, (middle_comb.center[0], middle_comb.center[1] - 30)
            )
            bottom_text = COMB.add_ref(pg.text(f"{pitch2}NM", size=10, layer=layer2))
            bottom_text.move(bottom_text.center, (140, -30))

            # additional markers (made of layer1), for clarity
            rect1a = pg.rectangle((5, 20), layer=layer1)
            marksa = COMB.add_array(rect1a, 3, 2, spacing=(100, 110))
            marksa.move(marksa.center, middle_comb.center)

            rect1b = pg.rectangle((5, 10), layer=layer1)
            marksb = COMB.add_array(rect1b, 2, 2, spacing=(100, 100))
            marksb.move(marksb.center, middle_comb.center)

            return COMB

        VERNIER = Device("VERNIER(500, 200, 100, 50)")
        comb51 = create_comb(pitch1=500, pitch2=100, layer1=layer1, layer2=layer2)

        top = VERNIER.add_ref(comb51)
        top.move((0, 0), (0, 200))

        left = VERNIER.add_ref(comb51)
        left.rotate(90)
        left.move((0, 0), (-200, 0))

        comb205 = create_comb(pitch1=200, pitch2=50, layer1=layer1, layer2=layer2)

        bottom = VERNIER.add_ref(comb205)
        bottom.rotate(180)
        bottom.move((0, 0), (0, -200))

        right = VERNIER.add_ref(comb205)
        right.rotate(-90)
        right.move((0, 0), (200, 0))
        MARK << VERNIER.flatten()

        MARK.move(MARK.center, (0, 0))

        # text
        TEXT = Device(f"TEXT({layer2} ON {layer1})")
        text1 = TEXT << pg.text(str(layer2), size=50, layer={layer1, layer2})
        text1.move(text1.center, (220, 200))
        text2 = TEXT << pg.text(f"{layer2} ON {layer1}", size=10, layer=layer2)
        text2.move(text2.center, (220, 240))
        MARK << TEXT.flatten()

        MARK.name = f"ALIGN {layer2} ON {layer1}"
        return MARK

    ALIGN = Device("ALIGN ")
    markers_pitch = 600
    for i, layer1 in enumerate(layers):
        n = len(layers) - i - 1
        if n != 0:
            for j, layer2 in enumerate(layers[-n:]):
                MARK = create_marker(layer1, layer2)
                MARK.move((j * markers_pitch, i * markers_pitch))
                ALIGN << MARK
            text = pg.text(str(layer1), size=160, layer=layer1)
            text.name = f"TEXT({str(layer1)})"
            text.move(text.center, (-340, i * markers_pitch))
            ALIGN << text

    num_layers = len(layers)
    offset = -(num_layers - 2) * markers_pitch / 2
    ALIGN.move((0, 0), (offset, offset))
    return ALIGN


def resolution_test(
    resolutions: List[float] = [0.8, 1, 1.2, 1.4, 1.6, 1.8, 2.0],
    inverted: Union[bool, float] = False,
    layer: int = 1,
) -> Device:
    """Creates test structures for determining a process resolution.

    Args:
        resolutions (List[float]): List of resolutions (in µm) to be tested.
        inverted (Union[bool, float]): If True, invert the device. If float, outline the device by this width.
        layer (int): Layer to put the device on.

    Returns:
        Device: The test structures, in the specified layer.
    """

    def create_3L(res=1):

        LLL = Device()

        def create_L(w, spacing):

            L = Device()

            bar = pg.rectangle((min(100 * w, 100), w))
            bars = Device()
            bars.add_array(bar, 1, 5, spacing=(0, spacing))
            v_bars = L << bars
            h_bars = L << bars
            h_bars.rotate(90)

            L.align("all", "xmin")
            L.move((L.xmin, L.ymin), (0, 0))
            return L

        grid_spacing = (13 * res, 13 * res)

        space = [0.8, 1, 1.2]
        for i, percent in enumerate(space):
            lll = LLL << create_L(percent * res, 2 * res)
            lll.move([i * space for space in grid_spacing])

        text = LLL << pg.text(str(res), size=20)
        text.move(
            text.get_bounding_box()[0], [(i + 1) * space for space in grid_spacing]
        )

        LLL.flatten(single_layer=layer)
        LLL.name = f"3L({space} x {res})"
        return LLL

    def create_waffle(res=1):

        WAFFLE = Device()
        W = pg.rectangle(size=(res * 80, res * 80))

        pattern = [(res * x, res * 80) for x in [2, 1, 1, 2, 3, 5, 8, 13, 21, 15]]
        WOut = pg.gridsweep(
            function=pg.rectangle, param_x={"size": pattern}, param_y={}, spacing=res
        )

        WOut.move(WOut.center, W.center)
        W1 = pg.boolean(W, WOut, "A-B")

        WOut.rotate(90, center=WOut.center)
        W2 = pg.boolean(W, WOut, "A-B")

        WAFFLE << W1
        WAFFLE << W2
        text = WAFFLE << pg.text(str(res), size=20)
        text.move(
            (text.get_bounding_box()[0][0], text.get_bounding_box()[1][1]),
            (2 * res, -2 * res),
        )

        WAFFLE.flatten(single_layer=layer)
        WAFFLE.name = f"WAFFLE({res})"
        return WAFFLE

    RES_TEST1 = pg.gridsweep(
        function=create_3L,
        param_x={"res": resolutions},
        param_y={},
        spacing=10,
        align_y="ymin",
        label_layer=None,
    )
    RES_TEST1.name = "3Ls"
    RES_TEST2 = pg.gridsweep(
        function=create_waffle,
        param_x={"res": resolutions},
        param_y={},
        spacing=10,
        align_y="ymax",
        label_layer=None,
    )
    RES_TEST2.name = "WAFFLES"
    RES_TEST = pg.grid(
        device_list=[[RES_TEST1], [RES_TEST2]],
        spacing=20,
        align_x="xmin",
    )

    if inverted:
        if inverted == True:
            RES_TEST = pg.invert(RES_TEST, border=5, precision=0.0000001, layer=layer)
        else:
            RES_TEST = pg.outline(RES_TEST, inverted, layer=layer)
        res_test_name = "RESOLUTION TEST INVERTED "
    else:
        res_test_name = "RESOLUTION TEST "

    RES_TEST.move(RES_TEST.center, (0, 0))
    RES_TEST.name = res_test_name
    return RES_TEST


def vdp(l: float = 400, w: float = 40, layer: int = 1) -> Device:
    """Creates a Van der Pauw (VDP) device with specified dimensions.

    Args:
        l (float): Length of the VDP device, overall maximum dimension, in µm.
        w (float): Width of the contact points (width of the ports), in µm.
        layer (int): Layer to put the device on.

    Returns:
        Device: VDP device object.
    """
    VDP = pg.Device("VAN DER PAUW")

    xpts = [-w / 2, w / 2, l / 2, l / 2, w / 2, -w / 2, -l / 2, -l / 2]
    ypts = [l / 2, l / 2, w / 2, -w / 2, -l / 2, -l / 2, -w / 2, w / 2]

    polygon = pg.polygon_ports(xpts=xpts, ypts=ypts, layer=layer)
    VDP << polygon
    VDP.flatten()

    VDP.add_port(port=polygon.ports["1"], name="N1")
    VDP.add_port(port=polygon.ports["3"], name="E1")
    VDP.add_port(port=polygon.ports["5"], name="S1")
    VDP.add_port(port=polygon.ports["7"], name="W1")

    return VDP
