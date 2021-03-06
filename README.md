# Drum Sequencer for NeoTrellis M4

`drum-sequencer.py` contains the code for a full - featured drum machine that is designed to work with the Adafruit NeoTrellis M4 4x8 button grid. It is designed to receive MIDI sync messages and in turn play MIDI notes according to the buttons activated on the grid. Each column represents a different MIDI note, which can be mapped to an instrument or a drum hit in a DAW, and each row is an eighth-note, allowing a measure to be seen and modified at any given time.

The suggested DAW is Ableton, but should be able to work with any DAW that has MIDI in and out. In Ableton, be sure to have "Sync" in and out selected in the "Trellis M4 Express" MIDI Port and the "Trellis M4 Express" on the "MIDI From" selection on the track containing your drum rack.

## Basic Usage

With the correct MIDI I/O setup, the sequence will mirror your DAW's transport controls and stay in sync with the beat. Use different modes to edit the sequence.

## Modes

Different modes can be accessed by specific button combinations, listed below. Pressing these two buttons together will not cause a note to be added to the grid, but immediately switch to the mode selected.

### Main Mode

No combo is needed for this mode. This is the main grid of notes available to you in the sequencer. To add a note, press the button in the row of the hit that you want and the column of the beat you want it to play at. The button for that note will light up. A long press will add an accented note and pressing the button again will remove it.

Each row corresponds to a MIDI note, stating at C1 at the bottom row and going up one note for every row. This can be shifted up 3 times, giving up access to notes up to D#2, four notes at a time. See changing offset.

Each column corresponds to an eighth-note step in the sequence, starting at the beginning of the measure. With all 8 columns, you have access to a full measure in 4/4 time. To access other measures, you need to adjust the last step and the offset. This can create a pattern of up to 4 measures.

### Shift Mode

| x   |     | x   |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     |     |
|     |     |     |     |     |     |     |     |
| x   |     |     |     |     |     |     |     |

To enter "Shift Mode" press these 3 buttons at the same time. You will see the colors shift and the grid change to whatever notes are in the shift grid. This is another set of notes that wil play along with the main grid and work the same way, however these note are shifted over a 16th note. To exit this mode, press the same button combo.

### Clear

| x   | x   |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     |     |
|     |     |     |     |     |     |     |     |
| x   |     |     |     |     |     |     |     |

Pressing this combination will remove all notes on both the main and shift grids, leaving you with a blank slate.

### Edit CC Mode

| x   |     |     | x   |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     |     |
|     |     |     |     |     |     |     |     |
| x   |     |     |     |     |     |     |     |

The NeoTrellis is equipped with a built-in accelerometer, which is able to send MIDI Control Change data to your DAW based on the position of the unit. The accelerometer tracks the X, Y and Z axes and will send CC data on CCs 3, 9, 14, 15, 20, 21 depending on the mode. There are 6 different modes, with the option of sending no CC data for the axis, and each axis can be set independency. To select a CC mode while in the CC Edit Mode, press the buttons of the corresponding CC mode in either the second row for X, third row for Y or fourth row for Z. To exit this mode, press the same button combo.

- Direct Mode:
  - the CC value (0-127) directly corresponds with the value of the axis.
  - CCs: X - 3, Y - 14, Z - 20
  - 2nd column
- Flip Mode:
  - the CC value (0-127) corresponds negatively with the value of the axis.
  - CCs: X - 3, Y - 14, Z - 20
  - 3rd column
- Split Mode:
  - the axis is split in two, above halfway will send data on one CC, below the other.
  - CCs: X - 3 and 4, Y - 14 and 15, Z - 20 and 21
  - 4th column
- On Off Mode:
  - the CC value is either 0 or 127 depending on the half of the axis.
  - CCs: X - 3, Y - 14, Z - 20
  - 5th column
- On Off Flip Mode:
  - the CC value is either 0 or 127 depending on the half of the axis but flipped from "On Off Mode".
  - CCs: X - 3, Y - 14, Z - 20
  - 6th column
- On Off Split Mode:
  - the CC value is either 0 or 127, but split at half of the axis.
  - CCs: X - 3 and 4, Y - 14 and 15, Z - 20 and 21
  - 7th column
- None:
  - no CC data will be sent for this axis.
  - 8th column

### Manual Note Mode

| D#3 | B2  | G2  | D#2 | x   |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D3  | A#2 | F#2 | D2  |     |     |     |     |
| C#3 | A2  | F2  | C#2 |     |     |     |     |
| C3  | G#2 | E2  | C2  |     | x   |     |     |

Holding the two button marked with an "x" and any button on the left half of the grid will result in a Midi note of the corresponding value to be triggered. Because there is the pads are not velocity sensitive, all note on events will have velocity of 127 when the button is pressed and 0 when it is released. Buttons should light up when played. This is a momentary mode and will no longer be in effect when the two buttons are released.

### Change Manual Note Channel

|     |     |     |     | x   |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     | x   |     |     |     |
|     |     |     |     |     |     |     |     |
|     |     |     |     |     | x   |     |     |

This combination toggles if notes played in manual note mode are played in the same channel as the main sequence (channel 1 by default) or in a different channel (channel 2).

### Record Note Mode

| D#3 | B2  | G2  | D#2 |     | x   |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D3  | A#2 | F#2 | D2  |     |     |     |     |
| C#3 | A2  | F2  | C#2 |     |     |     |     |
| C3  | G#2 | E2  | C2  |     | x   |     |     |

This mode work similarly to manual note mode - hold down the two buttons and press the left half to trigger a note - however playing a note in this will also add it to the sequence, quantized to the beat you played it on.

### Manual CC Mode

| 22  | 23  | 24  | 25  | x   |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 26  | 27  | 28  | 29  |     |     |     |     |
| 30  | 31  | 85  | 86  |     |     |     |     |
| 87  | 88  | 89  | 90  | x   |     |     |     |

Holding the two buttons marked with an "x" and any button on the left half of the grid will result in a Midi note of the corresponding value to be triggered. The top half of the left half toggle between 0 and 127, the rest are momentary, sending 127 on press and 0 on release.

### Select Slot Mode

| x   |     |     |     | x   |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     |     |
|     |     |     |     |     |     |     |     |
| x   |     |     |     |     |     |     |     |

This mode allows you to switch between and save different patterns. A pattern can be saved in 16 different slots, represented by the 16 buttons on the left side of the board. To switch patterns, enter this mode and press any of the slot buttons, causing the pattern to be played instantly. A slot that is empty, with no pattern in it, is not lit, whereas if there is a pattern in the slot it is lit. Switching to any other slot will cause the current pattern to be saved in the current slot.

### Delete Slot Mode

| x   |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     | x   |     |     |     |
|     |     |     |     |     |     |     |     |
| x   |     |     |     |     |     |     |     |

This mode allows you to delete a pattern that has been previously saved. In this mode, the slots will light up red, indicating that you will delete this slot. After selecting a slot to delete, you will return to the Main Mode.

### Delete All Slots Mode

| x   |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     |     |
|     |     |     |     | x   |     |     |     |
| x   |     |     |     |     |     |     |     |

This mode allows you to delete all of the slots save on the device. If this mode is engaged, the grid will light up with green and red lights. If you press any green light, all slots will be deleted. If you press the red, nothing will happen. Either selecting will return you to the Main Mode.

### Change Offset Mode

|     |     |     |     | ^   |     | x   |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     | <   |     | >   |     |     |
|     |     |     |     | v   |     |     |     |
|     |     |     |     |     |     | x   |     |

This mode changes the parts of the sequence the visible grid represents. This mode, like a few others, works in two parts. First, hold the two button marked with x's, then press any of the the buttons marked with up, down, left or right carets. 

Up and down will allow you to shift up and down four rows, changing the visible grid to the next or previous four midi notes, if pressing up, or the previous four notes. This will not extend beyond notes C2 to D3#.

Left and right will shift left and right eight columns, changing the visible grid to the next or previous measure, given that you are in 4/4 time. If another measure is not within the last step, the grid will not change.

### Pattern Shift Mode

|     |     |     |     |     |     |     | x   |
| --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     | <   |     | >   |     |
|     |     |     |     |     |     |     |     |
|     |     |     |     |     |     |     | x   |

This mode allows you to shift the entire pattern by eighth notes either forwards or back. To do so, hold the two buttons marked by x's, then press either the button marked left or right. Left will shift the pattern back one eighth note, with the first eighth note wrapping around to the end, and right will shift the pattern forward one eighth note, with the last eighth note wrapping around to the first.


### Last Step Mode

|     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     | x   |
|     |     |     | <<  | <   | >   | >>  |     |
|     |     |     |     |     |     |     | x   |

This mode allows you to edit the last step, or the last eighth note before the pattern repeats, of the pattern. This will allow for odd time signatures or isometric rhythms. To do so, hold the two buttons marked by x's, then press the buttons marked by carets. 

The buttons to the left will shorten then pattern. The single caret will shorten the pattern by one step, or eighth note, and the double caret will shorten the pattern by a measure. The shortest the pattern can be is a single eighth note. 

Conversely, the buttons to the right will lengthen the pattern in the same manner. The single caret will extend the pattern by one step and the double caret will extend the pattern by a measure. The longest a pattern can be is four measures. 
