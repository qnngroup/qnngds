from qnngds.qnngds.long_meander_helpers.coords import *

'''
Functions that use the Coords class to generate meanders/tapers

* generate_taper - generates a Coords taper based on input x values & associated widths
* generate_slope - based on an existing Coords meander, adds an exponential constant-Z taper
                   with simultaneously increasing gap and width
* generate_meander - generates a meander appropriate for an SNSPI
'''

def generate_taper(ls, w_design, w_l, n_w, gap, dlmd0_um, brf=3, lmax=2500, M=360, offset=0):
    ''' 
    based on Di Zhu and Marco Colangelo's generate_optimal_taper.m code
        ls: array indicating physical distance [um] between normalized x coords
        w_design: w value [um] corresponding to each l value
        w_l: interpolation function giving w(l) [um -> um]
        n_w: interpolation function givin n(w) [um -> unitless]
        gap: width of gap [um]
        dlmd0_um: length per section [um]
        brf: bending radius factor
        lmax: maximum length of each turn [um]
        M: # pts while turning

        returns taper coordinates
        x0: center of trace
        x1: outermost (top) edge of taper
        x2: inner (top) edge of gap
        x3: inner (bottom) edge of gap
        x4: outermost (bottom) edge of taper
    '''
    coords = Coords()
    coords.initialize_horizontal(w_design[0], gap, offset)

    print('start generating gds coords')

    # tracking variables
    row = 1
    flag_finish_before_turn = 0
    i = 1
    ltrack = 0

    # go to the second-to-last l value
    while ltrack < max(ls):
        w = w_l(ltrack)

        '''compute r0, radius of curvature to width [um]
        '''
        if w + 2*gap < 25:
            r0 = brf*(w + 2*gap)
        # reduce curvature radius for wide wires
        else:
            if row % 2 == 1:
                factor = 3
            else:
                factor = 1.5
            r0 = factor*(w + 2*gap)
            if r0 < brf*25:
                r0 = brf*25 
        
        if row % 2 == 1:
            ''' if on an odd row, go right or turn clockwise
            choose direction to move
            '''
            if coords.x0[i-1] + r0 < lmax/2:
                # straight, to the right
                dl = dlmd0_um/n_w(w)
                coords.straight_xs(i, dl)
                coords.repeat_y0(i)
                coords.set_ys(i, w, gap)

                i+= 1
                ltrack += dl
            
            else:
                # start to turn, clockwise)
                theta = np.arange(0, np.pi, np.pi/M)

                xorigin = coords.x0[i-1]
                yorigin = coords.y0[i-1] - r0

                for elt in theta[1:]:
                    if ltrack >= max(ls):
                        w = w_design[-2]
                    else:
                        w = w_l(ltrack)

                    coords.turn('x', r0, w, gap, np.sin(elt), xorigin)
                    coords.turn('y', r0, w, gap, np.cos(elt), yorigin)

                    i+= 1
                    ltrack += r0*np.pi/M 

                    if ltrack > max(ls):
                        # keep turning until finished, even if length exceeded, but warn
                        flag_finish_before_turn = 1

                if flag_finish_before_turn:
                    print('finished while turning')
                # increase row index since we have turned onto the next one    
                row += 1
        elif row % 2 == 0:
            if coords.x0[i-1] - r0 > -lmax/2:
                # straight, to the left
                dl = dlmd0_um/n_w(w)
                coords.straight_xs(i, -dl)
                coords.repeat_y0(i)
                coords.set_ys(i, -w, -gap)

                i += 1
                ltrack += dl 

            else:
                # start to turn, counter-clockwise
                theta = np.arange(0, np.pi, np.pi/M)

                xorigin = coords.x0[i-1]
                yorigin = coords.y0[i-1] - r0

                for elt in theta:
                    if ltrack >= max(ls):
                        w = w_design[-2]
                    else:
                        w = w_l(ltrack)
                    
                    coords.turn('x', r0, -w, -gap, -np.sin(elt), xorigin)
                    coords.turn('y', r0, -w, -gap, np.cos(elt), yorigin)

                    i += 1
                    ltrack += r0*np.pi/M

                    if ltrack > max(ls):
                        # keep turning until finished, even if length exceeded, but warn
                        flag_finish_before_turn = 1
                if flag_finish_before_turn:
                    print('finished while turning')
                # increase row index since we have turned onto the next one    
                row += 1
    return coords, row

def generate_slope(coords, g_fxn, slope=0.1, Z=50, step=1, target_w=200, sgn = 1, analytical=False):
    '''
    coords: Coords class containing coordinates to add to
    g_fxn: function giving gap(w, Z) [um]
    slope: desired slope for w/y [um/um]
    Z: Z value to remain constant at [Ohms]
    step: step size for y [um]
    target_w: final width [um]
    '''
    w_init = coords.x2[-1] - coords.x3[-1]
    y_init = coords.y0[-1]
    x_origin = coords.x0[-1]
    
    w = w_init
    y = y_init

    while w < target_w:
        # step forward in y coord
        y -= step
        for yi in coords.ylist:
            yi.append(y)
        
        # linear increase to w
        w += slope*np.abs(y - y_init)
        # increase g to maintain constant Z
        if not analytical:
            g = g_fxn(np.stack([[w], [Z]], -1))[0]
        else:
            g = g_fxn(w)

        # add next step of x coords
        coords.x0.append(x_origin)
        coords.x1.append(x_origin + sgn*(0.5*w + g))
        coords.x2.append(x_origin + sgn*0.5*w)
        coords.x3.append(x_origin - sgn*0.5*w)
        coords.x4.append(x_origin - sgn*(0.5*w + g))
    return coords

def generate_meander(coords, w, g, array_length, array_height, min_conductor, line_height, dl):
    '''
    coords = Coords class for building meander in
    w = width of central conductor of CPW [um]
    g = gap width of CPW [um]
    array_length = total length of SNSPI array [um]
    array_height = total height of SNSPI array [um]
    min_conductor = minimum width of conductor allowed between CPWs [um]
    line_height = height of a single line of the SNSPI array [um]
    dl = step size for geometry shape [um]

    generates the meander
    '''

    # geometry tracking variables
    row_index = 0
    current_length = 0
    current_line_height = 0
    total_height = 0
    i = 1

    radius = min_conductor/2 + 2*g

    # TODO temporary bugfix
    array_length = array_length/2

    #i = quarter9to12(coords, w, g, radius, i)
    #i = quarter6to3(coords, w, g, radius, i)
    i = quarter12to3(coords, w, g, radius, i)
    while current_line_height < line_height:
        # draw line straight down
        vertical_line(coords, i, -dl, w, g)
        current_line_height += dl
        i += 1
    i = lower9to3(coords, w, g, radius, i)
    current_line_height = 0


    # draw new rows until array height is met
    while total_height < array_height:
        # if row index even, traveling left to right
        if row_index % 2 == 0:
            # draw new columns until array length is met
            new_row = True
            while current_length + radius < array_length:
                # check if we need to draw a connecting turn
                if not new_row:
                    i = lower9to3(coords, w, g, radius, i)
                else:
                    new_row = False
                # draw 1st column line
                while current_line_height < line_height:
                    # draw line straight up
                    vertical_line(coords, i, dl, w, g)
                    current_line_height += dl
                    i += 1
                # turn over clockwise
                i = upper9to3(coords, w, g, radius, i)

                # reset line height
                current_line_height = 0

                # draw 2nd column line
                while current_line_height < line_height:
                    # draw line straight up
                    vertical_line(coords, i, -dl, w, g)
                    current_line_height += dl
                    i += 1

                # reset line height
                current_line_height = 0
                current_length += 2*radius

            # draw turns to connect to next row
            i = quarter9to6(coords, w, g, radius, i)
            
            total_height += line_height + 2*radius + min_conductor
            row_index += 1

        # if row index odd, traveling right to left
        else:
            # draw new columns until array length is met
            new_row = True

            i = quarter12to3(coords, w, g, radius, i)
            # add conductor width line
            while current_line_height < min_conductor:
                vertical_line(coords, i, -dl, w, g)
                current_line_height += dl
                i += 1
            current_line_height = 0
            current_length = 0

            # add one 'partial' turn unit
            while current_line_height < line_height:
                vertical_line(coords, i, -dl, w, g)
                current_line_height += dl 
                i += 1
            current_line_height = 0

            while current_length + radius < array_length:
                # draw a connecting turn
                i = lower3to9(coords, w, g, radius, i)
                # draw 1st column line
                while current_line_height < line_height:
                    # draw line straight up
                    vertical_line(coords, i, dl, w, g)
                    current_line_height += dl
                    i += 1
                # turn over clockwise
                i = upper3to9(coords, w, g, radius, i)

                # reset line height
                current_line_height = 0

                # draw 2nd column line
                while current_line_height < line_height:
                    # draw line straight up
                    vertical_line(coords, i, -dl, w, g)
                    current_line_height += dl
                    i += 1

                # reset line height
                current_line_height = 0
                current_length += 2*radius

            # draw turns to connect to next row
            i = quarter3to6(coords, w, g, radius, i)
            i = quarter12to9(coords, w, g, radius, i)
            while current_line_height < min_conductor + line_height:
                vertical_line(coords, i, -dl, w, g)
                current_line_height += dl
                i += 1

            i = lower9to3(coords, w, g, radius, i)

            current_line_height = 0
            current_length = 0

            total_height += line_height + 2*radius + min_conductor
            row_index += 1
    if row_index % 2 == 0:
        i = quarter9to12(coords, w, g, radius, i)

    return coords