from functions import *
from constants import *

"""
======== Classes ========
"""

class Grid:
    __slots__ = ["grid"]
    def __init__(self, columns, rows):
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
        
    def play(self, note_on, note_off):
        self.stop(note_off)
        if self.is_on:
            self.send(note_on(self.note, 127 if self.is_accented else 96))
        
    def stop(self, note_off):
        if self.is_on:
            self.send(note_off(self.note, 0))
        
    def toggle_accent(self):
        self.is_accented = True if not self.is_accented else False