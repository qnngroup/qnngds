Welcome to qnngds documentation!
===================================

``qnngds`` is a toolbox built on top of gdsfactory for device design in the `QNN
group <https://qnn-rle.mit.edu/>`_. It is made for helping in the design of gds
files.

.. note::

   This project is under active development.

General description
-------------------

The package is built so that any person wanting to create a new design can do it
easily and quickly. It offers various devices, circuits, and test structures
used and designed in the `QNN group <https://qnn-rle.mit.edu/>`_. The package
follows the following hierarchy for designing layouts:

* Sample: toplevel of design, either a wafer or piece that contains multiple experiments.

    * Experiment: an individual experiment that has a specific intended use case.
      Includes circuit/device and pads.

        * Circuit: a circuit comprised of multiple devices e.g. SNSPD with nTron amplifier.
          Use of pads is generally discouraged, as it decreases reusability of circuits.
          Typically defined in a PDK.

        * Device: a single device e.g. individual nTron, hTron, etc.

This library is intended to be used alongside a PDK that defines a specific
layer stackup and any custom circuits/layouts for a fabrication process.


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
