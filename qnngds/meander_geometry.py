import numpy as np
from phidl import Device
import phidl.geometry as pg
from qnngds.qnngds.geometry import hyper_taper

'''
Building blocks useful to mix-and-match different kinds of meander geometries

Currently necessary for long_meanders tapers & SNSPIs, but ultimately may want to
merge with geometry.py
'''

'''
Solid components
'''

def solid_pad(width1=200, layer=1):
    '''
    Pad for microwire [solid]

    width1 = width of square pad [um]
    '''
    D=Device('Pad')
    R1=pg.rectangle(size=(width1,width1))
    R1.add_port(name = 1, midpoint = [R1.center[0],2*R1.center[1]], width = 2*R1.center[1], orientation = 90)

    # add pad to device
    r = D.add_ref(R1)
    
    D.flatten(single_layer = layer)
    D.add_port(name = 'out', midpoint = [R1.center[0],2*R1.center[1]], width = 2*R1.center[1], orientation = 90)
    
    return D  


def solid_microwire(length, width, ht, pad, layer=1):
    '''
    length: length of microwire [um]
    width: width of microwire [um]
    ht: phidl device representing taper to pads
    pad: phidl device representing pads

    returns one complete microwire (solid)
    '''
    # device "canvas" to draw wire into
    D = Device('microwire')

    # create rectangle for wire and add ports
    R = pg.rectangle(size = (width, length), layer=layer)
    R.add_port(name='wire1', midpoint = [width/2, length], width=width, orientation = 90)
    R.add_port(name='wire2', midpoint=[width/2, 0], width=width, orientation = 270)
    rect_ref = D.add_ref(R)

    # make two references to hypertaper, one for each side
    ht_ref1 = D.add_ref(ht)
    ht_ref2 = D.add_ref(ht)

    # connect narrow ends to the wire
    ht_ref1.connect(port='narrow', destination=rect_ref.ports['wire1'])
    ht_ref2.connect(port='narrow', destination=rect_ref.ports['wire2'])

    # make two references to pad, one for each side
    pad_ref1 = D.add_ref(pad)
    pad_ref2 = D.add_ref(pad)

    # connect to wide ends of tapers
    pad_ref1.connect(port='out', destination=ht_ref1.ports['wide'])
    pad_ref2.connect(port='out', destination=ht_ref2.ports['wide'])

    D.flatten(layer)
    return D

'''
Outline components
'''

def microwire_outline(length, width, ht, pad, layer=1):
    '''
    returns phidl Device of outline of microwire

    length: length of microwire [um]
    width: width of microwire [um]
    ht: phidl device representing taper to pads
    pad: phidl device representing pads
    '''
    microwire_shape = solid_microwire(length, width, ht, pad)
    return pg.outline(microwire_shape)

def hypertaper_outline(length, wide_w, narrow_w, wide_g, narrow_g, layer=1):
    taper = Device('taper')

    solid_taper = hyper_taper(length, wide_w+2*wide_g, narrow_w+2*narrow_g, layer)
    central_conductor = pg.taper(length, narrow_w, wide_w)
    bool_conductor = pg.boolean(A=solid_taper, B=central_conductor, operation='not')

    taper_ref = taper.add_ref(bool_conductor)
    taper.add_port(name='narrow', midpoint=(0, 0), width=narrow_w+2*narrow_g, orientation=180)
    taper.add_port(name='wide', midpoint=(length, 0), width=wide_w+2*wide_g)
    return taper

def microstrip_taper_c(coords, port1='narrow', port2='wide'):
    '''
    coords = Coords class with CPW/microstrip values to write to gds
    returns phidl Device matching Python coords

    Written by Marco Colangelo, modified by Emma Batson to
    work with Coords
    '''
    T = Device('taper')

    #plt.plot(x0, y0)
    x0 = np.reshape(coords.x0, (len(coords.x0), 1))
    y0 = np.reshape(coords.y0, (len(coords.x0), 1))

    #print(coords.x1)
    x1 = np.reshape(coords.x1, (len(coords.x0), 1))
    y1 = np.reshape(coords.y1, (len(coords.x0), 1))
    x2 = np.reshape(coords.x2, (len(coords.x0), 1))
    y2 = np.reshape(coords.y2, (len(coords.x0), 1))
    x3 = np.reshape(coords.x3, (len(coords.x0), 1))
    y3 = np.reshape(coords.y3, (len(coords.x0), 1))
    x4 = np.reshape(coords.x4, (len(coords.x0), 1))
    y4 = np.reshape(coords.y4, (len(coords.x0), 1))
    
    #cut the structure every 100 points
    N = 200
    for i in range(1, len(x1)//N+1):
        x2_1 = x2[(i-1)*N:i*N+1]
        y2_1 = y2[(i-1)*N:i*N+1]   
        x3_1 = x3[(i-1)*N:i*N+1]
        y3_1 = y3[(i-1)*N:i*N+1]
        xlist23 = np.vstack((x2_1, x3_1[::-1]))
        ylist23 = np.vstack((y2_1, y3_1[::-1]))
        xylist23 = np.column_stack((xlist23, ylist23))
        T.add_polygon(xylist23,layer = 1)
    x2_1 = x2[(len(x2)-1)//N*N:len(x2)+1]
    y2_1 = y2[(len(x2)-1)//N*N:len(x2)+1]
    x3_1 = x3[(len(x2)-1)//N*N:len(x2)+1]
    y3_1 = y3[(len(x2)-1)//N*N:len(x2)+1]
    xlist23 = np.vstack((x2_1, x3_1[::-1]))
    ylist23 = np.vstack((y2_1, y3_1[::-1]))
    xy23list = np.column_stack((xlist23, ylist23))
    T.add_polygon(xy23list, layer = 1)
    T.add_port(name = port1, midpoint = [float(x0[0]),float(y0[0])], width = float(abs(x2[0]-x3[0])), orientation = 90)
    T.add_port(name = port2, midpoint = [float(x0[-1]),float(y0[-1])], width = float(abs(x2_1[-1]-x3_1[-1])), orientation = -90)
    T.flatten(single_layer = 0)
    #T.write_gds('impedancematchedtaped.gds')
    return T

def CPW_to_phidl(coords, port1="narrow", port2="wide"):
    '''
    coords = Coords class with CPW values to write to gds
    returns phidl Device matching Python coords

    Written by Marco Colangelo, modified by Emma Batson to
    work with Coords
    '''
    T = Device('taper')

    #plt.plot(x0, y0)
    x0 = np.reshape(coords.x0, (len(coords.x0), 1))
    y0 = np.reshape(coords.y0, (len(coords.x0), 1))

    #print(coords.x1)
    x1 = np.reshape(coords.x1, (len(coords.x0), 1))
    y1 = np.reshape(coords.y1, (len(coords.x0), 1))
    x2 = np.reshape(coords.x2, (len(coords.x0), 1))
    y2 = np.reshape(coords.y2, (len(coords.x0), 1))
    x3 = np.reshape(coords.x3, (len(coords.x0), 1))
    y3 = np.reshape(coords.y3, (len(coords.x0), 1))
    x4 = np.reshape(coords.x4, (len(coords.x0), 1))
    y4 = np.reshape(coords.y4, (len(coords.x0), 1))

#cut the structure every 100 points
    N = 100
    for i in range(1, len(x1)//N+1):
        x1_1 = x1[(i-1)*N:i*N+1]
        y1_1 = y1[(i-1)*N:i*N+1]
        x2_1 = x2[(i-1)*N:i*N+1]
        y2_1 = y2[(i-1)*N:i*N+1]    
        xlist12 = np.vstack((x1_1, x2_1[::-1]))
        ylist12 = np.vstack((y1_1, y2_1[::-1]))
        xylist12 = np.column_stack((xlist12, ylist12))
        T.add_polygon(xylist12,layer = 1)
        x3_1 = x3[(i-1)*N:i*N+1]
        y3_1 = y3[(i-1)*N:i*N+1]
        x4_1 = x4[(i-1)*N:i*N+1]
        y4_1 = y4[(i-1)*N:i*N+1]    
        xlist34 = np.vstack((x3_1, x4_1[::-1]))
        ylist34 = np.vstack((y3_1, y4_1[::-1]))
        xylist34 = np.column_stack((xlist34, ylist34))
        T.add_polygon(xylist34,layer = 1)

    x1_1 = x1[(len(x1)-1)//N*N:len(x1)+1]
    y1_1 = y1[(len(x1)-1)//N*N:len(x1)+1]
    x2_1 = x2[(len(x1)-1)//N*N:len(x1)+1]
    y2_1 = y2[(len(x1)-1)//N*N:len(x1)+1]
    x3_1 = x3[(len(x1)-1)//N*N:len(x1)+1]
    y3_1 = y3[(len(x1)-1)//N*N:len(x1)+1]
    x4_1 = x4[(len(x1)-1)//N*N:len(x1)+1]
    y4_1 = y4[(len(x1)-1)//N*N:len(x1)+1]
    xlist12 = np.vstack((x1_1, x2_1[::-1]))
    ylist12 = np.vstack((y1_1, y2_1[::-1]))
    xy12list = np.column_stack((xlist12, ylist12))
    T.add_polygon(xy12list, layer = 1)
    xlist34 = np.vstack((x3_1, x4_1[::-1]))
    ylist34 = np.vstack((y3_1, y4_1[::-1])) 
    xylist34 = np.column_stack((xlist34, ylist34))
    T.add_polygon(xylist34, layer = 1)

    T.add_port(name = port1, midpoint = [float(x0[0]),float(y0[0])], width = float(abs(x1[0]-x2[0])), orientation = 90)
    T.add_port(name = port2, midpoint = [float(x0[-1]),float(y0[-1])], width = float(abs(x1[-1]-x2[-1])), orientation = 270)
    return T

def cpw_pad(width1=5, gap1=5, taper=True, length=1, width2 = 1, gap2 = 1,layer=1):
    '''
    Written by Marco Colangelo
    '''
    D=Device('Pad')
    R1=pg.rectangle(size=(width1,width1))
    R1.add_port(name = 1, midpoint = [R1.center[0],2*R1.center[1]], width = 2*R1.center[1], orientation = 90)
    R2=pg.outline(R1, distance = gap1, open_ports = 2*gap1+width1)
    r=D.add_ref(R2)
    if taper:
        T1=pg.taper(length, width1, width2)
        T1.rotate(90)
        T2=pg.taper(length, width1+2*gap1, width2+2*gap2)
        T2.rotate(90)
        TB=pg.boolean(T2, T1, 'A-B', 0.001)
        TB.add_port(name = 'wide', midpoint = T1.ports[1].midpoint, width = T1.ports[1].width, orientation = -90)
        TB.add_port(name = 'narrow', midpoint = T1.ports[2].midpoint, width = T1.ports[2].width, orientation = 90)
        t=D.add_ref(TB)
        r.move(r.ports[1],t.ports['wide'])
        D.flatten(single_layer = layer)
        D.add_port(name = 'out', midpoint = T1.ports[2].midpoint, width = T1.ports[2].width, orientation = 90)
    else:
        D.flatten(single_layer = layer)
        D.add_port(name = 'out', midpoint = [R1.center[0],2*R1.center[1]], width = 2*R1.center[1], orientation = 90)
    return D  