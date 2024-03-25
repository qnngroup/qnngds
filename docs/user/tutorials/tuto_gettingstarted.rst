Getting started
===============

Setup your workspace
--------------------
* Create a new folder that will contain everything related to your new design
  (versions, gds files, notes).

* Create a new virtual environment:

    * Open a terminal in the directory you want to put your virtual environment.

    * Execute:

      .. code-block:: bash

          python -m venv/your-env-name
          .\.venv\your-env-name\Scripts\Activate


Install the package
-------------------
The qnngds package needs gdspy to be installed first. To do so, you can follow
instruction `here <https://pypi.org/project/gdspy/>`_. For windows, what works
best is to `install a pre-built wheel
<https://github.com/heitzmann/gdspy/releases>`_ and run :

.. code-block:: bash

    pip install path/to/gdspy-1.6.12-cp38-cp38-win_amd64.whl

Make sure you download the wheel corresponding to your device:

* `cpXX` is the version of python that it is built for.
* `winxx_amdXX` should be selected based on your system type.

Once gdspy is installed in your virtual environment, you can install qnngds by executing:

.. code-block:: bash

    pip install qnngds

Start coding
------------

.. note::
    This section is not yet completed because the ``design`` module is susceptible to change (class management).

Start with the basis
~~~~~~~~~~~~~~~~~~~~

Import the packages.

.. code-block:: python
    :linenos:

    from phidl import quickplot as qp
    from phidl import set_quickplot_options
    import qnngds.design as qd

    set_quickplot_options(blocking=True)

Choose your design parameters, create a new design and build the chip.

.. code-block:: python
    :lineno-start: 8

    chip_w = 5000
    chip_margin = 50
    N_dies = 5

    pad_size = (150, 250)
    outline_coarse = 10
    outline_fine = 0.5
    ebeam_overlap = 10

    layers = {'annotation':0, 'mgb2_fine':1, 'mgb2_coarse':2, 'pad':3}

    design = qd.Design(name = 'demo_design',
                        chip_w = chip_w, 
                        chip_margin = chip_margin, 
                        N_dies = N_dies, 

                        pad_size = pad_size,
                        device_outline = outline_fine,
                        die_outline = outline_coarse,
                        ebeam_overlap = ebeam_overlap,

                        annotation_layer = layers['annotation'],
                        device_layer = layers['mgb2_fine'],
                        die_layer = layers['mgb2_coarse'],
                        pad_layer = layers['pad'])

    CHIP = design.create_chip(create_devices_map_txt=False)

.. image:: docs\user\tutorials\tutorials_images\tuto_gettingstarted_basis.png
   :alt: create_chip.png

Add test vehicules cells
~~~~~~~~~~~~~~~~~~~~~~~~

Add alignement cells like:

.. code-block:: python
    :lineno-start: 38
    
    ALIGN_CELL_LEFT = design.create_alignement_cell(layers_to_align = [layers['mgb2_coarse'], layers['pad']], 
                                                    text = 'LEFT')
    design.place_on_chip(ALIGN_CELL_LEFT, (0, 2))

Add Van der pauw cells like:

.. code-block:: python
    :lineno-start: 46

    VDP_TEST_MGB2 = design.create_vdp_cell(layers_to_probe   = [layers['mgb2_coarse']], 
                                       layers_to_outline = [layers['mgb2_coarse']], 
                                       text = 'MGB2')
    design.place_on_chip(VDP_TEST_MGB2, (0, 0))

Add resolution test cells like:

.. code-block:: python
    :lineno-start: 56

    RES_TEST_MGB2_FINE = design.create_resolution_test_cell(layer_to_resolve = layers['mgb2_fine'],
                                                            text = 'MGB2 FINE')
    design.place_on_chip(RES_TEST_MGB2_FINE, (2, 2))

Add etch test cell like:

.. code-block:: python
    :lineno-start: 69

    ETCH_TEST = design.create_etch_test_cell(layers_to_etch = [[layers['pad']]],
                                         text = 'PAD')
    design.place_on_chip(ETCH_TEST, (3, 0))


.. image:: docs\user\tutorials\tutorials_images\tuto_gettingstarted_test_structures.png
   :alt: tuto_gettingstarted_test_structures.png


Some nanowire electronics
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
    :lineno-start: 75

    #SNSPD-NTRON

    SNSPD_NTRON_01  = design.create_snspd_ntron_cell(w_choke=0.1)
    design.place_on_chip(SNSPD_NTRON_01, (1, 0))

    # NANOWIRES

    channels_w = [0.025, 0.1, 0.5, 1, 2]
    channels_sources_w = [(x, 10*x) for x in channels_w]
    NANOWIRES = design.create_nanowires_cell(channels_sources_w=channels_sources_w,
                                            text = '\nsrc=10chn')
    design.place_on_chip(NANOWIRES, (1, 1))

    channels_sources_w = [(x, 4*x) for x in channels_w]
    NANOWIRES = design.create_nanowires_cell(channels_sources_w=channels_sources_w,
                                            text = '\nsrc=4chn')
    design.place_on_chip(NANOWIRES, (3, 1))

    # NTRONS

    remaining_cells = []
    chokes_w = [0.025, 0.05, 0.1, 0.25, 0.5]
    channel_to_choke_ratios = [5, 10]
    for ratio in channel_to_choke_ratios:
        for choke_w in chokes_w:
            channel_w = choke_w*ratio
            NTRON = design.create_ntron_cell(choke_w, channel_w)
            remaining_cells.append(NTRON)
    design.place_remaining_devices(remaining_cells, write_remaining_devices_map_txt = False)

.. image:: docs\user\tutorials\tutorials_images\tuto_gettingstarted_some_electronics.png
   :alt: tuto_gettingstarted_some_electronics.png

See full code `in GitHub <https://github.com/qnngroup/qnngds>`_.