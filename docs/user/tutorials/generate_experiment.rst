.. _Generate Experiment:

Usage of ``generate_experiment``
===============================

Let's look at how the ``_experiment`` functions are defined in the PDK so we can understand
how to define custom experiments.

.. note::
   Implementation for keepout layers is planned, but not yet complete.
   This will allow more fully-featured positive-tone layouts without a lot of manual work.
   For example, it is currently not possible to use ``generate_experiment`` to automatically
   outline a resistor with superconducting contacts where the superconductor is defined with a positive tone mask.
   Currently, the contacts are outlined, but the area covered by the meander is not also removed,
   causing the entire resistor to be shorted by the superconductor.



nTron
~~~~~

.. code-block:: python
    :linenos:

    @gf.cell
    def ntron(
        choke_w: float = 1,
        channel_w: float = 3,
        n_branch: int = 1,
        layer: LayerSpec = "NTRON_COARSE",
    ) -> gf.Component:
        slot_w = channel_w / n_branch
        total_channel_w = (2 * n_branch - 1) * slot_w
        gate_w = 2 * choke_w + 0.5
        # define the base nTron geometry for the slotted nTron
        smooth_ntron = partial(
            qg.devices.ntron.smooth,
            choke_w=choke_w,
            gate_w=gate_w,
            channel_w=total_channel_w,
            source_w=total_channel_w * 1.2 + 0.2,
            drain_w=total_channel_w * 1.2 + 0.2,
            choke_shift=0.0,
            layer=layer,
            num_pts=20,
        )
        # add the slots
        slotted_ntron = partial(
            qg.devices.ntron.slotted,
            base_spec=smooth_ntron,
            slot_width=slot_w,
            slot_length=10 * n_branch**0.5 * slot_w,
            slot_pitch=2 * slot_w,
            n_slot=n_branch - 1,
            num_pts=20,
        )

Now we've created our DUT (``slotted_ntron``), which is an nTron with one or more parallel channels.

We can define our text label and the pads used to connect to the device (depending on the desired layer).

.. code-block:: python
    :linenos:
    :lineno-start: 32
        # define text label
        label = f"nTron\nwg/wc/Nc\n{choke_w}/{channel_w}/{n_branch}"
        # determine pads automatically from layer
        if "fine" in str(gf.get_layer(layer)).lower():
            layer = str(gf.get_layer(layer)).split("_")[0] + "_COARSE"
        pad_layers = [layer]
        if gf.get_layer(layer)[0] < gf.get_layer("VIA")[0]:
            pad_layers += ["VIA", "RESISTOR"]

Finally, we can construct the experiment by passing the DUT and constructing a pad array.
``route_groups`` is used to specify how the ports should be connected/routed between
the DUT and the pad array.  However, in this case, the DUT and pad array are simple
enough that this can be determined automatically (even if the PAD and DUT are on different
layers, provided there's a defined transition between the layers), so we just pass
``None`` as an argument for ``route_groups``.

.. code-block:: python
    :linenos:
    :lineno-start: 32

        # generate an experiment: a gf.Component with pads, routing between
        # DUT and pads, and a text label
        NT = gf.Component()
        NT << qg.utilities.generate_experiment(
            # extend gate port with an optimal taper
            dut=slotted_ntron,
            pad_array=pad_ntron(
                pad_spec=pad_stack(layers=pad_layers), xspace=100, yspace=400
            ),
            label=gf.components.texts.text(label, size=25, layer=layer, justify="right"),
            route_groups=None,  # automatically select cross_section and DUT/Pad pairings
            dut_offset=(0, 0),
            pad_offset=(0, 0),
            # offset text label
            label_offset=(-120, -200),
            # how many times to try sbend routing if regular routing
            # fails
            retries=1,
        )
        return NT


hTron
~~~~~
