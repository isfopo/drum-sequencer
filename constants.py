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
SAVE_SLOT_COLOR        = ( 191, 191,  11 )
DELETE_SLOT_COLOR      = ( 191,  11,  11 )
CONFIRM_COLOR          = (   0, 255,   0 )
DECLINE_COLOR          = ( 255,   0,   0 )
LAST_STEP_COLOR        = ( 255,  11, 191 )
PATTERN_SHIFT_COLOR    = ( 255,  11,  11 )

"""
Grid Parameters
"""
STARTING_NOTE     = const(36)
NUMBER_OF_COLUMNS = const(17)
NUMBER_OF_ROWS    = const(12) #TODO should be 16, but there are still memory allocation errors

"""
Button Combonations
"""
MANUAL_CC_COMBO                  = [(3, 4), (0, 4)]
MANUAL_NOTE_COMBO                = [(3, 4), (0, 5)]
CHANGE_MANUAL_NOTE_CHANNEL_COMBO = [(3, 4), (2, 4), (0, 5)] 
RECORD_NOTE_COMBO                = [(3, 5), (0, 5)]
CLEAR_COMBO                      = [(3, 0), (0, 0), (3, 1)]
SHIFT_MODE_COMBO                 = [(3, 0), (0, 0), (3, 2)]
EDIT_CC_COMBO                    = [(3, 0), (0, 0), (3, 3)]
OFFSET_CHANGE_MODE_COMBO         = [(3, 6), (0, 6)]
CHANGE_OFFSET                    = [(3, 4), (1, 4), (2, 5), (2, 3)]
PATTERN_SHIFT_MODE_COMBO         = [(3, 7), (0, 7)]
PATTERN_SHIFT_BUTTONS            = ((2, 4), (2, 6))
LAST_STEP_EDIT_COMBO             = [(2, 7), (0, 7)]
LAST_STEP_BUTTONS                = ((1, 3), (1, 4), (1, 5), (1, 6))
SELECT_SLOT_MODE                 = [(3, 0), (0, 0), (3, 4)]
DELETE_SLOT_MODE                 = [(3, 0), (0, 0), (2, 4)]
DELETE_ALL_SLOTS_MODE            = [(3, 0), (0, 0), (1, 4)]

"""
Integers
"""
HOLD_TIME = const(24) #in ticks

"""
Axis CCs
"""
AXIS_CCS = (3, 9, 14, 15, 20, 21)

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

MANUAL_NOTES      = ( ( 48, 44, 40, 36 ),
                      ( 49, 45, 41, 37 ),
                      ( 50, 46, 42, 38 ),
                      ( 51, 47, 43, 39 ) )

MANUAL_CC         = ( ( 22, 23, 24, 25 ),
                      ( 26, 27, 28, 29 ),
                      ( 30, 31, 85, 86 ),
                      ( 87, 88, 89, 90 ) )

