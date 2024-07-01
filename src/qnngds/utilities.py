"""Utilies is used for building cells in design.

Cells are made of devices
(found in utilities) and a die_cell border, wich contains pads, text etc... The
device and its die are linked thanks to functions present in this module.
"""

from phidl import Device, Port
import phidl.geometry as pg
import phidl.routing as pr
from typing import Optional, Tuple, List, Union, Dict, Set
from phidl.device_layout import (
    Device,
    Port,
)
import qnngds.geometries as geometry


class DieParameters:
    """A class regrouping every parameter proper to a die_cell.

    This class does not include anything linked to the device/circuit/experiment to
    be placed in the cells.

    Parameters:
        unit_die_size (tuple of (int or float, int or float)): Dimensions of a unit die/cell (width, height).
        pad_size (tuple of int or float): Dimensions of the die's pads (width, height).
        contact_l (int or float): Extra length of the routes above the die's
            ports to assure alignment with the device (useful for ebeam
            lithography).
        outline (int or float): The width of the pads' outline.
        die_layer (int): The layer where the die is placed.
        pad_layer (int): The layer where the pads are placed.
        fill_pad_layer (bool): If True, the cells are filled with ground in
            pad's layer.
        invert (bool): If True, inverts the die's layer for positive lithography.
        text_size (int or float): The size of the text in the cells.
    """

    def __init__(
        self,
        unit_die_size: Tuple[Union[int, float], Union[int, float]] = (980, 980),
        pad_size: Tuple[Union[int, float], Union[int, float]] = (150, 250),
        contact_l: Union[int, float] = 10,
        outline: Union[int, float] = 10,
        die_layer: int = 2,
        pad_layer: int = 3,
        fill_pad_layer: bool = False,
        invert: bool = True,
        text_size: Union[int, float] = 40,
    ):

        self.unit_die_size = unit_die_size
        self.unit_die_w = unit_die_size[0]
        self.unit_die_h = unit_die_size[1]
        self.pad_size = pad_size
        self.contact_l = contact_l
        self.outline = outline
        self.die_layer = die_layer
        self.pad_layer = pad_layer
        self.fill_pad_layer = fill_pad_layer
        self.invert = invert
        self.text_size = text_size

        self.die_border_w = round(
            min((pad_size[0] + outline) / 2, 0.15 * min(unit_die_size))
        )

    def calculate_available_space_for_dev(
        self,
        device_ports: List[str] = ["N", "W", "S", "E"],
    ) -> Tuple[float, float]:
        """Calculates the maximum space available for a device in a
        unit_die_cell.

        Note that the device should be even smaller than this function's output, as
        it does not account for routing from the device to the die's ports.

        Parameters:
            device_ports (List of string): a list of existing ports in the device.
                E.g.: the device has 2 ports North and 1 South, device_ports = ["N", "S"].

        Returns:
            Tuple[float, float]: A tuple containing the width and height of space
            available for a device in a die_cell
        """

        num_pads_y = 0
        num_pads_x = 0
        if "N" in device_ports:
            num_pads_y += 1
        if "S" in device_ports:
            num_pads_y += 1
        if "E" in device_ports:
            num_pads_x += 1
        if "W" in device_ports:
            num_pads_x += 1

        dev_max_x = (
            self.unit_die_size[0]
            - 2 * self.outline
            - max(
                2 * self.die_border_w,
                num_pads_x * (2 * self.outline + self.pad_size[1] + 2 * self.contact_l),
            )
        )
        dev_max_y = (
            self.unit_die_size[1]
            - 2 * self.outline
            - max(
                2 * self.die_border_w,
                num_pads_y * (2 * self.outline + self.pad_size[1] + 2 * self.contact_l),
            )
        )
        return dev_max_x, dev_max_y

    def find_num_diecells_for_dev(
        self,
        device_max_size: Tuple[Union[int, float], Union[int, float]],
        device_ports: Dict[str, int] = {"N": 1, "E": 1, "W": 1, "S": 1},
    ) -> Tuple[float, float]:
        """Finds the number of unit die cells that can accommodate a device.

        Parameters:
            device_max_size (tuple of int or float, optional): Max dimensions of the
                device inside the cell (width, height).
            device_ports (dict): The ports of the device, format must be {'N':m, 'E':n, 'W':p, 'S':q}.

        Returns:
            Tuple[float, float]: A tuple containing the number of die cells in width
            and height required to accommodate the device
        """

        max_num_ports_y = max(device_ports.get("E", 0), device_ports.get("W", 0))
        max_num_ports_x = max(device_ports.get("N", 0), device_ports.get("S", 0))

        max_x = max(
            device_max_size[0],
            max_num_ports_x * 1.5 * self.pad_size[0] + 2 * self.die_border_w,
        )
        max_y = max(
            device_max_size[1],
            max_num_ports_y * 1.5 * self.pad_size[0] + 2 * self.die_border_w,
        )
        compass_ports = [W for W in ["N", "E", "S", "W"] if device_ports.get(W, 0) != 0]

        n = 1
        dev_x_bigger = True
        available_space_for_dev = self.calculate_available_space_for_dev(
            compass_ports,
        )

        while dev_x_bigger:

            if max_x > n * available_space_for_dev[0]:
                n += 1
            else:
                break

        m = 1
        dev_y_bigger = True

        while dev_y_bigger:

            if max_y > m * available_space_for_dev[1]:
                m += 1
            else:
                break

        return n, m

    def calculate_contact_w(
        self,
        circuit_ports: List[Port],
    ) -> Union[int, float]:
        """Calculate the minimal width acceptable for the contact from the
        die_cell to the circuit/experiment.

        The conditions are that the contact width should be bigger than (1) the
        biggest port of the circuit, (2) the contact_l (to avoid a short/open circuit).

        Parameters:
            circuit_ports (list of Port): The ports of the circuit to be placed in the
                cell (use .get_ports()).

        Returns:
            (int or float): the suggested contact_w to input in the die_cell of the
            given circuit
        """
        max_circuit_port_width = max([port.width for port in circuit_ports])
        return max(max_circuit_port_width, self.contact_l)


def die_cell(
    die_parameters: DieParameters = DieParameters(),
    n_m_units: Tuple[int, int] = (1, 1),
    contact_w: Union[int, float] = 50,
    device_max_size: Tuple[Union[int, float], Union[int, float]] = (
        round(DieParameters().unit_die_w / 3),
        round(DieParameters().unit_die_h / 3),
    ),
    ports: Dict[str, int] = {"N": 1, "E": 1, "W": 1, "S": 1},
    ports_gnd: List[str] = ["E", "S"],
    text: str = "",
    text_size: Union[None, int, float] = None,
) -> Device:
    """Creates a die cell with dicing marks, text, and pads to connect to a
    device.

    Parameters:
        die_parameters (DieParameters): the die's parameters.
        n_m_units (tuple of int): number of unit dies that compose the cell in width and height.
        device_max_size (tuple of int or float): Max dimensions of the device
            inside the cell (width, height).
        ports (dict): The ports of the device, format must be {'N':m, 'E':n, 'W':p, 'S':q}.
        ports_gnd (list of string): The ports connected to ground.
        text (string): The text to be displayed on the cell.
        text_size (int or float): If specified, overwrites the Die's
            text_size. Size of text, corresponds to phidl geometry std.

    Returns:
        DIE (Device): The cell, with ports of width contact_w positioned around a device_max_size area.
    """

    def offset(overlap_port):
        port_name = overlap_port.name[0]
        if port_name == "N":
            overlap_port.midpoint[1] += -die_parameters.contact_l
        elif port_name == "S":
            overlap_port.midpoint[1] += die_parameters.contact_l
        elif port_name == "W":
            overlap_port.midpoint[0] += die_parameters.contact_l
        elif port_name == "E":
            overlap_port.midpoint[0] += -die_parameters.contact_l

    die_name = text.replace("\n", "")
    die_size = [n_m_units[i] * die_parameters.unit_die_size[i] for i in [0, 1]]
    DIE = Device(f"DIE {die_name} ")

    border = pg.rectangle(die_size)
    border.move(border.center, (0, 0))

    borderOut = Device()

    ## Make the routes and pads
    padOut = Device()

    pad_block_size = (
        die_size[0] - 2 * die_parameters.pad_size[1] - 4 * die_parameters.outline,
        die_size[1] - 2 * die_parameters.pad_size[1] - 4 * die_parameters.outline,
    )
    inner_block = pg.compass_multi(device_max_size, ports)
    outer_block = pg.compass_multi(pad_block_size, ports)
    inner_ports = list(inner_block.ports.values())

    for i, port in enumerate(list(outer_block.ports.values())):

        CONNECT = Device()
        port.rotate(180)

        # create the pad
        pad = pg.rectangle(
            die_parameters.pad_size,
            layer={die_parameters.die_layer, die_parameters.pad_layer},
        )
        pad.add_port(
            "1",
            midpoint=(die_parameters.pad_size[0] / 2, 0),
            width=die_parameters.pad_size[0],
            orientation=90,
        )
        pad_ref = CONNECT << pad
        pad_ref.connect(pad.ports["1"], port)

        # create the route from pad to contact
        port.width = die_parameters.pad_size[0]
        inner_ports[i].width = contact_w
        CONNECT << pr.route_quad(port, inner_ports[i], layer=die_parameters.die_layer)

        # create the route from contact to overlap
        overlap_port = CONNECT.add_port(port=inner_ports[i])
        offset(overlap_port)
        overlap_port.rotate(180)
        CONNECT << pr.route_quad(
            inner_ports[i], overlap_port, layer=die_parameters.die_layer
        )

        # isolate the pads that are not grounded
        port_grounded = any(port.name[0] == P for P in ports_gnd)
        if not port_grounded:
            padOut << pg.outline(
                CONNECT,
                distance=die_parameters.outline,
                join="round",
                open_ports=2 * die_parameters.outline,
            )

        # add the port to the die
        DIE.add_port(port=inner_ports[i].rotate(180))
        DIE << CONNECT

    borderOut << padOut

    ## Add the die markers

    # mark the corners
    cornersOut = Device()

    corners_coord = [
        (
            -die_size[0] / 2 + die_parameters.die_border_w / 2,
            -die_size[1] / 2 + die_parameters.die_border_w / 2,
        ),
        (
            die_size[0] / 2 - die_parameters.die_border_w / 2,
            -die_size[1] / 2 + die_parameters.die_border_w / 2,
        ),
        (
            die_size[0] / 2 - die_parameters.die_border_w / 2,
            die_size[1] / 2 - die_parameters.die_border_w / 2,
        ),
        (
            -die_size[0] / 2 + die_parameters.die_border_w / 2,
            die_size[1] / 2 - die_parameters.die_border_w / 2,
        ),
    ]
    for corner_coord in corners_coord:
        corner = pg.rectangle(
            (
                die_parameters.die_border_w - die_parameters.outline,
                die_parameters.die_border_w - die_parameters.outline,
            )
        )
        corner = pg.outline(corner, -1 * die_parameters.outline)
        corner.move(corner.center, corner_coord)
        cornersOut << corner

    borderOut << cornersOut

    # label the cell
    if text_size is not None:
        label_size = text_size
    else:
        label_size = die_parameters.text_size

    label = pg.text(text, size=label_size, layer=die_parameters.die_layer)
    label.move((label.xmin, label.ymin), (0, 0))
    pos = [
        x + 2 * die_parameters.outline + 10
        for x in (-die_size[0] / 2, -die_size[1] / 2)
    ]
    label.move(pos)
    DIE << label
    labelOut = pg.outline(label, die_parameters.outline)

    borderOut << labelOut

    border = pg.boolean(border, borderOut, "A-B", layer=die_parameters.die_layer)
    DIE << border

    if die_parameters.fill_pad_layer:
        border_filled = pg.rectangle(die_size)
        center = pg.rectangle(device_max_size)
        border_filled.move(border_filled.center, (0, 0))
        center.move(center.center, (0, 0))
        border_filled = pg.boolean(border_filled, center, "A-B")

        border_filled = pg.boolean(
            border_filled, borderOut, "A-B", layer=die_parameters.pad_layer
        )
        DIE << border_filled

    DIE.flatten()
    ports = DIE.get_ports()
    DIE = pg.union(DIE, by_layer=True)
    if die_parameters.invert:
        PADS = pg.deepcopy(DIE)
        PADS.remove_layers([die_parameters.die_layer])
        PADS.name = "pads"
        DIE = pg.invert(DIE, border=0, layer=die_parameters.die_layer)
        DIE << PADS
    for port in ports:
        DIE.add_port(port)

    DIE.name = f"DIE {die_name}"
    return DIE


def add_optimalstep_to_dev(
    DEVICE: Device, ratio: Union[int, float] = 10, layer: int = 1
) -> Device:
    """Add an optimal step to the device's ports.

    Note that the subports of the input Device are ignored but still conserved
    in the returned device.

    Parameters:
        DEVICE (Device): The Phidl Device to add the optimal steps to.
        ratio (int or float): the ratio between the width at the end of the step
            and the width of the device's ports.
        layer (int or array-like[2]): the layer to place the optimal steps into.

    Returns:
        (Device): The given Device, with additional steps on its ports. The
        ports of the returned device have the same name than the ports of the
        input device and correspond to the steps extremities.
    """
    DEV_STP = Device(DEVICE.name)

    DEV_STP << DEVICE
    for port in DEVICE.flatten().get_ports():
        STP = pg.optimal_step(
            port.width, port.width * ratio, symmetric=True, layer=layer
        )
        STP.name = f"optimal step x{ratio} "
        stp = DEV_STP << STP
        stp.connect(port=1, destination=port)
        DEV_STP.add_port(port=stp.ports[2], name=port.name)

    return DEV_STP


def rename_ports_to_compass(DEVICE: Device, depth: Union[int, None] = 0) -> Device:
    """Rename ports of a Device based on compass directions.

    Parameters:
        DEVICE (Device): The Phidl Device object whose ports are to be renamed.

    Returns:
        Device: A new Phidl Device object with ports renamed to compass directions.
    """

    ports = DEVICE.get_ports(depth=depth)
    # Create a new Device object to store renamed ports
    DEV_COMPASS = Device(DEVICE.name)

    # Copy ports from the original device to the new device
    DEV_COMPASS << DEVICE

    # Initialize counters for each direction
    E_count = 1
    N_count = 1
    W_count = 1
    S_count = 1

    # Iterate through each port in the original device
    for port in ports:
        # Determine the orientation of the port and rename it accordingly
        if port.orientation % 360 == 0:
            DEV_COMPASS.add_port(port=port, name=f"E{E_count}")
            E_count += 1
        elif port.orientation % 360 == 90:
            DEV_COMPASS.add_port(port=port, name=f"N{N_count}")
            N_count += 1
        elif port.orientation % 360 == 180:
            DEV_COMPASS.add_port(port=port, name=f"W{W_count}")
            W_count += 1
        elif port.orientation % 360 == 270:
            DEV_COMPASS.add_port(port=port, name=f"S{S_count}")
            S_count += 1

    return DEV_COMPASS


def add_hyptap_to_cell(
    die_ports: List[Port],
    contact_l: Union[int, float] = 10,
    contact_w: Union[int, float] = 5,
    layer: int = 1,
) -> Tuple[Device, Device]:
    """Takes the cell and adds hyper taper at its ports.

    Parameters:
        die_ports (list of Port): The ports of the die cell (use .get_ports()).
        contact_l (int or float): The overlap width (accounts for
            misalignment between 1st and 2nd ebeam exposures). Will also
            correspond to the hyper taper's length.
        contact_w (int or float): The width of the contact with the device's
            route (width of hyper taper's end).
        layer (int or array-like[2]): The layer on which to place the tapers
            (usually the same as the circuit's layer).

    Returns:
        Tuple[Device, Device]: a tuple containing:

        - **HT** (*Device*): The hyper tapers, positioned at the die's ports.
          Ports of the same name as the die's ports are added to the output of
          the tapers.
        - **device_ports** (*Device*): A device containing only the input ports
          of the tapers, named as the die's ports.
    """

    HT = Device("HYPER TAPERS ")
    device_ports = Device()

    for port in die_ports:
        ht_w = port.width + 2 * contact_l
        ht = HT << geometry.hyper_taper(contact_l, ht_w, contact_w)
        ht.connect(ht.ports[2], port)
        HT.add_port(port=ht.ports[1], name=port.name)
        device_ports.add_port(port=ht.ports[2], name=port.name)

    HT.flatten(single_layer=layer)
    return HT, device_ports


def route_to_dev(ext_ports: List[Port], dev_ports: Set[Port], layer: int = 1) -> Device:
    """Creates smooth routes from external ports to the device's ports. If
    route_smooth is not working, routes quad.

    Parameters:
        ext_ports (list of Port): The external ports, e.g., of the die or hyper tapers (use .get_ports()).
        dev_ports (set of Port): The device's ports, should be named as the external ports (use .ports).
        layer (int or array-like[2]): The layer to put the routes on.

    Returns:
        ROUTES (Device): The routes from ports to ports, on the specified layer.
    """

    ROUTES = Device("ROUTES ")

    for port in ext_ports:
        dev_port = dev_ports[port.name]
        try:
            radius = port.width
            length1 = 2 * radius
            length2 = 2 * radius
            ROUTES << pr.route_smooth(
                port, dev_port, radius, path_type="Z", length1=length1, length2=length2
            )
        except ValueError:
            try:
                radius = dev_port.width
                length1 = radius
                length2 = radius
                ROUTES << pr.route_smooth(
                    port,
                    dev_port,
                    radius,
                    path_type="Z",
                    length1=length1,
                    length2=length2,
                )
            except ValueError:
                ROUTES << pr.route_quad(port, dev_port)
    ROUTES.flatten(single_layer=layer)
    return ROUTES


# from previous qnngds: to be tested...

# def outline(elements, distance = 1, precision = 1e-4, num_divisions = [1, 1],
#             join = 'miter', tolerance = 2, join_first = True,
#             max_points = 4000, layer = 0, open_ports=-1, rotate_ports=False):
#     """ Creates an outline around all the polygons passed in the `elements`
#     argument. `elements` may be a Device, Polygon, or list of Devices.
#     Parameters
#     ----------
#     elements : Device(/Reference), list of Device(/Reference), or Polygon
#         Polygons to outline or Device containing polygons to outline.
#     distance : int or float
#         Distance to offset polygons. Positive values expand, negative shrink.
#     precision : float
#         Desired precision for rounding vertex coordinates.
#     num_divisions : array-like[2] of int
#         The number of divisions with which the geometry is divided into
#         multiple rectangular regions. This allows for each region to be
#         processed sequentially, which is more computationally efficient.
#     join : {'miter', 'bevel', 'round'}
#         Type of join used to create the offset polygon.
#     tolerance : int or float
#         For miter joints, this number must be at least 2 and it represents the
#         maximal distance in multiples of offset between new vertices and their
#         original position before beveling to avoid spikes at acute joints. For
#         round joints, it indicates the curvature resolution in number of
#         points per full circle.
#     join_first : bool
#         Join all paths before offsetting to avoid unnecessary joins in
#         adjacent polygon sides.
#     max_points : int
#         The maximum number of vertices within the resulting polygon.
#     layer : int, array-like[2], or set
#         Specific layer(s) to put polygon geometry on.
#   open_ports : int or float
#       Trims the outline at each port of the element. The value of open_port
#       scales the length of the trim gemoetry (must be positive).
#       Useful for positive tone layouts.
#     Returns
#     -------
#     D : Device
#         A Device containing the outlined polygon(s).
#     """
#     D = Device('outline')
#     if type(elements) is not list: elements = [elements]
#     for e in elements:
#         if isinstance(e, Device): D.add_ref(e)
#         else: D.add(e)
#     gds_layer, gds_datatype = _parse_layer(layer)
#     D_bloated = pg.offset(D, distance = distance, join_first = join_first,
#                        num_divisions = num_divisions, precision = precision,
#                        max_points = max_points, join = join,
#                        tolerance = tolerance, layer = layer)
#     Outline = pg.boolean(A = D_bloated, B = D, operation = 'A-B',
#                       num_divisions = num_divisions, max_points = max_points,
#                       precision = precision, layer = layer)
#     if open_ports>=0:
#       for i in e.ports:
#           trim = pg.rectangle(size=(distance, e.ports[i].width+open_ports*distance))

#           trim.rotate(e.ports[i].orientation)
#           trim.move(trim.center, destination=e.ports[i].midpoint)
#           if rotate_ports:
#               trim.movex(-np.cos(e.ports[i].orientation/180*np.pi)*distance/2)
#               trim.movey(-np.sin(e.ports[i].orientation/180*np.pi)*distance/2)
#           else:
#               trim.movex(np.cos(e.ports[i].orientation/180*np.pi)*distance/2)
#               trim.movey(np.sin(e.ports[i].orientation/180*np.pi)*distance/2)

#           Outline = pg.boolean(A = Outline, B = trim, operation = 'A-B',
#                      num_divisions = num_divisions, max_points = max_points,
#                      precision = precision, layer = layer)
#       for i in e.ports: Outline.add_port(port=e.ports[i])
#     return Outline

# def assign_ids(device_list, ids):
#     """
#     Attach device ID to device list.

#     Parameters
#     ----------
#     device_list : LIST
#         List of phidl device objects.
#     ids : LIST
#         list of identification strings.
#         typically generated from packer_rect/text_labels.

#     Returns
#     -------
#     None.

#     """
#     device_list = list(filter(None,device_list))
#     for i in range(len(device_list)):
#         device_list[i].name = ids[i]

# def packer(D_list,
#            text_letter,
#            text_pos=(0,-70),
#            text_layer=1,
#            text_height=50,
#            spacing = 100,
#            aspect_ratio = (1,1),
#            max_size = (None,750),
#            sort_by_area = False,
#            density = 1.1,
#            precision = 1e-2,
#            verbose = False):
#     """
#     Returns Device "p" with references from D_list. Names, or index, of each device is assigned and can be called from p.references[i].parent.name


#     Parameters
#     ----------
#     D_list : TYPE
#         DESCRIPTION.
#     text_letter : TYPE
#         DESCRIPTION.
#     text_pos : TYPE, optional
#         DESCRIPTION. The default is None.
#     text_layer : TYPE, optional
#         DESCRIPTION. The default is 1.
#     text_height : TYPE, optional
#         DESCRIPTION. The default is 50.
#     spacing : TYPE, optional
#         DESCRIPTION. The default is 10.
#     aspect_ratio : TYPE, optional
#         DESCRIPTION. The default is (1,1).
#     max_size : TYPE, optional
#         DESCRIPTION. The default is (None,None).
#     sort_by_area : TYPE, optional
#         DESCRIPTION. The default is True.
#     density : TYPE, optional
#         DESCRIPTION. The default is 1.1.
#     precision : TYPE, optional
#         DESCRIPTION. The default is 1e-2.
#     verbose : TYPE, optional
#         DESCRIPTION. The default is False.
#      : TYPE
#         DESCRIPTION.

#     Returns
#     -------
#     TYPE
#         DESCRIPTION.

#     """

#     p = pg.packer(D_list,
#         spacing = spacing,
#         aspect_ratio = aspect_ratio,
#         max_size = max_size,
#         sort_by_area = sort_by_area,
#         density = density,
#         precision = precision,
#         verbose = verbose,
#         )


#     for i in range(len(p[0].references)):
#         device_text = text_letter+str(i)
#         text_object = pg.text(text=device_text, size = text_height, justify='left', layer=text_layer)
#         t = p[0].references[i].parent.add_ref(text_object)
#         t.move(origin=text_object.bbox[0], destination= (text_pos[0], text_pos[1]))

#         p[0].references[i].parent.name = device_text

#     p = p[0]
#     p.name = text_letter
#     p._internal_name = text_letter
#     # p.flatten() # do not flatten.

#     return p

# def packer_rect(device_list, dimensions, spacing, text_pos=None, text_size = 50, text_layer = 1):
#     """
#     This function distributes devices from a list onto a rectangular grid. The aspect ratio (dimensions) and spacing must be specified.
#     If specified, text can be added automatically in a A1, B2, C3, style. The text will start with A0 in the NW corner.

#     Parameters
#     ----------
#     device_list : LIST
#         LIST OF PHIDL DEVICE OBJECTS
#     dimensions : TUPLE
#         (X,Y) X BY Y GRID POINTS
#     spacing : TUPLE
#         (dX,dY) SPACING BETWEEN GRID POINTS
#     text_pos : TUPLE, optional
#         IF SPECIFIED THE GENERATED TEXT IS LOCATED AT (dX,dY) FROM SW CORNER. The default is None.
#     text_size : INT, optional
#         SIZE OF TEXT LABEL. The default is 50.
#     text_layer : INT, optional
#         LAYER TO ADD TEXT LABEL TO The default is 1.

#     Returns
#     -------
#     D : DEVICE
#         PHIDL device object. List is entered and a single device is returned with labels.
#     text_list : LIST
#         LIST of strings of device labels.

#     """

#     letters = list(string.ascii_uppercase)

#     while len(device_list) < np.product(dimensions):
#         device_list.append(None)

#     new_shape = np.reshape(device_list,dimensions)
#     text_list=[]
#     D = Device('return')
#     for i in range(dimensions[0]):
#         for j in range(dimensions[1]):
#             if not new_shape[i][j] == None:
#                 moved_device = new_shape[i][j].move(origin=new_shape[i][j].bbox[0], destination=(i*spacing[0], -j*spacing[1]))
#                 D.add_ref(moved_device)
#                 if text_pos:
#                     device_text = letters[i]+str(j)
#                     text_list.append(device_text)
#                     text_object = pg.text(text=device_text, size = text_size, justify='left', layer=text_layer)
#                     text_object.move(destination= (i*spacing[0]+text_pos[0], -j*spacing[1]+text_pos[1]))
#                     D.add_ref(text_object)

#     return D, text_list

# def packer_doc(D_pack_list):
#     """
#     This function creates a text document to be referenced during meansurement.
#     Its primary purpose is to serve as a reference for device specifications on chip.
#     For instance, "A2 is a 3um device."

#     Currently. This function really only works with D_pack_list from packer().
#     It looks at each reference and grabs the device parameters (which are hard coded).
#     'line.append(str(D_pack_list[i].references[j].parent.width))'
#     It would be great to have this as a dynamical property that can be expounded for every kind of device/parameter.

#     'create_device_doc' predated this function and took every np.array parameter in the parameter-dict and wrote it to a .txt file.
#     The main problem with this function is that the device name is not associated in the parameter-dict.

#     Inputs
#     ----------
#     sample: STRING
#         enter a sample name "SPX000". The file path will be generated on the NAS and the .txt file will be saved there.

#     Parameters
#     ----------
#     D_pack_list : LIST
#         List containing PHIDL Device objects.

#     Returns
#     -------
#     None.

#     """

#     """ Safety net for writing to the correct location"""

#     sample = input('enter a sample name: ')
#     if sample == '':
#         print('Doc not created')
#         return
#     else:
#         path = os.path.join('S:\SC\Measurements',sample)
#         os.makedirs(path, exist_ok=True)

#         path = os.path.join('S:\SC\Measurements',sample, sample+'_device_doc.txt')

#         file = open(path, "w")

#         tab = ',\t'
#         string_list=[]
#         headers = ['ID', 'WIDTH', 'AREA', 'SQUARES']
#         headers.append('\n----------------------------------\n')

#         for i in range(len(D_pack_list)):
#             for j in range(len(D_pack_list[i].references)):
#                 line = []
#                 line.append(str(D_pack_list[i].references[j].parent.name))
#                 line.append(str(D_pack_list[i].references[j].parent.width))
#                 line.append(str(D_pack_list[i].references[j].parent.area))
#                 line.append(str(D_pack_list[i].references[j].parent.squares))

#                 line.append('\n')
#                 string_list.append(tab.join(line))
#                 string_list.append('. . . . . . . . . . . . . . . . \n')
#             string_list.append('\\-----------------------------------\\ \n')

#         file.write(tab.join(headers))
#         file.writelines(string_list)
#         file.close()

# def assign_ids(device_list, ids):
#     """
#     Attach device ID to device list.

#     Parameters
#     ----------
#     device_list : LIST
#         List of phidl device objects.
#     ids : LIST
#         list of identification strings.
#         typically generated from packer_rect/text_labels.

#     Returns
#     -------
#     None.

#     """
#     device_list = list(filter(None,device_list))
#     for i in range(len(device_list)):
#         device_list[i].name = ids[i]
