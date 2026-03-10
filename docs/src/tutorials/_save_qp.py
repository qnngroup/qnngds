import matplotlib.pyplot as plt
import os
from phidl import set_quickplot_options, quickplot as qp


def save_qp(file, device, xlim=None, ylim=None, zoom=True, plot_name=""):
    set_quickplot_options(show_subports=False)
    qp(device)
    dirname = os.path.dirname(file)
    basename = os.path.basename(file).split(".")[0]
    save_path = os.path.join(dirname, "generated", ".".join((basename, "png")))
    print(f"trying to save to path {save_path}")
    plt.savefig(save_path)
    if zoom:
        # zoom
        plt.xlim(xlim)
        plt.ylim(ylim)
        save_path = os.path.join(
            dirname, "generated", ".".join((basename + plot_name + "_zoom", "png"))
        )
        plt.savefig(save_path)
    plt.close()
