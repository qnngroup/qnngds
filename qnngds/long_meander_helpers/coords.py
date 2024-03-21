import numpy as np
from phidl import Device

'''
Coords class for keeping track of meanders and tapers, plus some 
functions to assist with basic drawing add-ons like circular turns

classes: Coords()
functions:
* vertical_line - adds a vertical line
* upper9to3 - draws half circle CW from 9:00 to 3:00
* lower9to3 - draws half circle CCW from 9:00 to 3:00
* upper3to9 - draws half circle CCW from 3:00 to 9:00
* lower3to9 - draws half circle CW from 3:00 to 9:00 
* quarter9to6 - draws quarter circle CCW from 9:00 to 6:00
* quarter12to3 - draws quarter circle CW from 12:00 to 3:00
* quarter3to6 - draws quarter circle CW from 3:00 to 6:00
* quarter12to9 - draws quarter circle CCW from 12:00 to 9:00
* quarter6to3 - draws quarter circle CCW from 6:00 to 3:00
* quarter9to12 - draws quarter circle CW from 9:00 to 12:00
'''

class Coords:
    '''class for storing and manipulating gds coordinate values
    for a CPW style meander

    modified from original Taper Coords class
    '''
    def __init__(self):
        ''' 
        w0 = initial width [um]
        gap = gap [um]
        initialize lists of coordinates as arrays with the same
        length as ls filled with zeros and create helper containers

        x0: center of trace
        x1: outermost (top) edge of taper
        x2: inner (top) edge of gap
        x3: inner (bottom) edge of gap
        x4: outermost (bottom) edge of taper
        '''
        # set up coordinate tracking indices
        self.x0 = []
        self.x1 = []
        self.x2 = []
        self.x3 = []
        self.x4 = []

        self.xlist = [self.x0, self.x1, self.x2, self.x3, self.x4]

        self.y0 = []
        self.y1 = []
        self.y2 = []
        self.y3 = []
        self.y4 = []

        self.ylist = [self.y0, self.y1, self.y2, self.y3, self.y4]

        self.all_coords = {'x': self.xlist, 'y': self.ylist}

    def get_current_index(self):
        return len(self.x0) - 1
    
    def initialize_vertical(self, w, gap):
        for y in self.ylist:
            y.append(0)

        self.x0.append(0)
        self.set_xs(0, w, gap)

    def initialize_horizontal(self, w, gap, offset=0):
        for x in self.xlist:
            x.append(offset)

        self.y0.append(0)
        self.set_ys(0, w, gap)

    def straight_xs(self, i, dl):
        ''' i: current index
        dl: change in absolute length between x[i-1], x[i] [um]

        populates all x-coords at i with x[i-1] + dl
        '''
        for xi in self.xlist:
            xi.append(self.x0[i-1] + dl)

    def straight_ys(self, i, dl):
        for yi in self.ylist:
            yi.append(self.y0[i-1] + dl)

    def set_xs(self, i, w, gap):
        self.x4.append(self.x0[i] + w/2 + gap)
        self.x3.append(self.x0[i] + w/2)
        self.x2.append(self.x0[i] - w/2)
        self.x1.append(self.x0[i] - (w/2 + gap))

    def set_ys(self, i, w, gap):
        '''i: current index
        w: width of wire [um]
        gap: width of gap [um]

        populates all y-coords at i with appropriate values
        relative to y0[i-1]
        '''
        self.y1.append(self.y0[i] + w/2 + gap) 
        self.y2.append(self.y0[i] + w/2)
        self.y3.append(self.y0[i] - w/2)
        self.y4.append(self.y0[i] - (w/2 + gap))

    def repeat_x0(self, i):
        self.x0.append(self.x0[i-1])

    def repeat_xs(self, i):
        for xi in self.xlist:
            xi.append(xi[i-1])
    
    def repeat_y0(self, i):
        '''i: current index

        populates y0[i] with same value as y0[i-1]
        '''
        self.y0.append(self.y0[i-1])

    def repeat_ys(self, i):
        for yi in self.ylist:
            yi.append(yi[i-1])

    def turn(self, axis, r0, w, gap, arc, origin, sgn=1):
        '''axis: x or y
        r0: radius of turn [um]
        w: width of wire [um]
        gap: width of gap [um]
        arc: trig(angle)
        origin: location of center of circle to draw

        populates all x or y at i with coordinates for turn
        '''
        coord_list = self.all_coords[axis]

        coord_list[0].append(origin + r0*arc)
        coord_list[1].append(origin + (r0 + sgn*(w/2 + gap))*arc) 
        coord_list[2].append(origin + (r0 + sgn*w/2)*arc) 
        coord_list[3].append(origin + (r0 - sgn*w/2)*arc) 
        coord_list[4].append(origin + (r0 - sgn*(w/2 + gap))*arc)

'''
Helper functions to keep track of important geometric components
for the meander, like straight vertical lines and various arclengths

Must particularly take care to maintain consistency between 
x1 <-> x4, x2 <-> x3 labels, therefore some sign conventions may not
transfer to shapes besides the meander
'''

def vertical_line(coords, i, dl, w=None, g=None):
    '''
    draws a vertical line

    coords: Coords object to add line to
    i: index at which to start drawing line
    dl: length of line
    '''
    coords.straight_ys(i, dl)
    coords.repeat_xs(i)

def upper9to3(coords, w, g, r, i, M=360):
    '''
    draws a half circle going clockwise from 9:00 to 3:00
    (upper half of circle)

    coords: Coords object to add half circle to
    w: width of center conductor [um]
    g: gap [um]
    r: radius of circle
    i: index at which to start drawing
    M: number of points to break circle into (resolution)
    '''
    theta = np.arange(0, np.pi+ np.pi/M, np.pi/M)

    xorigin = coords.x0[i-1] + r
    yorigin = coords.y0[i-1]

    for elt in theta[1:]:
        coords.turn('x', r, w, g, -np.cos(elt), xorigin)
        coords.turn('y', r, w, g, np.sin(elt), yorigin)
        i += 1
    return i

def lower9to3(coords, w, g, r, i, M=360):
    '''
    draws a half circle going counterclockwise from 9:00 to 3:00
    (lower half of circle)

    coords: Coords object to add half circle to
    w: width of center conductor [um]
    g: gap [um]
    r: radius of circle
    i: index at which to start drawing
    M: number of points to break circle into (resolution)
    '''
    theta = np.arange(0, np.pi+ np.pi/M, np.pi/M)

    xorigin = coords.x0[i-1] + r
    yorigin = coords.y0[i-1]

    for elt in theta[1:]:
        coords.turn('x', r, w, g, -np.cos(elt), xorigin, sgn=-1)
        coords.turn('y', r, w, g, -np.sin(elt), yorigin, sgn=-1)
        i += 1
    return i

def upper3to9(coords, w, g, r, i, M=360):
    '''
    draws a half circle going counterclockwise from 3:00 to 9:00
    (upper half of circle)

    coords: Coords object to add half circle to
    w: width of center conductor [um]
    g: gap [um]
    r: radius of circle
    i: index at which to start drawing
    M: number of points to break circle into (resolution)
    '''
    theta = np.arange(0, np.pi+ np.pi/M, np.pi/M)

    xorigin = coords.x0[i-1] - r
    yorigin = coords.y0[i-1]

    for elt in theta[1:]:
        coords.turn('x', r, w, g, np.cos(elt), xorigin, sgn=-1)
        coords.turn('y', r, w, g, np.sin(elt), yorigin, sgn=-1)
        i += 1
    return i

def lower3to9(coords, w, g, r, i, M=360):
    '''
    draws a half circle going clockwise from 3:00 to 9:00
    (lower half of circle)

    coords: Coords object to add half circle to
    w: width of center conductor [um]
    g: gap [um]
    r: radius of circle
    i: index at which to start drawing
    M: number of points to break circle into (resolution)
    '''
    theta = np.arange(0, np.pi+ np.pi/M, np.pi/M)

    xorigin = coords.x0[i-1] - r
    yorigin = coords.y0[i-1]

    for elt in theta[1:]:
        coords.turn('x', r, w, g, np.cos(elt), xorigin)
        coords.turn('y', r, w, g, -np.sin(elt), yorigin)
        i += 1
    return i

def quarter9to6(coords, w, g, r, i, M=360):
    '''
    draws a quarter circle going counterclockwise from 9:00 to 6:00

    coords: Coords object to add half circle to
    w: width of center conductor [um]
    g: gap [um]
    r: radius of circle
    i: index at which to start drawing
    M: number of points to break circle into (resolution)
    '''
    theta = np.arange(0, np.pi/2+ np.pi/M, np.pi/M)

    xorigin = coords.x0[i-1] + r
    yorigin = coords.y0[i-1]

    for elt in theta[1:]:
        coords.turn('x', r, w, g, -np.cos(elt), xorigin, sgn=-1)
        coords.turn('y', r, w, g, -np.sin(elt), yorigin, sgn=-1)
        i += 1
    return i

def quarter12to3(coords, w, g, r, i, M=360):
    '''
    draws a quarter circle going clockwise from 12:00 to 3:00

    coords: Coords object to add half circle to
    w: width of center conductor [um]
    g: gap [um]
    r: radius of circle
    i: index at which to start drawing
    M: number of points to break circle into (resolution)
    '''
    theta = np.arange(0, np.pi/2+ np.pi/M, np.pi/M)

    xorigin = coords.x0[i-1] 
    yorigin = coords.y0[i-1] - r

    for elt in theta[1:]:
        coords.turn('x', r, w, g, np.sin(elt), xorigin)
        coords.turn('y', r, w, g, np.cos(elt), yorigin)
        i += 1
    return i

def quarter3to6(coords, w, g, r, i, M=360):
    '''
    draws a quarter circle going clockwise from 3:00 to 6:00

    coords: Coords object to add half circle to
    w: width of center conductor [um]
    g: gap [um]
    r: radius of circle
    i: index at which to start drawing
    M: number of points to break circle into (resolution)
    '''
    theta = np.arange(0, np.pi/2+ np.pi/M, np.pi/M)

    xorigin = coords.x0[i-1] - r
    yorigin = coords.y0[i-1]

    for elt in theta[1:]:
        coords.turn('x', r, w, g, np.cos(elt), xorigin)
        coords.turn('y', r, w, g, -np.sin(elt), yorigin)
        i += 1
    return i

def quarter12to9(coords, w, g, r, i, M=360):
    '''
    coords: Coords object to add half circle to
    w: width of center conductor [um]
    g: gap [um]
    r: radius of circle
    i: index at which to start drawing
    M: number of points to break circle into (resolution)
    '''
    theta = np.arange(0, np.pi/2+ np.pi/M, np.pi/M)

    xorigin = coords.x0[i-1] 
    yorigin = coords.y0[i-1] - r

    for elt in theta[1:]:
        coords.turn('x', r, w, g, -np.sin(elt), xorigin, sgn=-1)
        coords.turn('y', r, w, g, np.cos(elt), yorigin, sgn=-1)
        i += 1
    return i

def quarter6to3(coords, w, g, r, i, M=360):
    '''
    coords: Coords object to add half circle to
    w: width of center conductor [um]
    g: gap [um]
    r: radius of circle
    i: index at which to start drawing
    M: number of points to break circle into (resolution)
    '''
    theta = np.arange(0, np.pi/2+ np.pi/M, np.pi/M)

    xorigin = coords.x0[i-1] 
    yorigin = coords.y0[i-1] + r

    for elt in theta[1:]:
        coords.turn('x', r, w, g, np.sin(elt), xorigin, sgn=-1)
        coords.turn('y', r, w, g, -np.cos(elt), yorigin, sgn=-1)
        i += 1
    return i

def quarter9to12(coords, w, g, r, i, M=360):
    '''
    coords: Coords object to add half circle to
    w: width of center conductor [um]
    g: gap [um]
    r: radius of circle
    i: index at which to start drawing
    M: number of points to break circle into (resolution)
    '''
    theta = np.arange(0, np.pi/2 + np.pi/M, np.pi/M)

    xorigin = coords.x0[i-1] + r 
    yorigin = coords.y0[i-1]

    for elt in theta[1:]:
        coords.turn('x', r, w, g, -np.cos(elt), xorigin, sgn=-1)
        coords.turn('y', r, w, g, np.sin(elt), yorigin, sgn=-1)
        i += 1
    return i