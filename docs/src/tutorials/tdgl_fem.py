## ruff: noqa: E402
# .. _tdgl_fem:
# TDGL and FEM analysis
# =====================
#
# In this set of tutorials, we will cover conversion of ``qnngds.Device`` to ``tdgl.Device`` and ``skfem.mesh.MeshTri1`` for analysis of device properties.
#
# First, we will show how to generate a ``tdgl.Device``
import qnngds as qg
from qnngds.analysis.tdgl import make_tdgl_device
import matplotlib.pyplot as plt

snspd = qg.devices.snspd.basic()
device = make_tdgl_device(
    device=snspd,
    coherence_length=0.005,
    london_lambda=0.35,
    thickness=0.01,
    gamma=23.8,
    layer=(1, 0),
)
fig, ax = device.draw()
plt.show()
## SKIPSTART
from _save_qp import save_fig

save_fig(__file__, plot_name="tdgldraw")
## SKIPSTOP
## IMAGE_tdgldraw

# Now, let's analyze the structure with femwell/skfem to visualize the current density.
from qnngds.analysis.fem import (
    make_mesh,
    solve_laplace,
    visualize_mesh,
    visualize_current,
)

# we can create a mesh as so:
mesh = make_mesh(device=snspd, layer=(1, 0), tolerance=0.01)
visualize_mesh(mesh)
plt.show()
## SKIPSTART
save_fig(__file__, plot_name="femmesh")
## SKIPSTOP
## IMAGE_femmesh
# Now, let's analyze the current density by solving the laplace equation
result = solve_laplace(mesh)
visualize_current(result, ("1", "2"))
plt.show()
## SKIPSTART
save_fig(__file__, plot_name="femj")
## SKIPSTOP
## IMAGE_femj
