from phidl import Device
import os
import importlib.util
import inspect

import qnngds


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
        except TypeError:
            pass

        MODULE << FUNCTION

    return MODULE


def test_qnngds_devices(src_path):
    GDS = Device()
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

    GDS.write_gds("all_dev.gds", max_cellname_length=32000)


if __name__ == "__main__":
    # current_path = os.getcwd()
    # directories = current_path.split(os.path.sep)
    # qnngds_index = directories.index("qnngds")
    # path_to_qnngds = os.path.sep.join(directories[:qnngds_index + 1])
    qnngds_path = os.path.join("..", "src", "qnngds")
    test_qnngds_devices(qnngds_path)
