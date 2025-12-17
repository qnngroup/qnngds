"""define a registry for devices"""

_devices = {}


def device(f):
    """Decorator to register devices into global variable _devices"""
    global _devices
    _devices[f.__name__] = f
    return f
