"""Define a registry for devices. Currently this is only used for documentation purposes."""

_devices = {}


def device(f):
    """Decorator to register DeviceFactories into the global variable qnngds.decorator._devices.

    For example, if we wish to define a new DeviceFactory that can
    be used to generate Devices, we can write the following:

    .. code-block:: python
        :linenos:

        import qnngds as qg
        from qnngds import Device

        @qg.device
        def my_new_device(
            some_param: int,
            some_other_param: str,
            layer: LayerSpec,
            ...
        ) -> Device:
            \"\"\"Docstring to explain my function.

            Parameters
                some_param (int): explanation of some_param.
                some_other_param (str): explanation of some_other_param.
                layer (LayerSpec): GDS layer specification.
                ...

            Returns
                (Device): description of the device returned
            \"\"\"
            ...
    """
    global _devices
    _devices[(f.__module__, f.__name__)] = f
    return f
