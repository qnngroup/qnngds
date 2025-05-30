"""Generate images for callable methods"""

import os
import importlib.util
import gdsfactory as gf
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
    """Plots and saves visual representations of PHIDL Device objects returned
    by functions within a module.

    Args:
        module (Module): The module containing the functions to be visualized.
        module_name (str): The name of the module, used to create a directory for saving plots.

    This function iterates over all attributes of the module, checking for callable objects that
    are not class definitions. If the callable returns a PHIDL Device or a tuple containing a PHIDL Device,
    it uses PHIDL's quickplot function to plot and then saves the plot to a directory corresponding to
    the module name. Plots are saved in PNG format.
    """
    save_dir = os.path.join(os.path.dirname(__file__), "images")
    os.makedirs(os.path.join(save_dir, module_name), exist_ok=True)
    func_names = dir(module)
    for func_name in func_names:
        func = getattr(module, func_name)
        if func_name[0] == "_":
            # skip hidden methods
            continue
        try:
            if (
                callable(func)
                and hasattr(func, "__call__")
                and not isinstance(func, type)
            ):
                device = False

                result = func()
                if isinstance(result, gf.Component):
                    device = result
                elif isinstance(result, tuple):
                    devices = [
                        item for item in result if isinstance(item, gf.Component)
                    ]  # gets all results that are devices
                    device = devices[0]  # keep only the first device returned

                if device:
                    # caching causes draw_ports() to modify other devices that are reused,
                    # so just make a copy
                    D = gf.Component()
                    D << device
                    D.add_ports(device.ports)
                    D.draw_ports()
                    D.plot()
                    # qp(device)
                    plt.savefig(os.path.join(save_dir, module_name, f"{func_name}.png"))
                    plt.close()
                    print(
                        f"Info: in module '{module_name}', function '{func_name}' was plotted"
                    )
        except Exception as e:
            if "missing" in str(e):
                print(
                    f"Warning: in module '{module_name}', function "
                    f"'{func_name}' did not specify default arguments and will "
                    f"not be plotted: {e}"
                )


def process_modules_in_folder(folder_path, module_prefix=""):
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
    for item in os.listdir(folder_path):
        if item.startswith("_"):
            continue  # Skip files or directories starting with __
        full_path = os.path.join(folder_path, item)
        if os.path.isdir(full_path):
            # For submodules, we append the current folder's name to the prefix
            new_prefix = f"{module_prefix}{item}/" if module_prefix else f"{item}/"
            process_modules_in_folder(full_path, new_prefix)
        elif item.endswith(".py"):
            module_name = item[:-3]
            full_module_name = (
                os.path.join(module_prefix, module_name)
                if module_prefix
                else module_name
            )
            module = import_module(full_path, module_name)
            plot_and_save_functions(module, full_module_name)


if __name__ == "__main__":
    folder_path = os.path.join("..", "..", "..", "src", "qnngds")
    try:
        process_modules_in_folder(folder_path)
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
