from math import floor
from board import ACCELEROMETER_SCL
from board import ACCELEROMETER_SDA
from busio import I2C
from json import loads
from json import dumps
from gc import collect
from os import listdir
from os import remove
from micropython import const

from usb_midi import ports
from adafruit_trellism4 import TrellisM4Express
from adafruit_adxl34x import ADXL345

from adafruit_midi import MIDI
from adafruit_midi.timing_clock import TimingClock
from adafruit_midi.start import Start
from adafruit_midi.stop import Stop
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.control_change import ControlChange

midi = MIDI(midi_in=ports[0], midi_out=ports[1], in_channel=0, out_channel=0)
receive = midi.receive
trellis = TrellisM4Express(rotation=90)
i2c = I2C(ACCELEROMETER_SCL, ACCELEROMETER_SDA)
accelerometer = ADXL345(i2c)

"""
======== Classes ========
"""

class Grid:
    __slots__ = ["grid"]
    def __init__(self, columns, rows, correction):
            index = 0
            grid = []
            for i in range(columns):
                column = []
                for j in range(rows):
                    if j % 4 == 0: index = 0
                    column.append(Cell(correct_index(index, i, CORRECT_INDEX)))
                    index += 1
                grid.append(tuple(column))
            self.grid = tuple(grid)

class NoteGrid:
    __slots__ = ["grid"]
    def __init__(self, columns, rows, starting_note, send):
            index = 0
            grid = []
            for i in range(columns):
                column = []
                note = starting_note
                for j in range(rows):
                    if j % 4 == 0: index = 0
                    column.append(Note(note, correct_index(index, i, CORRECT_INDEX), send))
                    index += 1
                    note += 1
                grid.append(tuple(column))
            self.grid = tuple(grid)

class Cell:
    __slots__ = ["index", "is_on"]
    def __init__(self, index):
        self.index = index
        self.is_on = False
        
    def toggle(self):
        self.is_on = True if not self.is_on else False
        
    def on(self):
        self.is_on = True
        
    def off(self):
        self.is_on = False

class Note(Cell):
    __slots__ = ["notes", "index", "is_on", "is_accented", "send"]
    def __init__(self, note, index, send):
        self.note = note
        self.index = index
        self.is_on = False
        self.is_accented = False
        self.send = send
        
    def play(self):
        self.stop()
        if self.is_on:
            self.send(NoteOn(self.note, 127 if self.is_accented else 96))
        
    def stop(self):
        if self.is_on:
            self.send(NoteOff(self.note, 0))
        
    def toggle_accent(self):
        self.is_accented = True if not self.is_accented else False

"""
======== Fuctions ======== #TODO can these functions be imported from a .mpy file?
"""
def reset_colors(nts, on, off=(0, 0, 0), row_offs=0, col_offs=0):
    np = trellis.pixels._neopixel
    for col in nts.grid[col_offs:col_offs+8]:
        for nt in col[row_offs:row_offs+4]:
            np[nt.index] = on if nt.is_on else off

def light_column(col, col_clr):
    np = trellis.pixels._neopixel
    for i in range(4): np[ col + (i*8) ] = col_clr
    
def reset_column(nts, offs, col, on, off, acct):
    np = trellis.pixels._neopixel
    for nt in nts.grid[col][offs:offs+4]:
        np[nt.index] = acct if nt.is_accented else on if nt.is_on else off

def play_column(nts, col):
    col = tuple(nts.grid[col])
    r = range(len(col))
    for i in r: col[i].play()
        
def stop_column(nts, col):
    col = tuple(nts.grid[col])
    r = range(len(col))
    for i in r: col[i].stop()

def move_column(ind, grd, lst_stp, col_clr, on, acct, off=(0, 0, 0), row_offs=0, col_offs=0):
    if ind % 8 == 0:
        if column_offset == lst_stp+1 - 8:
            if ind == 0:
                light_column(7, col_clr)
                reset_column(grd, row_offs, 6, on, off, acct) #BUG last column hangs up in shift mode
            
        else:
            if col_offs < ind <= col_offs + 8:
                light_column(7, col_clr)
                reset_column(grd, row_offs, col_offs + 6, on, off, acct)
    else:
        if ind % 8 == 1:
            reset_column(grd, row_offs, col_offs + 7, on, off, acct)
            
        if col_offs <= ind < col_offs + 8:
            light_column((ind-1)%8, col_clr)
            reset_column(grd, row_offs, (ind-2), on, off, acct)
            
    if ind == 1:
        reset_column(grd, row_offs, col_offs + 7, on, off, acct)
        reset_column(grd, row_offs, (lst_stp-1)%8, on, off, acct)

def stop_notes(notes):
    map(lambda x: map(lambda y: y.stop(), x), notes.grid)

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

def press_to_light(button, p2l):
    return p2l[button[0]][button[1]]

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

def handle_axes(modes, accel, ccs, cc):    
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
        if mode == None:  cc_edit.grid[7][offset].is_on = True
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
        if remainder == 0: return lst_stp + 8 if lst_stp + 8 < cols else lst_stp #TODO have a way to duplicate measures when changing last step
        else: return lst_stp + (8-remainder)

def fill_yes_no(conf_clr, dcln_clr, np):
    r = range(32)
    for i in r:
        np[i] = conf_clr if i < 16 else dcln_clr

def delete_all_slots():
    r = range(32)
    for i in r:
        try: remove("/{}.json".format(i))
        except OSError: pass

    
"""
======== Constants ========
"""

"""
Colors
"""
NOTE_ON                = (   0,  63,  63 )
NOTE_OFF               = (   0,   0,   0 )
COLUMN_COLOR           = ( 255,   0,  50 )
ACCENT                 = (  63, 191, 225 )
SHIFT_NOTE_ON          = (  63,  63,   0 )
SHIFT_COLUMN_COLOR     = (  50,   0, 255 )
SHIFT_ACCENT           = ( 255, 191,  63 )
EDIT_CC_COLOR          = ( 191, 191, 255 )
MANUAL_NOTE_COLOR      = (   0, 255,   0 )
MANUAL_NOTE_COLOR_ALT  = (   0, 191, 191 )
RECORD_NOTE_COLOR      = ( 255,   0,   0 )
MANUAL_CC_COLOR        = (   0, 255,  63 )
CURRENT_SLOT_COLOR     = (  11, 255,  11 )
SAVE_SLOT_COLOR		   = ( 191, 191,  11 )
DELETE_SLOT_COLOR      = ( 191,  11,  11 )
CONFIRM_COLOR		   = (   0, 255,   0 )
DECLINE_COLOR		   = ( 255,   0,   0 )

"""
Grid Parameters
"""
STARTING_NOTE     = const(36)
NUMBER_OF_COLUMNS = const(17)
NUMBER_OF_ROWS    = const(8)

"""
Button Combonations
"""
MANUAL_CC_COMBO                  = [(3, 4), (0, 4)]
MANUAL_NOTE_COMBO                = [(3, 4), (0, 5)]
RECORD_NOTE_COMBO                = [(3, 5), (0, 5)]
BACK_COMBO                       = [(3, 0), (0, 0), (3, 7)]
CLEAR_COMBO                      = [(3, 0), (0, 0), (3, 1)]
SHIFT_MODE_COMBO                 = [(3, 0), (0, 0), (3, 2)]
EDIT_CC_COMBO                    = [(3, 0), (0, 0), (3, 3)]
EDIT_CC_BACK                     = [(3, 0), (3, 1), (3, 7)]
TOGGLE_X_COMBO                   = [(2, 0), (0, 0), (2, 1)]
TOGGLE_Y_COMBO                   = [(2, 0), (0, 0), (2, 2)]
TOGGLE_Z_COMBO                   = [(2, 0), (0, 0), (2, 3)]
OFFSET_CHANGE_MODE_COMBO		 = [(3, 6), (0, 6)]
INCREASE_ROW_OFFSET       	     = (3, 4) #TODO these can be combined into one tuple
DECREASE_ROW_OFFSET         	 = (1, 4)
INCREASE_COLUMN_OFFSET	     	 = (2, 5)
DECREASE_COLUMN_OFFSET      	 = (2, 3)
PATTERN_SHIFT_MODE_COMBO	     = [(3, 7), (0, 7)]
SHIFT_UP			    		 = (3, 5) #TODO these can be combined into one tuple
SHIFT_DOWN                       = (1, 5)
SHIFT_LEFT	     			     = (2, 4)
SHIFT_RIGHT				   	     = (2, 6)
CHANGE_MANUAL_NOTE_CHANNEL_COMBO = [(3, 1), (2, 1), (0, 1)]
LAST_STEP_EDIT_COMBO             = [(2, 7), (0, 7)]
LAST_STEP_BUTTONS                = ( (1, 3), (1, 4), (1, 5), (1, 6) )
SELECT_SLOT_MODE			     = [(3, 0), (0, 0), (3, 4)]
DELETE_SLOT_MODE                 = [(3, 0), (0, 0), (2, 4)]
DELETE_ALL_SLOTS_MODE            = [(3, 0), (0, 0), (1, 4)]

"""
Integers
"""
HOLD_TIME = const(24) #in ticks

"""
Axis cc's
"""
axis_ccs = (3, 9, 14, 15, 20, 21)

"""
Lists
"""
CORRECT_INDEX  =  ( 24, 16,  8, 0,
                    25, 17,  9, 1,
                    26, 18, 10, 2,
                    27, 19, 11, 3,
                    28, 20, 12, 4,
                    29, 21, 13, 5,
                    30, 22, 14, 6,
                    31, 23, 15, 7 )

PRESS_TO_LIGHT    = ( ( 24, 25, 26, 27, 28, 29, 30, 31 ),
                      ( 16, 17, 18, 19, 20, 21, 22, 23 ),
                      (  8,  9, 10, 11, 12, 13, 14, 15 ),
                      (  0,  1,  2,  3,  4,  5,  6,  7 ) )

MANUAL_NOTES      = ( ( 48, 44, 40, 36 ),
                      ( 49, 45, 41, 37 ),
                      ( 50, 46, 42, 38 ),
                      ( 51, 47, 43, 39 ) )

MANUAL_CC         = ( ( 22, 23, 24, 25 ),
                      ( 26, 27, 28, 29 ),
                      ( 30, 31, 85, 86 ),
                      ( 87, 88, 89, 90 ) )

"""
======== Global Variables ========
"""
current_slot = 0
[ notes, shift, last_step, axis_modes ] = read_save(current_slot, NoteGrid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE, midi.send), NoteGrid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE, midi.send))
#TODO can notes and shift be combined into a single tuple?
cc_edit = Grid(8, 4, CORRECT_INDEX)
pattern_select = Grid(8, 4, CORRECT_INDEX)

#print(list(map(lambda x: list(map(lambda y: y.index, x)), notes.grid))) # prints note grid to show notes

ticks = 0
eighth_note = 0

old_message = None
last_press = None
held_note = None
last_tick = None
tick_placeholder = None

button_is_held = False
combo_pressed = False
manual_is_pressed = False
seperate_manual_note_channel = False

row_offset = 0
column_offset = 0

mode = b'm'

manual_notes = []
prev_manual_notes = []
manual_cc = []
prev_manual_cc = []
toggled_cc = []

while True:
    
    """
    ======== Play Sequence ========
    """
    
    """
    Receive MIDI
    """
    new_message = receive()
    if new_message != old_message and new_message != None:

        """
        Sync To TimingClock
        """
        if isinstance(new_message, TimingClock):
            """
            Main Grid
            """
            if ticks % 12 == 0:
                for i in range(NUMBER_OF_COLUMNS):
                    if eighth_note % last_step + 1 == i:
                        if mode == b'm':
                            move_column(i, notes, last_step, COLUMN_COLOR, NOTE_ON, ACCENT, NOTE_OFF, row_offset, column_offset)
                        play_column(notes, i-1)
                        stop_column(notes, i-2)
                eighth_note += 1           
            """
            Shift Grid
            """
            if ticks % 12 == 6:
                for i in range(NUMBER_OF_COLUMNS):
                    if eighth_note % last_step == i:
                        if mode == b's':
                            move_column(shift, last_step, SHIFT_COLUMN_COLOR, SHIFT_NOTE_ON, SHIFT_ACCENT, NOTE_OFF, row_offset, column_offset)
                        play_column(shift, i-1)
                        stop_column(shift, i-2)
            ticks += 1
            
        """
        Start and Stop
        """
        if isinstance(new_message, Start):
            ticks = 0
            eighth_note = 0
            
        if isinstance(new_message, Stop):
            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
            stop_notes(notes)

            
    old_message = new_message
    
    """
    ======== Read Buttons ========
    """
    
    pressed_buttons = trellis.pressed_keys
    
    if pressed_buttons != last_press:
        """
        Main Mode
        """
        if mode == b'm':
            if pressed_buttons and not combo_pressed:
                for note in notes.grid[pressed_buttons[0][1] + column_offset]:
                    if note.note == pressed_buttons[0][0] + STARTING_NOTE + row_offset:
                        tick_placeholder = ticks
                        held_note = note
                        button_is_held = True
                        
            elif button_is_held:
                if ticks - tick_placeholder < HOLD_TIME:
                    trellis.pixels._neopixel[held_note.index] = NOTE_ON if not held_note.is_on else NOTE_OFF
                    held_note.toggle() #TODO somehting is slow here - there is a slight delay when a new note is added
                    if held_note.is_accented:
                        held_note.toggle_accent()
                    button_is_held = False
                else:
                    if not held_note.is_on:
                        trellis.pixels._neopixel[held_note.index] = ACCENT if not held_note.is_accented else NOTE_OFF
                        held_note.toggle()
                    held_note.toggle_accent()
            if not pressed_buttons:
                combo_pressed = False
            
            """
            Main Combos
            """
            if len(pressed_buttons) > 1:
                combo_pressed = True
                if pressed_buttons == CLEAR_COMBO:
                    clear_grid(notes)
                    clear_grid(shift)
                    reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons == SHIFT_MODE_COMBO:
                    mode = b's'
                    reset_colors(shift, SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                
                elif pressed_buttons == EDIT_CC_COMBO:
                    mode = b'c'
                    reset_colors(cc_edit, EDIT_CC_COLOR, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons == SELECT_SLOT_MODE:
                    mode = b'p'
                    trellis.pixels.fill(NOTE_OFF)
                    
                elif pressed_buttons == DELETE_SLOT_MODE:
                    mode = b'd'
                    trellis.pixels.fill(NOTE_OFF)
                    
                elif pressed_buttons == DELETE_ALL_SLOTS_MODE:
                    mode = b'da'
                    trellis.pixels.fill(NOTE_OFF)
                
                elif pressed_buttons[-2:] == OFFSET_CHANGE_MODE_COMBO: #FEAT light up availible buttons
                    if len(pressed_buttons) > 2:
                        if pressed_buttons[0] == INCREASE_ROW_OFFSET:
                            row_offset = increase_row_offset(row_offset, NUMBER_OF_ROWS)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == DECREASE_ROW_OFFSET:
                            row_offset = decrease_row_offset(row_offset)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == INCREASE_COLUMN_OFFSET:
                            column_offset = increase_column_offset(column_offset, NUMBER_OF_COLUMNS)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == DECREASE_COLUMN_OFFSET:
                            column_offset = decrease_column_offset(column_offset)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons[-2:] == MANUAL_CC_COMBO:
                    for cc in toggled_cc:
                        trellis.pixels._neopixel[press_to_light(cc[1], PRESS_TO_LIGHT)] = MANUAL_CC_COLOR
                    if len(pressed_buttons) > 2:
                        manual_cc = []
                        for button in pressed_buttons:
                            if button == (3, 4) or button == (0, 4):#TODO use variables
                                pass
                            else:
                                manual_cc.append((MANUAL_CC[button[0]][button[1]], button))
                    else:
                        manual_cc = []
                    for cc in manual_cc:
                        if cc not in prev_manual_cc:
                            if cc[1][0] <= 1:
                                midi.send(ControlChange(cc[0], 127))
                                trellis.pixels._neopixel[press_to_light(cc[1], PRESS_TO_LIGHT)] = MANUAL_CC_COLOR
                            if cc[1][0] >= 2:
                                if cc not in toggled_cc:
                                    toggled_cc.append(cc)
                                    midi.send(ControlChange(cc[0], 127))
                                    trellis.pixels._neopixel[press_to_light(cc[1], PRESS_TO_LIGHT)] = MANUAL_CC_COLOR
                                else:
                                    toggled_cc.remove(cc)
                                    midi.send(ControlChange(cc[0], 0))
                                    trellis.pixels._neopixel[press_to_light(cc[1], PRESS_TO_LIGHT)] = NOTE_OFF
                    for cc in prev_manual_cc:
                        if cc not in manual_cc:
                            if cc[1][0] <=1:
                                midi.send(ControlChange(cc[0], 0))
                                trellis.pixels._neopixel[press_to_light(cc[1], PRESS_TO_LIGHT)] = NOTE_OFF
                    prev_manual_cc = manual_cc
                    
                elif pressed_buttons[-2:] == MANUAL_NOTE_COMBO: 
                    if len(pressed_buttons) > 2:
                        manual_notes = []
                        for button in pressed_buttons:
                            if button == (3, 4) or button == (0, 5): #TODO use variables
                                pass
                            else:
                                manual_notes.append((MANUAL_NOTES[button[0]][button[1]], button))
                    else:
                        manual_notes = []
                    for note in manual_notes:
                        if note not in prev_manual_notes:
                            midi.send(NoteOn(note[0], 127), channel=1 if seperate_manual_note_channel else 0)
                            trellis.pixels._neopixel[press_to_light(note[1], PRESS_TO_LIGHT)] = MANUAL_NOTE_COLOR_ALT if seperate_manual_note_channel else MANUAL_NOTE_COLOR
                    for note in prev_manual_notes:
                        if note not in manual_notes:
                            midi.send(NoteOff(note[0], 0), channel=1 if seperate_manual_note_channel else 0)
                            trellis.pixels._neopixel[press_to_light(note[1], PRESS_TO_LIGHT)] = NOTE_OFF
                    prev_manual_notes = manual_notes
                    
                elif pressed_buttons[-2:] == RECORD_NOTE_COMBO: 
                    if len(pressed_buttons) > 2:
                        manual_notes = []
                        for button in pressed_buttons:
                            if button == (3, 5) or button == (0, 5): #TODO use variables
                                pass
                            else:
                                manual_notes.append((MANUAL_NOTES[button[0]][button[1]], button)) #ERROR if button pressed in on second half for board
                    else:
                        manual_notes = []
                    for note in manual_notes:
                        if note not in prev_manual_notes:
                            column_now = ticks%(last_step*12)/6
                            if round(column_now) % 2 == 0:
                                for grid_note in notes.grid[floor(column_now/2)]:
                                    if grid_note.note == note[0]:
                                        grid_note.is_on = True
                            else:
                                for grid_note in shift.grid[floor(column_now/2)]:
                                    if grid_note.note == note[0]:
                                        grid_note.is_on = True
                            if round(column_now) - column_now < 0:
                                midi.send(NoteOn(note[0], 127))
                            trellis.pixels._neopixel[press_to_light(note[1], PRESS_TO_LIGHT)] = RECORD_NOTE_COLOR
                    for note in prev_manual_notes:
                        if note not in manual_notes:
                            midi.send(NoteOff(note[0], 0))
                            trellis.pixels._neopixel[press_to_light(note[1], PRESS_TO_LIGHT)] = NOTE_OFF
                    prev_manual_notes = manual_notes
                
                elif pressed_buttons == CHANGE_MANUAL_NOTE_CHANNEL_COMBO:
                    seperate_manual_note_channel = False if seperate_manual_note_channel else True
                
                elif pressed_buttons[-2:] == PATTERN_SHIFT_MODE_COMBO: #FEAT light up availible buttons
                    if len(pressed_buttons) > 2:
                        if pressed_buttons[0] == SHIFT_LEFT:
                            notes = shift_grid_left(notes)
                            shift = shift_grid_left(shift)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                        elif pressed_buttons[0] == SHIFT_RIGHT:
                            notes = shift_grid_right(notes)
                            shift = shift_grid_right(shift)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                
                elif pressed_buttons[-2:] == LAST_STEP_EDIT_COMBO: #FEAT light up availible buttons
                    if len(pressed_buttons) > 2:
                        last_step = handle_last_step_edit(last_step, pressed_buttons[0], LAST_STEP_BUTTONS, NUMBER_OF_COLUMNS)
                        
                else:
                    print(pressed_buttons)
                    
                button_is_held = False
            else:
                reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                
            """
            Shift Mode
            """
        elif mode == b's': #TODO all this "shift code" could be the same as "main code" with "or" statement
            if pressed_buttons and not combo_pressed:
                for note in shift.grid[pressed_buttons[0][1] + column_offset]:
                    if note.note == pressed_buttons[0][0] + STARTING_NOTE + row_offset:
                        tick_placeholder = ticks
                        held_note = note
                        button_is_held = True
                        
            elif button_is_held:
                if ticks - tick_placeholder < HOLD_TIME:
                    trellis.pixels._neopixel[held_note.index] = SHIFT_NOTE_ON if not held_note.is_on else NOTE_OFF
                    held_note.toggle()
                    if held_note.is_accented:
                        held_note.toggle_accent()
                    button_is_held = False
                else:
                    if not held_note.is_on:
                        trellis.pixels._neopixel[held_note.index] = SHIFT_ACCENT if not held_note.is_accented else NOTE_OFF
                        held_note.toggle()
                    held_note.toggle_accent()
            if not pressed_buttons:
                combo_pressed = False
            
            """
            Shift Combos
            """
            if len(pressed_buttons) > 1:
                combo_pressed = True
                if pressed_buttons == BACK_COMBO: #TODO don't use back combo, use the same combo as to get there
                    mode = b'm'
                    reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons == CLEAR_COMBO:
                    clear_grid(notes)
                    clear_grid(shift)
                    reset_colors(notes, SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                
                elif pressed_buttons[-2:] == OFFSET_CHANGE_MODE_COMBO:
                    if len(pressed_buttons) > 2:
                        if pressed_buttons[0] == INCREASE_ROW_OFFSET:
                            row_offset = increase_row_offset(row_offset)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == DECREASE_ROW_OFFSET:
                            row_offset = decrease_row_offset(row_offset)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == INCREASE_COLUMN_OFFSET:
                            column_offset = increase_column_offset(column_offset)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == DECREASE_COLUMN_OFFSET:
                            column_offset = decrease_column_offset(column_offset)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)

                elif pressed_buttons[-2:] == MANUAL_CC_COMBO:
                    for cc in toggled_cc:
                        trellis.pixels._neopixel[press_to_light(cc[1], PRESS_TO_LIGHT)] = MANUAL_CC_COLOR
                    if len(pressed_buttons) > 2:
                        manual_cc = []
                        for button in pressed_buttons:
                            if MANUAL_CC_COLOR.contains(button):
                                pass
                            else:
                                manual_cc.append((MANUAL_CC[button[0]][button[1]], button))
                    else:
                        manual_cc = []
                    for cc in manual_cc:
                        if cc not in prev_manual_cc:
                            if cc[1][0] <= 1:
                                midi.send(ControlChange(cc[0], 127))
                                trellis.pixels._neopixel[press_to_light(cc[1], PRESS_TO_LIGHT)] = MANUAL_CC_COLOR
                            if cc[1][0] >= 2:
                                if cc not in toggled_cc:
                                    toggled_cc.append(cc)
                                    midi.send(ControlChange(cc[0], 127))
                                    trellis.pixels._neopixel[press_to_light(cc[1], PRESS_TO_LIGHT)] = MANUAL_CC_COLOR
                                else:
                                    toggled_cc.remove(cc)
                                    midi.send(ControlChange(cc[0], 0))
                                    trellis.pixels._neopixel[press_to_light(cc[1], PRESS_TO_LIGHT)] = NOTE_OFF
                    for cc in prev_manual_cc:
                        if cc not in manual_cc:
                            if cc[1][0] <=1:
                                midi.send(ControlChange(cc[0], 0))
                                trellis.pixels._neopixel[press_to_light(cc[1], PRESS_TO_LIGHT)] = NOTE_OFF
                    prev_manual_cc = manual_cc
                    
                elif pressed_buttons[-2:] == MANUAL_NOTE_COMBO: 
                    if len(pressed_buttons) > 2:
                        manual_notes = []
                        for button in pressed_buttons:
                            if button == (3, 4) or button == (0, 5):
                                pass
                            else:
                                manual_notes.append((MANUAL_NOTES[button[0]][button[1]], button))
                    else:
                        manual_notes = []
                    for note in manual_notes:
                        if note not in prev_manual_notes:
                            midi.send(NoteOn(note[0], 127), channel=1 if seperate_manual_note_channel else 0)
                            trellis.pixels._neopixel[press_to_light(note[1], PRESS_TO_LIGHT)] = MANUAL_NOTE_COLOR_ALT if seperate_manual_note_channel else MANUAL_NOTE_COLOR
                    for note in prev_manual_notes:
                        if note not in manual_notes:
                            midi.send(NoteOff(note[0], 0), channel=1 if seperate_manual_note_channel else 0)
                            trellis.pixels._neopixel[press_to_light(note[1], PRESS_TO_LIGHT)] = NOTE_OFF
                    prev_manual_notes = manual_notes
                
                elif pressed_buttons[-2:] == RECORD_NOTE_COMBO: 
                    if len(pressed_buttons) > 2:
                        manual_notes = []
                        for button in pressed_buttons:
                            if button == (3, 5) or button == (0, 5):
                                pass
                            else:
                                manual_notes.append((MANUAL_NOTES[button[0]][button[1]], button))
                    else:
                        manual_notes = []
                    for note in manual_notes:
                        if note not in prev_manual_notes:
                            column_now = ticks%(last_step*12)/6
                            if round(column_now) % 2 == 0:
                                for grid_note in notes.grid[floor(column_now/2)]:
                                    if grid_note.note == note[0]:
                                        grid_note.is_on = True
                            else:
                                for grid_note in shift.grid[floor(column_now/2)]:
                                    if grid_note.note == note[0]:
                                        grid_note.is_on = True
                            if round(column_now) - column_now < 0:
                                midi.send(NoteOn(note[0], 127))
                            trellis.pixels._neopixel[press_to_light(note[1], PRESS_TO_LIGHT)] = RECORD_NOTE_COLOR
                    for note in prev_manual_notes:
                        if note not in manual_notes:
                            midi.send(NoteOff(note[0], 0))
                            trellis.pixels._neopixel[press_to_light(note[1], PRESS_TO_LIGHT)] = NOTE_OFF
                    prev_manual_notes = manual_notes
                
                elif pressed_buttons == CHANGE_MANUAL_NOTE_CHANNEL_COMBO:
                    seperate_manual_note_channel = False if seperate_manual_note_channel else True
                
                elif pressed_buttons[-2:] == PATTERN_SHIFT_MODE_COMBO:
                    if len(pressed_buttons) > 2:
                        if pressed_buttons[0] == SHIFT_LEFT:
                            notes = shift_grid_left(notes)
                            shift = shift_grid_left(shift)
                            reset_colors(notes, SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                        elif pressed_buttons[0] == SHIFT_RIGHT:
                            notes = shift_grid_right(notes)
                            shift = shift_grid_right(shift)
                            reset_colors(notes, SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                
                elif pressed_buttons[-2:] == LAST_STEP_EDIT_COMBO:
                    if len(pressed_buttons) > 2:
                        last_step = handle_last_step_edit(last_step, pressed_buttons[0], LAST_STEP_BUTTONS, NUMBER_OF_COLUMNS)
                            
                else:
                    print(pressed_buttons)
                    
                button_is_held = False
    
                """
                Edit CC Mode
                """
        elif mode == b'c':
            handle_cc_grid(cc_edit, axis_modes, 2)
            reset_colors(cc_edit, EDIT_CC_COLOR)
            
            if pressed_buttons and not combo_pressed:
                
                if pressed_buttons[0][1] == 0:
                    pass
                
                elif pressed_buttons[0][0] == 2:
                    axis_modes[0] = handle_select_mode(pressed_buttons[0][1])
                    row_off(cc_edit, 2)
                    handle_cc_lights(pressed_buttons, cc_edit, 2)
                    reset_colors(cc_edit, EDIT_CC_COLOR)

                elif pressed_buttons[0][0] == 1:
                    axis_modes[1] = handle_select_mode(pressed_buttons[0][1])
                    row_off(cc_edit, 1)
                    handle_cc_lights(pressed_buttons, cc_edit, 1)
                    reset_colors(cc_edit, EDIT_CC_COLOR)
                    
                elif pressed_buttons[0][0] == 0:
                    axis_modes[2] = handle_select_mode(pressed_buttons[0][1])
                    row_off(cc_edit, 0)
                    handle_cc_lights(pressed_buttons, cc_edit, 0)
                    reset_colors(cc_edit, EDIT_CC_COLOR)
            
            """
            Edit CC Combos
            """
            if len(pressed_buttons) > 2:
                if pressed_buttons == EDIT_CC_BACK:
                    mode = b'm'
                    reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                else:
                    print(pressed_buttons)
            if not pressed_buttons:
                combo_pressed = False
                
            """
            Pattern Select Mode
            """
        elif mode == b'p':
            slots = get_slots()
            light_slots(slots, SAVE_SLOT_COLOR, trellis.pixels._neopixel)
            trellis.pixels._neopixel[current_slot] = CURRENT_SLOT_COLOR
                
            if pressed_buttons and not combo_pressed:
                write_save(notes, shift, last_step, axis_modes)
                current_slot = press_to_light(pressed_buttons[0], PRESS_TO_LIGHT)
                [ notes, shift, last_step, axis_modes ] = read_save(current_slot, notes, shift)
                mode = b'm'
                
            if not pressed_buttons:
                combo_pressed = False
        
            """
            Pattern Delete Mode
            """
        elif mode == b'd':
            slots = get_slots()
            if slots: light_slots(slots, DELETE_SLOT_COLOR, trellis.pixels._neopixel)
            else: mode = b'm'
                
            if pressed_buttons and not combo_pressed and press_to_light(pressed_buttons[0], PRESS_TO_LIGHT) in slots:
                remove("/{}.json".format(press_to_light(pressed_buttons[0], PRESS_TO_LIGHT)))
                mode = b'm'
                
            if not pressed_buttons:
                combo_pressed = False
        
            """
            Delete All Pattern Mode
            """
        elif mode == b'da':
            fill_yes_no(CONFIRM_COLOR, DECLINE_COLOR, trellis.pixels._neopixel)
            
            if pressed_buttons and not combo_pressed:
                if press_to_light(pressed_buttons[0], PRESS_TO_LIGHT) < 16:
                    delete_all_slots()
                    current_slot = 0
                    clear_grid(notes)
                    clear_grid(shift)
                mode = b'm'
                
            if not pressed_buttons:
                combo_pressed = False
            
    last_press = pressed_buttons

    """
    ======== Send Axes CC ========
    """
    if ticks != last_tick:
        handle_axes(axis_modes, accelerometer.acceleration, axis_ccs, ControlChange)
        
    last_tick = ticks