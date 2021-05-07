import time
import usb_midi
import adafruit_midi
import adafruit_trellism4

from adafruit_midi.timing_clock import TimingClock
from adafruit_midi.start import Start
from adafruit_midi.stop import Stop
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn

midi = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], midi_out=usb_midi.ports[1], in_channel=0)

trellis = adafruit_trellism4.TrellisM4Express(rotation=90)

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
NOTE_ON = (0, 63, 63)
NOTE_OFF = (0, 0, 0)
COLUMN_COLOR = (255, 0, 50)
ACCENT = (0, 255, 225)
SHIFT_NOTE_ON = (0, 63, 63)
SHIFT_NOTE_OFF = (0, 0, 0)
SHIFT_COLUMN_COLOR = (255, 0, 50)
SHIFT_ACCENT = (0, 255, 225)

CORRECT_INDEX  =  [ 24, 16,  8, 0,
                    25, 17,  9, 1,
                    26, 18, 10, 2,
                    27, 19, 11, 3,
                    28, 20, 12, 4,
                    29, 21, 13, 5,
                    30, 22, 14, 6,
                    31, 23, 15, 7 ]

# note grid parameters
note_grid = []
shift_grid = []
STARTING_NOTE = 36
NUMBER_OF_COLUMNS = 4
NUMBER_OF_ROWS = 8
index = 0

for i in range(NUMBER_OF_COLUMNS):
    column = []
    note = STARTING_NOTE
    for j in range(NUMBER_OF_ROWS):
        column.append(Note(note, CORRECT_INDEX[index]))
        index += 1
        note += 1
    note_grid.append(column)
    
#print(list(map(lambda x: list(map(lambda y: y.index, x)), note_grid))) # prints note_grid to show notes

def reset_colors():
    for column in note_grid:
        for note in column:
            if note.isOn == True:
                trellis.pixels._neopixel[note.index] = NOTE_ON
            else:
                trellis.pixels._neopixel[note.index] = NOTE_OFF

def light_column(column):
    for i in range(NUMBER_OF_ROWS):
        trellis.pixels._neopixel[ column + (i*8) ] = COLUMN_COLOR
    
def reset_column(column):
    for note in note_grid[column]:
        if note.isOn:
            if note.isAccented:
                trellis.pixels._neopixel[note.index] = ACCENT
            else:
                trellis.pixels._neopixel[note.index] = NOTE_ON
        else:
            trellis.pixels._neopixel[note.index] = NOTE_OFF

def play_column(column):
    for note in note_grid[column]:
        note.play()

def stop_notes():
    map(lambda x: map(lambda y: y.stop(), x), note_grid)

#sync counters
ticks = 0
eighth_note = 0
bars = 0

#message placeholders
old_message = 0
last_press = 0
on = False

held_note = 0
tick_placeholder = 0
HOLD_TIME = 48 #in ticks
button_is_held = False

#modes
main_mode = True

while True:
    new_message = midi.receive()
    if new_message != old_message and new_message != None:

        if isinstance(new_message, TimingClock) and on:
            if ticks % 12 == 0:
                eighth_note += 1
                
                for i in range(8):
                    if eighth_note % 8 == i:
                        if i == 1:
                            bars += 1
                        if i == 0:
                            if main_mode:
                                light_column(7)
                                reset_column(6)
                            play_column(7)
                        else:
                            if main_mode:
                                light_column(i-1)
                                reset_column(i-2)
                            play_column(i-1)
            ticks += 1
            
            
        if isinstance(new_message, Start):
            on = True
            ticks = 0
            eighth_note = 0
            
        if isinstance(new_message, Stop):
            on = False
            reset_colors()
            stop_notes()

            
    old_message = new_message
    
    pressed_buttons = trellis.pressed_keys
    
    if pressed_buttons != last_press:
        if main_mode:
            if pressed_buttons:
                for note in note_grid[pressed_buttons[0][1]]:
                    if note.note == pressed_buttons[0][0] + STARTING_NOTE:
                        tick_placeholder = ticks
                        held_note = note
                        button_is_held = True
                        
            elif button_is_held:
                if ticks - tick_placeholder < HOLD_TIME:
                    trellis.pixels._neopixel[note.index] = NOTE_ON
                    held_note.toggle()
                    if held_note.isAccented:
                        held_note.toggle_accent()
                    button_is_held = False
                else:
                    if not held_note.isOn:
                        held_note.toggle()
                    held_note.toggle_accent()
            
            if len(pressed_buttons) > 1:
                print(pressed_buttons) # button combo
                main_mode = False
                button_is_held = False
        else:
            trellis.pixels._neopixel.fill((255, 0, 0))
        
    last_press = pressed_buttons
    