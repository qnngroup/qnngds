# Functions
`import qnngds.qnngds.omedeiro as om`


## adam_pads
`qp(om.adam_pads())`

![adam_pads](/docs/images/omedeiro/adam_pads.png)
## adam_pads_fill
`qp(om.adam_pads_fill())`

![adam_pads_fill](/docs/images/omedeiro/adam_pads_fill.png)
## adam_pads_quad
`qp(om.adam_pads_quad())`

![adam_pads_quad](/docs/images/omedeiro/adam_pads_quad.png)
## alignment_marks

## assign_ids

## create_device_doc

## heat_sameSidePort

## hyper_taper

## hyper_taper_outline

## meander
This function creates an snspd meander with two hyperbolic tapers and one pad. It returns a list of devices and a appended parameter dictionary.
```
parameters = {
        'pad_dim': (200,200),
        'pad_outline': 10,
        'pad_taper_length': 80,
        'pad_port_size': (40,10),
        'pad_layer': 2,
        'snspd_outline': 1,
        'snspd_width': np.array([.1]),
        'snspd_fill': 0.25,
        'snspd_area': np.array([8]),
        'snspd_taper_length': 40,
        'snspd_port': 150,
        'snspd_layer': 1,
        }
parameters, device_list = om.meander(parameters)
qp(device_list)
```

![meander](/docs/images/omedeiro/meander.png)

## nw_same_side

## nw_same_side_port

## nw_same_side_port_single

## outline_invert

## packer
Packer arranges devices using [phidl/geometry](https://phidl.readthedocs.io/en/latest/#packer-align-distribute) method `packer` and adds the device name to the layout.

This method is passed a list of devices. Each device in the list should have a `name` field attached. example: `device_in_list.name = 'A1'`
In addition to the parameters accepted by phidl.geometry.packer this method accepts parameters for text specifications. If no text is desired just use phidl. 

This method returns a single device object but each device from the list can be retreived using: `returned_variable.references[index_in_list].name`

```
parameters = {
        'pad_dim': (200,200),
        'pad_outline': 10,
        'pad_taper_length': 80,
        'pad_port_size': (40,10),
        'pad_layer': 3,
        'snspd_outline': 1,
        'snspd_width': np.array([.1,.1,.1]),
        'snspd_fill': 0.25,
        'snspd_area': np.array([8,10,12]),
        'snspd_taper_length': 40,
        'snspd_port': 150,
        'snspd_layer': 1,
        }
n = Namespace(**parameters) 
parameters, device_list = om.meander(parameters)
a=om.packer(device_list,text_letter='A', 
            text_pos=(0,-70),
            text_layer=n.pad_layer, 
            spacing = 100, 
            max_size=(None,750),
            sort_by_area=False)
qp(a)
```

![packer](/docs/images/omedeiro/packer.png)


## packer_doc


```
om.packer_doc(D_pack_list)
```

Output text file at S:\SC\Measurement\SAMPLENAME

```
ID,	WIDTH,	AREA,	SQUARES,	
----------------------------------
A0,	0.1,	8,	1600.0,	
. . . . . . . . . . . . . . . . 
A1,	0.1,	10,	2500.0,	
. . . . . . . . . . . . . . . . 
A2,	0.1,	12,	3600.0,	
. . . . . . . . . . . . . . . . 
\-----------------------------------\ 
```
## packer_rect

## pad_basic

## pad_basic_outline

## reset_time_calc

## save_gds

## squares_meander_calc

## text_labels