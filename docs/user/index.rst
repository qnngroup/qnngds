Welcome to qnngds documentation!
===================================

``qnngds`` is a toolbox built on top of phidl for device design in the `QNN
group <https://qnn-rle.mit.edu/>`_. It is made for helping in the design of gds
files.

.. note::

   This project is under active development.

General description
-------------------

The package is built so that any person wanting to create a new design can do it
easily and quickly. It offers various devices, circuits, and test structures
used and designed in the `QNN group <https://qnn-rle.mit.edu/>`_. The package hierarchy is though as follow:

- :ref:`Design`: contains classes from which a complete design can be built. The class
  inputs are the basic parameters of the chip. Its methods are pre-built cells
  and tools for distributing and managing the cells over the chip.
   - :ref:`Cells`: is a library of cells pre-built, that are called by the Design's
     classes. Each cell contains a text, border marks and an experiment (circuits, devices, or tests)
     connected to pads for external connection.
      - :ref:`Circuits`: is a library of circuits made of devices.
         - :ref:`Devices`: is a library of basic devices like nTron, hTron, nanowires, resistors etc...
      - :ref:`Tests`: is a library of test structures that help through the fabrication process and
        characterization.
      - :ref:`Geometries`: contains useful shapes/geometries that are not available in
        Phidl or has been adapted from it for special use case.
      - :ref:`Utilities`: contains useful tools for building cells and circuits.

Contents
--------

.. toctree::
   :maxdepth: 2

   api
   tutorials

.. _Want to contribute?:

Want to contribute?
-------------------

Access the `qnngds developer documentation <https://qnngds-dev.readthedocs.io/en/latest/>`_.

.. toctree::
   :hidden:

   Developer Documentation <https://qnngds-dev.readthedocs.io/en/latest/>
