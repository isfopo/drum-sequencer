from classes import *
from functions import *
from constants import *

from math import floor
from board import ACCELEROMETER_SCL
from board import ACCELEROMETER_SDA
from busio import I2C
from json import loads
from json import dumps
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
    
"""
======== Global Variables ========
"""

midi = MIDI(midi_in=ports[0], midi_out=ports[1], in_channel=0, out_channel=0)
receive = midi.receive
trellis = TrellisM4Express(rotation=90)
i2c = I2C(ACCELEROMETER_SCL, ACCELEROMETER_SDA)
accelerometer = ADXL345(i2c)

neop = trellis.pixels._neopixel
fill = trellis.pixels.fill

current_slot = 0
[ notes, shift, last_step, axis_modes ] = read_save(
        current_slot,
        NoteGrid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE, midi.send),
        NoteGrid(NUMBER_OF_COLUMNS, NUMBER_OF_ROWS, STARTING_NOTE, midi.send)
    )
#TODO can notes and shift be combined into a single tuple?
#TODO can there be a third note grid to make a triplet/swing feel?
cc_edit = Grid(8, 4)
pattern_select = Grid(8, 4)

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
separate_manual_note_channel = False

row_offset = 0
column_offset = 0

mode = b'm'

manual_notes = []
prev_manual_notes = []
manual_cc = []
prev_manual_cc = []
toggled_cc = []

reset_colors(notes, neop, NOTE_ON)

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
                        stop_column(notes, i-2, NoteOff)
                        play_column(notes, i-1, NoteOn, NoteOff)
                        if mode == b'm':
                            move_column(i, notes, last_step, COLUMN_COLOR, NOTE_ON, ACCENT, neop, NOTE_OFF, row_offset, column_offset)
                eighth_note += 1           
            """
            Shift Grid
            """
            if ticks % 12 == 7: #TODO add shift here - should be change-able and save-able or a three grid thing
                for i in range(NUMBER_OF_COLUMNS):
                    if eighth_note % last_step == i:
                        stop_column(shift, i-2, NoteOff)
                        play_column(shift, i-1, NoteOn, NoteOff)
                        if mode == b's':
                            move_column(i, shift, last_step, SHIFT_COLUMN_COLOR, SHIFT_NOTE_ON, SHIFT_ACCENT, neop, NOTE_OFF, row_offset, column_offset)
                        
            ticks += 1
            
        """
        Start and Stop
        """
        if isinstance(new_message, Start):
            ticks = 0
            eighth_note = 0
            
        if isinstance(new_message, Stop):
            reset_colors(notes, neop, NOTE_ON, NOTE_OFF, row_offset, column_offset)
            stop_notes(notes, NoteOff)

            
    old_message = new_message
    
    """
    ======== Read Buttons ========
    """
    
    pressed_buttons = trellis.pressed_keys
    
    if pressed_buttons != last_press:
        """
        Main Mode
        """
        if mode == b'm' or mode == b's':
            if pressed_buttons and not combo_pressed:
                for note in notes.grid[pressed_buttons[0][1] + column_offset] if mode == b'm' else shift.grid[pressed_buttons[0][1] + column_offset]:
                    if note.note == pressed_buttons[0][0] + STARTING_NOTE + row_offset:
                        tick_placeholder = ticks
                        held_note = note
                        button_is_held = True
                        
            elif button_is_held:
                if ticks - tick_placeholder < HOLD_TIME:
                    if mode == b'm':
                        neop[held_note.index] = NOTE_ON if not held_note.is_on else NOTE_OFF
                    elif mode == b's':
                        neop[held_note.index] = SHIFT_NOTE_ON if not held_note.is_on else NOTE_OFF
                    held_note.toggle() #TODO something is slow here - there is a slight delay when a new note is added
                    if held_note.is_accented:
                        held_note.toggle_accent()
                    button_is_held = False
                else:
                    if not held_note.is_on:
                        if mode == b'm':
                            neop[held_note.index] = ACCENT if not held_note.is_accented else NOTE_OFF
                        elif mode == b's':
                            neop[held_note.index] = SHIFT_NOTE_ON if not held_note.is_on else NOTE_OFF
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
                    reset_colors(notes, neop, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons == SHIFT_MODE_COMBO:
                    reset_colors(shift if mode == b'm' else notes, neop, NOTE_ON if mode == b's' else SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    mode = b's' if mode == b'm' else b'm'
                
                elif pressed_buttons == EDIT_CC_COMBO:
                    mode = b'c'
                    reset_colors(cc_edit, neop, EDIT_CC_COLOR, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons == SELECT_SLOT_MODE:
                    mode = b'p'
                    fill(NOTE_OFF)
                    
                elif pressed_buttons == DELETE_SLOT_MODE:
                    mode = b'd'
                    fill(NOTE_OFF)
                    
                elif pressed_buttons == DELETE_ALL_SLOTS_MODE:
                    mode = b'da'
                    fill(NOTE_OFF)
                
                elif pressed_buttons[-2:] == OFFSET_CHANGE_MODE_COMBO: #FEAT light up available buttons
                    if len(pressed_buttons) > 2:
                        if pressed_buttons[0] == CHANGE_OFFSET[0]:
                            row_offset = increase_row_offset(row_offset, NUMBER_OF_ROWS)
                            reset_colors(notes if mode == b'm' else shift, neop, NOTE_ON if mode == b'm' else SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == CHANGE_OFFSET[1]:
                            row_offset = decrease_row_offset(row_offset)
                            reset_colors(notes if mode == b'm' else shift, neop, NOTE_ON if mode == b'm' else SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == CHANGE_OFFSET[2]:
                            column_offset = increase_column_offset(column_offset, NUMBER_OF_COLUMNS)
                            reset_colors(notes if mode == b'm' else shift, neop, NOTE_ON if mode == b'm' else SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                            
                        elif pressed_buttons[0] == CHANGE_OFFSET[3]:
                            column_offset = decrease_column_offset(column_offset)
                            reset_colors(notes if mode == b'm' else shift, neop, NOTE_ON if mode == b'm' else SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                    
                elif pressed_buttons[-2:] == MANUAL_CC_COMBO:
                    for cc in toggled_cc:
                        neop[press_to_light(cc[1])] = MANUAL_CC_COLOR
                    if len(pressed_buttons) > 2:
                        manual_cc = []
                        for button in pressed_buttons:
                            if button == MANUAL_CC_COMBO[0] or button == MANUAL_CC_COMBO[1]:
                                pass
                            else:
                                manual_cc.append((MANUAL_CC[button[0]][button[1]], button))
                    else:
                        manual_cc = []
                    for cc in manual_cc:
                        if cc not in prev_manual_cc:
                            if cc[1][0] <= 1:
                                midi.send(ControlChange(cc[0], 127))
                                neop[press_to_light(cc[1])] = MANUAL_CC_COLOR
                            if cc[1][0] >= 2:
                                if cc not in toggled_cc:
                                    toggled_cc.append(cc)
                                    midi.send(ControlChange(cc[0], 127))
                                    neop[press_to_light(cc[1])] = MANUAL_CC_COLOR
                                else:
                                    toggled_cc.remove(cc)
                                    midi.send(ControlChange(cc[0], 0))
                                    neop[press_to_light(cc[1])] = NOTE_OFF
                    for cc in prev_manual_cc:
                        if cc not in manual_cc:
                            if cc[1][0] <=1:
                                midi.send(ControlChange(cc[0], 0))
                                neop[press_to_light(cc[1])] = NOTE_OFF
                    prev_manual_cc = manual_cc
                    
                elif pressed_buttons[-2:] == MANUAL_NOTE_COMBO: 
                    if len(pressed_buttons) > 2:
                        manual_notes = []
                        for button in pressed_buttons:
                            if button == MANUAL_NOTE_COMBO[0] or button == MANUAL_NOTE_COMBO[1]:
                                pass
                            else:
                                manual_notes.append((MANUAL_NOTES[button[0]][button[1]], button))
                    else:
                        manual_notes = []
                    for note in manual_notes:
                        if note not in prev_manual_notes:
                            midi.send(NoteOn(note[0], 127), channel=1 if separate_manual_note_channel else 0)
                            neop[press_to_light(note[1])] = MANUAL_NOTE_COLOR_ALT if separate_manual_note_channel else MANUAL_NOTE_COLOR
                    for note in prev_manual_notes:
                        if note not in manual_notes:
                            midi.send(NoteOff(note[0], 0), channel=1 if separate_manual_note_channel else 0)
                            neop[press_to_light(note[1])] = NOTE_OFF
                    prev_manual_notes = manual_notes
                    
                elif pressed_buttons[-2:] == RECORD_NOTE_COMBO: 
                    if len(pressed_buttons) > 2:
                        manual_notes = []
                        for button in pressed_buttons:
                            if button == RECORD_NOTE_COMBO[0] or button == RECORD_NOTE_COMBO[1]:
                                pass
                            elif button[1] > 3: pass
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
                            neop[press_to_light(note[1])] = RECORD_NOTE_COLOR
                    for note in prev_manual_notes:
                        if note not in manual_notes:
                            midi.send(NoteOff(note[0], 0))
                            neop[press_to_light(note[1])] = NOTE_OFF
                    prev_manual_notes = manual_notes
                
                elif pressed_buttons == CHANGE_MANUAL_NOTE_CHANNEL_COMBO:
                    separate_manual_note_channel = False if separate_manual_note_channel else True
                
                elif pressed_buttons[-2:] == PATTERN_SHIFT_MODE_COMBO:
                    light_buttons(PATTERN_SHIFT_BUTTONS, PATTERN_SHIFT_COLOR, neop) #BUG lights are not resetting after release and are reset by column while held
                    if len(pressed_buttons) > 2:
                        if pressed_buttons[0] == PATTERN_SHIFT_BUTTONS[0]:
                            notes = shift_grid_left(notes)
                            shift = shift_grid_left(shift)
                            reset_colors(notes if mode == b'm' else shift, neop, NOTE_ON if mode == b'm' else SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                        elif pressed_buttons[0] == PATTERN_SHIFT_BUTTONS[1]:
                            notes = shift_grid_right(notes)
                            shift = shift_grid_right(shift)
                            reset_colors(notes if mode == b'm' else shift, neop, NOTE_ON if mode == b'm' else SHIFT_NOTE_ON, NOTE_OFF, row_offset, column_offset)
                
                elif pressed_buttons[-2:] == LAST_STEP_EDIT_COMBO:
                    light_buttons(LAST_STEP_BUTTONS, LAST_STEP_COLOR, neop)
                    if len(pressed_buttons) > 2:
                        last_step = handle_last_step_edit(last_step, pressed_buttons[0], LAST_STEP_BUTTONS, NUMBER_OF_COLUMNS)
                        if pressed_buttons[0] == LAST_STEP_BUTTONS[3]:
                            [notes.grid, shift.grid] = duplicate_measure((notes.grid, shift.grid))
                        
                else:
                    print(pressed_buttons)
                    
                button_is_held = False
                
                """
                Edit CC Mode
                """
        elif mode == b'c':
            handle_cc_grid(cc_edit, axis_modes, 2)
            reset_colors(cc_edit, neop, EDIT_CC_COLOR)
            
            if pressed_buttons and not combo_pressed:
                
                if pressed_buttons[0][1] == 0:
                    pass
                
                elif pressed_buttons[0][0] == 2:
                    axis_modes[0] = handle_select_mode(pressed_buttons[0][1])
                    row_off(cc_edit, 2)
                    handle_cc_lights(pressed_buttons, cc_edit, 2)
                    reset_colors(cc_edit, neop, EDIT_CC_COLOR)

                elif pressed_buttons[0][0] == 1:
                    axis_modes[1] = handle_select_mode(pressed_buttons[0][1])
                    row_off(cc_edit, 1)
                    handle_cc_lights(pressed_buttons, cc_edit, 1)
                    reset_colors(cc_edit, neop, EDIT_CC_COLOR)
                    
                elif pressed_buttons[0][0] == 0:
                    axis_modes[2] = handle_select_mode(pressed_buttons[0][1])
                    row_off(cc_edit, 0)
                    handle_cc_lights(pressed_buttons, cc_edit, 0)
                    reset_colors(cc_edit, neop, EDIT_CC_COLOR)
            
            """
            Edit CC Combos
            """
            if len(pressed_buttons) > 2:
                if pressed_buttons == EDIT_CC_COMBO:
                    mode = b'm'
                    reset_colors(notes, neop, NOTE_ON, NOTE_OFF, row_offset, column_offset)
                else:
                    print(pressed_buttons)
            if not pressed_buttons:
                combo_pressed = False
                
            """
            Pattern Select Mode
            """
        elif mode == b'p':
            slots = get_slots()
            light_slots(slots, SAVE_SLOT_COLOR, neop)
            neop[current_slot] = CURRENT_SLOT_COLOR
                
            if pressed_buttons and not combo_pressed:
                write_save(notes, shift, last_step, axis_modes)
                current_slot = press_to_light(pressed_buttons[0])
                [ notes, shift, last_step, axis_modes ] = read_save(current_slot, notes, shift)
                mode = b'm'
                
            if not pressed_buttons:
                combo_pressed = False
        
            """
            Pattern Delete Mode
            """
        elif mode == b'd':
            slots = get_slots()
            if slots: light_slots(slots, DELETE_SLOT_COLOR, neop)
            else: mode = b'm'
                
            if pressed_buttons and not combo_pressed and press_to_light(pressed_buttons[0]) in slots:
                remove("/{}.json".format(press_to_light(pressed_buttons[0])))
                mode = b'm'
                
            if not pressed_buttons:
                combo_pressed = False
        
            """
            Delete All Pattern Mode
            """
        elif mode == b'da':
            fill_yes_no(CONFIRM_COLOR, DECLINE_COLOR, neop)
            
            if pressed_buttons and not combo_pressed:
                if press_to_light(pressed_buttons[0]) < 16:
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
        handle_axes(axis_modes, accelerometer.acceleration, AXIS_CCS, ControlChange, midi)
    
    last_tick = ticks