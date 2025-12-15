"""Extend phidl's Port to add layer information, augment CellArray with ports"""

from __future__ import annotations

from phidl import Port as phPort
from phidl import Device as phDevice
from phidl import Layer as phLayer
from phidl import LayerSet as phLayerSet
from phidl import CrossSection as phCrossSection
from phidl.device_layout import CellArray as phCellArray
from phidl.device_layout import _parse_move
from phidl.device_layout import _rotate_points
import copy

from numpy.typing import ArrayLike
from collections.abc import Sequence

from qnngds.typing import LayerSpecs

import numpy as np


class Port(phPort):
    """Port object used to snap objects together. Extends phidl.Port to add layer information"""

    def __init__(
        self,
        name: str = None,
        midpoint: ArrayLike = (0, 0),
        width: float = 1,
        orientation: float = 0,
        layer: tuple | str = (1, 0),
        parent=None,
    ):
        """Constructor for Port.

        Parameters:
            name (str): name of port
            midpoint (np.ArrayLike): midpoint of port location
            width (float): width of float
            orientation (float): rotation of port
            layer (tuple | tuple): GDS layer/datatype or name of layer
            parent:
        """
        super().__init__(
            name=name,
            midpoint=midpoint,
            width=width,
            orientation=orientation,
            parent=parent,
        )
        self.layer = layer

    def __repr__(self):
        """Augment phidl.Port __repr__ to add layer info"""
        return super().__repr__()[:-1] + f", layer {self.layer})"

    def _copy(self, new_uid: bool = True):
        """Copies a port

        Parameters:
            new_uid (bool): if True (default), use a new uid for the port

        Returns:
            Copied port
        """
        new_port = Port(
            name=self.name,
            midpoint=self.midpoint,
            width=self.width,
            orientation=self.orientation,
            layer=self.layer,
            parent=self.parent,
        )
        new_port.info = copy.deepcopy(self.info)
        if not new_uid:
            new_port.uid = self.uid
            Port._next_uid -= 1
        return new_port


class Device(phDevice):
    """The basic object that holds polygons, labels, and ports in PHIDL.
    Augmented with methods for layer-assigned ports."""

    def add_port(
        self,
        name: str = None,
        midpoint: ArrayLike = (0, 0),
        width: float = 1,
        orientation: float = 0,
        layer: tuple | str = None,
        port: Port | None = None,
    ):
        """Adds a Port to the Device.

        Parameters
            name (str): name of port
            midpoint (tuple[float,float]): midpoint of port location
            width (float): width of float
            orientation (float): rotation of port
            layer (tuple | str): GDS layer/datatype or name of layer
            port (Port | None): a Port if the added Port is a copy of an existing Port.

        Notes
            Can be called to copy an existing port like
            add_port(port = existing_port) or to create a new port
            add_port(myname, mymidpoint, mywidth, myorientation, mylayer).
            Can also be called to copy an existing port with a new name like
            add_port(port = existing_port, name = new_name)
        """
        if port is not None:
            if not (isinstance(port, phPort) or isinstance(port, Port)):
                raise ValueError(
                    "[qnngds] add_port() error: Argument `port` must be a Port or phidl.Port for copying"
                )
            if not isinstance(port, Port):
                p = Port(
                    name=port.name,
                    midpoint=port.midpoint,
                    width=port.width,
                    orientation=port.orientation,
                    layer=layer,
                    parent=self,
                )
            else:
                p = port._copy(new_uid=True)
                p.parent = self
        else:
            p = Port(
                name=name,
                midpoint=midpoint,
                width=width,
                orientation=orientation,
                layer=layer,
                parent=self,
            )
        if name is not None:
            p.name = name
        if layer is not None:
            p.layer = layer
        if p.name in self.ports:
            raise ValueError(
                '[DEVICE] add_port() error: Port name "%s" already exists in this Device (name "%s", uid %s)'
                % (p.name, self.name, self.uid)
            )
        self.ports[p.name] = p
        return p

    def add_ports(self, ports: Sequence[Port]):
        """Add multiple Ports to Device

        Parameters
            ports (Sequence[Port]): multiple Port objects to be added
        """
        if isinstance(ports, dict):
            for name, port in ports.items():
                self.add_port(name=name, port=port)
        else:
            for port in ports:
                self.add_port(port)

    def add_array(self, device, columns=2, rows=2, spacing=(100, 100), alias=None):
        """Creates a DeviceArray reference.

        Parameters
            device (Device): the referenced Device.
            columns (int): number of columns in the array.
            rows (int): number of rows in the array.
            spacing (Arraylike): (column spacing, row spacing)
            alias (str | None): Alias of the referenced Device.

        Returns
            A CellArray containing references to the input Device.
        """
        if not isinstance(device, phDevice):
            raise TypeError(
                """[qnngds] add_array() was passed something that
            was not a Device object. """
            )

        if np.size(spacing) != 2:
            raise ValueError(
                """[qnngds] add_array() The spacing argument must
            have exactly 2 elements, e.g. (150,80) """
            )
        a = DeviceArray(
            device=device,
            columns=int(round(columns)),
            rows=int(round(rows)),
            spacing=spacing,
        )
        a.owner = self
        self.add(a)  # Add DeviceReference (CellReference) to Device (Cell)
        if alias is not None:
            self.aliases[alias] = a
        return a  # Return the CellArray


class DeviceArray(phCellArray):
    """Augmentation of gdspy/phidl's CellArray class, autogenerates a port dictionary for all instances"""

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """Calls PHIDL constructor for CellArray, then generates ports for each reference in array"""
        super().__init__(*args, **kwargs)
        device = args[0] if len(args) >= 1 else kwargs["device"]
        self.columns = args[1] if len(args) >= 2 else kwargs["columns"]
        self.rows = args[2] if len(args) >= 3 else kwargs["rows"]
        spacing = args[3] if len(args) >= 4 else kwargs["spacing"]
        # generate ports
        self.ports = np.empty((self.rows, self.columns), dtype=object)
        for row in range(self.rows):
            dy = row * spacing[1]
            for column in range(self.columns):
                dx = column * spacing[0]
                self.ports[row, column] = {}
                for name, port in device.ports.items():
                    self.ports[row, column][name] = Port(
                        name=port.name,
                        midpoint=np.array(port.midpoint) + np.array((dx, dy)),
                        width=port.width,
                        orientation=port.orientation,
                        layer=port.layer,
                        parent=self,  # not sure what exactly this should be
                    )

    def rotate(self, angle=45, center=(0, 0)):
        """Rotate underlying CellArray and update ports

        Parameters
            angle (float): rotation angle
            center (Arraylike): coordinates about which to perform rotation
        """
        super().rotate(angle, center)
        for row in range(self.rows):
            for column in range(self.columns):
                for port in self.ports[row, column].values():
                    port.midpoint = _rotate_points(port.midpoint, angle, center)
                    port.orientation = np.mod(port.orientation + angle, 360)

    def move(self, origin=(0, 0), destination=None, axis=None):
        """Translate underlying CellArray and update ports

        Parameters
            origin (tuple): starting location
            destination (Arraylike | None): destination
            axis
        """
        dx, dy = _parse_move(origin, destination, axis)
        super().move(origin, destination, axis)
        for row in range(self.rows):
            for column in range(self.columns):
                for port in self.ports[row, column].values():
                    port.midpoint = np.array(port.midpoint) + np.array((dx, dy))


class Layer(phLayer):
    """Augment PHIDL Layer with outline and keepout information"""

    def __init__(
        self,
        gds_layer: int = 0,
        gds_datatype: int = 0,
        name: str = "unnamed",
        description: str | bool = None,
        inverted: bool = False,
        color: str | tuple | None = None,
        alpha: int | float = 0.6,
        dither: str | None = None,
        keepout: LayerSpecs | Sequence[Layer] | None = None,
        outline: int | float = 0,
    ):
        """Constructor for qnngds.Layer

        Parameters
            keepout (LayerSpecs | Layers | None): if not None, defines one or more Layers for which the current layer defines keepout regions.
            outline (int | float): if non-zero, makes layer positive tone, written with a linewidth of outline.
        """
        super().__init__(
            gds_layer=gds_layer,
            gds_datatype=gds_datatype,
            name=name,
            description=description,
            inverted=inverted,
            color=color,
            alpha=alpha,
            dither=dither,
        )
        self.keepout = keepout
        self.outline = outline
        self.tuple = (gds_layer, gds_datatype)


class LayerSet(phLayerSet):
    """Augment PHIDL LayerSet to use Layers with outline and keepout information"""

    def add_layer(self, layer: Layer):
        """Add a layer to the LayerSet

        Parameters
            layer (Layer): layer to add
        """
        if layer.name in self._layers:
            raise ValueError(
                f"[qnngds] LayerSet: Tried to add layer with name {layer.name}, but it already exists"
            )
        self._layers[layer.name] = layer

    def __iter__(self):
        """Iter method, looping over LayerSet will return an iterator of the layer names"""
        for name in self._layers:
            yield name


class CrossSection(phCrossSection):
    """Augment PHIDL CrossSection to allow for hidden layers and radius specification"""

    def __init__(self, radius: int | float = 0):
        """Constructor for CrossSection

        Parameters
            radius (float | int): nominal radius used when autogenerating paths.
                NB explicitly providing a radius (e.g. when manually creating paths) will override this setting
        """
        super().__init__()
        self.radius = radius

    def add(
        self,
        width: float | int = 1,
        offset: float | int = 0,
        layer: int | tuple[int, int] = 0,
        ports: tuple[int | str | None] = (None, None),
        name: str | None = None,
        hidden: bool = False,
        min_radius: float | int = 0,
    ):
        """Calls phidl.CrossSection.add() method, and also updates hidden variable

        Parameters
            width (float | int | callable ): Width of the segment
            offset (float | int | callable ): Offset of the segment (positive values = right hand side)
            layer (int | tuple[int, int]): The polygon layer to put the segment on
            ports (array-like[2] of str | int | None): If not None, specifies the names for the ports at the
                ends of the cross-sectional element.
            name (str | int | None): Name of the cross-sectional element for later access
            hidden (bool): if True, does not add polygon during extrusion
        """
        super().add(width=width, offset=offset, layer=layer, ports=ports, name=name)
        self.sections[-1]["hidden"] = hidden
        self.sections[-1]["layer"] = (-1, -1)
        return self

    def extrude(self, path, simplify=None):
        """Calls phidl.CrossSection.extrude() method and removes any polygons corresponding
        to hidden layers"""
        D = super().extrude(path, simplify)
        D.remove(D.get_polygons(by_spec=(-1, -1)))
        return D
