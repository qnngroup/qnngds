# -*- coding: utf-8 -*-
"""Created on Wed Nov 18 20:51:47 2020.

@author: omedeiro
"""


from __future__ import division, print_function, absolute_import
import numpy as np
from phidl import Device
import phidl.geometry as pg
import phidl.routing as pr
from phidl import quickplot as qp

# import colang as mc
import string
from datetime import datetime
import os
import sys
from time import sleep
from phidl.device_layout import _parse_layer, DeviceReference
import math
from argparse import Namespace

sys.path.append(r"Q:\qnngds")
import qnngds.utilities as qu


from phidl import set_quickplot_options

set_quickplot_options(show_ports=True, show_subports=True)


def outline(
    elements,
    distance=1,
    precision=1e-4,
    num_divisions=[1, 1],
    join="miter",
    tolerance=2,
    join_first=True,
    max_points=4000,
    layer=0,
    open_ports=-1,
    rotate_ports=False,
):
    """Creates an outline around all the polygons passed in the `elements`
    argument. `elements` may be a Device, Polygon, or list of Devices.

      Parameters
      ----------
      elements : Device(/Reference), list of Device(/Reference), or Polygon
          Polygons to outline or Device containing polygons to outline.
      distance : int or float
          Distance to offset polygons. Positive values expand, negative shrink.
      precision : float
          Desired precision for rounding vertex coordinates.
      num_divisions : array-like[2] of int
          The number of divisions with which the geometry is divided into
          multiple rectangular regions. This allows for each region to be
          processed sequentially, which is more computationally efficient.
      join : {'miter', 'bevel', 'round'}
          Type of join used to create the offset polygon.
      tolerance : int or float
          For miter joints, this number must be at least 2 and it represents the
          maximal distance in multiples of offset between new vertices and their
          original position before beveling to avoid spikes at acute joints. For
          round joints, it indicates the curvature resolution in number of
          points per full circle.
      join_first : bool
          Join all paths before offsetting to avoid unnecessary joins in
          adjacent polygon sides.
      max_points : int
          The maximum number of vertices within the resulting polygon.
      layer : int, array-like[2], or set
          Specific layer(s) to put polygon geometry on.
    open_ports : int or float
        Trims the outline at each port of the element. The value of open_port
        scales the length of the trim gemoetry (must be positive).
        Useful for positive tone layouts.
      Returns
      -------
      D : Device
          A Device containing the outlined polygon(s).
    """
    D = Device("outline")
    if type(elements) is not list:
        elements = [elements]
    for e in elements:
        if isinstance(e, Device):
            D.add_ref(e)
        else:
            D.add(e)
    gds_layer, gds_datatype = _parse_layer(layer)
    D_bloated = pg.offset(
        D,
        distance=distance,
        join_first=join_first,
        num_divisions=num_divisions,
        precision=precision,
        max_points=max_points,
        join=join,
        tolerance=tolerance,
        layer=layer,
    )
    Outline = pg.boolean(
        A=D_bloated,
        B=D,
        operation="A-B",
        num_divisions=num_divisions,
        max_points=max_points,
        precision=precision,
        layer=layer,
    )
    if open_ports >= 0:
        for i in e.ports:
            trim = pg.rectangle(
                size=(distance, e.ports[i].width + open_ports * distance)
            )

            trim.rotate(e.ports[i].orientation)
            trim.move(trim.center, destination=e.ports[i].midpoint)
            if rotate_ports:
                trim.movex(-np.cos(e.ports[i].orientation / 180 * np.pi) * distance / 2)
                trim.movey(-np.sin(e.ports[i].orientation / 180 * np.pi) * distance / 2)
            else:
                trim.movex(np.cos(e.ports[i].orientation / 180 * np.pi) * distance / 2)
                trim.movey(np.sin(e.ports[i].orientation / 180 * np.pi) * distance / 2)

            Outline = pg.boolean(
                A=Outline,
                B=trim,
                operation="A-B",
                num_divisions=num_divisions,
                max_points=max_points,
                precision=precision,
                layer=layer,
            )
        for i in e.ports:
            Outline.add_port(port=e.ports[i])
    return Outline


def nw_same_side(wire_width=0.2, wire_pitch=0.6, size=(22, 11), layer=1):
    """Create a two port nanowire meander with 1um ports extended 15um.

    Parameters
    ----------
    wire_width : FLOAT, optional
        MEANDER WIDTH. The default is 0.2.
    wire_pitch : FLOAT, optional
        MEANDER PITCH. The default is 0.6.
    size : TUPLE, optional
        (X,Y) MEANDER AREA DIMENSIONS. The default is (22,11).
    layer : INT, optional
        Layer for device to be created on. The default is 1.

    Returns
    -------
    wire : DEVICE
        PHIDL device object is returned.

    Example
    -------
    qp(om.nw_same_side())
    """

    wire = Device("wire")
    nw = pg.snspd(
        wire_width=wire_width,
        wire_pitch=wire_pitch,
        size=size,
        terminals_same_side=True,
        layer=layer,
    )
    NW = wire.add_ref(nw)

    extend = pg.straight(size=(1, 15))
    EXTEND = wire.add_ref(extend)
    EXTEND.rotate(-90).move(EXTEND.ports[1], destination=NW.ports[1]).movex(-5)

    EXTEND1 = wire.add_ref(extend)
    EXTEND1.rotate(-90).move(EXTEND1.ports[1], destination=NW.ports[2]).movex(-5)

    bump = pr.route_basic(
        NW.ports[1], EXTEND.ports[1], path_type="sine", width_type="sine"
    )
    wire.add_ref(bump)

    bump = pr.route_basic(
        NW.ports[2], EXTEND1.ports[1], path_type="sine", width_type="sine"
    )
    wire.add_ref(bump)
    wire.move(origin=NW.center, destination=(0, 0))
    wire.flatten(single_layer=layer)
    wire.add_port(
        name=1, midpoint=(wire.bbox[0][0], wire.bbox[1][1] - 1 / 2), orientation=180
    )
    wire.add_port(
        name=2, midpoint=(wire.bbox[0][0], -wire.bbox[1][1] + 1 / 2), orientation=180
    )

    return wire


def nw_same_side_port(wire_width=0.2, wire_pitch=0.6, size=(22, 11), layer=1):
    """Create a nanowire meander section coupled to two macroscopic ports for
    pad connection.

    Future: define destination as an imput. Make connection straight taper

    Parameters
    ----------
    wire_width : FLOAT, optional
        MEANDER WIDTH. The default is 0.2.
    wire_pitch : FLOAT, optional
        MEANDER PITCH. The default is 0.6.
    size : TUPLE, optional
        (X,Y) MEANDER AREA DIMENSIONS. The default is (22,11).
    layer : INT, optional
        Layer for device to be created on. The default is 1.

    Returns
    -------
    nwOut :  DEVICE
        PHIDL device object is returned.
    """

    device = Device("nw")
    WIRE = nw_same_side(
        wire_width=wire_width, wire_pitch=wire_pitch, size=size, layer=layer
    )
    WIRE.rotate(-90).move(origin=(0, 0), destination=(52.5, 52.2))
    wire = device.add_ref(WIRE)

    d = pads_adam_quad(layer=1)
    d.move(origin=d.center, destination=(0, 0))

    hTAPER = hyper_taper(length=50, wide_section=45, narrow_section=5, layer=0)
    htaper = device.add_ref(hTAPER)
    htaper.rotate(90).move(origin=htaper.ports[2], destination=d.ports["21"])
    ROUT = pr.route_basic(
        wire.ports[1], htaper.ports[1], width_type="straight", path_type="sine"
    )
    rout = device.add_ref(ROUT)

    htaper1 = device.add_ref(hTAPER)
    htaper1.rotate(90).move(origin=htaper1.ports[2], destination=d.ports["22"])
    ROUT = pr.route_basic(
        wire.ports[2], htaper1.ports[1], width_type="straight", path_type="sine"
    )
    rout = device.add_ref(ROUT)

    nwOut = pg.outline(device, distance=0.1, precision=1e-4, layer=0)
    trim = pg.rectangle(size=(150, 0.2))
    trim.move(origin=trim.center, destination=(nwOut.center[0], nwOut.bbox[1][1]))
    t = nwOut.add_ref(trim)
    nwOut = pg.boolean(nwOut, t, "A-B", precision=1e-4, layer=layer)
    nwOut.add_port(name="wide0", port=htaper.ports[2])
    nwOut.add_port(name="wide1", port=htaper1.ports[2])

    return nwOut


def nw_same_side_port_single(
    wire_width=0.2,
    wire_pitch=0.6,
    size=(22, 11),
    terminals_same_side=True,
    layer=1,
    portLoc1=(37.5, 131.25),
    portLoc2=(-52.5, 131.25),
    nwLoc=(0, 0),
):
    """Broken do not use..."""
    device = Device("nw")
    WIRE = nw_same_side(
        wire_width=wire_width,
        wire_pitch=wire_pitch,
        size=size,
        terminals_same_side=terminals_same_side,
        layer=layer,
    )
    WIRE.rotate(-90).move(origin=(0, 0), destination=nwLoc)
    wire = device.add_ref(WIRE)

    d = pads_adam_quad(layer=1)
    d.move(origin=d.center, destination=(0, 0))

    hTAPER = hyper_taper(length=50, wide_section=45, narrow_section=5, layer=0)
    htaper = device.add_ref(hTAPER)
    htaper.rotate(90).move(origin=htaper.ports[2], destination=d.ports["23"])
    ROUT = pr.route_basic(
        wire.ports[1], htaper.ports[1], width_type="straight", path_type="sine"
    )
    rout = device.add_ref(ROUT)

    hTAPER1 = hyper_taper(length=15, wide_section=15, narrow_section=5, layer=0)
    htaper1 = device.add_ref(hTAPER1)
    htaper1.rotate(90).move(
        origin=htaper1.ports[2], destination=[nwLoc[0] - 95, nwLoc[1] + 95]
    )
    ROUT = pr.route_basic(
        wire.ports[2], htaper1.ports[1], width_type="straight", path_type="sine"
    )
    rout = device.add_ref(ROUT)

    nwOut = pg.outline(device, distance=0.1, precision=1e-4, layer=0)
    trim = pg.rectangle(size=(55, 0.1))
    trim.move(
        origin=trim.center, destination=(htaper.center[0], htaper.bbox[1][1] + 0.05)
    )
    trim1 = pg.rectangle(size=(20, 0.1))
    trim1.move(
        origin=trim1.center, destination=(htaper1.center[0], htaper1.bbox[1][1] + 0.05)
    )

    t = nwOut.add_ref(trim)
    t1 = nwOut.add_ref(trim1)
    nwOut = pg.boolean(nwOut, t, "A-B", precision=1e-4, layer=layer)
    nwOut = pg.boolean(nwOut, t1, "A-B", precision=1e-4, layer=layer)
    nwOut.add_port(name="wide0", port=htaper.ports[2])
    nwOut.add_port(name="wide1", port=htaper1.ports[2])
    return nwOut


def heat_sameSidePort(
    wire_width=0.2,
    wire_pitch=0.6,
    size=(22, 11),
    layer=1,
    portLoc1=(37.5, 131.25),
    portLoc2=(-52.5, 131.25),
    nwLoc=(0, 0),
):
    """Filled nanowire meander with poits on same side. Used as heater for
    hTron devices.

    Parameters
    ----------
    wire_width : FLOAT, optional
        MEANDER WIDTH. The default is 0.2.
    wire_pitch : FLOAT, optional
        MEANDER PITCH. The default is 0.6.
    size : TUPLE, optional
        (X,Y) MEANDER AREA DIMENSIONS. The default is (22,11).
    layer : INT, optional
        Layer for device to be created on. The default is 1.

    portLoc1 : TUPLE, optional
        Location of port 1. The default is (37.5,131.25).
    portLoc2 : TUPLE, optional
        Location of port 2. The default is (-52.5,131.25).
    nwLoc : TUPLE, optional
        Location of center of nanowire. The default is (0,0).

    Returns
    -------
    device : DEVICE
        PHIDL device object is returned.
    """
    device = Device("nw")
    WIRE = nw_same_side(
        wire_width=wire_width, wire_pitch=wire_pitch, size=size, layer=layer
    )
    WIRE.rotate(-90).move(origin=(0, 0), destination=nwLoc)
    wire = device.add_ref(WIRE)

    PADc = pg.straight(size=(5, 5), layer=layer)
    PADc.move(origin=PADc.ports[2], destination=portLoc1)
    padc = device.add_ref(PADc)

    PADl = pg.straight(size=(5, 5), layer=layer)
    PADl.move(origin=PADl.ports[2], destination=portLoc2)
    padl = device.add_ref(PADl)

    r1 = pr.route_basic(
        wire.ports[1],
        PADc.ports[2],
        width_type="straight",
        path_type="sine",
        layer=layer,
    )
    device.add_ref(r1)
    r2 = pr.route_basic(
        wire.ports[2],
        PADl.ports[2],
        width_type="straight",
        path_type="sine",
        layer=layer,
    )
    device.add_ref(r2)

    return device


def alignment_marks(
    locations=((-3500, -3500), (3500, 3500), (-3500, 3500), (3500, -3500)),
    size=(200, 5),
    layer=1,
):
    """Create cross-style alignment marks.

    Parameters
    ----------
    locations : TUPLE, optional
        Tuple of (X,Y) locations. The default is ((-3500, -3500), (3500, 3500)).
    layer : INT, optional
        Layer for device to be created on. The default is 1.


    Returns
    -------
    marks : DEVICE
        PHIDL device object is returned.
    """
    marks = Device("Marks")
    alignMARK = pg.cross(size[0], size[1], layer=layer)

    for i in np.arange(0, len(locations), 1):
        alignMark = marks.add_ref(alignMARK)
        alignMark.move(origin=alignMark.center, destination=locations[i])

    marks = pg.union(marks, layer=layer)
    marks.flatten()
    return marks


def etch_square(layers=[1], size=(1500, 1500), location=(2500, 1000), outline=None):
    D = Device("etch_square")
    for l in layers:
        rec = pg.rectangle(size=size, layer=l)
        if outline:
            rec = pg.outline(rec, distance=outline, layer=l)
        r = D << rec
        r.move(origin=r.center, destination=location)
    return D


def optimal_taper(width=100.0, num_pts=15, length_adjust=3, layer=0):
    D = Device("optimal_taper")

    t1 = D << pg.optimal_90deg(width, num_pts, length_adjust)
    t2 = D << pg.optimal_90deg(width, num_pts, length_adjust)
    t2.mirror()
    t2.move(t2.ports[1], t1.ports[1])

    D.movex(-t1.ports[1].midpoint[0])
    D.movey(-width)
    D = pg.union(D, layer=layer)

    # wide port trim
    trim = pg.straight(size=(width, -2.5 * D.bbox[0][0]))
    trim.rotate(90)
    trim.move(trim.bbox[0], D.bbox[0])
    trim.movex(-0.005)
    trim.movey(-0.0001)
    A = pg.boolean(t1, trim, "A-B", layer=layer, precision=1e-9)
    B = pg.boolean(t2, trim, "A-B", layer=layer, precision=1e-9)

    # #top length trim
    trim2 = D << pg.straight(size=(width * 2, t1.ports[1].midpoint[1] - width * 4))
    trim2.connect(trim2.ports[1], t1.ports[1].rotate(180))
    A = pg.boolean(A, trim2, "A-B", layer=layer, precision=1e-9)
    B = pg.boolean(B, trim2, "A-B", layer=layer, precision=1e-9)

    # # width trim 1
    trim3 = A << pg.straight(size=(width / 2, t1.ports[1].midpoint[1] + 0.1))
    trim3.connect(trim3.ports[1], t1.ports[1].rotate(180))
    trim3.movex(-width / 2)
    A = pg.boolean(A, trim3, "A-B", layer=layer, precision=1e-9)

    # # width trim 2
    trim3 = B << pg.straight(size=(width / 2, t1.ports[1].midpoint[1] + 0.1))
    trim3.connect(trim3.ports[1], t1.ports[1].rotate(180))
    trim3.movex(width / 2)
    B = pg.boolean(B, trim3, "A-B", layer=layer, precision=1e-9)

    p = B.get_polygons()
    x1 = p[0][0, 0]

    A.movex(width / 2 + x1)
    B.movex(-width / 2 - x1)
    D = A
    D << B
    D = pg.union(D, layer=layer)

    D.add_port(name=1, midpoint=(0, width * 4), width=width, orientation=90)
    D.add_port(name=2, midpoint=(0, 0), width=D.bbox[0][0] * -2, orientation=-90)

    return D


def hyper_taper(length, wide_section, narrow_section, layer=0):
    """Hyperbolic taper (solid). Designed by colang.

    Parameters
    ----------
    length : FLOAT
        Length of taper.
    wide_section : FLOAT
        Wide width dimension.
    narrow_section : FLOAT
        Narrow width dimension.
    layer : INT, optional
        Layer for device to be created on. The default is 1.


    Returns
    -------
    HT :  DEVICE
        PHIDL device object is returned.
    """
    taper_length = length
    wide = wide_section
    zero = 0
    narrow = narrow_section
    x_list = np.arange(0, taper_length + 0.1, 0.1)
    x_list2 = np.arange(taper_length, -0.1, -0.1)
    pts = []

    a = np.arccosh(wide / narrow) / taper_length

    for x in x_list:
        pts.append((x, np.cosh(a * x) * narrow / 2))
    for y in x_list2:
        pts.append((y, -np.cosh(a * y) * narrow / 2))
        HT = Device("hyper_taper")
        hyper_taper = HT.add_polygon(pts, layer=2)
        HT.add_port(name=1, midpoint=[0, 0], width=narrow, orientation=180)
        HT.add_port(name=2, midpoint=[taper_length, 0], width=wide, orientation=0)
        HT.flatten(single_layer=layer)
    return HT


# def hyper_taper_outline(length=15, wide_section=80, narrow_section=.1, outline=0.5, layer=1):
#     """
#     Outlined hyper taper for etch process. Derived from colang's hyper taper

#     Parameters
#     ----------
#     length : FLOAT, optional
#         Length of taper. The default is 50.
#     wide_section : FLOAT, optional
#         Wide width dimension. The default is 30.
#     narrow_section : FLOAT, optional
#         Narrow width dimension. The default is 5.
#     outline : FLOAT, optional
#         Width of device outline. The default is 0.5.
#     layer : INT, optional
#         Layer for device to be created on. The default is 1.


#     Returns
#     -------
#     ht : DEVICE
#         PHIDL device object is returned.

#     """

#     ht = Device('ht')
#     hyper_import = hyper_taper(length, wide_section, narrow_section)
#     hyper_outline = pg.outline(hyper_import,distance=outline,layer=layer)
#     ht.add_ref(hyper_outline)

#     trim_left = pg.rectangle(size=(outline+.001,narrow_section+2*outline))
#     ht.add_ref(trim_left)
#     trim_left.move(destination=(-outline,-(narrow_section/2+outline)))
#     ht = pg.boolean(ht,trim_left,'A-B', precision=1e-6,layer=layer)

#     max_y_point = ht.bbox[1,1]
#     trim_right = pg.rectangle(size=(outline,2*max_y_point))
#     ht.add_ref(trim_right)
#     trim_right.move(destination=(length, -max_y_point))
#     ht = pg.boolean(ht,trim_right,'A-B', precision=1e-6,layer=layer)

#     ht.add_port(name = 1, midpoint = [.0015, 0],  width = narrow_section, orientation = 180)
#     ht.add_port(name = 2, midpoint = [length-.0015, 0],  width = wide_section, orientation = 0)
#     ht.flatten(single_layer = layer)

#     return ht


def straight_taper(width=2, length=10, t_length=10, t_width=100, outline=1, layer=1):
    S = Device("straight")

    s = pg.straight(size=(width, length))
    t = hyper_taper(t_length, t_width, width)
    t.rotate(90)
    t.move(origin=t.ports[1], destination=s.ports[1])
    S.add_ref([s, t])

    S.flatten(single_layer=layer)
    S.add_port(port=s.ports[2], name=1)
    return S


def snspd_vert(
    wire_width=0.2,
    wire_pitch=0.6,
    size=(6, 10),
    num_squares=None,
    terminals_same_side=False,
    extend=None,
    layer=0,
):

    D = Device("snspd_vert")
    S = pg.snspd(
        wire_width=wire_width,
        wire_pitch=wire_pitch,
        size=size,
        num_squares=num_squares,
        terminals_same_side=terminals_same_side,
        layer=layer,
    )
    s1 = D << S

    HP = pg.optimal_hairpin(
        width=wire_width, pitch=wire_pitch, length=size[0] / 2, layer=layer
    )
    h1 = D << HP
    h1.connect(h1.ports[1], S.references[0].ports["E"])
    h1.rotate(180, h1.ports[1])

    h2 = D << HP
    h2.connect(h2.ports[1], S.references[-1].ports["E"])
    h2.rotate(180, h2.ports[1])

    T = pg.optimal_90deg(width=wire_width, layer=layer)
    t1 = D << T
    T_width = t1.ports[2].midpoint[0]
    t1.connect(t1.ports[1], h1.ports[2])
    t1.movex(-T_width + wire_width / 2)

    t2 = D << T
    t2.connect(t2.ports[1], h2.ports[2])
    t2.movex(T_width - wire_width / 2)

    D = pg.union(D, layer=layer)
    D.flatten()
    if extend:
        E = pg.straight(size=(wire_width, extend), layer=layer)
        e1 = D << E
        e1.connect(e1.ports[1], t1.ports[2])
        e2 = D << E
        e2.connect(e2.ports[1], t2.ports[2])
        D = pg.union(D, layer=layer)
        D.add_port(name=1, port=e1.ports[2])
        D.add_port(name=2, port=e2.ports[2])
    else:
        D.add_port(name=1, port=t1.ports[2])
        D.add_port(name=2, port=t2.ports[2])

    D.info = S.info
    return D


def pad_taper(
    length=40,
    pad_width=250,
    pad_length=250,
    narrow_section=0.1,
    w_outline=5,
    n_outline=0.2,
    layer=1,
):
    """Create a pad with tapered connection.

    Parameters
    ----------
    length : TYPE, optional
        DESCRIPTION. The default is 15.
    pad_width : TYPE, optional
        DESCRIPTION. The default is 80.
    narrow_section : TYPE, optional
        DESCRIPTION. The default is .1.
    w_outline : TYPE, optional
        DESCRIPTION. The default is 5.
    n_outline : TYPE, optional
        DESCRIPTION. The default is 0.1.
    layer : TYPE, optional
        DESCRIPTION. The default is 1.

    Returns
    -------
    ht : TYPE
        DESCRIPTION.
    """
    I = Device("ht")
    hyper_wide1 = hyper_taper(
        length + w_outline, pad_width, narrow_section, layer=layer
    )
    pI = pg.rectangle(size=(pad_length, pad_width), layer=layer)
    pI.move(destination=(length + w_outline, -pad_width / 2))
    I.add_ref([hyper_wide1, pI])

    O = Device("ht")
    hyper_wide2 = hyper_taper(
        length, pad_width + w_outline * 2, narrow_section + n_outline * 2, layer=layer
    )
    pO = pg.rectangle(size=(pad_length + w_outline * 2, pad_width + w_outline * 2))
    pO.move(destination=(length, -(pad_width + w_outline * 2) / 2))
    O.add_ref([pO, hyper_wide2])

    ht = pg.boolean(O, I, "A-B", precision=1e-6, layer=layer)
    ht.add_port(port=hyper_wide1.ports[1], name=1)
    return ht


def pad_U(
    pad_width=250, pad_length=250, width=10, layer=1, port_yshift=0, port_width_add=0
):

    D = Device("C")
    C = pg.C(size=(pad_length, pad_width), width=width)
    D.add_ref(C)
    D.flatten(single_layer=layer)
    D.add_port(
        name=1,
        midpoint=(pad_length + port_yshift, pad_width / 2),
        width=pad_width + port_width_add,
        orientation=0,
    )
    return D


def pad_basic(base_size=(200, 200), port_size=10, taper_length=100, layer=1):
    """Creates a filled pad with port at narrow section.

    Parameters
    ----------
    base_size : TUPLE, optional
        (X,Y) dimensions of pad. The default is (200,200).
    port_size : FLOAT, optional
        Width of port. The default is 10.
    taper_length : FLOAT, optional
        Dimension of tapered section pad to port. The default is 100.
    layer : INT, optional
        Layer for device to be created on. The default is 1.


    Returns
    -------
    P : DEVICE
        PHIDL device object is returned.
    """
    P = Device("pad")

    base = pg.rectangle(size=base_size)
    taper = pg.taper(length=taper_length, width1=base_size[0], width2=port_size)
    taper.rotate(90)
    taper.move(destination=(base_size[0] / 2, base_size[1]))

    P.add_ref([base, taper])
    P.flatten(single_layer=layer)
    P.add_port(
        name=1,
        midpoint=(base_size[0] / 2, base_size[1] + taper_length),
        orientation=90,
        width=port_size,
    )
    P.add_port(name="center", midpoint=base.center, width=0.1, orientation=0)
    P.add_port(
        name="base",
        midpoint=(base_size[0] / 2, base_size[1]),
        width=port_size / 2,
        orientation=90,
    )

    return P


def pads_adam(trim=[True, True, True], layer=1):
    """Create three pads using adam's design Trim indicates if the pad should
    be open (connecting to a device on the same layer), or closed (connecting
    to device on a second layer).

    if only 1 pad is required use only one Trim specification

    Ports are added at each pad. Name: 1,2,3

    Parameters
    ----------
    trim : LIST, optional
        Trim indicates if the pad should be open (connecting to a device on the
        same layer), or closed (connecting to device on a second layer).
        List should be size 1-3 (for the number of desired pads) of T/F
        booleans.
        The default is [True,True,True].

    layer : INT, optional
        Layer for device to be created on. The default is 1.

    Returns
    -------
    OUT : DEVICE
        PHIDL device object is returned.

    Example
    -------
    qp(om.pads_adam())
    """
    threePad = Device("cell")

    base = pg.straight(size=(150, 250), layer=layer)
    post = pg.straight(size=(25, 25), layer=layer)

    b1 = threePad.add_ref(base)
    b2 = threePad.add_ref(base)
    b2.movex(170)
    b3 = threePad.add_ref(base)
    b3.movex(-170)

    p1 = threePad.add_ref(post)
    p1.move(origin=p1.center, destination=b1.center).movey(225)
    p2 = threePad.add_ref(post)
    p2.move(origin=p2.center, destination=p1.center).movex(90)
    p3 = threePad.add_ref(post)
    p3.move(origin=p3.center, destination=p1.center).movex(-90)

    r1 = pr.route_basic(
        b1.ports[1],
        p1.ports[2],
        path_type="straight",
        width_type="straight",
        num_path_pts=50,
        width1=25,
        layer=layer,
    )
    threePad.add_ref(r1)
    r2 = pr.route_basic(
        b2.ports[1],
        p2.ports[2],
        path_type="straight",
        width_type="straight",
        num_path_pts=50,
        width1=25,
        layer=layer,
    )
    threePad.add_ref(r2)
    r3 = pr.route_basic(
        b3.ports[1],
        p3.ports[2],
        path_type="straight",
        width_type="straight",
        num_path_pts=50,
        width1=25,
        layer=layer,
    )
    threePad.add_ref(r3)

    OUT = pg.outline(threePad, distance=5, precision=0.0001, layer=layer)

    for i in range(len(trim)):
        if trim[i] == True:
            trimpoly = pg.rectangle(size=(35, 5), layer=layer)
            t1 = OUT.add_ref(trimpoly)
            t1.move(origin=t1.center, destination=(-15 + 90 * i, 365))
            OUT = pg.boolean(OUT, t1, "A-B", precision=1e-4, layer=layer)
    OUT.add_port(name=1, midpoint=(-15, 360), width=25, orientation=90)
    OUT.add_port(name=2, midpoint=(75, 360), width=25, orientation=90)
    OUT.add_port(name=3, midpoint=(165, 360), width=25, orientation=90)
    return OUT


def pads_adam_quad(
    trim=(
        (True, True, True),
        (True, True, True),
        (True, True, True),
        (True, True, True),
    ),
    layer=1,
):
    """pads_adam_quad takes three pads and aranges them in a square.

    Trim is a tuple of 4x3 T/F booleans for deciding what pads should be open
    or closed.

    Ports are added at each pad. Name: 01,02,03,11,12,13,21,...33


    Parameters
    ----------
    trim : TUPLE, optional
        Trim indicates if the pad should be open (connecting to a device on the
        same layer), or closed (connecting to device on a second layer).
        List should be size 1-3 (for the number of desired pads) of T/F booleans.
       The default is ((True,True,True),(True,True,True),(True,True,True),(True,True,True)).
    layer : INT, optional
        Layer for device to be created on. The default is 1.

    Returns
    -------
    quadPad : DEVICE
        PHIDL device object is returned.
    """

    quadPad = Device("quad")
    for i in range(4):
        quarter = pads_adam(trim[i], layer=layer)
        quarter.move(origin=quarter.center, destination=(0, 0))
        quarter.rotate(angle=90 * -i, center=(0, 345))
        q = quadPad.add_ref(quarter)
        quadPad.add_port(name=3 * i + 1, port=quarter.ports[3])
        quadPad.add_port(name=3 * i + 2, port=quarter.ports[2])
        quadPad.add_port(name=3 * i + 3, port=quarter.ports[1])
    return quadPad


def pads_adam_fill(style="right", layer=1):
    """Filled Adam style pad for lift-off process.

    Parameters
    ----------
    style : STRING, optional
        'left', 'right', 'center' specification for pad-port direction.
        The default is 'right'.
    layer : INT, optional
        Layer for device to be created on. The default is 1.

    Returns
    -------
    pad_cover : DEVICE
        PHIDL device object is returned.
    """
    pad_cover = Device("pad_cover")
    base = pg.straight(size=(140, 240), layer=layer)
    post = pg.straight(size=(20, 50), layer=layer)

    if style == "center":
        b1 = pad_cover.add_ref(base)

        p1 = pad_cover.add_ref(post)
        p1.move(origin=p1.center, destination=b1.center).movey(225)

        r1 = pr.route_basic(
            b1.ports[1],
            p1.ports[2],
            path_type="straight",
            width_type="straight",
            num_path_pts=50,
            width1=20,
            layer=layer,
        )
        pad_cover.add_ref(r1)
    if style == "right":
        b1 = pad_cover.add_ref(base)
        b1.movex(170)
        p1 = pad_cover.add_ref(post)
        p1.move(origin=p1.center, destination=b1.center).movex(90).movey(225)
        r1 = pr.route_basic(
            b1.ports[1],
            p1.ports[2],
            path_type="straight",
            width_type="straight",
            num_path_pts=50,
            width1=20,
            layer=layer,
        )
        pad_cover.add_ref(r1)
    if style == "left":
        b1 = pad_cover.add_ref(base)
        b1.movex(-170)

        p1 = pad_cover.add_ref(post)
        p1.move(origin=p1.center, destination=b1.center).movex(-90).movey(225)

        r1 = pr.route_basic(
            b1.ports[1],
            p1.ports[2],
            path_type="straight",
            width_type="straight",
            num_path_pts=50,
            width1=20,
            layer=layer,
        )
        pad_cover.add_ref(r1)

    #    OUT = pg.outline(pad_cover,distance = 5,precision=0.0001,layer = layer)
    pad_cover.add_port(name=1, port=p1.ports[1])
    return pad_cover


def pad_array(
    num=8,
    size1=(100, 100),
    size2=(200, 250),
    outline=None,
    layer=1,
    pad_layers=None,
    pad_iso=None,
    de_etch=False,
):
    """

    Parameters
    ----------
    num : INT, optional
        THE NUMBER OF PADS. PAD LOCATION IS AUTOMATED TO HANDLE ODD NUMBERS. The default is 8.
    size1 : TUPLE, optional
        THE SIZE OF THE WORKSPACE. TYPICALLY SMALLER THAN THE SIZE OF THE FIELD (450,450). The default is (100, 100).
    size2 : TUPLE, optional
        THE SIZE OF EACH PAD. The default is (200, 250).
    outline : FLOAT, optional
        THE OUTLINE DISTANCE. IF NONE NO OUTLINE WILL BE PERFORMED. The default is None.
    layer : INT, optional
        LAYER FOR GEOMETRY TO EXIST ON. The default is 1.
    pad_layers : INT, optional
        THE OPTION pad_layers WILL PLACE EACH PAD ON A SEPARATE LAYER FOR EASIER
        BEAMER(LITHOGRAPHY PROGRAMMING), ie PLACING FIELDS BASED ON LAYER.
        LAYERS INCREMENT FROM THE SPECIFIED INT. The default is None.

    Returns
    -------
    D : TYPE
        DESCRIPTION.

    """

    if outline is None:
        out_dis = 10
    else:
        out_dis = outline

    D = Device("pad_array")
    if pad_iso:
        B = Device()

    a, b = divmod(num, 4)
    conn_side = np.tile(a, 4)
    for i in range(b):
        conn_side[i] = conn_side[i] + 1
    conn_side.sort()
    conn_dict = {
        "W": conn_side[0],
        "E": conn_side[1],
        "S": conn_side[2],
        "N": conn_side[3],
    }

    rec1 = pg.compass_multi(size=size1, ports=conn_dict, layer=1)
    size2_x = max([size1[0], max(conn_side) * (size2[0] + out_dis * 5)])

    rec2 = pg.compass_multi(size=(size2_x, size2_x), ports=conn_dict, layer=1)

    port_list1 = rec1.get_ports()
    port_list2 = rec2.get_ports()
    final_ports = []
    for prt1, prt2 in zip(port_list1, port_list2):
        p1 = D << pg.straight(size=(prt1.width / 2 - out_dis, prt1.width / 2))
        p1.connect(p1.ports[1], prt1)

        final_ports.append(p1.ports[1])
        p2 = D << pg.straight(size=size2)

        p2.connect(p2.ports[1], prt2)

        if pad_iso:
            Bp2 = B << pg.straight(size=size2)
            Bp2.connect(Bp2.ports[1], prt2)

        if de_etch:
            pad_etch = B << pg.straight(
                size=(size2[0] - 10, size2[1] - 10), layer=layer + 1
            )
            pad_etch.connect(pad_etch.ports[1], prt2)
            pad_etch.move(pad_etch.center, p2.center)

        D << pr.route_basic(
            p1.ports[2],
            p2.ports[1],
            path_type="straight",
            width_type="straight",
            width1=None,
            width2=p2.ports[1].width / 2,
        )

    D = pg.union(D)
    [D.add_port(name=i, port=final_ports[i]) for i in range(len(final_ports))]

    if outline:
        D = pg.outline(D, distance=out_dis, open_ports=True)
        if pad_iso:
            B = pg.outline(B, distance=out_dis, layer=pad_iso)
    D.flatten(single_layer=layer)

    if pad_layers:
        for p, i in zip(D.polygons, range(len(D.polygons))):
            C = Device()
            C.add(p)
            C.flatten(single_layer=pad_layers + i)
            D << C

        n = len(D.polygons)
        for p in range(n):
            D.remove(D.polygons[0])

    if pad_iso and pad_layers == None:
        D << B
    if pad_iso and pad_layers:

        for p, i in zip(B.polygons, range(len(B.polygons))):
            A = Device()
            A.add(p)
            A.flatten(single_layer=pad_iso + i)
            B << A

        n = len(B.polygons)
        for p in range(n):
            B.remove(B.polygons[0])
        D << B
    D.flatten()
    return D


def resistor_pos(
    size=(6, 20), width=20, length=40, overhang=10, pos_outline=0.5, layer=1, rlayer=2
):
    rwidth = size[0]
    rlength = size[1]
    spacing = rlength - overhang
    res = pg.straight((rwidth, rlength), layer=rlayer)
    s1 = pg.outline(
        pg.straight((width, length + spacing)),
        distance=pos_outline,
        layer=layer,
        open_ports=pos_outline,
        precision=1e-6,
    )

    rout = pg.straight((width + pos_outline * 2, rlength - overhang), layer=layer)
    rout.move(rout.ports[2], s1.ports[1])

    res.move(res.center, rout.center)

    s2 = pg.outline(
        pg.straight((width, length + spacing)),
        distance=pos_outline,
        layer=layer,
        open_ports=2,
        precision=1e-6,
    )

    s2.move(s2.ports[2], rout.ports[1])

    D = Device("resistor")
    D.add_ref([res, s1, rout, s2])
    D = pg.union(D, by_layer=True)
    D.add_port(s1.ports[2])
    D.add_port(s2.ports[1])
    D.squares = (size[1] - overhang) / size[0]
    return D


def resistor_neg(
    size=(6, 20), width=20, length=40, overhang=10, pos_outline=0.5, layer=1, rlayer=2
):
    rwidth = size[0]
    rlength = size[1]
    spacing = rlength - overhang
    res = pg.straight((rwidth, rlength), layer=rlayer)
    s1 = pg.straight((width, length + spacing), layer=layer)
    rout = pg.straight((width + pos_outline * 2, rlength - overhang), layer=layer)
    rout.move(rout.ports[2], s1.ports[1])

    res.move(res.center, rout.center)

    s2 = pg.straight((width, length + spacing), layer=layer)

    s2.move(s2.ports[2], rout.ports[1])

    D = Device("resistor")
    D.add_ref([res, s1, s2])
    D = pg.union(D, by_layer=True)
    D.add_port(s1.ports[2])
    D.add_port(s2.ports[1])
    D.squares = (size[1] - overhang) / size[0]
    return D


def ntron(choke_w=0.03, gate_w=0.2, channel_w=0.1, source_w=0.3, drain_w=0.3, layer=1):

    D = Device(name="nTron")

    choke = pg.optimal_step(gate_w, choke_w, symmetric=True, num_pts=100)
    k = D << choke

    channel = pg.compass(size=(channel_w, choke_w))
    c = D << channel
    c.connect(channel.ports["W"], choke.ports[2])

    drain = pg.optimal_step(drain_w, channel_w)
    d = D << drain
    d.connect(drain.ports[2], c.ports["N"])

    source = pg.optimal_step(channel_w, source_w)
    s = D << source
    s.connect(source.ports[1], c.ports["S"])

    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(name=3, port=k.ports[1])
    D.add_port(name=1, port=d.ports[1])
    D.add_port(name=2, port=s.ports[2])
    D.name = "nTron"
    D.info = locals()
    return D


def ntron_v2(
    choke_w=0.04,
    gate_w=0.5,
    channel_w=0.3,
    source_w=1,
    drain_w=1,
    choke_offset=1.5,
    layer=1,
):

    D = Device(name="nTron")

    # choke = pg.optimal_step(gate_w, choke_w, symmetric=True)
    # k = D<<choke

    drain = pg.optimal_step(drain_w, channel_w)
    d = D << drain
    d.rotate(-90)
    d.move(d.ports[2], (0, 0))

    source = pg.optimal_step(channel_w, source_w)
    s = D << source
    s.connect(s.ports[1], d.ports[2])

    choke = pg.optimal_step(gate_w, choke_w, symmetric=True, num_pts=150)
    k = D << choke
    k.move(k.ports[2].center, (-channel_w / 2, -choke_offset))

    tee = D << pg.tee(
        size=(drain_w * 10, drain_w),
        stub_size=(drain_w, drain_w * 5),
        taper_type="fillet",
    )
    tee.connect(tee.ports[2], d.ports[1])

    ind = D << pg.snspd(size=(100, 50), wire_width=drain_w, wire_pitch=drain_w * 2)
    ind.connect(ind.ports[1], tee.ports[1])

    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(name=3, port=k.ports[1])
    D.add_port(name=1, port=ind.ports[2])
    D.add_port(name=2, port=s.ports[2])
    D.add_port(name=4, port=tee.ports[3])
    D.name = "nTron"
    D.info = locals()

    return D


# qp(ntron_v2(choke_w=0.05, choke_offset=3))


def ntron_sharp(
    choke_w=0.03,
    choke_l=0.5,
    gate_w=0.2,
    channel_w=0.1,
    source_w=0.3,
    drain_w=0.3,
    layer=1,
):

    D = Device("nTron")

    choke = pg.taper(choke_l, gate_w, choke_w)
    k = D << choke

    channel = pg.compass(size=(channel_w, choke_w / 10))
    c = D << channel
    c.connect(channel.ports["W"], choke.ports[2])

    drain = pg.taper(channel_w * 6, drain_w, channel_w)
    d = D << drain
    d.connect(drain.ports[2], c.ports["N"])

    source = pg.taper(channel_w * 6, channel_w, source_w)
    s = D << source
    s.connect(source.ports[1], c.ports["S"])

    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(name="g", port=k.ports[1])
    D.add_port(name="d", port=d.ports[1])
    D.add_port(name="s", port=s.ports[2])
    D.name = "nTron"
    D.info = locals()
    return D


def ntron_sharp_shift(
    choke_w=0.03,
    choke_l=0.5,
    gate_w=0.2,
    channel_w=0.1,
    source_w=0.3,
    drain_w=0.3,
    layer=1,
    choke_shift=-0.5,
):

    D = Device("nTron")

    choke = pg.taper(choke_l, gate_w, choke_w)
    k = D << choke

    channel = pg.compass(size=(channel_w, choke_w))
    c = D << channel
    c.connect(channel.ports["W"], choke.ports[2])

    drain = pg.optimal_step(drain_w, channel_w)
    d = D << drain
    d.connect(drain.ports[2], c.ports["N"])

    source = pg.optimal_step(channel_w, source_w)
    s = D << source
    s.connect(source.ports[1], c.ports["S"])

    k.movey(choke_shift)
    D = pg.union(D)
    D.add_port(name="g", port=k.ports[1])
    D.add_port(name="d", port=d.ports[1])
    D.add_port(name="s", port=s.ports[2])
    return D


def ntron_sharp_shift_fanout(
    choke_w=0.03,
    choke_l=0.5,
    gate_w=0.2,
    channel_w=0.1,
    source_w=0.3,
    drain_w=0.3,
    routing=1,
    layer=1,
    choke_shift=-0.5,
    choke_taper="optimal",
):

    D = Device("nTron")

    if choke_taper == "straight":
        choke = pg.taper(choke_l, gate_w, choke_w)
    elif choke_taper == "optimal":
        choke = pg.optimal_step(gate_w, choke_w, symmetric=True)
    k = D << choke

    channel = pg.compass(size=(channel_w, choke_w))
    c = D << channel
    c.connect(channel.ports["W"], choke.ports[2])

    drain = pg.optimal_step(drain_w, channel_w)
    d = D << drain
    d.connect(drain.ports[2], c.ports["N"])

    source = pg.optimal_step(channel_w, source_w)
    s = D << source
    s.connect(source.ports[1], c.ports["S"])

    k.movey(choke_shift)

    step = pg.optimal_step(routing, gate_w, symmetric=True, width_tol=1e-8)
    s1 = D << step
    s1.connect(s1.ports[2], k.ports[1])

    step = pg.optimal_step(routing, drain_w, symmetric=True, width_tol=1e-8)
    s2 = D << step
    s2.connect(s2.ports[2], d.ports[1])

    step = pg.optimal_step(routing, source_w, symmetric=True, width_tol=1e-8)
    s3 = D << step
    s3.connect(s3.ports[2], s.ports[2])

    D = pg.union(D)
    D.add_port(name="g", port=s1.ports[1])
    D.add_port(name="d", port=s2.ports[1])
    D.add_port(name="s", port=s3.ports[1])
    return D


def ntron_multi_gate(
    num_gate=4,
    gate_w=0.250,
    gate_p=0.4,
    choke_w=0.03,
    choke_l=0.5,
    channel_w=0.3,
    source_w=0.6,
    drain_w=0.6,
    symmetric=False,
    layer=1,
    choke_taper="optimal",
):

    D = Device("nTron")
    channel = pg.compass_multi(
        size=(channel_w, gate_p * (num_gate + 1)), ports={"N": 1, "S": 1, "W": num_gate}
    )
    c = D << channel

    if choke_taper == "straight":
        choke = pg.taper(choke_l, gate_w, choke_w)
    elif choke_taper == "optimal":
        choke = pg.optimal_step(gate_w, choke_w, symmetric=True)
    port_list = []
    for i in range(num_gate):
        k = D << choke
        k.connect(k.ports[2], channel.ports["W" + str(i + 1)])
        port_list.append(k.ports[1])

    drain = pg.optimal_step(drain_w, channel_w, symmetric=symmetric)
    d = D << drain
    d.connect(drain.ports[2], c.ports["N1"])
    #
    source = pg.optimal_step(channel_w, source_w, symmetric=symmetric)
    s = D << source
    s.connect(source.ports[1], c.ports["S1"])

    D = pg.union(D, by_layer=True)
    for i in range(len(port_list)):
        D.add_port(name="g" + str(i + 1), port=port_list[i])
    D.add_port(name="d", port=d.ports[1])
    D.add_port(name="s", port=s.ports[2])
    return D


def ntron_multi_gate_fanout(
    num_gate=5,
    gate_w=0.15,
    gate_p=0.20,
    choke_w=0.05,
    choke_l=0.3,
    channel_w=0.15,
    source_w=0.6,
    drain_w=0.6,
    routing=1,
    outline_dis=0.2,
    layer=1,
    gate_factor=2.5,
    choke_taper="optimal",
):

    D = Device("ntron_multi_gate")

    ntron = ntron_multi_gate(
        num_gate,
        gate_w,
        gate_p,
        choke_w,
        choke_l,
        channel_w,
        source_w,
        drain_w,
        layer=layer,
        choke_taper=choke_taper,
    )
    step = pg.optimal_step(routing, drain_w, symmetric=True, width_tol=1e-8)

    n1 = D << ntron
    s1 = D << step
    s2 = D << step

    s1.connect(s1.ports[2], n1.ports["d"])
    s2.connect(s2.ports[2], n1.ports["s"])

    # FANOUT PROGRAMMING
    gate_ports = [x.name for x in D.get_ports() if str(x.name)[0] == "g"]

    fanout_ports = []
    fanout_ports.append(s2.ports[1])

    length = gate_factor * num_gate
    for i in range(1, num_gate + 1):
        mid = (num_gate / 2) - i + 0.5
        scalef = 1 - abs(mid) / num_gate
        flength = length * scalef - length / 2
        fan_straight = pg.straight(size=(gate_w, flength))

        fs = D << fan_straight
        fs.connect(fs.ports[2], n1.ports[gate_ports[i - 1]])
        T = pg.optimal_90deg(width=gate_w)
        S = pg.optimal_step(routing, gate_w, symmetric=True)
        if mid > 0:
            turn = D << T
            turn.connect(turn.ports[1], fs.ports[1])
            step1 = D << S
            step1.connect(step1.ports[2], turn.ports[2])
            fanout_ports.append(step1.ports[1])
        if mid < 0:
            turn = D << T
            turn.connect(turn.ports[2], fs.ports[1])
            step1 = D << S
            step1.connect(step1.ports[2], turn.ports[1])
            fanout_ports.append(step1.ports[1])
        if mid == 0:
            step1 = D << S
            step1.connect(step1.ports[2], fs.ports[1])
            fanout_ports.append(step1.ports[1])

    fanout_ports.append(s1.ports[1])
    [D.add_port(name=n + 1, port=fanout_ports[n]) for n in range(len(fanout_ports))]

    D = pg.outline(D, distance=outline_dis, open_ports=outline_dis * 1.5)
    D.flatten(single_layer=1)

    return D


def ntron_multi_gate_dual(num_gate, **kwargs):
    if not np.mod(num_gate, 2) == 0:
        raise ValueError("number of gates must be even")
    num_gateh = num_gate // 2
    ntron = ntron_multi_gate(num_gate=num_gateh, symmetric=True, **kwargs)
    D = Device()
    d1 = D << ntron
    d2 = D << ntron
    d2.mirror()
    gate_ports = [x for x in D.get_ports() if str(x.name)[0] == "g"]
    sp = d1.ports["s"]
    dp = d1.ports["d"]
    D = pg.union(D)
    [
        D.add_port(name="g" + str(n + 1), port=gate_ports[n])
        for n in range(len(gate_ports))
    ]
    D.add_port(name="s", port=sp)
    D.add_port(name="d", port=dp)
    return D


def ntron_multi_gate_dual_fanout(
    num_gate=10,
    gate_w=0.15,
    gate_p=0.20,
    choke_w=0.05,
    choke_l=0.3,
    channel_w=0.15,
    source_w=0.6,
    drain_w=0.6,
    routing=1,
    outline_dis=None,
    layer=1,
    gate_factor=2.5,
    choke_taper="straight",
):
    if not np.mod(num_gate, 2) == 0:
        raise ValueError("number of gates must be even")
    num_gate = num_gate // 2  # for half on each side
    D = Device("ntron_multi_gate")

    ntron = ntron_multi_gate(
        num_gate,
        gate_w,
        gate_p,
        choke_w,
        choke_l,
        channel_w,
        source_w,
        drain_w,
        layer=layer,
        symmetric=True,
        choke_taper=choke_taper,
    )
    step = pg.optimal_step(routing, drain_w, symmetric=True, width_tol=1e-8)

    n1 = D << ntron
    s1 = D << step
    s2 = D << step

    s1.connect(s1.ports[2], n1.ports["d"])
    s2.connect(s2.ports[2], n1.ports["s"])

    # FANOUT PROGRAMMING
    gate_ports = [x.name for x in D.get_ports() if str(x.name)[0] == "g"]

    fanout_ports = []
    fanout_ports.append(s2.ports[1])
    fanout_ports.append(s1.ports[1])

    length = gate_factor * num_gate
    for i in range(1, num_gate + 1):
        mid = (num_gate / 2) - i + 0.5
        scalef = 1 - abs(mid) / num_gate
        flength = length * scalef - length / 2
        fan_straight = pg.straight(size=(gate_w, flength))

        fs = D << fan_straight
        fs.connect(fs.ports[2], n1.ports[gate_ports[i - 1]])
        T = pg.optimal_90deg(width=gate_w)
        S = pg.optimal_step(routing, gate_w, symmetric=True)
        if mid > 0:
            turn = D << T
            turn.connect(turn.ports[1], fs.ports[1])
            step1 = D << S
            step1.connect(step1.ports[2], turn.ports[2])
            fanout_ports.append(step1.ports[1])
        if mid < 0:
            turn = D << T
            turn.connect(turn.ports[2], fs.ports[1])
            step1 = D << S
            step1.connect(step1.ports[2], turn.ports[1])
            fanout_ports.append(step1.ports[1])
        if mid == 0:
            step1 = D << S
            step1.connect(step1.ports[2], fs.ports[1])
            fanout_ports.append(step1.ports[1])

    D = pg.union(D)

    [D.add_port(name=n + 1, port=fanout_ports[n]) for n in range(len(fanout_ports))]
    E = pg.copy(D)
    e1 = D << E.mirror()
    [fanout_ports.append(e1.ports[num_gate + 2 - j]) for j in range(num_gate)]

    D = pg.union(D)
    [D.add_port(name=n + 1, port=fanout_ports[n]) for n in range(len(fanout_ports))]

    if outline_dis:
        D = pg.outline(D, distance=outline_dis, open_ports=outline_dis * 1.5)

    D.flatten(single_layer=1)
    return D


def ntron_multi_gate_dual_fanout_ind(
    num_gate=10,
    gate_w=0.2,
    gate_p=0.30,
    choke_w=0.05,
    choke_l=0.3,
    channel_w=0.12,
    source_w=0.3,
    drain_w=0.3,
    inductor_a1=30,
    inductor_a2=5,
    routing=1,
    outline_dis=None,
    layer=1,
    gate_factor=15,
    choke_taper="straight",
    sheet_inductance=50,
):
    if not np.mod(num_gate, 2) == 0:
        raise ValueError("number of gates must be even")
    num_gate = num_gate // 2  # for half on each side
    D = Device("ntron_multi_gate_ind")

    ntron = ntron_multi_gate(
        num_gate,
        gate_w,
        gate_p,
        choke_w,
        choke_l,
        channel_w,
        source_w,
        drain_w,
        layer=layer,
        symmetric=True,
        choke_taper=choke_taper,
    )
    step = pg.optimal_step(routing, drain_w, symmetric=True, width_tol=1e-8)

    tee = pg.tee(
        size=(drain_w * 3, drain_w), stub_size=(drain_w, 10), taper_type="fillet"
    )

    n1 = D << ntron

    # # FANOUT PROGRAMMING
    gate_ports = [x.name for x in D.get_ports() if str(x.name)[0] == "g"]

    fanout_ports = []

    length = gate_factor * num_gate
    for i in range(1, num_gate + 1):
        mid = (num_gate / 2) - i + 0.5
        scalef = 1 - abs(mid) / num_gate
        flength = length * scalef - length / 2
        fan_straight = pg.straight(size=(gate_w, flength))

        fs = D << fan_straight
        fs.connect(fs.ports[2], n1.ports[gate_ports[i - 1]])
        T = pg.optimal_90deg(width=gate_w)
        S = pg.optimal_step(routing, gate_w, symmetric=True)
        if mid > 0:
            turn = D << T
            turn.connect(turn.ports[1], fs.ports[1])
            step1 = D << S
            step1.connect(step1.ports[2], turn.ports[2])
            fanout_ports.append(step1.ports[1])
        if mid < 0:
            turn = D << T
            turn.connect(turn.ports[2], fs.ports[1])
            step1 = D << S
            step1.connect(step1.ports[2], turn.ports[1])
            fanout_ports.append(step1.ports[1])
        if mid == 0:
            step1 = D << S
            step1.connect(step1.ports[2], fs.ports[1])
            fanout_ports.append(step1.ports[1])

    # D = pg.union(D)

    [D.add_port(name=n + 1, port=fanout_ports[n]) for n in range(len(fanout_ports))]
    # D.remove([tur1, tur2, t1, l1, s1])
    E = pg.copy(D)
    e1 = D << E.mirror()
    [fanout_ports.append(e1.ports[num_gate - j]) for j in range(num_gate)]

    s1 = D << step
    s2 = D << step

    inductor = snspd_vert(drain_w, drain_w * 2, size=(inductor_a1, inductor_a2))

    print("sheet_inductance: " + str(sheet_inductance))
    print(
        "Inductors "
        + str(float(inductor.info["num_squares"]) * sheet_inductance * 1e-3)
        + " nH"
    )
    l1 = D << inductor
    l1.connect(l1.ports[1], n1.ports["d"])
    s1.connect(s2.ports[2], l1.ports[2])
    s2.connect(s2.ports[2], n1.ports["s"])
    fanout_ports.append(s2.ports[1])
    fanout_ports.append(s1.ports[1])

    D = pg.union(D)
    [D.add_port(name=n + 1, port=fanout_ports[n]) for n in range(len(fanout_ports))]

    if outline_dis:
        D = pg.outline(D, distance=outline_dis, open_ports=outline_dis * 1.5)

    D.flatten(single_layer=1)
    return D


def ntron_amp(
    device_layer=1,
    pad_layer=2,
    choke_w=0.05,
    choke_l=0.3,
    gate_w=0.2,
    gate_p=0.4,
    channel_w=0.2,
    source_w=0.5,
    drain_w=0.5,
    inductor_w=0.5,
    inductor_a1=20,
    inductor_a2=50,
    outline_dis=0.1,
    routing=0.5,
    sheet_inductance=50,
    sheet_resistance=5,
):
    D = Device()
    ntron = ntron_multi_gate_fanout(
        1,
        gate_w,
        gate_p,
        choke_w,
        choke_l,
        channel_w,
        source_w,
        drain_w,
        routing,
        outline_dis,
        device_layer,
    )
    n1 = D << ntron

    inductor = snspd_vert(inductor_w, inductor_w * 2, size=(inductor_a1, inductor_a2))

    print("sheet_inductance: " + str(sheet_inductance))
    print(
        "Inductors "
        + str(
            qu.squares_calc(inductor_w, inductor_w * 2, size=(inductor_a1, inductor_a2))
            * sheet_inductance
            * 1e-3
        )
        + " nH"
    )
    inductor = outline(inductor, distance=outline_dis, open_ports=2, layer=device_layer)
    l1 = D << inductor
    l1.connect(l1.ports[1], n1.ports[3])

    tee1 = pg.outline(
        pg.tee((routing * 4, routing), (routing, routing), taper_type="fillet"),
        distance=outline_dis,
        open_ports=True,
        layer=device_layer,
    )
    t1 = D << tee1
    t1.connect(t1.ports[2], l1.ports[2])

    stepR = pg.outline(
        pg.optimal_step(routing, routing * 2, symmetric=True),
        distance=outline_dis,
        open_ports=True,
        layer=device_layer,
    )
    s1 = D << stepR
    s1.connect(s1.ports[1], n1.ports[2])

    res = resistor_pos(
        size=(0.5, 3),
        width=routing * 2,
        length=3,
        overhang=1,
        pos_outline=outline_dis,
        layer=device_layer,
        rlayer=3,
    )
    r1 = D << res
    r1.connect(r1.ports[1], s1.ports[2])
    print("sheet_resistance: " + str(sheet_resistance))
    print("Resistors: " + str((res.squares * sheet_resistance)) + "Ω")

    tee2 = pg.outline(
        pg.tee((routing * 4, routing * 2), (routing, routing), taper_type="fillet"),
        distance=outline_dis,
        open_ports=True,
        layer=device_layer,
    )
    t2 = D << tee2
    t2.connect(t2.ports[1], r1.ports[2])

    l2 = D << inductor
    l2.connect(l2.ports[2], t2.ports[3])

    r2 = D << res
    r2.connect(r2.ports[1], t2.ports[2])

    s2 = D << stepR
    s2.connect(s2.ports[2], r2.ports[2])

    gtaper = pg.outline(
        hyper_taper(1, 10, routing),
        distance=outline_dis,
        open_ports=2,
        layer=device_layer,
    )
    gt = D << gtaper
    gt.connect(gt.ports[1], n1.ports[1])

    gt1 = D << gtaper
    gt1.connect(gt1.ports[1], l2.ports[1])
    D = pg.union(D, by_layer=True)
    port_list = [s2.ports[1], t1.ports[1], t1.ports[3]]
    [D.add_port(name=n + 1, port=port_list[n]) for n in range(len(port_list))]

    return D


# def ntron_four_port(device_layer = 1,
#               pad_layer = 2,
#               choke_w = 0.05,
#               choke_l = .3,
#               gate_w = 0.2,
#               channel_w = 0.1,
#               source_w = .2,
#               drain_w = .2,
#               inductor_w = 0.2,
#               inductor_a1 = 15,
#               inductor_a2 = 5,
#               outline_dis = 0.2,
#               routing = .5,
#               sheet_inductance=50):

#     D = Device('ntron')
#     ntron = outline(ntron_sharp(choke_w, choke_l, gate_w, channel_w, source_w,
#                         drain_w, device_layer), distance=outline_dis, open_ports=3, layer=device_layer, precision=1e-6)
#     n1 = D<<ntron


#     tee1 = pg.outline(pg.tee((drain_w*10, drain_w), (drain_w, drain_w), taper_type='fillet'), distance=outline_dis, open_ports=3, layer=device_layer,  precision=1e-6)
#     t1 = D<<tee1
#     t1.connect(t1.ports[2], n1.ports['d'])

#     # inductor = snspd_vert(inductor_w, inductor_w*2,
#     #                           size=(inductor_a1, inductor_a2))
#     inductor = pg.snspd(inductor_w, inductor_w*2, size=(inductor_a1, inductor_a2))

#     print('sheet_inductance: ' + str(sheet_inductance))
#     print('Inductors ' + str(qu.squares_calc(inductor_w, inductor_w*2,
#                        size=(inductor_a1, inductor_a2))*sheet_inductance*1e-3) +' nH' )
#     inductor= outline(inductor,distance=outline_dis,open_ports=0, layer=device_layer)
#     l1 = D<<inductor
#     l1.connect(l1.ports[1],t1.ports[1])


#     stepR = pg.outline(pg.optimal_step(drain_w, routing, symmetric=True), distance=outline_dis, open_ports=3, layer=device_layer)
#     s1 = D<<stepR
#     s1.connect(s1.ports[1], t1.ports[3])

#     gtaper = pg.outline(pg.optimal_step(gate_w, drain_w, symmetric=True), distance=outline_dis, open_ports=3, layer=device_layer)
#     gt = D<<gtaper
#     gt.connect(gt.ports[1], n1.ports['g'])

#     tee2 = pg.outline(pg.tee((drain_w*20, drain_w), (drain_w, drain_w*5), taper_type='fillet'), distance=outline_dis, open_ports=True, layer=device_layer)
#     t2 = D<<tee2
#     t2.connect(t2.ports[1], gt.ports[2])

#     l2 = D<<inductor
#     l2.connect(l2.ports[2], t2.ports[3])

#     s2 = D<<stepR
#     s2.connect(s2.ports[1],t2.ports[2])


#     ground = pg.outline(hyper_taper(1, wide_section=drain_w*19, narrow_section=source_w), distance=outline_dis, open_ports=drain_w*19, layer=device_layer)
#     gt1 = D<<ground
#     gt1.connect(gt1.ports[1], n1.ports['s'])
#     D = pg.union(D, by_layer=True)
#     port_list = [s2.ports[2], s1.ports[2], l1.ports[2], l2.ports[1]]
#     [D.add_port(name=n+1, port=port_list[n]) for n in range(len(port_list))]

#     return D


def ntron_three_port(
    choke_w=0.015,
    choke_l=0.3,
    gate_w=0.2,
    channel_w=0.10,
    source_w=0.4,
    drain_w=0.4,
    inductor_a1=30,
    inductor_a2=10,
    routing=3,
    layer=1,
    sheet_inductance=50,
):

    D = Device("ntron")
    ntron = ntron_sharp(choke_w, choke_l, gate_w, channel_w, source_w, drain_w, layer)
    n1 = D << ntron

    # inductor = snspd_vert(inductor_w, inductor_w*2,
    #                           size=(inductor_a1, inductor_a2))
    inductor = pg.snspd(drain_w, drain_w * 2, size=(inductor_a1, inductor_a2))

    print("sheet_inductance: " + str(sheet_inductance))
    print(
        "Inductors "
        + str(float(inductor.info["num_squares"]) * sheet_inductance * 1e-3)
        + " nH"
    )
    l1 = D << inductor
    l1.connect(l1.ports[1], n1.ports["d"])

    tee1 = pg.tee((drain_w * 20, drain_w), (drain_w, drain_w * 5), taper_type="fillet")
    t1 = D << tee1
    t1.connect(t1.ports[2], l1.ports[2])
    # print(inductor.info['num_squares'])
    stepR = pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s1 = D << stepR
    s1.connect(s1.ports[1], t1.ports[3])
    # print(stepR.info['num_squares'])
    gtaper = pg.optimal_step(gate_w, routing, symmetric=True, anticrowding_factor=3)
    gt = D << gtaper
    gt.connect(gt.ports[1], n1.ports["g"])

    # s2 = D<<stepR
    # s2.connect(s2.ports[1], n1.ports[3])

    s3 = D << pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s3.connect(s3.ports[1], t1.ports[1])

    straight = pg.straight(size=(source_w, drain_w * 7.5))
    st = D << straight
    st.connect(st.ports[1], n1.ports["s"])

    ground = hyper_taper(1, wide_section=drain_w * 19, narrow_section=source_w)
    gt1 = D << ground
    gt1.connect(gt1.ports[1], st.ports[2])

    D = pg.union(D, by_layer=False)
    D.flatten(single_layer=layer)
    port_list = [gt.ports[2], s3.ports[2], s1.ports[2], gt1.ports[2]]
    [D.add_port(name=n + 1, port=port_list[n]) for n in range(len(port_list))]

    return D


def ntron_three_port1(
    choke_w=0.015,
    choke_l=0.3,
    gate_w=0.2,
    channel_w=0.10,
    source_w=0.4,
    drain_w=0.4,
    inductor_a1=30,
    inductor_a2=10,
    routing=3,
    layer=1,
    sheet_inductance=50,
):

    D = Device("ntron")
    ntron = ntron_sharp(choke_w, choke_l, gate_w, channel_w, source_w, drain_w, layer)
    n1 = D << ntron

    # inductor = snspd_vert(inductor_w, inductor_w*2,
    #                           size=(inductor_a1, inductor_a2))
    inductor = pg.snspd(drain_w, drain_w * 2, size=(inductor_a1, inductor_a2))
    straight = pg.straight(size=(source_w, drain_w * 7.5))
    st1 = D << straight
    st1.connect(st1.ports[1], n1.ports["d"])

    print("sheet_inductance: " + str(sheet_inductance))
    print(
        "Inductors "
        + str(float(inductor.info["num_squares"]) * sheet_inductance * 1e-3)
        + " nH"
    )
    l1 = D << inductor
    l1.connect(l1.ports[1], st1.ports[2])

    gtaper = pg.optimal_step(gate_w, routing, symmetric=True, anticrowding_factor=3)
    gt = D << gtaper
    gt.connect(gt.ports[1], n1.ports["g"])

    s2 = D << pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s2.connect(s2.ports[1], n1.ports["s"])

    s3 = D << pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s3.connect(s3.ports[1], l1.ports[2])

    straight = pg.straight(size=(source_w, drain_w * 7.5))
    st = D << straight
    st.connect(st.ports[1], n1.ports["s"])

    D = pg.union(D, by_layer=False)
    D.flatten(single_layer=layer)
    port_list = [
        s2.ports[2],
        gt.ports[2],
        s3.ports[2],
    ]
    [D.add_port(name=n + 1, port=port_list[n]) for n in range(len(port_list))]

    return D


def ntron_three_port_gnd(
    choke_w=0.015,
    choke_l=0.3,
    gate_w=0.2,
    channel_w=0.10,
    source_w=0.4,
    drain_w=0.4,
    inductor_a1=30,
    inductor_a2=10,
    routing=3,
    layer=1,
    sheet_inductance=50,
):

    D = Device("ntron")
    ntron = ntron_sharp(choke_w, choke_l, gate_w, channel_w, source_w, drain_w, layer)
    n1 = D << ntron

    tee1 = pg.tee((drain_w * 25, drain_w), (drain_w, drain_w * 5), taper_type="fillet")
    t1 = D << tee1
    t1.connect(t1.ports[2], n1.ports["d"])

    # inductor = snspd_vert(inductor_w, inductor_w*2,
    #                           size=(inductor_a1, inductor_a2))
    inductor = pg.snspd(drain_w, drain_w * 2, size=(inductor_a1, inductor_a2))

    print("sheet_inductance: " + str(sheet_inductance))
    print(
        "Inductors "
        + str(float(inductor.info["num_squares"]) * sheet_inductance * 1e-3)
        + " nH"
    )
    l1 = D << inductor
    l1.connect(l1.ports[1], t1.ports[1])

    # print(inductor.info['num_squares'])
    stepR = pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s1 = D << stepR
    s1.connect(s1.ports[1], t1.ports[3])
    # print(stepR.info['num_squares'])
    gtaper = pg.optimal_step(gate_w, routing, symmetric=True, anticrowding_factor=3)
    gt = D << gtaper
    gt.connect(gt.ports[1], n1.ports["g"])

    s3 = D << pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s3.connect(s3.ports[1], l1.ports[2])

    straight = pg.optimal_step(source_w, routing, symmetric=True)
    st = D << straight
    st.connect(st.ports[1], n1.ports["s"])

    D = pg.union(D, by_layer=False)
    D.flatten(single_layer=layer)
    port_list = [gt.ports[2], st.ports[2], s1.ports[2], s3.ports[2]]
    [D.add_port(name=n + 1, port=port_list[n]) for n in range(len(port_list))]

    return D


def ntron_four_port(
    choke_w=0.015,
    choke_l=0.3,
    gate_w=0.2,
    channel_w=0.10,
    source_w=0.3,
    drain_w=0.4,
    inductor_a1=20,
    inductor_a2=10,
    routing=0.5,
    layer=1,
    sheet_inductance=50,
):

    D = Device("ntron")
    ntron = ntron_sharp(choke_w, choke_l, gate_w, channel_w, source_w, drain_w, layer)
    n1 = D << ntron

    tee1 = pg.tee((drain_w * 15, drain_w), (drain_w, drain_w * 5), taper_type="fillet")
    t1 = D << tee1
    t1.connect(t1.ports[2], n1.ports["d"])

    # inductor = snspd_vert(inductor_w, inductor_w*2,
    #                           size=(inductor_a1, inductor_a2))
    inductor = pg.snspd(drain_w, drain_w * 2, size=(inductor_a1, inductor_a2))

    print("sheet_inductance: " + str(sheet_inductance))
    print(
        "Inductors "
        + str(float(inductor.info["num_squares"]) * sheet_inductance * 1e-3)
        + " nH"
    )
    l1 = D << inductor
    l1.connect(l1.ports[1], t1.ports[1])

    # print(inductor.info['num_squares'])
    stepR = pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s1 = D << stepR
    s1.connect(s1.ports[1], t1.ports[3])

    gtaper = pg.optimal_step(gate_w, drain_w, symmetric=True)
    gt = D << gtaper
    gt.connect(gt.ports[1], n1.ports["g"])

    tee2 = pg.tee((drain_w * 20, drain_w), (drain_w, drain_w * 5), taper_type="fillet")
    t2 = D << tee2
    t2.connect(t2.ports[1], gt.ports[2])

    l2 = D << inductor
    l2.connect(l2.ports[2], t2.ports[3])

    s2 = D << stepR
    s2.connect(s2.ports[1], t2.ports[2])

    s3 = D << pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s3.connect(s3.ports[1], l1.ports[2])
    s4 = D << pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s4.connect(s4.ports[1], l2.ports[1])

    straight = pg.straight(size=(source_w, drain_w * 7.5))
    st = D << straight
    st.connect(st.ports[1], n1.ports["s"])
    ground = hyper_taper(1, wide_section=drain_w * 19, narrow_section=source_w)

    gt1 = D << ground
    gt1.connect(gt1.ports[1], st.ports[2])
    D = pg.union(D, by_layer=False)
    D.flatten(single_layer=layer)
    port_list = [s2.ports[2], s1.ports[2], s3.ports[2], s4.ports[2], gt1.ports[2]]
    [D.add_port(name=n + 1, port=port_list[n]) for n in range(len(port_list))]

    return D


def ntron_four_port_gnd(
    choke_w=0.015,
    choke_l=0.3,
    gate_w=0.2,
    channel_w=0.10,
    source_w=0.3,
    drain_w=0.4,
    inductor_a1=20,
    inductor_a2=10,
    routing=0.5,
    layer=1,
    sheet_inductance=50,
):

    D = Device("ntron")
    ntron = ntron_sharp(choke_w, choke_l, gate_w, channel_w, source_w, drain_w, layer)
    n1 = D << ntron

    tee1 = pg.tee((drain_w * 15, drain_w), (drain_w, drain_w * 5), taper_type="fillet")
    t1 = D << tee1
    t1.connect(t1.ports[2], n1.ports["d"])

    # inductor = snspd_vert(inductor_w, inductor_w*2,
    #                           size=(inductor_a1, inductor_a2))
    inductor = pg.snspd(drain_w, drain_w * 2, size=(inductor_a1, inductor_a2))

    print("sheet_inductance: " + str(sheet_inductance))
    print(
        "Inductors "
        + str(float(inductor.info["num_squares"]) * sheet_inductance * 1e-3)
        + " nH"
    )
    l1 = D << inductor
    l1.connect(l1.ports[1], t1.ports[1])

    # print(inductor.info['num_squares'])
    stepR = pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s1 = D << stepR
    s1.connect(s1.ports[1], t1.ports[3])

    gtaper = pg.optimal_step(gate_w, drain_w, symmetric=True)
    gt = D << gtaper
    gt.connect(gt.ports[1], n1.ports["g"])

    tee2 = pg.tee((drain_w * 20, drain_w), (drain_w, drain_w * 5), taper_type="fillet")
    t2 = D << tee2
    t2.connect(t2.ports[1], gt.ports[2])

    l2 = D << inductor
    l2.connect(l2.ports[2], t2.ports[3])

    s2 = D << stepR
    s2.connect(s2.ports[1], t2.ports[2])

    s3 = D << pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s3.connect(s3.ports[1], l1.ports[2])
    s4 = D << pg.optimal_step(drain_w, routing, symmetric=True, anticrowding_factor=3)
    s4.connect(s4.ports[1], l2.ports[1])

    straight = pg.optimal_step(source_w, routing, symmetric=True)
    st = D << straight
    st.connect(st.ports[1], n1.ports["s"])

    turng = pg.optimal_90deg(routing, length_adjust=3)
    tg1 = D << turng
    tg1.connect(tg1.ports[1], s2.ports[2])

    D = pg.union(D, by_layer=False)
    D.flatten(single_layer=layer)
    port_list = [s2.ports[2], s1.ports[2], s3.ports[2], s4.ports[2], st.ports[2]]
    [D.add_port(name=n + 1, port=port_list[n]) for n in range(len(port_list))]

    return D


def not_gate(
    choke_w=0.05,
    choke_l=1,
    gate_w=0.5,
    channel_w=0.2,
    source_w=0.5,
    drain_w=0.5,
    constriciton_w=0.1,
    layer=1,
):

    D = Device("not_gate")

    nt = ntron_sharp(choke_w, choke_l, gate_w, channel_w, source_w, drain_w, layer)
    n1 = D << nt

    tee = pg.tee(
        size=(source_w * 10, source_w),
        stub_size=(source_w, source_w * 5),
        taper_type="fillet",
    )
    t1 = D << tee
    t1.connect(t1.ports[1], n1.ports["s"])

    t2 = D << tee
    t2.connect(t2.ports[2], n1.ports["d"])
    step = pg.optimal_step(source_w, constriciton_w, symmetric=True)
    s1 = D << step
    s1.connect(s1.ports[1], t1.ports[2])

    straight = pg.straight(size=(constriciton_w, constriciton_w * 3))
    st1 = D << straight
    st1.connect(st1.ports[1], s1.ports[2])

    htaper = hyper_taper(0.8, constriciton_w * 50, constriciton_w)
    ht = D << htaper
    ht.connect(ht.ports[1], st1.ports[2])

    D.flatten(single_layer=layer)
    port_list = [t2.ports[1], t2.ports[3], t1.ports[3], n1.ports["g"], ht.ports[2]]
    for p, i in zip(port_list, range(len(port_list))):
        D.add_port(name=i + 1, port=p)

    return D


def memory_loop(loop_size=(1, 2), lw=0.2, rw=0.4, port=1, vert=1.5, layer=1):
    """


    Parameters
    ----------
    loop_size : TYPE, optional
        DESCRIPTION. The default is (1, 2).
    lw : TYPE, optional
        left branch width. The default is 0.2.
    rw : TYPE, optional
        right branch width. The default is 0.4.
    port : TYPE, optional RENAME
        adjusts the distance between the top of the loop and the begining of the taper. The default is 1.
    vert : TYPE, optional
        height/2. The default is 1.5.
    layer : TYPE, optional
        DESCRIPTION. The default is 1.

    Returns
    -------
    D : TYPE
        DESCRIPTION.

    """

    D = Device()

    left = pg.flagpole(
        size=(loop_size[0] + lw + rw, port / 4), stub_size=(lw, rw), taper_type="fillet"
    )
    right = pg.flagpole(
        size=(loop_size[0] + lw + rw, port / 4),
        stub_size=(rw, rw),
        taper_type="fillet",
        shape="q",
    )

    topL = D << left
    topR = D << right
    topL.move(topL.ports[2], topR.ports[2])

    branchL = pg.straight(size=(lw, loop_size[1] - 2 * rw))
    bL = D << branchL
    bL.connect(bL.ports[1], topL.ports[1])

    branchR = pg.straight(size=(rw, loop_size[1] - 2 * rw))
    bR = D << branchR
    bR.connect(bR.ports[1], topR.ports[1])

    bleft = pg.flagpole(
        size=(loop_size[0] + lw + rw, port / 4),
        stub_size=(lw, rw),
        taper_type="fillet",
        shape="q",
    )
    bottomL = D << bleft
    bottomL.connect(bottomL.ports[1], bL.ports[2])

    bright = pg.flagpole(
        size=(loop_size[0] + lw + rw, port / 4),
        stub_size=(rw, rw),
        taper_type="fillet",
        shape="p",
    )
    bottomR = D << bright
    bottomR.connect(bottomR.ports[1], bR.ports[2])

    fake_port = D.add_port(
        name="top", midpoint=(-(loop_size[0] + lw + rw) / 2, vert / 2), orientation=-90
    )

    prout = pr.route_basic(
        topL.ports[2], fake_port, path_type="sine", width_type="sine"
    )
    conn1 = D << prout
    conn2 = D << prout
    conn2.connect(conn2.ports[1], bottomL.ports[2])

    D = pg.union(D)
    D.add_port(name=1, port=conn1.ports[2])
    D.add_port(name=2, port=conn2.ports[2])

    D.flatten(single_layer=layer)
    return D


def memory(
    loop_size=(1, 2),
    lw=0.2,
    rw=0.4,
    port=0.2,
    vert=1.5,
    layer=1,
    hwl=0.1,
    hwr=0.1,
    hll=0.5,
    hlr=1.25,
    hrout=0.75,
    hlayer=2,
):

    D = Device()
    # LEFT SIDE
    heaterL = pg.flagpole(
        size=(hll, hwl), stub_size=(hwl, 2 * hwl), taper_type="fillet", shape="p"
    )
    heaterR = pg.flagpole(
        size=(hll, hwl), stub_size=(hwl, 2 * hwl), taper_type="fillet", shape="d"
    )

    h1 = D << heaterL.rotate(-90)
    h2 = D << heaterR.rotate(-90)
    h1.move(
        h1.ports[2],
        destination=(-loop_size[0] - rw - lw / 2 + hwl / 2, -loop_size[1] / 2),
    )
    h2.move(h2.ports[2], h1.ports[2]).movex(-hwl)

    # RIGHT SIDE
    heaterL = pg.flagpole(
        size=(hlr, hwr), stub_size=(hwr, 2 * hwr), taper_type="fillet", shape="p"
    )
    heaterR = pg.flagpole(
        size=(hlr, hwr), stub_size=(hwr, 2 * hwr), taper_type="fillet", shape="d"
    )

    h3 = D << heaterL.rotate(-90)
    h4 = D << heaterR.rotate(-90)
    h3.move(h3.ports[2], destination=(-rw / 2 + hwr / 2, -loop_size[1] / 2))
    h4.move(h4.ports[2], h3.ports[2]).movex(-hwr)

    # CENTER BIT
    height = h3.ports[1].midpoint[1] - h2.ports[1].midpoint[1] + hwl / 2 + hwr / 2
    width = loop_size[0] / 4
    stubL = ((-rw - loop_size[0] / 2) - h2.ports[1].midpoint[0]) - width
    stubR = (h3.ports[1].midpoint[0] - (-rw - loop_size[0] / 2)) - width
    fpcenter = pg.flagpole(
        size=(height, width), stub_size=(hwl, stubL), shape="q", taper_type="fillet"
    )
    c1 = D << fpcenter.rotate(-90)
    c1.move(c1.ports[1], h2.ports[1])

    fpcenter = pg.flagpole(
        size=(height, width), stub_size=(hwl, stubR), shape="q", taper_type="fillet"
    )
    c2 = D << fpcenter.rotate(90)
    c2.move(c2.ports[1], h3.ports[1])

    step1 = pg.optimal_step(hwl, hrout, symmetric=True, anticrowding_factor=0.5)
    s1 = D << step1
    s1.connect(s1.ports[1], h1.ports[1])

    step2 = pg.optimal_step(hwr, hrout, symmetric=True, anticrowding_factor=0.5)
    s2 = D << step2
    s2.connect(s2.ports[1], h4.ports[1])

    D = pg.union(D)
    D.flatten(single_layer=hlayer)
    outline_loop = pg.outline(
        memory_loop(loop_size, lw, rw, port, vert, layer=layer),
        distance=0.1,
        open_ports=True,
        layer=layer,
    )
    loop = D << outline_loop
    D.add_port(name=1, port=loop.ports[1])
    D.add_port(name=2, port=loop.ports[2])
    D.add_port(name=3, port=s1.ports[2])
    D.add_port(name=4, port=s2.ports[2])
    D.flatten()
    return D


def memory1(
    loop_size=(1, 2),
    lw=0.2,
    rw=0.4,
    port=1,
    vert=1.5,
    layer=1,
    hwl=0.2,
    hwr=0.1,
    hll=0.5,
    hlr=1.25,
    hlayer=2,
):

    D = Device()
    # LEFT SIDE
    heaterL = pg.straight(size=(hwl, hll))
    h1 = D << heaterL
    h1.rotate(-90)
    h1.move(h1.center, destination=(-loop_size[0] - rw - lw / 2, -loop_size[1] / 2))

    # #RIGHT SIDE
    h3 = D << pg.straight(size=(hwr, hlr))
    h3.rotate(-90)
    # h4 = D<<heaterR.rotate(-90)
    h3.move(h3.center, destination=(-rw / 2, -loop_size[1] / 2))
    # h4.move(h4.ports[2], h3.ports[2]).movex(-hwr)

    step1 = pg.optimal_step(hwl, hwl * 2, symmetric=True, anticrowding_factor=0.5)
    s1 = D << step1
    s1.connect(s1.ports[1], h1.ports[1])
    s2 = D << step1
    s2.connect(s2.ports[1], h1.ports[2])

    step2 = pg.optimal_step(hwr, hwl * 2, symmetric=True, anticrowding_factor=0.5)
    s3 = D << step2
    s3.connect(s3.ports[1], h3.ports[2])
    s4 = D << step2
    s4.connect(s4.ports[1], h3.ports[1])
    # height = h3.ports[1].midpoint[1]-h2.ports[1].midpoint[1]+hwl/2+hwr/2
    # width = loop_size[0]/4
    # stubL = ((-rw-loop_size[0]/2)-h2.ports[1].midpoint[0]) - width
    # stubR = (h3.ports[1].midpoint[0]-(-rw-loop_size[0]/2)) - width
    # fpcenter = pg.flagpole(size=(height, width), stub_size=(hwl, stubL), shape='q', taper_type='fillet')
    # c1 = D<<fpcenter.rotate(-90)
    # c1.move(c1.ports[1], h2.ports[1])

    # fpcenter = pg.flagpole(size=(height, width), stub_size=(hwl, stubR), shape='q', taper_type='fillet')
    # c2 = D<<fpcenter.rotate(90)
    # c2.move(c2.ports[1], h3.ports[1])

    # D = pg.union(D)
    # D.flatten(single_layer=hlayer)
    loop = D << memory_loop(loop_size, lw, rw, port, vert, layer=layer)
    # D.add_port(name=1, port=loop.ports[1])
    # D.add_port(name=2, port=loop.ports[2])
    # D.add_port(name=3, port=h1.ports[1])
    # D.add_port(name=4, port=h4.ports[1])
    # D.flatten()
    return D


# def memory_filled(loop_size=(2, 2), lw=0.2, rw=0.4, port=.2, vert=1.5, layer=1, hwl=.1, hwr=.1, hll=.5, hlr=1.25, hrout=.75, hlayer=2, port_shift=0.5):


#     D = Device()

#     left = pg.flagpole(size=(loop_size[0]+lw+rw, port/4), stub_size=(lw,rw), taper_type='fillet')
#     right = pg.flagpole(size=(loop_size[0]+lw+rw, port/4), stub_size=(rw,rw), taper_type='fillet', shape='q')

#     topL = D<<left
#     topR = D<<right
#     topL.move(topL.ports[2], topR.ports[2])

#     branchL = pg.straight(size=(lw, loop_size[1]-2*rw))
#     bL = D<<branchL
#     bL.connect(bL.ports[1], topL.ports[1])

#     branchR = pg.straight(size=(rw, loop_size[1]-2*rw))
#     bR = D<<branchR
#     bR.connect(bR.ports[1], topR.ports[1])

#     bleft = pg.flagpole(size=(loop_size[0]+lw+rw, port/4), stub_size=(lw,rw), taper_type='fillet',  shape='q')
#     bottomL = D<<bleft
#     bottomL.connect(bottomL.ports[1], bL.ports[2])

#     bright = pg.flagpole(size=(loop_size[0]+lw+rw, port/4), stub_size=(rw,rw), taper_type='fillet',  shape='p')
#     bottomR = D<<bright
#     bottomR.connect(bottomR.ports[1], bR.ports[2])

#     fake_port = D.add_port(name='top', midpoint=(-(loop_size[0]+lw+rw)/2+port_shift, vert/2), orientation=-90)

#     prout = pr.route_basic(topL.ports[2], fake_port, path_type='sine', width_type='sine')
#     conn1 = D<<prout
#     conn2 = D<<prout
#     conn2.connect(conn2.ports[1], bottomL.ports[2])

#     rec = pr.route_basic(conn1.ports[1], conn2.ports[1])
#     fill = D<<rec

#     D = pg.union(D)
#     D.add_port(name=1, port=conn1.ports[2])
#     D.add_port(name=2, port=conn2.ports[2])

#     D.flatten(single_layer=layer)
#     D.move(D.center, (0,0))
#     qp(D)
#     return D


def memory_filled(loop_size=(2, 2), lw=0.2, rw=0.4):

    D = Device()
    opts = pg.optimal_step(1.5, loop_size[0] + lw + rw, anticrowding_factor=0.1)
    conn1 = D << opts

    return D


# DEV = memory(loop_size=(1, 2),
#               lw=0.1,
#               rw=0.69,
#               port=0.5,
#               vert=1.5,
#               layer=1,
#               hwl=.1,
#               hwr=.1,
#               hll=.5,
#               hlr=1.25,
#               hrout=.75,
#               hlayer=2)
# DEV.move(DEV.center, (0,0))
# cell = pg.extract(DEV, [1])
# HEATER = pg.extract(DEV, [2])
# x=5
# y = cell.bbox[1][1]*2
# box = pg.rectangle((x,y),layer=3)
# box.move(box.center, (0,0))
# OUTLINE = pg.boolean(box, cell, 'A-B')

# D = Device()
# D<<OUTLINE
# # D.write_gds(r'G:\My Drive\...Projects\_electronics\nMem\simulation\geometry\phidl_exports\nMem_comsol_outline.gds')
# qp(D)

# # D = Device()
# # D<<HEATER
# # D.write_gds(r'G:\My Drive\...Projects\_electronics\nMem\simulation\geometry\phidl_exports\nMem_comsol_heater.gds')

# D = Device()
# D<<memory_filled()
# D.write_gds(r'G:\My Drive\...Projects\_electronics\nMem\simulation\geometry\phidl_exports\nMem_comsol_filled.gds')


# def tesla_valve(width=0.2, length=4, angle=18, num=5):
#     D = Device('tesla_valve')

#     hp = pg.optimal_hairpin(width, width*3, length)
#     hp.rotate(180)
#     ramp = pg.ramp(length=length/1.6, width1=width*7, width2=width*3)
#     r = D<<ramp
#     h = D<<hp
#     h.connect(h.ports[2], r.ports[1]).rotate(180, h.ports[2])

#     d = pg.boolean(h, r, 'A-B')
#     D.remove([r, h])
#     port_list = []
#     D.add_port(name='start', midpoint=(0,0), width=width, orientation=0)
#     for i in range(num):
#         turn = D<<hp
#         turn.rotate(-angle)
#         turn.movex(length*i)
#         turn.movey(origin=turn.ports[1].midpoint[1], destination=0)

#         if i%2 == 0:
#             turn.mirror(p1=(1,0))

#     port_list.extend(D.get_ports(depth=3))
#     D.add_port(name='end', midpoint=(length*num,0), width=width, orientation=0)
#     port_list.append(D.ports['end'])

#     for port in port_list:
#         if port.name == 1:
#             port_list.remove(port)
#     for i in range(1, len(port_list)):
#         new_port = port_list[i]
#         new_port.orientation = port_list[i-1].orientation+180
#         print(port_list[i-1].orientation)
#         print(new_port.orientation)
#         D<<pr.route_basic(port_list[i-1], new_port, path_type='straight')

#     return D, port_list


def tesla_valve(width=0.2, pitch=0.6, length=4, angle=15, num=5):
    D = Device("tesla_valve")

    hp = pg.optimal_hairpin(width, pitch, length)
    hp.move(hp.bbox[0], destination=(0, 0))
    hp.rotate(-angle, center=(hp.ports[1].midpoint))

    ramp = pg.straight(size=(length, width + pitch))
    r = D << ramp
    r.movex(-pitch)
    h = D << hp

    d = pg.boolean(h, r, "A-B")
    d.movex(d.bbox[0][0], destination=0)
    d.rotate(angle / 2)
    D.remove([h, r])

    d.add_port(name=1, midpoint=(0, width / 2), width=width, orientation=180)
    d.add_port(
        name=2,
        midpoint=(
            length * np.cos(angle / 2 * np.pi / 180),
            width / 2 + length * np.sin(angle / 2 * np.pi / 180),
        ),
        width=width,
        orientation=0,
    )
    d << pr.route_basic(d.ports[1], d.ports[2], path_type="straight")

    dd = pg.union(d, precision=1e-8)
    dd.add_port(name=1, port=d.ports[1])
    dd.add_port(name=2, port=d.ports[2])

    D_list = np.tile(dd, num)

    for i in range(num):

        vert = D << D_list[i]

        if i % 2 == 0:
            vert.mirror(p1=(1, 0))
        if i == 0:
            next_port = vert.ports[2]
        if i > 0:
            vert.connect(vert.ports[1], next_port)
            next_port = vert.ports[2]

    port_list = D.get_ports()
    D = pg.union(D, precision=1e-10)
    D.add_port(name=1, port=port_list[0])
    D.add_port(name=2, port=port_list[-1])
    return D


def via_square(width=3, inset=2, layers=[0, 1, 2], outline=False):
    D = Device("via")
    via0 = pg.compass(size=(width + 2 * inset, width + 2 * inset), layer=layers[0])
    v0 = D << via0

    via1 = pg.compass(size=(width, width), layer=layers[1])
    v1 = D << via1
    v1.move(v1.center, v0.center)

    via2 = pg.compass(size=(width + 2 * inset, width + 2 * inset), layer=layers[2])
    v2 = D << via2
    v2.move(v2.center, v1.center)

    D.flatten()

    if outline:
        E = pg.copy_layer(D, layer=0, new_layer=0)
        D.remove_layers(layers=[0])
        E = pg.outline(E, distance=outline, layer=0)
        D << E

        F = pg.copy_layer(D, layer=2, new_layer=2)
        D.remove_layers(layers=[2])
        F = pg.outline(F, distance=outline, layer=2)
        D << F

    port_list = [v0.ports["N"], v0.ports["S"], v0.ports["E"], v0.ports["W"]]
    [D.add_port(name=n + 1, port=port_list[n]) for n in range(len(port_list))]

    return D


def via_round(width=3, inset=2, layers=[0, 1, 2], outline=False):
    D = Device("via")
    via0 = pg.compass(size=(width + 2 * inset, width + 2 * inset), layer=layers[0])
    v0 = D << via0

    via1 = pg.circle(radius=width / 2, layer=layers[1])
    v1 = D << via1
    v1.move(v1.center, v0.center)

    via2 = pg.compass(size=(width + 2 * inset, width + 2 * inset), layer=layers[2])
    v2 = D << via2
    v2.move(v2.center, v1.center)

    D.flatten()

    if outline:
        E = pg.copy_layer(D, layer=0, new_layer=0)
        D.remove_layers(layers=[0])
        E = pg.outline(E, distance=outline, layer=0)
        D << E

        F = pg.copy_layer(D, layer=2, new_layer=2)
        D.remove_layers(layers=[2])
        F = pg.outline(F, distance=outline, layer=2)
        D << F

    port_list = [v0.ports["N"], v0.ports["S"], v0.ports["E"], v0.ports["W"]]
    [D.add_port(name=n + 1, port=port_list[n]) for n in range(len(port_list))]

    return D


# def mTron(num_gate=4, gate_p=0.3, choke_w=0.03, channel_w=0.1, layer=1,
#           t_max=60, t_min=0):
#     '''
#     PROBABLY WOULD NOT WORK AS THE FIRST GATE WILL ALWAYS BE HOT AND LIKELY
#     SWITCH THE WHOLE CHANNEL. ALSO THE MOTION OF THE HOTSPOT IS UNCONTROLALLBLE.

#     Parameters
#     ----------
#     num_gate : TYPE, optional
#         DESCRIPTION. The default is 4.
#     gate_p : TYPE, optional
#         DESCRIPTION. The default is 0.3.
#     choke_w : TYPE, optional
#         DESCRIPTION. The default is 0.03.
#     channel_w : TYPE, optional
#         DESCRIPTION. The default is 0.1.
#     layer : TYPE, optional
#         DESCRIPTION. The default is 1.
#     t_max : TYPE, optional
#         DESCRIPTION. The default is 60.
#     t_min : TYPE, optional
#         DESCRIPTION. The default is 0.

#     Returns
#     -------
#     D : TYPE
#         DESCRIPTION.

#     '''

#     choke_l = 0.4
#     gate_w = 0.2
#     D = Device('mTron')
#     channel = pg.compass_multi(size=(channel_w, gate_p*(num_gate+1)), ports={'N':1, 'S':1, 'W':num_gate})
#     c = D<<channel

#     choke = pg.taper(choke_l, gate_w, choke_w)

#     port_list=[]
#     thetas = np.linspace(t_min, t_max, num_gate)
#     for i, t in zip(range(num_gate), thetas):
#         k = D<<choke
#         k.connect(k.ports[2],channel.ports['W'+str(i+1)])
#         k.rotate(-t, k.ports[2])
#         k.movex(np.sin(np.pi*t/180)*k.ports[2].width/2)
#         port_list.append(k.ports[1])

#     return D


def _via_iterable(
    via_spacing, wire_width, wiring1_layer, wiring2_layer, via_layer, via_width
):
    """Helper function for test_via.

    Parameters
    ----------
    via_spacing : int or float
        Distance between vias.
    wire_width : int or float
        The width of the wires.
    wiring1_layer : int
        Specific layer to put the top wiring on.
    wiring2_layer : int
        Specific layer to put the bottom wiring on.
    via_layer : int
        Specific layer to put the vias on.
    via_width : int or float
        Diameter of the vias.

    Returns
    -------
    VI : Device
    """
    VI = Device("test_via_iter")
    wire1 = VI.add_ref(pg.compass(size=(via_spacing, wire_width), layer=wiring1_layer))
    wire2 = VI.add_ref(pg.compass(size=(via_spacing, wire_width), layer=wiring2_layer))
    via1 = VI.add_ref(pg.compass(size=(via_width, via_width), layer=via_layer))
    via2 = VI.add_ref(pg.compass(size=(via_width, via_width), layer=via_layer))
    wire1.connect(port="E", destination=wire2.ports["W"], overlap=wire_width)
    via1.connect(
        port="W", destination=wire1.ports["E"], overlap=(wire_width + via_width) / 2
    )
    via2.connect(
        port="W", destination=wire2.ports["E"], overlap=(wire_width + via_width) / 2
    )
    VI.add_port(name="W", port=wire1.ports["W"])
    VI.add_port(name="E", port=wire2.ports["E"])
    VI.add_port(
        name="S",
        midpoint=[wire2.xmax - wire_width / 2, -wire_width / 2],
        width=wire_width,
        orientation=-90,
    )
    VI.add_port(
        name="N",
        midpoint=[wire2.xmax - wire_width / 2, wire_width / 2],
        width=wire_width,
        orientation=90,
    )

    return VI


def test_via(
    num_vias=100,
    wire_width=10,
    via_width=15,
    via_spacing=40,
    max_y_spread=300,
    wiring1_layer=1,
    wiring2_layer=2,
    via_layer=3,
):
    """Via chain test structure.

    Parameters
    ----------
    num_vias : int
        The total number of requested vias (must be an even number).
    wire_width : int or float
        The width of the wires.
    via_width : int or float
        Diameter of the vias.
    via_spacing : int or float
        Distance between vias.
    pad_size : array-like[2]
        (width, height) of the pads.
    min_pad_spacing : int or float
        Defines the minimum distance between the two pads.
    pad_layer : int
        Specific layer to put the pads on.
    wiring1_layer : int
        Specific layer to put the top wiring on.
    wiring2_layer : int
        Specific layer to put the bottom wiring on.
    via_layer : int
        Specific layer to put the vias on.

    !! Design rules : wire_width - via_width > 0.6um !!
    (The via should be smaller than the route)



    Returns
    -------
    VR : Device
        A Device containing the test via structures.

    Usage
    -----
    Call via_route_test_structure() by indicating the number of vias you want
    drawn. You can also change the other parameters however if you do not
    specifiy a value for a parameter it will just use the default value
    Ex::

        via_route_test_structure(num_vias=54)

    - or -::

        via_route_test_structure(num_vias=12, pad_size=(100,100),wire_width=8)

    ex: via_route(54, min_pad_spacing=300)
    """
    VR = Device("test_via")

    nub = VR.add_ref(pg.compass(size=(3 * wire_width, wire_width), layer=wiring1_layer))
    # nub_overlay = VR.add_ref(pg.compass(size=(3 * wire_width, wire_width), layer=wiring1_layer))

    # Square at the start of the chain
    head = VR.add_ref(pg.compass(size=(wire_width, wire_width), layer=wiring1_layer))
    # head_overlay = VR.add_ref(pg.compass(size=(wire_width, wire_width), layer=wiring1_layer))
    nub.ymax = wire_width / 2
    nub.xmin = 0
    # nub_overlay.ymax = wire_width/2
    # nub_overlay.xmin = 0
    head.connect(port="W", destination=nub.ports["E"])
    # head_overlay.connect(port="W", destination=nub_overlay.ports["E"])
    # pad1_overlay.xmin = pad1.xmin
    # pad1_overlay.ymin = pad1.ymin

    old_port = head.ports["N"]
    count = 0
    width_via_iter = 2 * via_spacing - 2 * wire_width

    current_width = 3 * wire_width + wire_width  # width of nub and 1 overlap
    obj_old = head
    obj = head
    via_iterable = _via_iterable(
        via_spacing, wire_width, wiring1_layer, wiring2_layer, via_layer, via_width
    )

    while (count + 2) <= num_vias:
        obj = VR.add_ref(via_iterable)
        obj.connect(port="W", destination=old_port, overlap=wire_width)
        old_port = obj.ports["E"]
        # Check if the vias chain reaches the max height
        if obj.ymax > max_y_spread / 2:
            obj.connect(port="W", destination=obj_old.ports["S"], overlap=wire_width)
            old_port = obj.ports["S"]
            current_width += width_via_iter

        elif obj.ymin < -max_y_spread / 2:
            obj.connect(port="W", destination=obj_old.ports["N"], overlap=wire_width)
            old_port = obj.ports["N"]
            current_width += width_via_iter
        count = count + 2
        obj_old = obj

    # Square at the end
    tail = VR.add_ref(
        pg.compass(
            size=(wire_width, wire_width),
            layer=wiring1_layer,
        )
    )

    tail.connect(port="W", destination=obj.ports["S"], overlap=wire_width)

    VR.add_port(
        name=1,
        midpoint=(obj.center[0] + 2 * via_spacing + wire_width, 0),
        width=wire_width,
        orientation=180,
    )
    VR << pr.route_smooth(
        port1=VR.ports[1],
        port2=obj.ports["E"],
        radius=2 * wire_width,
        layer=wiring1_layer,
    )
    VR.add_port(name=2, port=nub.ports["W"])
    VR.ports[1].orientation = (
        0  # Change the orientation otherwize won't connect to pads
    )

    return VR


def memory_v2(left_side=0.2, right_side=0.4, notch_factor=0.25):
    D = Device("nMem")

    top = pg.flagpole(size=(2, 1.5), stub_size=(0.5, 0.25), taper_type="fillet")
    t1 = D << top

    left = pg.optimal_step(
        start_width=0.5, end_width=left_side, anticrowding_factor=0.5, symmetric=True
    )
    l1 = D << left
    l1.rotate(-90)
    l1.move((l1.bbox[0][0], l1.bbox[1][1]), t1.bbox[0])

    top2 = pg.flagpole(
        size=(2, 0.25), stub_size=(0.5, 0.25), taper_type="fillet", shape="q"
    )
    t2 = D << top2
    t2.connect(t2.ports[1], l1.ports[1])
    t2.movex(2)

    corner = pg.optimal_step(2, 2.5, anticrowding_factor=0.05)
    c1 = D << corner
    c1.connect(c1.ports[1], t1.ports[2].rotate(180))
    c1.movey(-0.3)

    straight = pg.straight(size=(2.5, 0.25))
    s1 = D << straight
    s1.connect(s1.ports[1], c1.ports[2])

    right = pg.optimal_step(
        start_width=0.5, end_width=right_side, symmetric=False, anticrowding_factor=0.1
    )
    r1 = D << right
    r1.connect(r1.ports[1], t2.ports[1])

    leftstraight = pg.straight(size=(left_side, 0.1))
    ls = D << leftstraight
    ls.connect(ls.ports[1], l1.ports[2])

    rightstriaght = pg.straight(
        size=(right_side, -ls.ports[2].midpoint[1] + r1.ports[2].midpoint[1])
    )
    rs = D << rightstriaght
    rs.connect(rs.ports[2], r1.ports[2])
    D = pg.union(D)
    tophalf = pg.union(D)

    bottomhalf = tophalf.mirror(p1=ls.ports[2].midpoint, p2=rs.ports[1].midpoint)
    bf = D << bottomhalf
    D = pg.union(D)
    # qp(D)

    return D


def memory_v3(
    left_side=0.2,
    right_side=0.4,
    notch_factor=None,
    layer=1,
    right_notch_shift=0.6,
    cell_width=4,
    right_side_length=0.8,
):
    D = Device("nMem")

    column_width = 2

    left_side_buffer = column_width / 1.25
    right_side_buffer = right_side
    stub_length = 1
    stub_substract = stub_length / 2

    left_side_length = left_side

    top = pg.optimal_step(column_width, cell_width, anticrowding_factor=0.05)
    t1 = D << top
    t1.rotate(-90)
    t1.move(t1.bbox[0], (0, 0))

    topright = pg.flagpole(
        size=(cell_width, right_side / 2),
        stub_size=(right_side_buffer, stub_length),
        taper_type="fillet",
        shape="q",
    )
    tright = D << topright
    tright.connect(tright.ports[2], t1.ports[2])

    topleft = pg.flagpole(
        size=(cell_width, right_side / 2),
        stub_size=(left_side_buffer, stub_length),
        taper_type="fillet",
    )
    tleft = D << topleft
    tleft.connect(tleft.ports[2], t1.ports[2])

    stub_cut = pg.straight(size=(cell_width, stub_substract))
    scut = D << stub_cut
    scut.move(scut.bbox[0], D.bbox[0])
    D = pg.boolean(D, scut, "A-B")
    D.add_port(port=t1.ports[1])
    D.add_port(port=tleft.ports[1], name=2)
    D.add_port(port=tright.ports[1], name=3)

    D.ports[2].midpoint = D.ports[2].midpoint + (0, stub_substract)
    D.ports[3].midpoint = D.ports[3].midpoint + (0, stub_substract)

    rightcon = pg.straight(size=(right_side, right_side_length))
    rightc = D << rightcon
    rightc.move(rightc.ports[1], D.ports[3].midpoint - (0, right_side_length / 2))

    leftcon = pg.straight(size=(left_side, left_side_length))
    leftc = D << leftcon
    leftc.connect(leftc.ports[1], D.ports[2])
    leftc.move(leftc.center, (leftc.ports[1].midpoint[0], rightc.center[1]))

    leftconnect = pr.route_basic(D.ports[2], leftc.ports[1], width_type="sine")
    leftstub = D << leftconnect

    rightconnect = pr.route_basic(D.ports[3], rightc.ports[1], width_type="sine")
    rightstub = D << rightconnect

    D = pg.union(D)
    D.add_port(port=t1.ports[1])
    D.add_port(port=leftc.ports[2])
    D.add_port(port=rightc.ports[2], name=3)
    A = pg.copy(D)
    A.mirror(p1=leftc.center, p2=leftc.center + (1, 0))
    D << A
    D.ports[2].midpoint = (
        D.ports[2].midpoint[0],
        D.ports[2].midpoint[1] + left_side_length / 2,
    )
    D.move(origin=D.ports[2], destination=(0, 0))
    D.ports[3].midpoint = (D.ports[3].midpoint[0], 0)
    port_list = [D.ports[1], D.references[0].ports[1], D.ports[2], D.ports[3]]

    D = pg.union(D)
    D.add_port(port=port_list[0], name=1)
    D.add_port(port=port_list[1], name=2)
    D.add_port(port=port_list[2], name=3)
    D.add_port(port=port_list[3], name=4)

    if notch_factor:
        notchl = pg.straight(size=(left_side * notch_factor, left_side * notch_factor))
        leftn = D << notchl
        leftn.move(leftn.center, D.ports[3])
        leftn.rotate(45, D.ports[3].midpoint)
        leftn.movex(-left_side / 2)

        notchr = pg.straight(
            size=(right_side * notch_factor, right_side * notch_factor)
        )
        rightn = D << notchr
        rightn.move(rightn.center, D.ports[4])
        rightn.rotate(45, D.ports[4])
        rightn.movex(-right_side / 2)
        rightn.movey(-right_notch_shift)

        rightnclip = D << notchr
        rightnclip.rotate(45)
        rightnclip.move(rightnclip.center, rightn.center)
        rightnclip.move(
            rightnclip.center,
            rightnclip.center
            - (right_side * notch_factor / 2, right_side * notch_factor / 2),
        )
        D = pg.boolean(D, [leftn, rightn, rightnclip], "A-B")
        D.add_port(port=port_list[0])
        D.add_port(port=port_list[1], name=2)
    D.flatten(single_layer=layer)
    return D


# D = memory_v3(notch_factor=.25, cell_width=5, right_side_length=1)
# qp(D)


def memory_v4(
    left_width=0.2,
    right_width=0.4,
    right_extension=1,
    route_width=2,
    device_layer=1,
    heater_layer=2,
):

    D = Device()

    top_conn = pg.compass_multi(
        size=(route_width, route_width), ports={"N": 1, "E": 3, "W": 1, "S": 2}
    )
    TCONN = D << top_conn

    port1 = TCONN.ports["N1"]

    top_right = pg.flagpole(
        size=(route_width, route_width),
        stub_size=(right_width, right_extension),
        taper_type="fillet",
    )
    TRIGHT = D << top_right
    TRIGHT.connect(TRIGHT.ports[2], TCONN.ports["W1"].rotate(180))

    arc_right = pg.arc(radius=right_width, width=right_width, theta=-90, start_angle=90)
    AR = D << arc_right
    AR.connect(AR.ports[1], TRIGHT.ports[1])

    top_left = pg.flagpole(
        size=(route_width, route_width),
        stub_size=(route_width / 2, right_width),
        taper_type="fillet",
    )
    TLEFT = D << top_left
    TLEFT.connect(TLEFT.ports[2], TCONN.ports["N1"].rotate(180))

    D.add_port(
        name="l",
        midpoint=(TLEFT.ports[1].midpoint[0], TLEFT.ports[1].midpoint[1] - 0.5),
        orientation=90,
        width=left_width,
    )  ################

    LR = D << pr.route_basic(TLEFT.ports[1], D.ports["l"], width_type="sine")

    left_ext = pg.straight(size=(left_width, 0.5))  ##############
    LEFTEXT = D << left_ext
    LEFTEXT.connect(LEFTEXT.ports[2], LR.ports[2])

    D.add_port(
        name="r",
        midpoint=(AR.ports[2].midpoint[0], LEFTEXT.ports[1].midpoint[1]),
        orientation=90,
        width=right_width,
    )  ################
    RR = D << pr.route_basic(AR.ports[2], D.ports["r"], width_type="sine")

    E = pg.union(D)

    E.mirror(LEFTEXT.ports[1].midpoint, D.ports["r"].midpoint)
    D << E

    DD = pg.copy(D)
    D = pg.union(D, precision=1e-5, layer=device_layer)

    notch_size = 0.1 / np.sqrt(2)  ###########

    heater_spacing = 1.5  #############
    heater_width = 0.1

    notch_bool = True
    if notch_bool == True:
        E = Device()
        notch = pg.rectangle(size=(notch_size, notch_size))
        N1a = E << notch
        N1a.rotate(45)
        N1a.move(N1a.center, LEFTEXT.ports[1].midpoint)
        N1a.movex(-left_width / 2)

        N1b = E << notch
        N1b.rotate(45)
        N1b.move(N1b.center, LEFTEXT.ports[1].midpoint)
        N1b.movex(left_width / 2)

        N2a = E << notch
        N2a.rotate(45)
        N2a.move(N2a.center, DD.ports["r"].midpoint)
        N2a.movex(-right_width / 2)
        N2a.movey(-heater_spacing / 2)

        N2b = E << notch
        N2b.rotate(45)
        N2b.move(N2b.center, DD.ports["r"].midpoint)
        N2b.movex(right_width / 2)
        N2b.movey(-heater_spacing / 2)

        D = pg.boolean(D, E, "A-B", layer=device_layer)

    heater_bool = True
    if heater_bool == True:
        E = Device()
        heater = pg.straight(size=(heater_width, 1))

        H1 = E << heater
        H1.rotate(90)
        H1.move(H1.center, LEFTEXT.ports[1].midpoint)

        H2 = E << heater
        H2.rotate(90)
        H2.move(H2.center, DD.ports["r"].midpoint)
        H2.movey(-heater_spacing / 2)

        H3 = E << heater
        H3.rotate(90)
        H3.move(H3.center, DD.ports["r"].midpoint)
        H3.movey(heater_spacing / 2)

        h0 = E << pg.straight(size=(heater_width * 4, heater_width))

        p0 = (H1.ports[1].midpoint[0] - 0.25, H1.ports[2].midpoint[1])
        p1 = (H1.ports[2].midpoint[0] + 0.25, H1.ports[2].midpoint[1])
        p2 = (H2.ports[1].midpoint[0] - 0.25, H2.ports[2].midpoint[1])
        p3 = (H2.ports[2].midpoint[0] + 0.25, H2.ports[2].midpoint[1])
        p4 = (H3.ports[1].midpoint[0] - 0.25, H3.ports[1].midpoint[1])
        p5 = (H3.ports[2].midpoint[0] + 0.25, H3.ports[1].midpoint[1])
        p6 = (H1.ports[2].midpoint[0] + right_extension + 4, H1.ports[2].midpoint[1])

        E.add_port(name=0, midpoint=p0, orientation=0, width=heater_width * 4)
        E.add_port(name=1, midpoint=p1, orientation=180, width=heater_width * 4)
        E.add_port(name=2, midpoint=p2, orientation=0, width=heater_width * 4)
        E.add_port(name=3, midpoint=p3, orientation=180, width=heater_width * 3)
        E.add_port(name=4, midpoint=p4, orientation=0, width=heater_width * 4)
        E.add_port(name=5, midpoint=p5, orientation=180, width=heater_width * 3)
        E.add_port(name=6, midpoint=p6, orientation=180, width=heater_width * 4)
        E.add_port(
            name=7,
            midpoint=E.ports[4].midpoint + (0, 1.5),
            orientation=180,
            width=heater_width * 4,
        )

        h0.connect(h0.ports[2], E.ports[0].rotate(180))
        E << pr.route_sharp(H1.ports[1], E.ports[0].rotate(180))
        E << pr.route_sharp(H1.ports[2], E.ports[1])
        E << pr.route_sharp(H2.ports[1], E.ports[2])
        E << pr.route_sharp(H2.ports[2], E.ports[3])
        E << pr.route_sharp(H3.ports[1], E.ports[4])
        E << pr.route_sharp(H3.ports[2], E.ports[5])

        E << pr.route_sharp(
            E.ports[1].rotate(180),
            E.ports[2].rotate(180),
            path_type="Z",
            length1=0.2,
            length2=0.2,
        )
        E << pr.route_sharp(
            E.ports[4].rotate(180), E.ports[7], path_type="U", length1=0.3
        )
        # E<<pr.route_smooth(E.ports[7].rotate(180), E.ports[8], path_type='Z', length1=1, length2=0.5, radius=0.6)
        E << pr.route_sharp(
            E.ports[5].rotate(180), E.ports[3], path_type="U", length1=0.2
        )

        # arc1 = E<<pg.arc(radius=heater_spacing/2, width=heater_width*3, theta=180)
        # arc1.connect(arc1.ports[1], E.ports[3].rotate(180))

        port3 = h0.ports[1]

        E << pr.route_sharp(
            E.ports[7].rotate(180), E.ports[6], path_type="Z", length1=2, length2=0.5
        )
        port4 = E.ports[6].rotate(180)
        E = pg.union(E, layer=heater_layer)
    D << E

    D = pg.union(D, by_layer=True)
    D.flatten()

    D.add_port(1, port=TCONN.ports["N1"])
    D.add_port(2, midpoint=(0, D.bbox[0][1]), width=route_width, orientation=-90)
    D.add_port(3, port=port3)
    D.add_port(4, port=port4)

    D.move(H1.center, (0, 0))
    D.flatten()

    return D


# D = memory_v4(right_extension=1)
# qp(D)


def memory_heater(
    left_side=0.1,
    right_side1=0.1,
    right_side2=0.1,
    right_space=1.2,
    right_sidex=3,
    layer=2,
):
    D = Device("memory_heater")

    left_length = left_side * 5
    right_length = right_side1 * 7

    centerx = 0.7
    centery = 0.3
    routing = 0.5
    turnback_width = 0.3
    heater_out_dist = right_sidex + 2.5

    heatleft = pg.straight(size=(left_side, left_length))
    heatl = D << heatleft
    heatl.rotate(90)
    heatl.move(heatl.center, (0, 0))

    heatright1 = pg.straight(size=(right_side1, right_length))
    heatr1 = D << heatright1
    heatr1.rotate(90)
    heatr1.move(heatr1.center, (right_sidex, -right_space / 2))

    heatright2 = pg.straight(size=(right_side2, right_length))
    heatr2 = D << heatright2
    heatr2.rotate(90)
    heatr2.move(heatr2.center, (right_sidex, right_space / 2))

    leftstep = pg.optimal_step(
        left_side, centery, symmetric=True, anticrowding_factor=0.5
    )
    lefts1 = D << leftstep
    lefts1.connect(lefts1.ports[1], heatl.ports[2])
    lefts2 = D << pg.optimal_step(
        left_side, routing, symmetric=True, anticrowding_factor=0.5
    )
    lefts2.connect(lefts2.ports[1], heatl.ports[1])

    rightstep = pg.optimal_step(
        left_side, centery, symmetric=True, anticrowding_factor=0.5
    )
    rights1 = D << rightstep
    rights1.connect(rights1.ports[1], heatr1.ports[1])
    rights2 = D << pg.optimal_step(
        left_side, centery * 1.5, symmetric=True, anticrowding_factor=0.5
    )
    rights2.connect(rights2.ports[1], heatr2.ports[1])

    leftcon = pr.route_basic(lefts1.ports[2], rights1.ports[2], width_type="sine")
    D << leftcon

    rightstep = pg.optimal_step(
        left_side, centery, symmetric=True, anticrowding_factor=0.5
    )
    rights3 = D << rightstep
    rights3.connect(rights3.ports[1], heatr1.ports[2])
    rights4 = D << rightstep
    rights4.connect(rights4.ports[1], heatr2.ports[2])

    turnback = pg.arc(radius=right_space / 2, width=centery, theta=180, start_angle=-90)
    tb = D << turnback
    tb.connect(tb.ports[1], rights3.ports[2])

    turnback = pg.arc(radius=0.5, width=centery * 1.5, theta=180, start_angle=-90)
    tb1 = D << turnback
    tb1.connect(tb1.ports[2], rights2.ports[2])

    hs_length = (rights4.ports[2].midpoint[0] - rights2.ports[2].midpoint[0]) + 0.5
    heatstraight = pg.straight(size=(centery * 1.5, hs_length))
    hstraight = D << heatstraight
    hstraight.connect(hstraight.ports[1], tb1.ports[1])

    rightout = pg.optimal_step(
        centery, routing, symmetric=True, anticrowding_factor=0.5
    )
    ro = D << rightout
    ro.move(ro.ports[1], (heater_out_dist, 0))

    routout = pr.route_basic(hstraight.ports[2], ro.ports[1])
    D << routout
    port_list = [lefts2.ports[2], ro.ports[2]]
    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(port=port_list[0], name=1)
    D.add_port(port=port_list[1], name=2)

    return D


def memory_heater_dual(
    left_side=0.1,
    right_side1=0.1,
    right_side2=0.1,
    right_space=1.2,
    right_sidex=3,
    layer=2,
):
    D = Device("memory_heater_dual")

    left_length = left_side * 3
    right_length = right_side1 * 4

    centerx = 0.7
    centery = 0.4
    routing = 0.5
    turnback_width = 0.3
    heater_out_dist = right_sidex + 2

    heatleft = pg.straight(size=(left_side, left_length))
    heatl = D << heatleft
    heatl.rotate(90)
    heatl.move(heatl.center, (0, 0))

    heatright1 = pg.straight(size=(right_side1, right_length))
    heatr1 = D << heatright1
    heatr1.rotate(90)
    heatr1.move(heatr1.center, (right_sidex, -right_space / 2))

    heatright2 = pg.straight(size=(right_side2, right_length))
    heatr2 = D << heatright2
    heatr2.rotate(90)
    heatr2.move(heatr2.center, (right_sidex, right_space / 2))

    leftstep = pg.optimal_step(
        left_side, centery, symmetric=True, anticrowding_factor=0.5
    )
    lefts1 = D << leftstep
    lefts1.connect(lefts1.ports[1], heatl.ports[2])
    lefts2 = D << pg.optimal_step(
        left_side, routing, symmetric=True, anticrowding_factor=0.5
    )
    lefts2.connect(lefts2.ports[1], heatl.ports[1])

    turnback = pg.arc(radius=right_space / 3, width=centery, theta=180, start_angle=-90)
    tb1 = D << turnback
    tb1.connect(tb1.ports[2], lefts1.ports[2])

    hs_left_length = -heatl.ports[1].midpoint[0] + tb1.ports[1].midpoint[0]
    hs_left = pg.straight(size=(centery, hs_left_length))
    hsl = D << hs_left
    hsl.connect(hsl.ports[1], tb1.ports[1])

    leftstep1 = pg.optimal_step(
        centery, routing, symmetric=True, anticrowding_factor=0.4
    )
    lefts3 = D << leftstep1
    lefts3.connect(lefts3.ports[1], hsl.ports[2])

    rightstep = pg.optimal_step(
        left_side, centery, symmetric=True, anticrowding_factor=0.5
    )
    rights1 = D << rightstep
    rights1.connect(rights1.ports[1], heatr1.ports[1])
    rights2 = D << pg.optimal_step(
        left_side, centery, symmetric=True, anticrowding_factor=0.5
    )
    rights2.connect(rights2.ports[1], heatr2.ports[1])

    rightstep = pg.optimal_step(
        left_side, routing, symmetric=True, anticrowding_factor=0.5
    )
    rights3 = D << rightstep
    rights3.connect(rights3.ports[1], heatr1.ports[2])
    rights4 = D << rightstep
    rights4.connect(rights4.ports[1], heatr2.ports[2])

    turnback = pg.arc(radius=right_space / 2, width=centery, theta=180, start_angle=-90)
    tb = D << turnback
    tb.connect(tb.ports[1], rights2.ports[2])

    port_list = [lefts2.ports[2], lefts3.ports[2], rights3.ports[2], rights4.ports[2]]
    D = pg.union(D)
    D.flatten(single_layer=layer)
    D.add_port(port=port_list[0], name=1)
    D.add_port(port=port_list[1], name=2)
    D.add_port(port=port_list[2], name=3)
    D.add_port(port=port_list[3], name=4)

    return D


# qp(memory_heater_dual())


def nMem(dual_heater=False, layer1=1, layer2=2):
    D = Device("nMem")

    port_list = []
    memory = memory_v3(notch_factor=0.25, layer=layer1)
    if dual_heater:
        heater = memory_heater_dual(layer=layer2)
    else:
        heater = memory_heater(layer=layer2)
    D << memory
    port_list.extend(memory.get_ports())
    D << heater
    port_list.extend(heater.get_ports())

    D = pg.union(D, by_layer=True)

    for p, i in zip(port_list, range(0, len(port_list))):
        D.add_port(name=i + 1, port=p)

    return D


# qp(nMem(dual_heater=False))


def nanoSQUID(cwidth=0.05, width=1, loop_size=(2, 10), layer=1):
    D = Device("nanoSQUID")

    hairpin = pg.optimal_hairpin(width=width, pitch=loop_size[0], length=loop_size[1])

    hp1 = D << hairpin
    hp2 = D << hairpin

    hp1.connect(hp1.ports[1], hp2.ports[2])
    D.move(D.center, (0, 0))
    D.rotate(-90)
    h = width / 2 - cwidth / 2
    hp1.movey(h)
    hp2.movey(-h)

    D.add_port(
        "left", midpoint=(hp1.ports[1].midpoint[0], 0), orientation=90, width=cwidth
    )
    D.add_port(
        "right", midpoint=(hp2.ports[1].midpoint[0], 0), orientation=90, width=cwidth
    )
    D.add_port(
        "top", midpoint=(0, D.bbox[1][1]), width=width + loop_size[0], orientation=90
    )
    D.add_port(
        "bottom",
        midpoint=(0, D.bbox[0][1]),
        width=width + loop_size[0],
        orientation=-90,
    )

    D << pr.route_sharp(hp1.ports[1], D.ports["left"])
    D << pr.route_sharp(hp2.ports[2], D.ports["left"].rotate(180))
    D << pr.route_sharp(hp1.ports[2], D.ports["right"])
    D << pr.route_sharp(hp2.ports[1], D.ports["right"].rotate(180))

    tee = pg.tee(
        size=(loop_size[1] / 2, width),
        stub_size=(width, 3 * width),
        taper_type="fillet",
    )

    t1 = D << tee
    t1.connect(t1.ports[2], hp1.ports[2].rotate(180))
    t2 = D << tee
    t2.connect(t2.ports[1], hp2.ports[1].rotate(180))

    port_list = [D.ports["top"], D.ports["bottom"], t1.ports[3], t2.ports[3]]

    D = pg.union(D, by_layer=True)
    D.flatten(single_layer=layer)

    for p, i in zip(port_list, range(0, len(port_list))):
        D.add_port(name=i + 1, port=p)

    return D


def clover(cwidth=0.03, cwidth2=0.01, width=1, layer=1):
    D = Device("clover")

    step = pg.optimal_step(cwidth, width, symmetric="True", num_pts=200)
    s1 = D << step
    s1.move(s1.ports[1], (0, 0))
    s1.rotate(90)

    s2 = D << step
    s2.connect(s2.ports[1], s1.ports[1])

    step2 = pg.optimal_step(cwidth2, width, symmetric="True", num_pts=200)
    r1 = D << step2
    r1.move(r1.ports[1], (cwidth / 2 + 0.002, 0))
    r2 = D << step2
    r2.rotate(180)
    r2.move(r2.ports[1], (-cwidth / 2 - 0.002, 0))

    port_list = [s1.ports[2], s2.ports[2], r1.ports[2], r2.ports[2]]

    D = pg.union(D, by_layer=True)
    D.flatten(single_layer=layer)

    for p, i in zip(port_list, range(0, len(port_list))):
        D.add_port(name=i + 1, port=p)

    return D


def nw_diode(width_ch=0.5, angle=90, length=5, routing=1, layer=1):

    D = Device("nw_diode")
    info = locals()

    height = routing - width_ch
    base = 2 * height * math.tan((angle / 180) * math.pi / 2)

    nw = pg.taper(length=length, width1=routing, width2=routing, port=None, layer=0)
    nw.rotate(90)
    nw.center = (0, 0)
    tr = pg.taper(length=height, width1=base, width2=0.0001, port=None, layer=0)
    tr.move((-routing / 2, 0))

    b = D << pg.boolean(
        A=nw, B=tr, operation="not", precision=1e-6, num_divisions=[1, 1], layer=0
    )

    D = pg.union(D)
    D.add_port(port=nw.ports[2], name=1)
    D.add_port(port=nw.ports[1], name=2)
    D.flatten(single_layer=layer)

    D.info = info
    return D
