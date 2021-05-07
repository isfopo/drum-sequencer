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

class Grid:
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
STARTING_NOTE = 36
NUMBER_OF_COLUMNS = 8
NUMBER_OF_ROWS = 4

#button combonations
CLEAR_COMBO = [(3, 0), (0, 0), (3, 1)]

notes = Grid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE, CORRECT_INDEX)
shift = Grid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE, CORRECT_INDEX)

#print(list(map(lambda x: list(map(lambda y: y.index, x)), notes.grid))) # prints note_grid to show notes

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
combo_pressed = False

#modes
main_mode = True
shift_mode = False

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
                                light_column(notes, 7, COLUMN_COLOR)
                                reset_column(notes, 6, NOTE_ON, NOTE_OFF, ACCENT)
                            play_column(notes, 7)
                        else:
                            if main_mode:
                                light_column(notes, i-1, COLUMN_COLOR)
                                reset_column(notes, i-2, NOTE_ON, NOTE_OFF, ACCENT)
                            play_column(notes, i-1)
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
                    trellis.pixels._neopixel[note.index] = NOTE_ON
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
                print(pressed_buttons) # 3 button combos will help against acciental combos
                combo_pressed = True
                if pressed_buttons == CLEAR_COMBO:
                    clear_grid(notes)
                    reset_colors(notes, NOTE_ON, NOTE_OFF)
                else:
                    main_mode = False
                button_is_held = False
        else:
            trellis.pixels._neopixel.fill((255, 0, 0))
        
    last_press = pressed_buttons
    
