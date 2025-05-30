"""Sample defines the Sample class which is used to generate a wafer/piece layout from multiple experiments"""

import numpy as np

import gdsfactory as gf
from gdsfactory.typings import ComponentSpecOrComponent

from typing import overload


@gf.cell
def _wafer(radius: float, flat: float) -> gf.Component:
    """Generic template for wafers

    Args:
        radius (float): radius of wafer
        flat (float): length of primary flat

    Returns:
        (gf.Component): wafer template
    """
    flat_dist = (radius**2 - (flat / 2) ** 2) ** 0.5
    circ = gf.components.circle(radius=radius, angle_resolution=2.5, layer=(1, 0))
    FLAT = gf.Component()
    flat = FLAT << gf.components.rectangle(
        size=(flat, radius - flat_dist), layer=(1, 0)
    )
    flat.move((flat.x, flat.ymin), (circ.x, circ.ymin))
    W = gf.Component()
    w_i = W << gf.boolean(
        A=circ, B=FLAT, operation="A-B", layer1=(1, 0), layer2=(1, 0), layer=(1, 0)
    )
    w_i.move(w_i.center, (0, 0))
    return W


@gf.cell
def wafer150mm():
    """Template for 150 mm wafer"""
    return _wafer(radius=75e3, flat=57.5e3)


@gf.cell
def wafer100mm():
    """Template for 100 mm wafer"""
    return _wafer(radius=50e3, flat=32.5e3)


@gf.cell
def piece10mm():
    """Template for 10 mm piece"""
    P = gf.Component()
    p_i = P << gf.components.rectangle(size=(10e3, 10e3), layer=(1, 0))
    p_i.move(p_i.center, (0, 0))
    return


class Sample:
    """Class for managing die/experiment area, with manual placement and basic autoplacement

    Defines a grid size and divides a sample (wafer/piece) into cells.
    Experiments (generated with :py:func:`qnngds.utilities.generate_experiment`)
    can be placed on one or more cells in the grid, manually or automatically.
    If initialized with ``allow_cell_span``, experiments can span multiple columns/rows.

    For a wafer, it is recommended to have two hierarchies of ``Sample``s.
    At the top-level, define a wafer-sized Sample, with a number of cells that
    can be cut/cleaved into dies. Each cell may be defined as a ``Sample`` to place
    multiple experiments on a grid within the die. For example:

    >>> my_experiment_die_1 = qg.sample.Sample(
    >>>     cell_size=1e3, sample=qg.sample.piece10mm, edge_exclusion=500, allow_cell_span=True,
    >>> )
    >>> # place experiments (e.g. circuits, devices, lithographic structures etc.) on nTron_die
    >>> # ...
    >>> # create other dies
    >>> # ...
    >>> # ...
    >>> sample = qg.sample.Sample(
    >>>     cell_size=10e3, sample=qg.sample.wafer100mm, edge_exclusion=10e3, allow_cell_span=False,
    >>> )
    >>> # place nTron_die and other dies on sample
    """

    def __init__(
        self,
        cell_size: float = 1000,
        sample: ComponentSpecOrComponent = wafer150mm,
        edge_exclusion: float = 10000,
        allow_cell_span: bool = False,
    ) -> None:
        """Constructor for Sample class

        Args:
            cell_size (float): pitch of cell grid
            sample (Component | ComponentSpec): desired sample shape (e.g. wafer/piece)
            edge_exclusion (float): desired edge exclusion for die placement
            allow_cell_span (bool): if True, allows a component added to the sample to span multiple cells

        Returns:
            None

        """
        # Component containing all components added to the sample
        self.components = gf.Component()

        # save the cell_size
        self.cell_size = cell_size

        # save if cell spanning is allowed
        self.allow_cell_span = allow_cell_span

        ##################################
        # Determine the legal cell regions
        # that do not fall within the
        # edge exclusion region
        ##################################
        self.sample = sample
        sample_region = gf.get_component(sample).get_region(layer=(1, 0))
        mask_region = sample_region.sized(-edge_exclusion / gf.kcl.dbu)

        # get number of rows/columns
        bbox = mask_region.bbox()
        n_cols = int(np.floor(bbox.width() * gf.kcl.dbu / cell_size))
        n_rows = int(np.floor(bbox.height() * gf.kcl.dbu / cell_size))

        # create a component whose area defines which placements are legal
        mask = gf.Component()
        mask.add_polygon(mask_region, layer=(1, 0))
        mask.move(mask.center, (0, 0))

        # coordinates from left-to-right, top-to-bottom
        self.origin = (-n_cols * cell_size / 2, n_rows * cell_size / 2)
        self.open_cells = set([])
        rect = gf.components.rectangle(size=(cell_size, cell_size), layer=(1, 0))
        dummy = gf.Component()
        for row in range(n_rows):
            for col in range(n_cols):
                d = dummy << rect
                d.move((d.xmin, d.ymax), self.origin).movex(col * cell_size).movey(
                    -row * cell_size
                )
                intersection = gf.boolean(
                    A=d,
                    B=mask,
                    operation="A-B",
                    layer1=(1, 0),
                    layer2=(1, 0),
                    layer=(1, 0),
                )
                if intersection.get_region(layer=(1, 0)).is_empty():
                    self.open_cells.add((row, col))

    def visualize_open_cells(self, blocking: bool = True) -> None:
        """Visualize open cells

        Args:
            blocking (bool): if True, waits for user input before exiting

        Returns:
            None
        """
        dies = gf.Component()
        rect = gf.components.rectangle(
            size=(self.cell_size, self.cell_size), layer=(1, 0)
        )
        for cell in self.open_cells:
            d = dies << rect
            d.move((d.xmin, d.ymax), self.origin).movex(cell[0] * self.cell_size).movey(
                -cell[1] * self.cell_size
            )
        dies.show()
        if blocking:
            input("press enter to continue")

    @overload
    def place_on_sample(self, component: gf.Component, cell_coordinates: tuple) -> None:
        """Place component on sample

        Args:
            component (Component): component to place
            cell_coordinates (tuple): coordiantes of cell to place component in.
                If component spans multiple cells, this is the top-left cell

        Returns:
            None
        """
        pass

    @overload
    def place_on_sample(self, component: gf.Component, placement_area: str) -> None:
        """Place component on sample

        Args:
            component (Component): component to place
            placement_area (str): desired region of the chip to place sample in.
                Must be one of "c", "n", "s", "e", "w", "nw", "ne", "sw", "se"

        Returns:
            None
        """
        allowed_placement_areas = ["c", "n", "s", "e", "w", "nw", "ne", "sw", "se"]
        if placement_area.lower() not in allowed_placement_areas:
            raise ValueError(
                f"{placement_area=} is not one of {allowed_placement_areas}"
            )
        # find open cell(s) to place on

    def _check_component_size(self, component: gf.Component) -> None:
        """Checks component size

        Args: component (Component): component to check

        Returns: None

        Raises:
            RuntimeError if component requires more than one (1) cell of area,
            but ``allow_cell_span`` is false
        """
        too_big = component.xsize > self.cell_size or component.ysize > self.cell_size
        if too_big and not self.allow_cell_span:
            raise RuntimeError(
                f"allow_cell_span is set to False, but the provided component {component.name} is larger than a single cell {self.cell_size=}"
            )
