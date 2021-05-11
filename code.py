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

midi = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1], in_channel=0)
trellis = adafruit_trellism4.TrellisM4Express(rotation=90)
i2c = busio.I2C(board.ACCELEROMETER_SCL, board.ACCELEROMETER_SDA)
accelerometer = adafruit_adxl34x.ADXL345(i2c)

"""
Classes
"""

class Grid: # a grid for on/off cells - use for editing modes
    def __init__(self, columns, rows, correction):
            index = 0
            self.grid = []
            for i in range(columns):
                column = []
                for j in range(rows):
                    column.append(Cell(correction[index]))
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
        self.isOn = False
        
    def toggle(self):
        self.isOn = True if not self.isOn else False
        
    def on(self):
        self.isOn = True
        
    def off(self):
        self.isOn = False

class Note:
    def __init__(self, note, index):
        self.note = note
        self.index = index
        self.isOn = False
        self.isAccented = False
        
    def play(self):
        self.stop()
        if self.isOn:
            midi.send(NoteOn(self.note, 127 if self.isAccented else 96))
        
    def stop(self):
        if self.isOn:
            midi.send(NoteOff(self.note, 0))
        
    def toggle(self):
        self.isOn = True if not self.isOn else False
        
    def toggle_accent(self):
        self.isAccented = True if not self.isAccented else False

"""
Functions
"""
def reset_colors(notes, note_on, note_off):
    for column in notes.grid:
        for note in column:
            if note.isOn == True:
                trellis.pixels._neopixel[note.index] = note_on
            else:
                trellis.pixels._neopixel[note.index] = note_off

def light_column(notes, column, column_color):
    for i in range(len(notes.grid[0])):
        trellis.pixels._neopixel[ column + (i*8) ] = column_color
    
def reset_column(notes, column, note_on, note_off, accent):
    for note in notes.grid[column]:
        if note.isOn:
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
            note.isOn = False
            
def scale(val, src, dst):
    output = ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]
    if output < dst[0]: return dst[0]
    if output > dst[1]: return dst[1]
    return output

def correct_index(index, i):
    return CORRECT_INDEX[index+((i%8)*4)]

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

def handle_select_mode(pressed_buttons):
    if pressed_buttons[0][1] == 1: return 'direct'
    if pressed_buttons[0][1] == 2: return 'flip'
    if pressed_buttons[0][1] == 3: return 'split'
    if pressed_buttons[0][1] == 4: return 'on_off'
    if pressed_buttons[0][1] == 5: return 'flip_on_off'
    if pressed_buttons[0][1] == 6: return 'split_on_off'
    else: return 'none'
   
"""
======== Constants ========
"""

"""
Colors
"""
NOTE_ON            = (0, 63, 63)
NOTE_OFF           = (0, 0, 0)
COLUMN_COLOR       = (255, 0, 50)
ACCENT             = (63, 191, 225)
SHIFT_NOTE_ON      = (63, 63, 0)
SHIFT_COLUMN_COLOR = (50, 0, 255)
SHIFT_ACCENT       = (255, 191, 63)
EDIT_CC_COLOR      = (255, 191, 191)

"""
Sets
"""
CORRECT_INDEX  =  [ 24, 16,  8, 0,
                    25, 17,  9, 1,
                    26, 18, 10, 2,
                    27, 19, 11, 3,
                    28, 20, 12, 4,
                    29, 21, 13, 5,
                    30, 22, 14, 6,
                    31, 23, 15, 7 ]

"""
Grid Parameters
"""
STARTING_NOTE     = 36
NUMBER_OF_COLUMNS = 16
NUMBER_OF_ROWS    = 8

"""
Button Combonations
"""
BACK_COMBO        = [(3, 0), (0, 0), (3, 7)]
CLEAR_COMBO       = [(3, 0), (0, 0), (3, 1)]
SHIFT_COMBO       = [(3, 0), (0, 0), (3, 2)]
EDIT_CC_COMBO     = [(3, 0), (0, 0), (3, 3)]
EDIT_CC_BACK      = [(3, 0), (3, 1), (3, 7)]
MANUAL_CC_COMBO   = [(3, 4), (0, 4)]
MANUAL_NOTE_COMBO = [(3, 4), (0, 5)]
TOGGLE_X_COMBO    = [(2, 0), (0, 0), (2, 1)]
TOGGLE_Y_COMBO    = [(2, 0), (0, 0), (2, 2)]
TOGGLE_Z_COMBO    = [(2, 0), (0, 0), (2, 3)]

HOLD_TIME = 48 #in ticks

"""
======== Global Variables ========
"""

"""
Grid Objects
"""
notes = NoteGrid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE)
shift = NoteGrid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE)
cc_edit = Grid(8, 4, CORRECT_INDEX)

print(list(map(lambda x: list(map(lambda y: y.index, x)), notes.grid))) # prints note grid to show notes

"""
Counters
"""
ticks = 0
eighth_note = 0
shift_note = 0
bars = 0

"""
Placeholders
"""
old_message = 0
last_press = 0
held_note = 0
tick_placeholder = 0

on = False
button_is_held = False
combo_pressed = False

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
x_mode = 'split_on_off'
y_mode = 'none'
z_mode = 'none'

"""
Axis cc's
"""
x_up_cc = 14
x_down_cc = 15
y_up_cc = 23 #TODO make sure these are unused
y_down_cc = 24
z_up_cc = 25
z_down_cc = 26

while True:
    
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
                eighth_note += 1
                
                for i in range(NUMBER_OF_COLUMNS):
                    if eighth_note % NUMBER_OF_COLUMNS == i:
                        if i == 1:
                            bars += 1
                        if i == 0:
                            if main_mode:
                                light_column(notes, 7, COLUMN_COLOR)
                                reset_column(notes, 6, NOTE_ON, NOTE_OFF, ACCENT)
                            play_column(notes, 7)
                        else:
                            if main_mode:
                                light_column(notes, i-1, COLUMN_COLOR)
                                reset_column(notes, i-2, NOTE_ON, NOTE_OFF, ACCENT)
                            play_column(notes, i-1)
                            
            """
            Shift Grid
            """
            if ticks % 12 == 6:
                shift_note += 1 
                
                for i in range(NUMBER_OF_COLUMNS):
                    if eighth_note % NUMBER_OF_COLUMNS == i:
                        if i == 1:
                            bars += 1
                        if i == 0:
                            if shift_mode:
                                light_column(shift, 7, SHIFT_COLUMN_COLOR)
                                reset_column(shift, 6, SHIFT_NOTE_ON, NOTE_OFF, SHIFT_ACCENT)
                            play_column(shift, 7)
                        else:
                            if shift_mode:
                                light_column(shift, i-1, SHIFT_COLUMN_COLOR)
                                reset_column(shift, i-2, SHIFT_NOTE_ON, NOTE_OFF, SHIFT_ACCENT)
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
            reset_colors(notes, NOTE_ON, NOTE_OFF)
            stop_notes(notes)

            
    old_message = new_message
    
    """
    Read Buttons
    """
    
    pressed_buttons = trellis.pressed_keys
    
    if pressed_buttons != last_press:
        """
        Main Mode
        """
        if main_mode:
            if pressed_buttons and not combo_pressed:
                for note in notes.grid[pressed_buttons[0][1]]:
                    if note.note == pressed_buttons[0][0] + STARTING_NOTE:
                        tick_placeholder = ticks
                        held_note = note
                        button_is_held = True
                        
            elif button_is_held:
                if ticks - tick_placeholder < HOLD_TIME:
                    trellis.pixels._neopixel[held_note.index] = NOTE_ON if not held_note.isOn else NOTE_OFF
                    held_note.toggle()
                    if held_note.isAccented:
                        held_note.toggle_accent()
                    button_is_held = False
                else:
                    if not held_note.isOn:
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
                    reset_colors(notes, NOTE_ON, NOTE_OFF)
                    
                elif pressed_buttons == SHIFT_COMBO:
                    main_mode = False
                    shift_mode = True
                    reset_colors(shift, SHIFT_NOTE_ON, NOTE_OFF)
                    
                elif pressed_buttons == TOGGLE_X_COMBO:
                    send_x = True if not send_x else False
                    
                elif pressed_buttons == TOGGLE_Y_COMBO:
                    send_y = True if not send_y else False
                    
                elif pressed_buttons == TOGGLE_Z_COMBO:
                    send_z = True if not send_z else False
                
                elif pressed_buttons == EDIT_CC_COMBO:
                    main_mode = False
                    edit_cc_mode = True
                    reset_colors(cc_edit, EDIT_CC_COLOR, NOTE_OFF)
                
                elif pressed_buttons[-2:] == MANUAL_CC_COMBO:
                    if len(pressed_buttons) > 2:
                        print(pressed_buttons[0])
                    
                elif pressed_buttons == MANUAL_NOTE_COMBO:
                    if len(pressed_buttons) > 2:
                        print(pressed_buttons[2])
                else:
                    print(pressed_buttons)
                button_is_held = False
        
            """
            Shift Mode
            """
        elif shift_mode:
            if pressed_buttons and not combo_pressed:
                for note in shift.grid[pressed_buttons[0][1]]:
                    if note.note == pressed_buttons[0][0] + STARTING_NOTE:
                        tick_placeholder = ticks
                        held_note = note
                        button_is_held = True
                        
            elif button_is_held:
                if ticks - tick_placeholder < HOLD_TIME:
                    trellis.pixels._neopixel[held_note.index] = SHIFT_NOTE_ON if not held_note.isOn else NOTE_OFF
                    held_note.toggle()
                    if held_note.isAccented:
                        held_note.toggle_accent()
                    button_is_held = False
                else:
                    if not held_note.isOn:
                        trellis.pixels._neopixel[held_note.index] = SHIFT_ACCENT if not held_note.isAccented else NOTE_OFF
                        held_note.toggle()
                    held_note.toggle_accent()
            if not pressed_buttons:
                combo_pressed = False
            
            """
            Shift Combos
            """
            if len(pressed_buttons) > 2: #TODO include mode combos here as well
                combo_pressed = True
                if pressed_buttons == BACK_COMBO:
                    main_mode = True
                    shift_mode = False
                    reset_colors(notes, NOTE_ON, NOTE_OFF)
                elif pressed_buttons == CLEAR_COMBO:
                    clear_grid(notes)
                    clear_grid(shift)
                    reset_colors(notes, NOTE_ON, NOTE_OFF)
                else:
                    print(pressed_buttons)
                button_is_held = False
    
            """
            Edit CC Mode
            """
        elif edit_cc_mode:
            if pressed_buttons and not combo_pressed:
 
                if pressed_buttons[0][0] == 2:
                    x_mode = handle_select_mode(pressed_buttons)

                if pressed_buttons[0][0] == 1:
                    y_mode = handle_select_mode(pressed_buttons)

                if pressed_buttons[0][0] == 0:
                    z_mode = handle_select_mode(pressed_buttons)
            
            """
            Edit CC Combos
            """
            if len(pressed_buttons) > 2:
                if pressed_buttons == EDIT_CC_BACK:
                    main_mode = True
                    edit_cc_mode = False
                    reset_colors(notes, NOTE_ON, NOTE_OFF)
                else:
                    print(pressed_buttons)
            if not pressed_buttons:
                combo_pressed = False
            
    last_press = pressed_buttons
    
    """
    Axis CC Send
    """
    if on:
        handle_axis(x_mode, accelerometer.acceleration[1], x_up_cc, x_down_cc)
        handle_axis(y_mode, accelerometer.acceleration[0], y_up_cc, y_down_cc)
        handle_axis(z_mode, accelerometer.acceleration[2], z_up_cc, z_down_cc)

