import os
import importlib.util
from phidl import Device
from phidl import quickplot as qp
from phidl import set_quickplot_options
import matplotlib.pyplot as plt


def import_module(module_path):
    """Dynamically imports a Python module given its file path.

    Parameters:
        module_path (str): Path to the Python module.

    Returns:
        module: Imported module object.
    """
    module_name = os.path.basename(module_path).split(".")[0]
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plot_and_save_functions(module, module_name):
    """Iterates through the functions of a module, executes them, plots their
    return, and saves the plots.

    Parameters:
        module: Module object.
        module_name (str): Name of the module.
    """
    # Create folder for saving plots
    os.makedirs(module_name, exist_ok=True)

    # Get all functions defined in the module
    func_names = dir(module)

    set_quickplot_options(blocking=False)
    for func_name in func_names:

        func = getattr(module, func_name)
        # Try several sets of conditions to create the images only for functions that return a device object
        try:
            if (
                callable(func)
                and hasattr(func, "__call__")
                and not isinstance(func, type)
            ):
                result = func()
                if isinstance(result, tuple):
                    result = result[0]
                if isinstance(result, Device):
                    qp(result)
                    plt.savefig(os.path.join(module_name, f"{func_name}.png"))
                    plt.close()
                    print(
                        f"Info: in module '{module_name}', function '{func_name}' was plotted"
                    )
        except Exception as e:
            if "missing" in str(e):
                print(
                    f"Warning: in module '{module_name}', function '{func_name}' was not plotted: {e}"
                )


def process_modules_in_folder(folder_path):
    """Processes all modules in a folder.

    Parameters:
        folder_path (str): Path to the folder containing the modules.
    """
    for filename in ["devices", "circuits", "geometries", "utilities", "design"]:
        module_path = os.path.join(folder_path, filename + ".py")
        module = import_module(module_path)
        plot_and_save_functions(module, filename.split(".")[0])


if __name__ == "__main__":
    folder_path = os.path.join("..", "..", "..", "src", "qnngds")
    process_modules_in_folder(folder_path)
