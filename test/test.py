"""Basic test code"""

import unittest
import qnngds
import pkgutil
from functools import partial
import phidl.path as pp
import phidl.geometry as pg

helper_functions = [
    "compute_res_wavelength",
    "compute_veff",
    "device",
    "generate",
    "get_cross_section",
    "get_device",
    "get_layer",
    "get_outline_layers",
    "layer_auto_transitions",
    "outline",
    "extend_ports",
    "get_device_port_direction",
    "get_keepout_layers",
    "get_outline_layers",
    "hyper_taper_fn",
    "invert",
    "keepout",
    "outline",
    "to_qg_device",
    "create_layered_ports",
]


def get_all_modules(module):
    """Get all submodules within a module

    Parameters:
        module (module): module within which to search

    Returns:
        (list[module]): list of modules/submodules contained within module
    """
    modules = []
    for submodule in pkgutil.walk_packages(module.__path__):
        submodule_ref = pkgutil.resolve_name(module.__name__ + "." + submodule.name)
        if submodule.ispkg:
            modules += get_all_modules(submodule_ref)
        else:
            modules.append(submodule_ref)
    return modules


def get_all_factories():
    """Get all functions in qnngds that return a Device

    Returns:
        (list[function]): list of Device-returning functions within qnngds
    """
    modules = get_all_modules(qnngds)
    factories = []
    for module in modules:
        for attr in dir(module):
            member = getattr(module, attr)
            if attr.startswith("_"):
                continue
            if not (callable(member) and hasattr(member, "__call__")):
                continue
            if isinstance(member, type):
                continue
            if "qnngds" not in member.__module__:
                continue
            try:
                result = member()
                if isinstance(result, qnngds.Device):
                    factories.append(member)
            except TypeError as e:
                if "missing" in str(e):
                    if member.__name__ not in helper_functions:
                        raise TypeError(
                            f"Function `{member.__name__}` is missing one or more default arguments.\n"
                            f"If `{member.__name__}` is a device, make sure to register it with "
                            "the decorator @qnngds.device and provide default arguments for all "
                            f"of its inputs.\nIf `{member.__name__}` is a helper function, make "
                            f"sure to include it in the `helper_functions` list in this file:\n\t{__file__}."
                        ) from e
                else:
                    raise
    return factories


class RegisteredDevices(unittest.TestCase):
    """Verify that all functions returning a Device have been registered"""

    def test_registry(self):
        """Tests that list of functions that return Device matches list
        of functions registered with @qg.device decorator"""
        qnngds.pdk.get_generic_pdk().activate()
        factories = set([(f.__module__, f.__name__) for f in get_all_factories()])
        registry = set(qnngds.decorator._devices.keys())
        self.assertEqual(factories.difference(registry), set([]))


class PdkTestCase(unittest.TestCase):
    """Test cases for Pdk and Layout classes.

    - Test lookup of layers in PDK
    - Test lookup of cross sections

    TODO:
    - Test lookup of devices
    """

    def setUp(self):
        """Set up PDK test cases by initializing a simple PDK"""
        ls = qnngds.LayerSet()
        ls.add_layer(qnngds.Layer(name="layer1", gds_layer=1))
        ls.add_layer(qnngds.Layer(name="layer2", gds_layer=2))
        cross_sections = dict(
            xc1=partial(qnngds.geometries.default_cross_section, layer="layer1"),
        )
        layer_transitions = qnngds.layer_auto_transitions(ls)
        PDK = qnngds.Pdk(
            "test_pdk",
            layers=ls,
            cross_sections=cross_sections,
            layer_transitions=layer_transitions,
        )
        PDK.activate()

    def test_layer_lookup(self):
        """Tests layer lookup in example PDK

        - Verifies that layer lookup accepts string, tuple, and int arguments
        - Verifies that layer lookup raises an exception when passed an invalid layer
        """
        for i in range(2):
            self.assertEqual(
                qnngds.get_layer(f"layer{i + 1}").tuple,
                qnngds.get_layer((i + 1, 0)).tuple,
            )
            self.assertEqual(qnngds.get_layer(f"layer{i + 1}").tuple, (i + 1, 0))
            self.assertEqual(qnngds.get_layer(i + 1).tuple, (i + 1, 0))
        self.assertRaisesRegex(
            ValueError,
            "Could not find layer layer3 in Pdk.*",
            qnngds.get_layer,
            "layer3",
        )
        self.assertRaisesRegex(
            ValueError,
            "Could not find layer .*",
            qnngds.get_layer,
            3,
        )

    def test_cross_section_lookup(self):
        """Tests CrossSection lookup in example PDK

        - Compares manually-generated cross-section extrusion with one generated from PDK lookup
        - Verifies exception is thrown when passed an invalid cross-section specification
        """
        default = qnngds.geometries.default_cross_section(layer="layer1").extrude(
            pp.straight(length=1)
        )
        get = qnngds.get_cross_section("xc1").extrude(pp.straight(length=1))
        non_intersecting = pg.kl_boolean(
            A=default, B=get, operation="A-B"
        ).get_polygons()
        self.assertEqual(non_intersecting, [])
        self.assertRaisesRegex(
            ValueError, "xc2 from PDK.*", qnngds.get_cross_section, "xc2"
        )
        self.assertRaisesRegex(ValueError, "Callable.*", qnngds.get_cross_section, str)
