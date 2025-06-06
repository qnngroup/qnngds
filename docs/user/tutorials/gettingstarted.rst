Getting started
===============

Clone boilerplate PDK
------------
* Create a repository on github for your layouts using the template `qnngds-pdk <https://github.com/qnngroup/qnngds-pdk>`_.

* Clone the repository to your machine. The cloned directory will contain everything related to your new design
  (python files, gds files, notes).

Setup a virtual environment and install ``qnngds``
--------------------
* Navigate to the directory you cloned the repository to.

* Create a new virtual environment:

    * Using ``uv`` (recommended, `installation instructions <https://docs.astral.sh/uv/#installation>`_):

        * Open a terminal in the directory you want to put your virtual environment.

        * Execute:

          .. code-block:: bash

              uv venv --python 3.11

        * Follow the instructions from ``uv`` to activate the environment, as they will differ depending on the platform.

        * Install qnngds

    * Using ``conda`` (recommended, `miniforge installation instructions <https://github.com/conda-forge/miniforge?tab=readme-ov-file#install>`_):

        * Execute:

          .. code-block:: bash

              conda create -n my-project-env
              conda activate my-project-env

    * Using ``python``:

        * Open a terminal in the directory you want to put your virtual environment.

        * Execute:

          .. code-block:: powershell

              # windows
              python -m venv .venv/your-env-name
              .\.venv\your-env-name\Scripts\Activate

          .. code-block:: bash

              # Unix/macOS
              python -m venv .venv/your-env-name
              source .venv/your-env-name/scripts/activate

* Install ``qnngds``

    * Using ``uv``

        .. code-block:: bash

            uv pip install qnngds

    * Using ``conda`` or ``python`` ``venv``:

        .. code-block:: bash

            pip install qnngds


.. note::
    To install a development version of ``qnngds`` that hasn't been released yet, replace the command ``pip install qnngds`` with ``pip install -e /path/to/cloned/copy/of/qnngds``. Note that this is a different path from the PDK repo you cloned earlier.


Install klive and gdsfactory extensions for klayout
~~~~~~~~~~~~~~~~~~~~~

* Follow the instructions from the `gdsfactory docs <https://gdsfactory.github.io/klive>`_ and restart klayout.


Start with the basics
~~~~~~~~~~~~~~~~~~~~~

Create a file in the toplevel of the cloned repository.

Import the necessary packages and activate the PDK

.. code-block:: python
    :linenos:

    from pdk import PDK
    from pdk.components import *

    import qnngds as qg
    import gdsfactory as gf

    PDK.activate()

Now let's generate a few different nTron geometries and connect them up to pads.
We'll make use of the ``pads_tri`` pad layout defined in the custom PDK.

.. code-block:: python
    :linenos:
    :lineno-start: 8

    nTrons = []
    for choke_w in [0.01, 0.03, 0.1]:
        for channel_w in [0.3, 2]:
            # create our nTrons
            gate_w = 10 * choke_w
            smooth_ntron = qg.devices.ntron.smooth(
                choke_w=choke_w,
                gate_w=gate_w,
                channel_w=channel_w,
                source_w=max(2, channel_w + 0.1),
                drain_w=max(2, channel_w + 0.1),
                choke_shift=0.0,
                layer="EBEAM_FINE",
            )
            # extend the gate port with an optimal step
            dut = gf.components.extend_ports(
                component=smooth_ntron,
                port_names="g",
                extension=partial(
                    qg.geometries.optimal_step,
                    start_width=gate_w,
                    end_width=5,
                    num_pts=200,
                    symmetric=True,
                ),
            )
            # generate an experiment: a gf.Component with pads, routing between
            # DUT and pads, and a text label
            label = f"nTron\nwg/wc/Nc\n{choke_w}/{channel_w}/{n_branch}"
            nTrons.append(
                qg.utilities.generate_experiment(
                    # extend gate port with an optimal taper
                    dut=dut,
                    pad_array=pads_tri,
                    label=gf.components.texts.text(
                        label, size=25, layer="EBEAM_COARSE", justify="right"
                    ),
                    route_groups=(
                        # route g,s,d automatically to the closest pad using
                        # the ebeam cross section
                        qg.utilities.RouteGroup(
                            PDK.get_cross_section("ebeam"), ("g", "s", "d")
                        ),
                    ),
                    dut_offset=(0, 0),
                    pad_offset=(0, 0),
                    # offset text label
                    label_offset=(-120, -200),
                    # how many times to try sbend routing if regular routing
                    # fails
                    retries=1,
                )
            )

    # array the nTrons with flex_grid
    c = qg.utilities.flex_grid(nTrons, shape=(2, 3), spacing=(100, 100))
    c.show()

.. image:: images/ntrons.png
   :alt: example ntron array

Editing PDK
~~~~~~~~~~~~~~~~~~

Now, let's configure the layers to use positive tone with a different line width for two layers
(representing different beam currents). We'll use 200 nm line width for the low-current (fine) layer, and 5 μm for the high-current (coarse) layer.
Edit the class method ``outline`` in ``pdk/layer_map.py``.

Rewrite ``outline`` so that it looks like this

.. code-block:: python

    @classmethod
    def outline(cls, layer: Layer) -> int:
        """Used to define desired outline for positive tone layers.

        To make a layer positive tone, return a non-zero value for it.

        E.g. if you want EBEAM_FINE to be positive tone with an outline
        of 100 nm, then you should define this function to return 0.1
        when passed a value of EBEAM_FINE (either as an enum type, a string
        or tuple that is equivalent to the EBEAM_FINE GDS layer).
        """
        if gf.get_layer(layer) == cls.EBEAM_FINE:
            return 0.2
        elif gf.get_layer(layer) == cls.EBEAM_COARSE:
            return 5
        # by default, assume a layer is negative tone
        return 0
