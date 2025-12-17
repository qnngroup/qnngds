"""Generate images for functions that produce Devices"""

import os
from phidl import Device
from phidl import quickplot as qp
from phidl import set_quickplot_options
import matplotlib.pyplot as plt

import qnngds as qg


def plot_and_save_functions():
    """Plots and saves visual representations of devices

    This function iterates over all functions registered with the
    @qnngds.device decorator. Plots are saved in PNG format.
    """
    script_dir = os.path.dirname(__file__)
    save_dir = os.path.join(script_dir, "images")
    set_quickplot_options(blocking=False, show_subports=False)
    for name, attr in qg._devices.items():
        if not (
            callable(attr) and hasattr(attr, "__call__") and not isinstance(attr, type)
        ):
            print(
                f"WARNING, function {name} has the @qnngds.device decorator, but is not callable"
            )
            continue
        try:
            module_name = attr.__module__
            func_name = attr.__name__
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
                module_subpath = os.path.join(*module_name.split(".")[1:])
                os.makedirs(os.path.join(save_dir, module_subpath), exist_ok=True)
                save_path = os.path.join(save_dir, module_subpath, f"{func_name}.png")
                plt.savefig(save_path)
                plt.close()
                print(
                    f"Info: in module '{module_name}', function '{func_name}' was plotted and saved to '{save_path}'"
                )
        except Exception as e:
            if "missing" in str(e):
                print(
                    f"Warning: in module '{module_name}', function "
                    f"'{func_name}' did not specify default arguments and will "
                    f"not be plotted: {e}"
                )
            else:
                raise Exception(f"failed to plot Device {func_name}") from e
