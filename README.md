# Drum Sequencer for NeoTrellis M4

`drum-sequencer.py` contains the code for a **soon** full - featured drum machine that is designed to work with the Adafruit NeoTrellis M4 4x8 button grid. It is designed to receive MIDI sync messages and in turn play MIDI notes according to the buttons activated on the grid. Each column represents a different MIDI note, which can be mapped to an instrument or a drum hit in a DAW, and each row is an eighth-note, allowing a measure to be seen and modified at any given time.

The suggested DAW is Ableton, but should be able to work with any DAW that has MIDI in and out. In Ableton, be sure to have "Sync" in and out selected in the "Trellis M4 Express" MIDI Port and the "Trellis M4 Express" on the "MIDI From" selection on the track containing your drum rack.

## Basic Usage

With the correct MIDI I/O setup, the sequence will mirror your DAW's transport controls and stay in sync with the beat. Use different modes to edit the sequence.

## Modes

Different modes can be accessed by specific button combinations, listed below. Pressing these two buttons together will not cause a note to be added to the grid, but immediately switch to the mode selected.

### Main Mode

No combo is needed for this mode. This is the main grid of notes availible to you in the sequencer. To add a note, press the button in the row of the hit that you want and the column of the beat you want it to play at. The button for that note will light up. A long press will add an accented note and pressing the button again will remove it.

Each row corresonds to a MIDI note, stating at C1 at the bottom row and going up one note for every row. This can be shifted up 3 times, giving up access to notes up to D#2, four notes at a time. See changing offset. 

Each column corresopnds to an eighth-note step in the sequence, starting at the beginning of the measure. With all 8 columns, you have access to a full measure in 4/4 time. To access other measures, you need to adjust the last step and the offset. This can create a pattern of up to 4 measures.

### Shift Mode

|x| |x| | | | | |
|-|-|-|-|-|-|-|-|
| | | | | | | | |
| | | | | | | | |
|x| | | | | | | |

To enter "Shift Mode" press these 3 buttons at the same time. You will see the colors shift and the grid change to whatever notes are in the shift grid. This is another set of notes that wil play along with the main grid and work the same way, however these note are shifted over a 16th note. To exit this mode, press the same button combo.

### Edit CC Mode

|x| | |x| | | | |
|-|-|-|-|-|-|-|-|
| | | | | | | | |
| | | | | | | | |
|x| | | | | | | |

The NeoTrellis is equiped with a built-in accelrometer, which is able to send MIDI Control Change data to your DAW based on the position of the unit. The accelormoter tracks the X, Y and Z axes and will send CC data on CCs 3, 9, 14, 15, 20, 21 depending on the mode. There are 6 different modes, with the option of sending no CC data for the axis, and each axis can be set independenly. To select a CC mode while in the CC Edit Mode, press the buttons of the corresonding CC mode in either the second row for X, third row for Y or fourth row for Z.
- Direct Mode: in this mode, the CC value (0-127) directly correponds with the value of the axis.
