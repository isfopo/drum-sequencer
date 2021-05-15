from math import floor
import board
import busio

import usb_midi
import adafruit_midi
import adafruit_trellism4
import adafruit_adxl34x

from adafruit_midi.timing_clock import TimingClock
from adafruit_midi.start import Start
from adafruit_midi.stop import Stop
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.control_change import ControlChange

midi = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1], in_channel=0, out_channel=0)
trellis = adafruit_trellism4.TrellisM4Express(rotation=90)
i2c = busio.I2C(board.ACCELEROMETER_SCL, board.ACCELEROMETER_SDA)
accelerometer = adafruit_adxl34x.ADXL345(i2c)

"""
======== Classes ========
"""

class Grid:
    def __init__(self, columns, rows, correction):
            index = 0
            self.grid = []
            for i in range(columns):
                column = []
                for j in range(rows):
                    if j % 4 == 0:
                        index = 0
                    column.append(Cell(correct_index(index, i)))
                    index += 1
                self.grid.append(column)

class NoteGrid:
    def __init__(self, columns, rows, starting_note):
            index = 0
            self.grid = []
            for i in range(columns):
                column = []
                note = starting_note
                for j in range(rows):
                    if j % 4 == 0:
                        index = 0
                    column.append(Note(note, correct_index(index, i)))
                    index += 1
                    note += 1
                self.grid.append(column)

class Cell:
    def __init__(self, index):
        self.index = index
        self.is_on = False
        
    def toggle(self):
        self.is_on = True if not self.is_on else False
        
    def on(self):
        self.is_on = True
        
    def off(self):
        self.is_on = False

class Note:
    def __init__(self, note, index):
        self.note = note
        self.index = index
        self.is_on = False
        self.isAccented = False
        
    def play(self):
        self.stop()
        if self.is_on:
            midi.send(NoteOn(self.note, 127 if self.isAccented else 96))
        
    def stop(self):
        if self.is_on:
            midi.send(NoteOff(self.note, 0))
        
    def toggle(self):
        self.is_on = True if not self.is_on else False
        
    def toggle_accent(self):
        self.isAccented = True if not self.isAccented else False

"""
======== Fuctions ========
"""
def reset_colors(notes, note_on, note_off=(0, 0, 0), row_offset=0, column_offset=0):
    for column in notes.grid[column_offset:column_offset+8]:
        for note in column[row_offset:row_offset+4]:
            if note.is_on == True:
                trellis.pixels._neopixel[note.index] = note_on
            else:
                trellis.pixels._neopixel[note.index] = note_off

def light_column(column, column_color):
    for i in range(ROWS_ON_BOARD):
        trellis.pixels._neopixel[ column + (i*len(trellis._matrix.row_pins)) ] = column_color
    
def reset_column(notes, offset, column, note_on, note_off, accent):
    for note in notes.grid[column][offset:offset+4]:
        if note.is_on:
            if note.isAccented:
                trellis.pixels._neopixel[note.index] = accent
            else:
                trellis.pixels._neopixel[note.index] = note_on
        else:
            trellis.pixels._neopixel[note.index] = note_off

def play_column(notes, column):
    for note in notes.grid[column]:
        note.play()

def stop_notes(notes):
    map(lambda x: map(lambda y: y.stop(), x), notes.grid)

def clear_grid(notes):
    for column in notes.grid:
        for note in column:
            note.is_on = False
            
def scale(val, src, dst):
    output = ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]
    if output < dst[0]: return dst[0]
    if output > dst[1]: return dst[1]
    return output

def correct_index(index, i):
    return CORRECT_INDEX[index+((i%8)*4)]

def press_to_light(button):
    return PRESS_TO_LIGHT[button[0]][button[1]]

def handle_axis(mode, axis, up_cc, down_cc):
    if mode == 'direct':
        midi.send(ControlChange(up_cc, int(scale(axis, (-10, 10), (0, 127)))))
    elif mode == 'flip':
        midi.send(ControlChange(up_cc, int(scale(axis, (10, -10), (0, 127)))))
    elif mode == 'split':
        if axis > 0:
            midi.send(ControlChange(up_cc, int(scale(axis, (0, 10), (0, 127)))))
        else:
            midi.send(ControlChange(down_cc, int(scale(axis, (0, -10), (0, 127)))))
    elif mode == 'on_off':
        if axis > 0: #TODO is there a way to only send the cc on change?
            midi.send(ControlChange(up_cc, 127))
        else:
            midi.send(ControlChange(up_cc, 0))
    elif mode == 'flip_on_off':
        if axis > 0:
            midi.send(ControlChange(up_cc, 0))
        else:
            midi.send(ControlChange(up_cc, 127))
    elif mode == 'split_on_off':
        if axis > 0:
            if axis > 5:
                midi.send(ControlChange(up_cc, 127))
            else:
                midi.send(ControlChange(up_cc, 0))
        else:    
            if axis < -5:
                midi.send(ControlChange(down_cc, 127))
            else:
                midi.send(ControlChange(down_cc, 0))

def handle_cc_grid(cc_edit, modes, offset):
    for mode in modes:
        if mode == 'direct':       cc_edit.grid[1][offset].is_on = True
        if mode == 'flip':         cc_edit.grid[2][offset].is_on = True
        if mode == 'split':        cc_edit.grid[3][offset].is_on = True
        if mode == 'on_off':       cc_edit.grid[4][offset].is_on = True
        if mode == 'flip_on_off':  cc_edit.grid[5][offset].is_on = True
        if mode == 'split_on_off': cc_edit.grid[6][offset].is_on = True
        if mode == 'none':         cc_edit.grid[7][offset].is_on = True
        offset -= 1

def handle_select_mode(pressed_buttons):
    if pressed_buttons[0][1] == 1: return 'direct'
    if pressed_buttons[0][1] == 2: return 'flip'
    if pressed_buttons[0][1] == 3: return 'split'
    if pressed_buttons[0][1] == 4: return 'on_off'
    if pressed_buttons[0][1] == 5: return 'flip_on_off'
    if pressed_buttons[0][1] == 6: return 'split_on_off'
    else: return 'none'

def handle_cc_lights(pressed_buttons, cc_edit, row):
    cc_edit.grid[pressed_buttons[0][1]][row].is_on = True

def increase_row_offset(row_offset):
    new_offset = row_offset + 4
    return new_offset if new_offset < NUMBER_OF_ROWS else row_offset
    
def decrease_row_offset(row_offset):
    new_offset = row_offset - 4
    return new_offset if new_offset >= 0 else row_offset
 
def increase_column_offset(column_offset):
    new_offset = column_offset + 8
    return new_offset if new_offset < NUMBER_OF_COLUMNS else column_offset
    
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

"""
Grid Parameters
"""
STARTING_NOTE     = 36
NUMBER_OF_COLUMNS = 32
NUMBER_OF_ROWS    = 16
COLUMNS_ON_BOARD  = len(trellis._matrix.row_pins)
ROWS_ON_BOARD     = len(trellis._matrix.col_pins)


"""
Button Combonations
"""
MANUAL_CC_COMBO              = [(3, 4), (0, 4)]
MANUAL_NOTE_COMBO            = [(3, 4), (0, 5)]
RECORD_NOTE_COMBO            = [(3, 5), (0, 5)]
BACK_COMBO                   = [(3, 0), (0, 0), (3, 7)]
CLEAR_COMBO                  = [(3, 0), (0, 0), (3, 1)]
SHIFT_MODE_COMBO             = [(3, 0), (0, 0), (3, 2)]
EDIT_CC_COMBO                = [(3, 0), (0, 0), (3, 3)]
EDIT_CC_BACK                 = [(3, 0), (3, 1), (3, 7)]
TOGGLE_X_COMBO               = [(2, 0), (0, 0), (2, 1)]
TOGGLE_Y_COMBO               = [(2, 0), (0, 0), (2, 2)]
TOGGLE_Z_COMBO               = [(2, 0), (0, 0), (2, 3)]
OFFSET_CHANGE_MODE_COMBO	 = [(3, 6), (0, 6)]
INCREASE_ROW_OFFSET_COMBO    = (3, 4)
DECREASE_ROW_OFFSET_COMBO    = (1, 4)
INCREASE_COLUMN_OFFSET_COMBO = (2, 5)
DECREASE_COLUMN_OFFSET_COMBO = (2, 3)
PATTERN_SHIFT_MODE_COMBO     = [(3, 7), (0, 7)]
SHIFT_LEFT				     = (2, 4)
SHIFT_RIGHT				     = (2, 6)
CHANGE_MANUAL_NOTE_CHANNEL_COMBO = [(3, 1), (2, 1), (0, 1)]
LAST_STEP_EDIT_COMBO         = [(2, 7), (0, 7)]
LAST_STEP_INCREASE	         = (1, 6)
LAST_STEP_DECREASE           = (1, 4)
"""
Integers
"""
HOLD_TIME = 48 #in ticks

"""
Lists
"""
CORRECT_INDEX  =  [ 24, 16,  8, 0,
                    25, 17,  9, 1,
                    26, 18, 10, 2,
                    27, 19, 11, 3,
                    28, 20, 12, 4,
                    29, 21, 13, 5,
                    30, 22, 14, 6,
                    31, 23, 15, 7 ]

PRESS_TO_LIGHT    = [ [ 24, 25, 26, 27, 28, 29, 30, 31 ],
                      [ 16, 17, 18, 19, 20, 21, 22, 23 ],
                      [  8,  9, 10, 11, 12, 13, 14, 15 ],
                      [  0,  1,  2,  3,  4,  5,  6,  7 ] ]

MANUAL_NOTES      = [ [ 48, 44, 40, 36 ],
                      [ 49, 45, 41, 37 ],
                      [ 50, 46, 42, 38 ],
                      [ 51, 47, 43, 39 ] ]

MANUAL_CC         = [ [ 22, 23, 24, 25 ],
                      [ 26, 27, 28, 29 ],
                      [ 30, 31, 85, 86 ],
                      [ 87, 88, 89, 90 ] ]

"""
======== Global Variables ========
"""

"""
Grid Objects
"""
notes = NoteGrid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE)
shift = NoteGrid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE)
cc_edit = Grid(8, 4, CORRECT_INDEX)

#print(list(map(lambda x: list(map(lambda y: y.index, x)), notes.grid))) # prints note grid to show notes

"""
Counters
"""
ticks = 0
eighth_note = 0

"""
Placeholders
"""
old_message = 0
last_press = 0
held_note = 0
tick_placeholder = 0

"""
Bools
"""
on = False
button_is_held = False
combo_pressed = False
manual_is_pressed = False

seperate_manual_note_channel = False

"""
Offset
"""
row_offset = 0
column_offset = 0
last_step = 8

"""
Modes
"""
main_mode = True
shift_mode = False
cc_edit_mode = False
manual_note_mode = False
manual_cc_mode = False

"""
Axis Modes
"""
x_mode = 'none'
y_mode = 'none'
z_mode = 'none'

"""
Axis cc's
"""
x_up_cc = 3
x_down_cc = 9
y_up_cc = 14
y_down_cc = 15
z_up_cc = 20
z_down_cc = 21

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
    new_message = midi.receive()
    if new_message != old_message and new_message != None:

        """
        Sync To TimingClock
        """
        if isinstance(new_message, TimingClock) and on:
            """
            Main Grid
            """
            if ticks % 12 == 0:
                for i in range(NUMBER_OF_COLUMNS):
                    if eighth_note % last_step + 1 == i:
                        if main_mode:
                            if i % 8 == 0:
                                if column_offset == last_step+1 - 8:
                                    if i == 0:
                                        light_column(7, COLUMN_COLOR)
                                        reset_column(notes, row_offset, 6, NOTE_ON, NOTE_OFF, ACCENT)
                                    
                                else:
                                    if column_offset < i <= column_offset + 8:
                                        light_column(7, COLUMN_COLOR)
                                        reset_column(notes, row_offset, column_offset + 6, NOTE_ON, NOTE_OFF, ACCENT)
                            else:
                                if i % 8 == 1:
                                    reset_column(notes, row_offset, column_offset + 7, NOTE_ON, NOTE_OFF, ACCENT)
                                if column_offset <= i < column_offset + 8:
                                    light_column((i-1)%8, COLUMN_COLOR)
                                    reset_column(notes, row_offset, (i-2), NOTE_ON, NOTE_OFF, ACCENT)
                            if i == 1:
                                reset_column(notes, row_offset, column_offset + 7, NOTE_ON, NOTE_OFF, ACCENT)
                                reset_column(notes, row_offset, (last_step-1)%8, NOTE_ON, NOTE_OFF, ACCENT)
                        play_column(notes, i-1)
                eighth_note += 1           
            """
            Shift Grid
            """
            if ticks % 12 == 6:
                for i in range(NUMBER_OF_COLUMNS):
                    if eighth_note % last_step == i:
                        if shift_mode:
                            if i % 8 == 0:
                                if column_offset == last_step - 8:
                                    if i == 0:
                                        light_column(7, SHIFT_COLUMN_COLOR)
                                        reset_column(shift, row_offset, 6, SHIFT_NOTE_ON, NOTE_OFF, SHIFT_ACCENT)
                                else:
                                    if column_offset < i <= column_offset + 8:
                                        light_column(7, SHIFT_COLUMN_COLOR)
                                        reset_column(shift, row_offset, column_offset + 6, SHIFT_NOTE_ON, NOTE_OFF, SHIFT_ACCENT)
                            else:
                                if i % 8 == 1:
                                    reset_column(shift, row_offset, column_offset + 7, SHIFT_NOTE_ON, NOTE_OFF, SHIFT_ACCENT)
                                if column_offset <= i < column_offset + 8:
                                    light_column((i-1)%8, SHIFT_COLUMN_COLOR)
                                    reset_column(shift, row_offset, (i-2), SHIFT_NOTE_ON, NOTE_OFF, SHIFT_ACCENT)
                            if i == 1:
                                reset_column(shift, row_offset, column_offset + 7, SHIFT_NOTE_ON, NOTE_OFF, SHIFT_ACCENT)
                        play_column(shift, i-1)
            ticks += 1
            
        """
        Start and Stop
        """
        if isinstance(new_message, Start):
            on = True
            ticks = 0
            eighth_note = 0
            
        if isinstance(new_message, Stop):
            on = False
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
        if main_mode:
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
                    if held_note.isAccented:
                        held_note.toggle_accent()
                    button_is_held = False
                else:
                    if not held_note.is_on:
                        trellis.pixels._neopixel[held_note.index] = ACCENT if not held_note.isAccented else NOTE_OFF
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
                    main_mode = False
                    shift_mode = True
                    reset_colors(shift, SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                
                elif pressed_buttons == EDIT_CC_COMBO:
                    main_mode = False
                    edit_cc_mode = True
                    reset_colors(cc_edit, EDIT_CC_COLOR, NOTE_OFF, row_offset, column_offset)
                
                elif pressed_buttons[-2:] == OFFSET_CHANGE_MODE_COMBO:
                    if len(pressed_buttons) > 2:
                        if pressed_buttons[0] == INCREASE_ROW_OFFSET_COMBO:
                            row_offset = increase_row_offset(row_offset)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == DECREASE_ROW_OFFSET_COMBO:
                            row_offset = decrease_row_offset(row_offset)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == INCREASE_COLUMN_OFFSET_COMBO:
                            column_offset = increase_column_offset(column_offset)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == DECREASE_COLUMN_OFFSET_COMBO:
                            column_offset = decrease_column_offset(column_offset)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons[-2:] == MANUAL_CC_COMBO:
                    for cc in toggled_cc:
                        trellis.pixels._neopixel[press_to_light(cc[1])] = MANUAL_CC_COLOR
                    if len(pressed_buttons) > 2:
                        manual_cc = []
                        for button in pressed_buttons:
                            if button == (3, 4) or button == (0, 4):
                                pass
                            else:
                                manual_cc.append((MANUAL_CC[button[0]][button[1]], button))
                    else:
                        manual_cc = []
                    for cc in manual_cc:
                        if cc not in prev_manual_cc:
                            if cc[1][0] <= 1:
                                midi.send(ControlChange(cc[0], 127))
                                trellis.pixels._neopixel[press_to_light(cc[1])] = MANUAL_CC_COLOR
                            if cc[1][0] >= 2:
                                if cc not in toggled_cc:
                                    toggled_cc.append(cc)
                                    midi.send(ControlChange(cc[0], 127))
                                    trellis.pixels._neopixel[press_to_light(cc[1])] = MANUAL_CC_COLOR
                                else:
                                    toggled_cc.remove(cc)
                                    midi.send(ControlChange(cc[0], 0))
                                    trellis.pixels._neopixel[press_to_light(cc[1])] = NOTE_OFF
                    for cc in prev_manual_cc:
                        if cc not in manual_cc:
                            if cc[1][0] <=1:
                                midi.send(ControlChange(cc[0], 0))
                                trellis.pixels._neopixel[press_to_light(cc[1])] = NOTE_OFF
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
                            trellis.pixels._neopixel[press_to_light(note[1])] = MANUAL_NOTE_COLOR_ALT if seperate_manual_note_channel else MANUAL_NOTE_COLOR
                    for note in prev_manual_notes:
                        if note not in manual_notes:
                            midi.send(NoteOff(note[0], 0), channel=1 if seperate_manual_note_channel else 0)
                            trellis.pixels._neopixel[press_to_light(note[1])] = NOTE_OFF
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
                            trellis.pixels._neopixel[press_to_light(note[1])] = RECORD_NOTE_COLOR
                    for note in prev_manual_notes:
                        if note not in manual_notes:
                            midi.send(NoteOff(note[0], 0))
                            trellis.pixels._neopixel[press_to_light(note[1])] = NOTE_OFF
                    prev_manual_notes = manual_notes
                
                elif pressed_buttons == CHANGE_MANUAL_NOTE_CHANNEL_COMBO:
                    seperate_manual_note_channel = False if seperate_manual_note_channel else True
                
                elif pressed_buttons[-2:] == PATTERN_SHIFT_MODE_COMBO:
                    if len(pressed_buttons) > 2:
                        if pressed_buttons[0] == SHIFT_LEFT:
                            notes = shift_grid_left(notes)
                            shift = shift_grid_left(shift)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                        elif pressed_buttons[0] == SHIFT_RIGHT:
                            notes = shift_grid_right(notes)
                            shift = shift_grid_right(shift)
                            reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                
                elif pressed_buttons[-2:] == LAST_STEP_EDIT_COMBO:
                    if len(pressed_buttons) > 2:
                        if pressed_buttons[0] == LAST_STEP_INCREASE:
                            last_step = last_step + 1 if last_step < NUMBER_OF_COLUMNS else last_step
                        if pressed_buttons[0] == LAST_STEP_DECREASE:
                            last_step = last_step - 1 if last_step > 1 else last_step
                        
                        
                else:
                    print(pressed_buttons)
                    
                button_is_held = False
            else:
                reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                
            """
            Shift Mode
            """
        elif shift_mode:
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
                    if held_note.isAccented:
                        held_note.toggle_accent()
                    button_is_held = False
                else:
                    if not held_note.is_on:
                        trellis.pixels._neopixel[held_note.index] = SHIFT_ACCENT if not held_note.isAccented else NOTE_OFF
                        held_note.toggle()
                    held_note.toggle_accent()
            if not pressed_buttons:
                combo_pressed = False
            
            """
            Shift Combos
            """
            if len(pressed_buttons) > 1:
                combo_pressed = True
                if pressed_buttons == BACK_COMBO:
                    main_mode = True
                    shift_mode = False
                    reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons == CLEAR_COMBO:
                    clear_grid(notes)
                    clear_grid(shift)
                    reset_colors(notes, SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                
                elif pressed_buttons == INCREASE_ROW_OFFSET_COMBO:
                    row_offset = increase_row_offset(row_offset)
                    reset_colors(shift, SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons == DECREASE_ROW_OFFSET_COMBO:
                    row_offset = decrease_row_offset(row_offset)
                    reset_colors(shift, SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons == INCREASE_COLUMN_OFFSET_COMBO:
                    column_offset = increase_column_offset(column_offset)
                    reset_colors(shift, SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons == DECREASE_COLUMN_OFFSET_COMBO:
                    column_offset = decrease_column_offset(column_offset)
                    reset_colors(shift, NOTE_ON, NOTE_OFF, row_offset, column_offset)

                elif pressed_buttons[-2:] == MANUAL_CC_COMBO:
                    for cc in toggled_cc:
                        trellis.pixels._neopixel[press_to_light(cc[1])] = MANUAL_CC_COLOR
                    if len(pressed_buttons) > 2:
                        manual_cc = []
                        for button in pressed_buttons:
                            if button == (3, 4) or button == (0, 4):
                                pass
                            else:
                                manual_cc.append((MANUAL_CC[button[0]][button[1]], button))
                    else:
                        manual_cc = []
                    for cc in manual_cc:
                        if cc not in prev_manual_cc:
                            if cc[1][0] <= 1:
                                midi.send(ControlChange(cc[0], 127))
                                trellis.pixels._neopixel[press_to_light(cc[1])] = MANUAL_CC_COLOR
                            if cc[1][0] >= 2:
                                if cc not in toggled_cc:
                                    toggled_cc.append(cc)
                                    midi.send(ControlChange(cc[0], 127))
                                    trellis.pixels._neopixel[press_to_light(cc[1])] = MANUAL_CC_COLOR
                                else:
                                    toggled_cc.remove(cc)
                                    midi.send(ControlChange(cc[0], 0))
                                    trellis.pixels._neopixel[press_to_light(cc[1])] = NOTE_OFF
                    for cc in prev_manual_cc:
                        if cc not in manual_cc:
                            if cc[1][0] <=1:
                                midi.send(ControlChange(cc[0], 0))
                                trellis.pixels._neopixel[press_to_light(cc[1])] = NOTE_OFF
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
                            trellis.pixels._neopixel[press_to_light(note[1])] = MANUAL_NOTE_COLOR_ALT if seperate_manual_note_channel else MANUAL_NOTE_COLOR
                    for note in prev_manual_notes:
                        if note not in manual_notes:
                            midi.send(NoteOff(note[0], 0), channel=1 if seperate_manual_note_channel else 0)
                            trellis.pixels._neopixel[press_to_light(note[1])] = NOTE_OFF
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
                            trellis.pixels._neopixel[press_to_light(note[1])] = RECORD_NOTE_COLOR
                    for note in prev_manual_notes:
                        if note not in manual_notes:
                            midi.send(NoteOff(note[0], 0))
                            trellis.pixels._neopixel[press_to_light(note[1])] = NOTE_OFF
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
                        if pressed_buttons[0] == LAST_STEP_INCREASE:
                            last_step = last_step + 1 if last_step < NUMBER_OF_COLUMNS else last_step
                        if pressed_buttons[0] == LAST_STEP_DECREASE:
                            last_step = last_step - 1 if last_step > 1 else last_step
                            
                else:
                    print(pressed_buttons)
                    
                button_is_held = False
    
            """
            Edit CC Mode
            """
        elif edit_cc_mode:
            handle_cc_grid(cc_edit, [x_mode, y_mode, z_mode], 2)
            reset_colors(cc_edit, EDIT_CC_COLOR)
            
            if pressed_buttons and not combo_pressed:
 
                if pressed_buttons[0][0] == 2:
                    x_mode = handle_select_mode(pressed_buttons)
                    row_off(cc_edit, 2)
                    handle_cc_lights(pressed_buttons, cc_edit, 2)
                    reset_colors(cc_edit, EDIT_CC_COLOR)

                if pressed_buttons[0][0] == 1:
                    y_mode = handle_select_mode(pressed_buttons)
                    row_off(cc_edit, 1)
                    handle_cc_lights(pressed_buttons, cc_edit, 1)
                    reset_colors(cc_edit, EDIT_CC_COLOR)
                    
                if pressed_buttons[0][0] == 0:
                    z_mode = handle_select_mode(pressed_buttons)
                    row_off(cc_edit, 0)
                    handle_cc_lights(pressed_buttons, cc_edit, 0)
                    reset_colors(cc_edit, EDIT_CC_COLOR)
            
            """
            Edit CC Combos
            """
            if len(pressed_buttons) > 2:
                if pressed_buttons == EDIT_CC_BACK:
                    main_mode = True
                    edit_cc_mode = False
                    reset_colors(notes, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                else:
                    print(pressed_buttons)
            if not pressed_buttons:
                combo_pressed = False
            
    last_press = pressed_buttons

    """
    ======== Send Axis CC ========
    """
    if on:
        handle_axis(x_mode, accelerometer.acceleration[1], x_up_cc, x_down_cc)
        handle_axis(y_mode, accelerometer.acceleration[0], y_up_cc, y_down_cc)
        handle_axis(z_mode, accelerometer.acceleration[2], z_up_cc, z_down_cc)