"""example code used in tutorial"""

from pdk import PDK
from pdk.components import experiment_ntron

import qnngds as qg


import matplotlib.pyplot as plt

PDK.activate()

nTrons = []
for choke_w in [1, 2]:
    for channel_w in [5, 10]:
        nTrons.append(
            experiment_ntron(choke_w=choke_w, channel_w=channel_w, n_branch=1)
        )
# create a 10 x 10 cm piece and place the nTrons on it
tron_sample = qg.sample.Sample(
    cell_size=1e3,
    sample=qg.sample.piece10mm,
    edge_exclusion=1e3,  # don't place within 1 mm of edge
    allow_cell_span=True,
)
tron_sample.place_multiple_on_sample(
    components=nTrons,
    # place only in 2x2 square in top-left
    cell_coordinate_bbox=((0, 0), (1, 1)),
    # place in column-major order
    column_major=True,
)
# plot it
tron_sample.components.plot()
plt.savefig(
    "/home/reedf/syncthing/qnn/qnngds-dev/docs/user/tutorials/images/ntron_neg.png"
)
plt.close()
