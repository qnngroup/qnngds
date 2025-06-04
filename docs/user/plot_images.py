"""Generate images for callable methods"""

import os
import traceback
import importlib.util
import gdsfactory as gf
import matplotlib.pyplot as plt

from pdk import ApiGenLayers


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


def plot_and_save_functions():
    """Plots and saves visual representations of components in currently active PDK

    This function iterates over all cells in the currently active PDK and plots them
    Plots are saved in PNG format.
    """
    save_dir = os.path.join(os.path.dirname(__file__), "images")
    for cell in gf.get_active_pdk().cells:
        module_name = "/".join(cell.split(".")[:-1])
        short_name = cell.split(".")[-1]
        os.makedirs(os.path.join(save_dir, module_name), exist_ok=True)
        try:
            # caching causes draw_ports() to modify other devices that are reused,
            # so just make a copy
            inst = gf.get_component(cell)
            D = gf.Component()
            D << inst
            D.add_ports(inst.ports)
            D.draw_ports()
            D.plot()
            # qp(device)
            save_path = os.path.join(save_dir, module_name, f"{short_name}.png")
            plt.savefig(save_path)
            plt.close()
            print(
                f"Info: in module '{module_name}', function '{short_name}' was plotted"
            )
        except Exception as e:
            if "missing" in str(e):
                print(
                    f"Warning: in module '{module_name}', function "
                    f"'{short_name}' did not specify default arguments and will "
                    f"not be plotted: {e}"
                )
            else:
                print(traceback.format_exc())


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


def generate_pdk(folder_path: str) -> None:
    """Generate and activate a PDK to be used for plotting

    Args:
        folder_path (str): Path to the directory containing module files and
        possibly other subdirectories.
    """
    # first get all of the submodules
    modules, module_names = get_modules(folder_path)
    # activate PDK
    cells = {}
    for module, module_name in zip(modules, module_names):
        new_cells = gf.get_factories.get_cells(module)
        prefix = module_name.replace("/", ".")
        for name, cell in new_cells.items():
            cells[f"{prefix}.{name}"] = cell
    pwd = os.path.dirname(os.path.realpath(__file__))
    PDK = gf.Pdk(
        name="apigen_pdk",
        layer_views=gf.technology.LayerViews(filepath=f"{pwd}/layer_views.yaml"),
        layers=ApiGenLayers,
        cells=cells,
    )
    PDK.activate()


if __name__ == "__main__":
    folder_path = os.path.join("..", "..", "src", "qnngds")
    try:
        generate_pdk(folder_path)
        plot_and_save_functions()
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
