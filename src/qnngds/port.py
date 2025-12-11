"""Extend phidl's Port to add layer information"""

from phidl import Port as phPort
from phidl import Device as phDevice
import copy

from numpy.typing import ArrayLike


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
        layer: tuple | str = (1, 0),
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
            if not isinstance(port, Port):
                raise ValueError(
                    "[PHIDL] add_port() error: Argument `port` must be a Port for copying"
                )
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
        if p.name in self.ports:
            raise ValueError(
                '[DEVICE] add_port() error: Port name "%s" already exists in this Device (name "%s", uid %s)'
                % (p.name, self.name, self.uid)
            )
        self.ports[p.name] = p
        return p
