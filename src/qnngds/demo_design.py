from phidl import quickplot as qp
from phidl import set_quickplot_options
import qnngds.design as qd

set_quickplot_options(blocking=True)


chip_w = 5000
chip_margin = 50
N_dies = 5

pad_size = (150, 250)
outline_coarse = 10
outline_fine = 0.5
ebeam_overlap = 10

layers = {'annotation':0, 'mgb2_fine':1, 'mgb2_coarse':2, 'pad':3}

design = qd.Design(name = 'demo_design',
                    chip_w = chip_w, 
                    chip_margin = chip_margin, 
                    N_dies = N_dies, 

                    pad_size = pad_size,
                    device_outline = outline_fine,
                    die_outline = outline_coarse,
                    ebeam_overlap = ebeam_overlap,

                    annotation_layer = layers['annotation'],
                    device_layer = layers['mgb2_fine'],
                    die_layer = layers['mgb2_coarse'],
                    pad_layer = layers['pad'])

CHIP = design.create_chip(create_devices_map_txt=False)

## test devices

ALIGN_CELL_LEFT = design.create_alignement_cell(layers_to_align = [layers['mgb2_coarse'], layers['pad']], 
                                                text = 'LEFT')
design.place_on_chip(ALIGN_CELL_LEFT, (0, 2))

ALIGN_CELL_RIGHT = design.create_alignement_cell(layers_to_align = [layers['mgb2_coarse'], layers['pad']], 
                                                 text = 'RIGHT')
design.place_on_chip(ALIGN_CELL_RIGHT, (4, 2))

VDP_TEST_MGB2 = design.create_vdp_cell(layers_to_probe   = [layers['mgb2_coarse']], 
                                       layers_to_outline = [layers['mgb2_coarse']], 
                                       text = 'MGB2')
design.place_on_chip(VDP_TEST_MGB2, (0, 0))

VDP_TEST_PAD = design.create_vdp_cell(layers_to_probe = [layers['mgb2_coarse'], layers['pad']], 
                                       layers_to_outline=[layers['mgb2_coarse']], 
                                       text = 'PAD & MGB2')
design.place_on_chip(VDP_TEST_PAD, (0, 1))

RES_TEST_MGB2_FINE = design.create_resolution_test_cell(layer_to_resolve = layers['mgb2_fine'],
                                                        text = 'MGB2 FINE')
design.place_on_chip(RES_TEST_MGB2_FINE, (2, 2))

RES_TEST_MGB2_COARSE = design.create_resolution_test_cell(layer_to_resolve = layers['mgb2_coarse'],
                                                          text = 'MGB2 COARSE')
design.place_on_chip(RES_TEST_MGB2_COARSE, (1, 2))

RES_TEST_PAD = design.create_resolution_test_cell(layer_to_resolve = layers['pad'],
                                                  resolutions_to_test = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2.0],
                                                  text = 'PAD')
design.place_on_chip(RES_TEST_PAD, (3, 2))

ETCH_TEST = design.create_etch_test_cell(layers_to_etch = [[layers['pad']]],
                                         text = 'PAD')
design.place_on_chip(ETCH_TEST, (3, 0))

qp(CHIP)
## nanowire electronics

#SNSPD-NTRON

SNSPD_NTRON_01  = design.create_snspd_ntron_cell(w_choke=0.1)
design.place_on_chip(SNSPD_NTRON_01, (1, 0))

# NANOWIRES

channels_w = [0.025, 0.1, 0.5, 1, 2]
channels_sources_w = [(x, 10*x) for x in channels_w]
NANOWIRES = design.create_nanowires_cell(channels_sources_w=channels_sources_w,
                                         text = '\nsrc=10chn')
design.place_on_chip(NANOWIRES, (1, 1))

channels_sources_w = [(x, 4*x) for x in channels_w]
NANOWIRES = design.create_nanowires_cell(channels_sources_w=channels_sources_w,
                                         text = '\nsrc=4chn')
design.place_on_chip(NANOWIRES, (3, 1))

# NTRONS

remaining_cells = []
chokes_w = [0.025, 0.05, 0.1, 0.25, 0.5]
channel_to_choke_ratios = [5, 10]
for ratio in channel_to_choke_ratios:
    for choke_w in chokes_w:
        channel_w = choke_w*ratio
        NTRON = design.create_ntron_cell(choke_w, channel_w)
        remaining_cells.append(NTRON)
design.place_remaining_devices(remaining_cells, write_remaining_devices_map_txt = False)


qp(CHIP)
# design.write_gds()
