"""Generate images for callable methods"""

import os
import importlib.util
from phidl import Device
from phidl import quickplot as qp
from phidl import set_quickplot_options
import matplotlib.pyplot as plt


def import_module(module_path, module_name):
    """Imports a module dynamically from a given file path and module name.

    Args:
        module_path (str): The path to the Python file from which to import the module.
        module_name (str): The name to assign to the imported module.

    Returns:
        Module: The module loaded from the specified file.
    """
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plot_and_save_functions(module, module_name):
    """Plots and saves visual representations of components.

    This function iterates over all callable functions that return a Device
    Plots are saved in PNG format.
    """
    script_dir = os.path.dirname(__file__)
    save_dir = os.path.join(script_dir, "images")
    module_attrs = dir(module)
    set_quickplot_options(blocking=False, show_subports=False)
    for attr_name in module_attrs:
        attr = getattr(module, attr_name)
        if not (
            callable(attr) and hasattr(attr, "__call__") and not isinstance(attr, type)
        ):
            continue
        try:
            device = None
            result = attr()
            if isinstance(result, Device):
                device = result
            elif isinstance(result, tuple):
                devices = [item for item in result if isinstance(item, Device)]
                if len(devices) >= 1:
                    device = devices[0]
            if device is not None:
                qp(device)
                os.makedirs(os.path.join(save_dir, module_name), exist_ok=True)
                save_path = os.path.join(save_dir, module_name, f"{attr_name}.png")
                plt.savefig(save_path)
                plt.close()
                print(
                    f"Info: in module '{module_name}', function '{attr_name}' was plotted"
                )
        except Exception as e:
            if "missing" in str(e):
                print(
                    f"Warning: in module '{module_name}', function "
                    f"'{attr_name}' did not specify default arguments and will "
                    f"not be plotted: {e}"
                )
            else:
                raise Exception(f"failed to plot Device {attr_name}") from e


def get_modules(folder_path, module_prefix=""):
    """Recursively processes Python files in a given folder (and subfolders) to
    plot and save functions.

    Args:
        folder_path (str): Path to the directory containing module files and
        possibly other subdirectories. module_prefix (str): A prefix to append
        to module names for subdirectories (used for nested modules).

    This function scans through all files and directories in a given folder,
    skipping items that start with '_' (like __init__.py and __pycache__ but
    also _default_param for e.g.). For Python files, it imports the module, and
    for directories, it recursively calls itself to handle any nested modules or
    Python files, appending the directory name to the module prefix.
    """
    modules = []
    full_module_names = []
    for item in os.listdir(folder_path):
        if item.startswith("_"):
            continue  # Skip files or directories starting with __
        full_path = os.path.join(folder_path, item)
        if os.path.isdir(full_path):
            # For submodules, we append the current folder's name to the prefix
            new_prefix = f"{module_prefix}{item}/" if module_prefix else f"{item}/"
            new_modules, new_full_module_names = get_modules(full_path, new_prefix)
            modules += new_modules
            full_module_names += new_full_module_names
        elif item.endswith(".py"):
            module_name = item[:-3]
            full_module_name = (
                os.path.join(module_prefix, module_name)
                if module_prefix
                else module_name
            )
            modules.append(import_module(full_path, module_name))
            full_module_names.append(full_module_name)
    return modules, full_module_names


if __name__ == "__main__":
    folder_path = os.path.join(os.path.dirname(__file__), "..", "..", "src", "qnngds")
    try:
        modules, module_names = get_modules(folder_path)
        for module, module_name in zip(modules, module_names):
            plot_and_save_functions(module, module_name)
    except FileNotFoundError as e:
        print(e)
        print(
            "\nMake sure you are running the file in the correct directory. "
            "To fix this, you can run: \n"
        )
        current_file_path = os.path.realpath(__file__)
        parent_folder = os.path.dirname(current_file_path)
        print("     cd ", parent_folder)
        print()
