"""This module is designed to generate a GDS file named "all_dev.gds". It loops
through the qnngds' modules, and add each function to the gds in the proper
package's hierarchy. If the function returns a Device object, it is written.

Run this test from its parent directory (qnngds/tests).

This test is helpfull to check what is the hierarchy and the name in the
Devices developped.

For eg., a phidl.geometry.union() will return an entirely flattened
Device named "union". Although very useful, union looses in some way the
hierachy information and it is important to determine whether or not
this information is to be kept. The same reflexion goes for
phidl.geometry.boolean().
"""

from phidl import Device
import os
import importlib.util
import inspect


def write_devices_from_module(module_name, src_path):

    MODULE = Device(str(module_name))

    # Import the module dynamically
    module_path = os.path.join(src_path, module_name)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Get all defined functions in the module
    functions = inspect.getmembers(module, inspect.isfunction)

    # Execute each function
    for name, func in functions:
        FUNCTION = Device(name)
        try:
            result = func()
            if isinstance(result, Device):
                FUNCTION << result
                print(f"From '{module_name}', writing '{name}' on the gds.")
            elif isinstance(result, tuple):
                result = [item for item in result if isinstance(item, Device)]
                for result in result:
                    FUNCTION << result
                    print(f"From '{module_name}', writing '{name}' on the gds.")
        except TypeError:
            pass

        MODULE << FUNCTION

    return MODULE


def test_qnngds_devices(src_path):
    GDS = Device()
    try:
        modules = [m for m in os.listdir(src_path) if not m.startswith("_")]

        for module in sorted(modules):
            if module.endswith(".py"):
                GDS << write_devices_from_module(module, src_path)
            else:
                SUBMOD = Device(f"{module}")
                module_path = os.path.join(src_path, module)
                submodules = sorted(
                    [
                        m
                        for m in os.listdir(module_path)
                        if not m.startswith("_") and m.endswith(".py")
                    ]
                )
                for submodule in submodules:
                    SUBMOD << write_devices_from_module(
                        submodule, os.path.join(src_path, module)
                    )
                GDS << SUBMOD

    except FileNotFoundError as e:
        print(e)
        print(
            "\nMake sure you are executing the test in the correct directory. "
            "To fix this, you can run: \n"
        )
        current_file_path = os.path.realpath(__file__)
        parent_folder = os.path.dirname(current_file_path)
        print("     cd ", parent_folder)
        print()

    GDS.write_gds("all_dev.gds", max_cellname_length=32000)


if __name__ == "__main__":
    qnngds_path = os.path.join("..", "src", "qnngds")
    test_qnngds_devices(qnngds_path)
