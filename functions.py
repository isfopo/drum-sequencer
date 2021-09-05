
"""
======== Functions ========
"""
def reset_colors(nts, np, on, off=(0, 0, 0), row_offs=0, col_offs=0):
    for col in nts.grid[col_offs:col_offs+8]:
        for nt in col[row_offs:row_offs+4]:
            np[nt.index] = on if nt.is_on else off

def light_buttons(bts, clr, np): 
    for bt in bts:
        np[press_to_light(bt)] = clr

def light_column(col, col_clr, np):
    for i in range(4): np[ col + (i*8) ] = col_clr
    
def reset_column(nts, offs, col, on, off, acct, np):
    for nt in nts.grid[col][offs:offs+4]:
        np[nt.index] = acct if nt.is_accented else on if nt.is_on else off

def play_column(nts, col, note_on, note_off):
    col = tuple(nts.grid[col])
    r = range(len(col))
    for i in r: col[i].play(note_on, note_off)
        
def stop_column(nts, col, note_off):
    col = tuple(nts.grid[col])
    r = range(len(col))
    for i in r: col[i].stop(note_off)

def move_column(i, grd, lst_stp, col_clr, on, acct, np, off=(0, 0, 0), row_offs=0, col_offs=0):
    if i % 8 == 0:
        if col_offs == lst_stp+1 - 8:
            if i == 0:
                light_column(7, col_clr, np)
                reset_column(grd, row_offs, 6, on, off, acct, np) #BUG last column hangs up in shift mode
            
        else:
            if col_offs < i <= col_offs + 8:
                light_column(7, col_clr, np)
                reset_column(grd, row_offs, col_offs + 6, on, off, acct, np)
    else:
        if i % 8 == 1:
            reset_column(grd, row_offs, col_offs + 7, on, off, acct, np)
            
        if col_offs <= i < col_offs + 8:
            light_column((i-1)%8, col_clr, np)
            reset_column(grd, row_offs, (i-2), on, off, acct, np)
            
    if i == 1:
        reset_column(grd, row_offs, col_offs + 7, on, off, acct, np)
        reset_column(grd, row_offs, (lst_stp-1)%8, on, off, acct, np)

def stop_notes(notes, note_off):
    map(lambda x: map(lambda y: y.stop(note_off), x), notes.grid)

def clear_grid(notes):
    for column in notes.grid:
        for note in column: note.is_on = False
            
def scale(val, src, dst):
    output = ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]
    if output < dst[0]: return int(dst[0])
    if output > dst[1]: return int(dst[1])
    return int(output)

def correct_index(index, i, ci):
    return ci[index+((i%8)*4)]

def press_to_light(btn):
    return  ( ( 24, 25, 26, 27, 28, 29, 30, 31 ),
              ( 16, 17, 18, 19, 20, 21, 22, 23 ),
              (  8,  9, 10, 11, 12, 13, 14, 15 ),
              (  0,  1,  2,  3,  4,  5,  6,  7 ) )[btn[0]][btn[1]]

def handle_axis(mode, axis, up_cc, down_cc, s, cc):
    if   mode == b'd': s(cc(up_cc, scale(axis, (-10, 10), (0, 127))))
    elif mode == b'f': s(cc(up_cc, scale(axis, (10, -10), (0, 127))))
    elif mode == b's':
        if axis > 0: s(cc(  up_cc, scale(axis, (0, 10), (0, 127))))
        else:        s(cc(down_cc, scale(axis, (0, -10), (0, 127))))
    elif mode == b'o':
        if axis > 0: s(cc(up_cc, 127))
        else:        s(cc(up_cc, 0))
    elif mode == b'fo':
        if axis > 0: s(cc(up_cc, 0))
        else:        s(cc(up_cc, 127))
    elif mode == b'so':
        if axis > 0:
            if axis > 5: s(cc(up_cc, 127))
            else:        s(cc(up_cc, 0))
        else:    
            if axis < -5: s(cc(down_cc, 127))
            else:         s(cc(down_cc, 0))

def handle_axes(modes, accel, ccs, cc, midi):    
    handle_axis(modes[0], accel[1], ccs[0], ccs[1], midi.send, cc)
    handle_axis(modes[1], accel[0], ccs[2], ccs[3], midi.send, cc)
    handle_axis(modes[2], accel[2], ccs[4], ccs[5], midi.send, cc)

def handle_cc_grid(cc_edit, modes, offset):
    for mode in modes:
        if mode == b'd':  cc_edit.grid[1][offset].is_on = True
        if mode == b'f':  cc_edit.grid[2][offset].is_on = True
        if mode == b's':  cc_edit.grid[3][offset].is_on = True
        if mode == b'o':  cc_edit.grid[4][offset].is_on = True
        if mode == b'fo': cc_edit.grid[5][offset].is_on = True
        if mode == b'so': cc_edit.grid[6][offset].is_on = True
        if mode == None: cc_edit.grid[7][offset].is_on = True
        offset -= 1

def handle_select_mode(pb):
    if   pb == 1: return b'd'
    elif pb == 2: return b'f'
    elif pb == 3: return b's'
    elif pb == 4: return b'o'
    elif pb == 5: return b'fo'
    elif pb == 6: return b'so'
    else: return None

def handle_cc_lights(pressed_buttons, cc_edit, row):
    cc_edit.grid[pressed_buttons[0][1]][row].is_on = True

def increase_row_offset(row_offset, rows):
    new_offset = row_offset + 4
    return new_offset if new_offset < rows else row_offset
    
def decrease_row_offset(row_offset):
    new_offset = row_offset - 4
    return new_offset if new_offset >= 0 else row_offset
 
def increase_column_offset(column_offset, cols):
    new_offset = column_offset + 8
    return new_offset if new_offset < cols else column_offset
    
def decrease_column_offset(column_offset):
    new_offset = column_offset - 8
    return new_offset if new_offset >= 0 else column_offset
   
def row_off(grid, row):   
    for column in grid.grid:
        column[row].is_on = False

def shift_grid_left(grid):
    for i in range(last_step + 1):
        if i == last_step:
            for j in range(len(grid.grid[0])):
                grid.grid[i][j].is_on = grid.grid[0][j].is_on
        else:
            for j in range(len(grid.grid[0])):
                grid.grid[i][j].is_on = grid.grid[i+1][j].is_on
    return grid

def shift_grid_right(grid):
    for i in reversed(range(last_step + 1)):
        if i == 0:
            for j in range(len(grid.grid[0])):
                grid.grid[i][j].is_on = grid.grid[last_step][j].is_on
        else:
            for j in range(len(grid.grid[0])):
                grid.grid[i][j].is_on = grid.grid[i-1][j].is_on
    return grid

def write_save(notes, shift, last_step, axis_modes):
    try:
        with open('{}.json'.format(current_slot), "w") as file:
            file.write(dumps({
                "notes": list(map(lambda x: list(map(lambda y: (y.is_on, y.is_accented), x)), notes.grid)),
                "shift": list(map(lambda x: list(map(lambda y: (y.is_on, y.is_accented), x)), shift.grid)),
                "last_step": last_step,
                "axis_modes": axis_modes
            }))
    except MemoryError as e:
        print(e)

def read_save(curr_slt, nts, shft):
    try:
        with open("/{}.json".format(curr_slt)) as save:
            pattern = loads(save.read())
            if pattern["notes"]:
                for column in range(len(pattern["notes"])):
                    for note in range(len(pattern["notes"][0])):
                        nts.grid[column][note].is_on = pattern["notes"][column][note][0]
                        nts.grid[column][note].is_accented = pattern["notes"][column][note][1]
                        shft.grid[column][note].is_on = pattern["shift"][column][note][0]
                        shft.grid[column][note].is_accented = pattern["shift"][column][note][1]
            
            lst_stp = pattern["last_step"] if pattern["last_step"] else 8
            ax_mds = pattern["axis_modes"] if pattern["axis_modes"] else [ None, None, None ]
        return [ nts, shft, lst_stp, ax_mds ]
    except:
        return [ nts, shft, 8, [ None, None, None ] ]
        
def get_slots():
    return list(map(lambda f: int(f.replace('.json', '')), [f for f in listdir() if f.endswith('.json')]))

def light_slots(sts, clr, np):
    for st in sts: np[st] = clr
    
def handle_last_step_edit(lst_stp, pb, bts, cols):
    if pb == bts[0]: # Decrease by measure
        remainder = lst_stp % 8
        if remainder == 0: return lst_stp - 8 if lst_stp - 8 != 0 else 1
        else: return lst_stp - remainder if lst_stp - remainder != 0 else 1
        
    elif pb == bts[1]: # Decrease by 1 Eighth note
        return lst_stp - 1 if lst_stp > 1 else lst_stp
    
    elif pb == bts[2]: # Increase by 1 Eighth note
        return lst_stp + 1 if lst_stp < cols - 1 else lst_stp
    
    elif pb == bts[3]: # Increase by measure
        remainder = lst_stp % 8
        if remainder == 0: return lst_stp + 8 if lst_stp + 8 < cols else lst_stp
        else: return lst_stp + (8-remainder)

def duplicate_measure(grids):
    for grid in grids:
        for i, column in enumerate(grid):
            if i >= 8:
                for j, note in enumerate(column):
                    note.is_on = grid[i-8][j].is_on
                    note.is_accented = grid[i-8][j].is_accented
    return grids

def fill_yes_no(conf_clr, dcln_clr, np):
    r = range(32)
    for i in r:
        np[i] = conf_clr if i < 16 else dcln_clr

def delete_all_slots():
    r = range(32)
    for i in r:
        try: remove("/{}.json".format(i))
        except OSError: pass

def print_grid(grid):
    print(list(map(lambda x: list(map(lambda y: y.index, x)), grid.grid)))
    
