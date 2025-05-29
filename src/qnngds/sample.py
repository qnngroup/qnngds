"""Sample defines the Sample class which is used to generate a wafer/piece layout from multiple experiments"""

import numpy as np

import gdsfactory as gf
from gdsfactory.typings import ComponentSpecOrComponent


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
    W << gf.boolean(
        A=circ, B=FLAT, operation="A-B", layer1=(1, 0), layer2=(1, 0), layer=(1, 0)
    )
    return W


@gf.cell
def wafer150mm():
    """Template for 150 mm wafer"""
    return _wafer(radius=75e3, flat=57.5e3)


@gf.cell
def wafer100mm():
    """Template for 100 mm wafer"""
    return _wafer(radius=50e3, flat=32.5e3)


class Sample:
    """Class for managing die/experiment area, with manual placement and basic autoplacement

    Defines a grid size and divides a sample (wafer/piece) into cells.
    Experiments (generated with :py:func:`qnngds.utilities.generate_experiment`)
    can be placed on one or more cells in the grid, manually or automatically.
    Experiments can span multiple columns/rows.

    """

    def __init__(
        self,
        grid_size: float = 1000,
        sample: ComponentSpecOrComponent = wafer150mm,
        edge_exclusion: float = 10000,
    ):
        """Constructor for Sample class

        Args:
            grid_size (float): pitch of die grid
            sample (Component | ComponentSpec): desired sample shape (e.g. wafer/piece)
            edge_exclusion (float): desired edge exclusion for die placement

        Returns:
            None

        """
        self.grid_size = (grid_size,)
        ############################
        # create grid
        ############################
        sample_region = gf.get_component(sample).get_region(layer=(1, 0))
        legal_region = sample_region.sized(-edge_exclusion / gf.kcl.dbu)

        # get number of rows/columns
        bbox = legal_region.bbox()
        n_cols = int(np.floor(bbox.width() * gf.kcl.dbu / grid_size))
        n_rows = int(np.floor(bbox.height() * gf.kcl.dbu / grid_size))

        # define which placements are legal
        mask = gf.Component()
        mask.add_polygon(legal_region, layer=(1, 0))
        mask.move(mask.center, (0, 0))

        # coordinates from left-to-right, top-to-bottom
        self.legal_placements = set([])
        rect = gf.components.rectangle(size=(grid_size, grid_size), layer=(1, 0))
        dummy = gf.Component()
        topleft = (-n_cols * grid_size / 2, n_rows * grid_size / 2)
        self.dies = gf.Component()
        for row in range(n_rows):
            for col in range(n_cols):
                d = dummy << rect
                d.move((d.xmin, d.ymax), topleft).movex(col * grid_size).movey(
                    -row * grid_size
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
                    self.legal_placements.add((row, col))
                    d = self.dies << rect
                    d.move((d.xmin, d.ymax), topleft).movex(col * grid_size).movey(
                        -row * grid_size
                    )
