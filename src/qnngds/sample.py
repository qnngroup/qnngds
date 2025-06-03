"""Sample defines the Sample class which is used to generate a wafer/piece layout from multiple experiments"""

import numpy as np

import gdsfactory as gf
from gdsfactory.typings import ComponentSpecOrComponent, LayerSpec

from collections.abc import Sequence

from itertools import product


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
    return P


class Sample(object):
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
        self.full_cells = set([])
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

    def visualize_open_cells(self, blocking: bool = True) -> gf.Component:
        """Visualize open cells

        Args:
            blocking (bool): if True, waits for user input before exiting

        Returns:
            (Component): component used for visualization
        """
        dies = gf.Component()
        rect = gf.components.rectangle(
            size=(self.cell_size, self.cell_size), layer=(1, 0)
        )
        for cell in self.open_cells:
            d = dies << rect
            d.move((d.xmin, d.ymax), self.origin).movex(cell[1] * self.cell_size).movey(
                -cell[0] * self.cell_size
            )
        dies.show()
        if blocking:
            input("press enter to continue")
        return dies

    @staticmethod
    def _get_bbox_extents(cell_coordinate_bbox: tuple) -> tuple:
        """Gets extents of a cell coordinate bounding box

        Args:
            cell_coordinate_bbox (tuple[tuple[int, int], tuple[int, int]]):
                bounding box of cell coordiantes within which a component should be placed.

        Returns:
            (tuple): xmin, ymin, xmax, ymax, row_span, col_span defined by bounding box
        """
        ymin, xmin = map(int, np.min(np.array(cell_coordinate_bbox), axis=0))
        ymax, xmax = map(int, np.max(np.array(cell_coordinate_bbox), axis=0))
        row_span = range(ymin, ymax + 1)
        col_span = range(xmin, xmax + 1)
        return xmin, ymin, xmax, ymax, row_span, col_span

    def place_on_sample(
        self,
        component: gf.Component,
        cell_coordinate_bbox: tuple,
        ignore_collisions: bool = False,
    ) -> None:
        """Place component on sample

        See also :py:meth:`place_multiple_on_sample`.
        Args:
            component (Component): component to place
            cell_coordinate_bbox (tuple[int, int] | tuple[tuple[int, int], tuple[int, int]]):
                bounding box of cell coordiantes within which the component should be placed.
                If the component fits within a single cell, then a tuple[int, int] is
                acceptable instead of passing a tuple with identical coordinates for the bbox.
                If component spans multiple cells, then the bbox coordinates must be unique.
            ignore_collisions (bool): If True, ignores any collision of component with
                previously-placed components.

        Returns:
            None

        Side Effects:
            Updates self.open_cells to remove newly allocated cells
            Updates self.full_cells to add newly allocated cells
        """
        spans_multiple = self._check_component_size(component)
        # check that component fits within specified bounding box
        if not isinstance(cell_coordinate_bbox[0], tuple) and spans_multiple:
            error_msg = f"component {component.name} spans multiple cells, "
            error_msg += "but bbox-like coordinates were not provided"
            raise ValueError(error_msg)
        # convert singleton to bbox with identical endpoints
        if not isinstance(cell_coordinate_bbox[0], tuple):
            cell_coordinate_bbox = (cell_coordinate_bbox, cell_coordinate_bbox)
        assert np.array(cell_coordinate_bbox).shape == (2, 2)
        # check that all cells within the bbox are available
        xmin, ymin, xmax, ymax, row_span, col_span = Sample._get_bbox_extents(
            cell_coordinate_bbox
        )
        cells_to_occupy = set(product(row_span, col_span))
        for row in row_span:
            for col in col_span:
                if (row, col) not in self.open_cells:
                    error_msg = f"cell {(row, col)=} is occupied when attempting "
                    error_msg += f"to place {component.name=}"
                    # cell isn't open
                    if (row, col) in self.full_cells:
                        # cell is occupied
                        if not ignore_collisions:
                            raise ValueError(error_msg)
                    else:
                        # illegal cell (e.g. in exclusion region)
                        raise ValueError(error_msg)
        # Placement can proceed.
        # First update our open/full tracking sets
        self.open_cells.difference_update(cells_to_occupy)
        self.full_cells.update(cells_to_occupy)
        # actually place the components
        c = self.components.add_ref(component)
        # move the component
        dcenter = np.array(((xmin + xmax + 1), -(ymin + ymax + 1))) * self.cell_size / 2
        c.move(c.center, np.array(self.origin) + dcenter)

    def place_multiple_on_sample(
        self,
        components: Sequence[gf.Component],
        cell_coordinate_bbox: tuple,
        column_major: bool = True,
        ignore_collisions: bool = False,
    ) -> None:
        """Place components on sample

        See also :py:meth:`place_on_sample`.
        Args:
            components (Sequence[Component]): sequence of components to place
            cell_coordinate_bbox (tuple[tuple[int, int], tuple[int, int]]):
                bounding box of cell coordiantes within which the component should be placed.
            column_major (bool): If True, orders components in column-major order within bbox.
                (top-to-bottom, then left-to-right). Otherwise, orders row-major (left-to-right,
                then top-to-bottom).
            ignore_collisions (bool): If True, ignores any collision of component with
                previously-placed components.

        Returns:
            None

        Side Effects:
            Updates self.open_cells to remove newly allocated cells
            Updates self.full_cells to add newly allocated cells
        """
        # infer desired grid from coordinate bbox
        _, _, _, _, row_span, col_span = Sample._get_bbox_extents(cell_coordinate_bbox)
        # iterate over ax_inner within ax_outer loop
        # by default, column-major iterates over rows within column loop
        ax_outer = list(col_span)
        ax_inner = list(row_span)
        if not column_major:
            ax_outer, ax_inner = ax_inner, ax_outer
        component_iter = iter(components)
        for iout, outer in enumerate(ax_outer):
            for iin, inner in enumerate(ax_inner):
                row = inner
                col = outer
                if not column_major:
                    row, col = col, row
                if (row, col) in self.open_cells:
                    try:
                        # generate a bounding box
                        component = next(component_iter)
                        rows = int(np.ceil(component.ysize / self.cell_size))
                        cols = int(np.ceil(component.xsize / self.cell_size))
                        self.place_on_sample(
                            component,
                            cell_coordinate_bbox=(
                                (row, col),
                                (row + rows - 1, col + cols - 1),
                            ),
                            ignore_collisions=ignore_collisions,
                        )
                    except StopIteration:
                        break
        if next(component_iter, None) is not None:
            r = 1
            while next(component_iter, None) is not None and r < 50:
                r += 1
            error_msg = "insufficient area provided, available space exhausted and "
            error_msg += f"still have {'>' if r >= 50 else ''}{r} remaining components."
            raise ValueError(error_msg)

    def write_cell_corners(self, width: float, layer: LayerSpec) -> None:
        """Adds corner markers to all full cells

        Args:
            width (float): width of corner marker
            layer (LayerSpec): layer to place marker on

        Returns:
            None

        Side Effects:
            Updates self.components with the new markers
        """
        corner = gf.components.L(
            width=width, size=(5 * width, 5 * width), layer=gf.get_layer(layer)
        )
        die_corners = gf.Component()
        for i in range(4):
            c = die_corners.add_ref(corner)
            c.rotate(90 * i)
            if i == 0 or i == 3:
                c.movex(-c.xmin)
            else:
                c.movex(self.cell_size - c.xmax)
            if i // 2 == 0:
                c.movey(-self.cell_size - c.ymin)
            else:
                c.movey(-c.ymax)
        for cell in self.full_cells:
            marks = self.components.add_ref(die_corners)
            dcenter = np.array((2 * cell[1] + 1, -2 * cell[0] - 1)) * self.cell_size / 2
            marks.move(marks.center, np.array(self.origin) + dcenter)

    def _check_component_size(self, component: gf.Component) -> bool:
        """Checks component size

        Args: component (Component): component to check

        Returns: True if component spans multiple cells

        Raises:
            RuntimeError if component requires more than one (1) cell of area,
            but ``allow_cell_span`` is false
        """
        spans_multiple = (
            component.xsize > self.cell_size or component.ysize > self.cell_size
        )
        if spans_multiple and not self.allow_cell_span:
            error_msg = "allow_cell_span is set to False, "
            error_msg += f"but the provided component {component.name} "
            error_msg += "is larger than a single cell {self.cell_size=}"
            raise RuntimeError(error_msg)
        return spans_multiple
