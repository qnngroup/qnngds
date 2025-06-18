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

There are 4 phases to the ``generate_experiment`` function.

1. Verifies the inputs as best it can to check for mistakes. For example, unconnected pads, a difference between the number of ports on the DUT and pad array.
2. Determines which device-under-test (DUT) ports will connect to which pad ports, using any information supplied from the ``route_groups`` argument.
3. Outlines the pads and DUT on all positive-tone layers.
4. Routes between DUT and pad ports, using the ``cross_section`` specified by each route group, automatically adding tapers defined in the PDK. In addition to same-layer tapers, layer transitions (e.g. bewteen fine and coarse layers for low and high beam current e-beam layers) must also be explicitly defined in the PDK.


nTron
~~~~~

Let's look at the source code for the nTron experiment.
This function creates an nTron with a specific choke width, channel width, and number of branches in the channel (use ``n_branch = 1`` for a standard nTron, ``n_branch > 1`` for a slotted nTron).

The following block sets up the device-under-test (DUT) to be connected to pads (and optionally outlined):

.. code-block:: python
    :linenos:

    @gf.cell
    def ntron(
        choke_w: float = 1,
        channel_w: float = 3,
        n_branch: int = 1,
        layer: LayerSpec = "NTRON_COARSE",
    ) -> gf.Component:
        """Generates an experiment with a nTron and pads

        nTron can optionally have slots by making n_branch > 1.

        Args:
            choke_w (float): width of choke
            channel_w (float): width of channel
            n_branch (int): number of branches in channel (num slots + 1)
            layer (LayerSpec): layer for ntron

        Returns:
            (gf.Component): nTron with connected pads
        """
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

Next, we'll define the label text for the experiment and the pads for the nTron.
In this case, we're placing all the pads on the same side, with a pitch of 150 μm
for use with a multi-contact wedge in a probe station.

.. code-block:: python
    :linenos:
    :lineno-start: 46

        # generate an experiment: a gf.Component with pads, routing between
        # DUT and pads, and a text label
        if "fine" in str(gf.get_layer(layer)).lower():
            layer = str(gf.get_layer(layer)).split("_")[0] + "_COARSE"
        pad_layers = [layer]
        if gf.get_layer(layer)[0] < gf.get_layer("VIA")[0]:
            pad_layers += ["VIA", "RESISTOR"]
        cross_section = qg.utilities.get_cross_section_with_layer(
            gf.get_layer(layer), default="default"
        )
        label = gf.Component()
        label.add_ref(
            gf.components.texts.text(
                f"wg/wc/Nc {choke_w}/{channel_w}/{n_branch}",
                size=25,
                layer=layer,
                justify="center",
            )
        ).rotate(-90)
        pitch = 300
        pads = pad_array(
            pad_specs=(pad_stack(layers=pad_layers, size=(200, 100)),),
            columns=1,
            rows=3,
            pitch=pitch,
        )

Now, we actually create the experiment by combining the DUT (``slotted_ntron``) with the pad array.

.. code-block:: python
    :linenos:
    :lineno-start: 71

        NT = gf.Component()
        NT << qg.utilities.generate_experiment(
            # extend gate port with an optimal taper
            dut=slotted_ntron,
            pad_array=pads,
            label=label,
            route_groups=(
                qg.utilities.RouteGroup(
                    gf.get_active_pdk().get_cross_section(cross_section),
                    {"s": "e1", "g": "e2", "d": "e3"},
                ),
            ),
            dut_offset=(50, 0),
            pad_offset=(-pads.xsize, -pitch),
            # offset text label
            label_offset=(100, 0),
            # how many times to try sbend routing if regular routing
            # fails
            retries=1,
        )
        NT.rotate(90)
        return NT


