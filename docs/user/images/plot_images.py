import os
import importlib.util
from phidl import Device
from phidl import quickplot as qp
from phidl import set_quickplot_options
import matplotlib.pyplot as plt

def import_module(module_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def plot_and_save_functions(module, module_name):
    os.makedirs(module_name, exist_ok=True)
    func_names = dir(module)
    set_quickplot_options(blocking=False)
    for func_name in func_names:
        func = getattr(module, func_name)
        try:
            if callable(func) and hasattr(func, "__call__") and not isinstance(func, type):
                result = func()
                if isinstance(result, tuple):
                    result = result[0]
                if isinstance(result, Device):
                    qp(result)
                    plt.savefig(os.path.join(module_name, f"{func_name}.png"))
                    plt.close()
                    print(f"Info: in module '{module_name}', function '{func_name}' was plotted")
        except Exception as e:
            if "missing" in str(e):
                print(f"Warning: in module '{module_name}', function '{func_name}' was not plotted: {e}")

def process_modules_in_folder(folder_path, module_prefix=""):
    for item in os.listdir(folder_path):
        if item.startswith('__'):
            continue  # Skip files or directories starting with __
        full_path = os.path.join(folder_path, item)
        if os.path.isdir(full_path):
            # For submodules, we append the current folder's name to the prefix
            new_prefix = f"{module_prefix}{item}/" if module_prefix else f"{item}/"
            process_modules_in_folder(full_path, new_prefix)
        elif item.endswith(".py"):
            module_name = item[:-3]
            full_module_name = os.path.join(module_prefix, module_name) if module_prefix else module_name
            module = import_module(full_path, module_name)
            plot_and_save_functions(module, full_module_name)

if __name__ == "__main__":
    folder_path = os.path.join("..", "..", "..", "src", "qnngds")
    process_modules_in_folder(folder_path)
