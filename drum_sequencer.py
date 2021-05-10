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
    def __init__(self, columns, rows, starting_note, correction):
            index = 0
            self.grid = []
            for i in range(columns):
                column = []
                note = starting_note
                for j in range(rows):
                    column.append(Note(note, correction[index]))
                    index += 1
                    note += 1
                self.grid.append(column)

class Cell:
    def __init__(self, index):
        self.index = index
        self.isOn = False
        
    def toggle(self):
        self.isOn = True if not self.isOn else False

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
        
#colors
NOTE_ON            = (0, 63, 63)
NOTE_OFF           = (0, 0, 0)
COLUMN_COLOR       = (255, 0, 50)
ACCENT             = (0, 191, 225)
SHIFT_NOTE_ON      = (63, 63, 0)
SHIFT_NOTE_OFF     = (0, 0, 0)
SHIFT_COLUMN_COLOR = (50, 0, 255)
SHIFT_ACCENT       = (255, 255, 0)
CC_MODE_COLOR      = (255, 191, 191)

CORRECT_INDEX  =  [ 24, 16,  8, 0,
                    25, 17,  9, 1,
                    26, 18, 10, 2,
                    27, 19, 11, 3,
                    28, 20, 12, 4,
                    29, 21, 13, 5,
                    30, 22, 14, 6,
                    31, 23, 15, 7 ]

# note grid parameters
STARTING_NOTE     = 36
NUMBER_OF_COLUMNS = 8
NUMBER_OF_ROWS    = 4

#button combonations
BACK_COMBO     = [(3, 0), (0, 0), (3, 7)]
CLEAR_COMBO    = [(3, 0), (0, 0), (3, 1)]
SHIFT_COMBO    = [(3, 0), (0, 0), (3, 2)]
EDIT_CC_COMBO  = [(3, 0), (0, 0), (3, 3)]
TOGGLE_X_COMBO = [(2, 0), (0, 0), (2, 1)]
TOGGLE_Y_COMBO = [(2, 0), (0, 0), (2, 2)]
TOGGLE_Z_COMBO = [(2, 0), (0, 0), (2, 3)]

notes = NoteGrid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE, CORRECT_INDEX)
shift = NoteGrid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE, CORRECT_INDEX)
cc_edit = Grid(8, 4, CORRECT_INDEX)

print(list(map(lambda x: list(map(lambda y: y.index, x)), cc_edit.grid))) # prints note grid to show notes

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


#sync counters
ticks = 0
eighth_note = 0
shift_note = 0
bars = 0

#message placeholders
old_message = 0
last_press = 0
on = False

held_note = 0
tick_placeholder = 0
HOLD_TIME = 48 #in ticks
button_is_held = False
combo_pressed = False

#modes
main_mode = True
shift_mode = False
cc_edit_mode = False
manual_note_mode = False
manual_cc_mode = False

send_x = True
send_y = True
send_z = True

x_cc = 14
y_cc = 15
z_cc = 23

while True:
    new_message = midi.receive()
    if new_message != old_message and new_message != None:

        if isinstance(new_message, TimingClock) and on:
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
            
            
        if isinstance(new_message, Start):
            on = True
            ticks = 0
            eighth_note = 0
            
        if isinstance(new_message, Stop):
            on = False
            reset_colors(notes, NOTE_ON, NOTE_OFF)
            stop_notes(notes)

            
    old_message = new_message
    
    pressed_buttons = trellis.pressed_keys
    
    if pressed_buttons != last_press:
        if main_mode:
            if pressed_buttons and not combo_pressed:
                for note in notes.grid[pressed_buttons[0][1]]:
                    if note.note == pressed_buttons[0][0] + STARTING_NOTE:
                        tick_placeholder = ticks
                        held_note = note
                        button_is_held = True
                        
            elif button_is_held:
                if ticks - tick_placeholder < HOLD_TIME:
                    trellis.pixels._neopixel[held_note.index] = NOTE_ON
                    held_note.toggle()
                    if held_note.isAccented:
                        held_note.toggle_accent()
                    button_is_held = False
                else:
                    if not held_note.isOn:
                        held_note.toggle()
                    held_note.toggle_accent()
            if not pressed_buttons:
                combo_pressed = False
            
            if len(pressed_buttons) > 2:
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
                else:
                    print(pressed_buttons)
                button_is_held = False
        
        elif shift_mode:
            if pressed_buttons and not combo_pressed:
                for note in shift.grid[pressed_buttons[0][1]]:
                    if note.note == pressed_buttons[0][0] + STARTING_NOTE:
                        tick_placeholder = ticks
                        held_note = note
                        button_is_held = True
                        
            elif button_is_held:
                if ticks - tick_placeholder < HOLD_TIME:
                    trellis.pixels._neopixel[held_note.index] = SHIFT_NOTE_ON
                    held_note.toggle()
                    if held_note.isAccented:
                        held_note.toggle_accent()
                    button_is_held = False
                else:
                    if not held_note.isOn:
                        held_note.toggle()
                    held_note.toggle_accent()
            if not pressed_buttons:
                combo_pressed = False
            
            if len(pressed_buttons) > 2:
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
        
        else:
            trellis.pixels._neopixel.fill((255, 0, 0))
        
    last_press = pressed_buttons
    
    if on:
        if send_x:
            midi.send(ControlChange(x_cc, int(scale(accelerometer.acceleration[1], (-10, 10), (0, 127)))))
        if send_y:
            midi.send(ControlChange(y_cc, int(scale(accelerometer.acceleration[0], (-10, 10), (0, 127)))))
        if send_z:
            midi.send(ControlChange(z_cc, int(scale(accelerometer.acceleration[2], (-10, 10), (0, 127)))))
