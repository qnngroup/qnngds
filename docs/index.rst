Welcome to qnngds documentation!
===================================

``qnngds`` is a toolbox built on top of `phidl <https://phidl.readthedocs.io/en/latest/index.html>`_
for device design in the `QNN group <https://qnn-rle.mit.edu/>`_. It is made to assist
with production of GDS files and facilitate easier sharing of layout-generation
code between users with different fabrication processes.

.. note::

   This project is under active development. Expect large breaking changes with major releases.

General description
-------------------

The package is built so that any person wanting to create a new design can do it
easily and quickly. It offers various devices and test structures used and designed
in the `QNN group <https://qnn-rle.mit.edu/>`_.

* :ref:`pdk`: captures information relevant to a specific fabrication process.
* :ref:`sample`: Contains utilities for placement of finished experiments on a sample.
  Composition of samples enables definition of large samples (e.g. wafers) comprised of
  multiple, smaller samples (e.g. 10 mm pieces) that each may have one or more experiments
  on them.

   * :ref:`experiment`: Provides utilities for converting a process-agnostic layout into an
     experiment that can be placed on a sample. Uses process-specific information specified
     by the :ref:`Pdk`. Can be constructed from circuits or devices.

      * :ref:`devices`: is a library of basic devices like nTron, hTron, nanowires, resistors etc...

      * :ref:`test_structures`: is a library of lithographic and electrical test structures that can
        be used for fabrication process characterization.

      * :ref:`geometries`: contains useful shapes/geometries that are not available in
        phidl or has been adapted from it for special use case.

      * :ref:`utilities`: contains useful tools for building cells and circuits.


Contents
--------

.. toctree::
   :maxdepth: 2

   src/api
   src/tutorials
   src/contributing
