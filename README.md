# QNNGDS

Toolbox built on top of phidl for device design in the QNN group. 

## Motivation
Design is the first step in our experimental work and our design process can dictate the quality of our research. 
This toolbox will not improve your devices designs but hopes to add functions that improve how we collect and save device parameters. 

For instance, when measuring a device we can identify it using the Sample ID and Device ID (SPG000, A1) but that does not tell us any information about the device e.g. what is the wire width? To answer this type of question we can make certain reconfigurations to our design scripts, similar to qnnpy with our measurement scripts. 

## Direction

##### functions should be as generic as possible. should not have any relation to a design.
`om.create_device_doc` is a good example of this. A user can generate device_list/ids/parameters in any manner.

`om.outline_invert` is a bad example. only works with mc.meander.

### notes

#### Designing a Device
- device design should be largely left to the user. 
	- new devices are built using phidl geometry methods. They should be configured in a fully parameterized way. 
	- **need to determine best way to pass information.** 
		1. create methods that accept variables. 
			- pros: thats how most functions are used. 
			- cons: saving all parameters at once is not a simple.
		2. create methods that accept dictionay and extract from that.  
			- pros: saving/writing parameters to file. 
			- cons: data types/loops can be bulky. if a variable is missing or incorrect.

- Where should loops be created? 
	- We often use loops to generate devices that have varying parameters. An example would be 10 snspds with increasing active area. The question is **whether to have the method that creates the device handle lists or arrays, or have the user call the method in a loop that they create? **
#### Designing a layout
Layouts should be compiled from a list of devices. This total device list should contain sublists for every "style" of device. Style here refers to any device that is repeated with zero to few parameters changing. For example, if creating a layout of snspd's you might create 10 snspds with width of 100nm and increasing length, then 10 snspds with 200nm width and increasing length

When a layout is complete (ready for writing) there should be a function that will:
- generate device ID's and attach device description/parameters. 
	- Textfile stored in the same location?
		- Simple text table that describes the device layout. Text table should only include variables that are itterated (different widths/dimensions). 
		- Naming should also follow the design (all 3um devices are A# and all 5um are B# etc.).
		- Would be a nice reference while measuring. (e.g. was A0 the 3um wire or the 5um?)
- provide a location for fabrication details.
	- Database?
			- Brainstormed some design ideas in excel. Can get quite messy. 
			
	
	
## Structure
Functions could be broken up into classes for device parameterization, device construction, device layout, and device saving. 

Links between sections: **Backward** *Forward*
### Parameterization
- Devices should be fully parameterized. See CNST Nanolithography Toolbox for examples. 
- There is the question of how to set up parameterization for "combined" devices. **Should a parameter dictionary contain parameters for every device (e.g. pad parameters, snspd parameters, etc.) or should there be a single dictionary for every device?** 
- *Every device is returned with ports for connections*

### Combination
- **Devices should be combined using the ports defined in parameterization**
- Functions that combine parameters should be written by each user. ? For instance, even simple snspd design changes depending on fab process, pads connected or not... 
- 
- *Devices should be compled into a list for orginization.*

### Orginization
- **Orginization functions should work with a list of functions **
- There should be different functions for arranging devices using static spacing or dynamic spacing to reduce area. 
- Names could be created here based on location/grouping
- *Pass layout and parameters to save*


### Saving
- Parameters used to define device should be saved.
	- This is more complicated with the sublists. Each sublist will have its own parameter definition. save_gds could be updated to handle lists of parameters then write to the file each sublist-parameters on new lines. 
	- An alternative would be to save a copy of the python script on the NAS. 
- GDS of layout created
- Create layout reference doc.
	- what parameters are worth saving.... how to specify. 
- Location for files created on network
- Protections for sample names (ask as input)



