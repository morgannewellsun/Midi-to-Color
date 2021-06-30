# -*- coding: utf-8 -*-
"""
Created on Sat Jun 22 23:54:23 2019

@author: Morgan
"""

import mido
from PIL import Image, ImageDraw

def parse_midi(input_name, track_list = None, time_sig_track = 0):
    """
    Parses a MIDI file, returning a list of notes. 
    Each note is represented by a tuple:
        Midi note number (-1 for a bar line)
        Current key signature
        Start time (in quarter-notes, from beginning of song)
        End time (in quarter-notes, from beginning of song)
    
    Parameters
    ----------
    input_name : str
        Name of the input MIDI file.
    track_list : list of ints
        List of tracks to parse from the input MIDI file.
        If this is None, all tracks will be parsed.
    time_sig_track : int
        Track to use when reading time signatures to place bar lines.
    """
    
    midi = mido.MidiFile(input_name)

    note_last_on_time = []
    for i in range(128):
        note_last_on_time.append(0)
        
    note_list = []
    
    for i, track in enumerate(midi.tracks):
        
        accum_ticks = 0
        
        current_8ths_per_bar = 8
        last_bar_line_ticks = 0
        
        current_key_signature = 'C'
        
        if(track_list is None or i in track_list):
            for msg in track:
                
                accum_ticks += msg.time
                
                if(msg.type == "note_on" and msg.velocity != 0):
                    note_last_on_time[msg.note] = accum_ticks
                    
                elif(msg.type == "note_off" or 
                         (msg.type == "note_on" and msg.velocity == 0)):
                    
                    if(i == time_sig_track and 
                               accum_ticks >= last_bar_line_ticks 
                               + current_8ths_per_bar 
                               * midi.ticks_per_beat / 2):
                        last_bar_line_ticks +=  (current_8ths_per_bar
                                                * midi.ticks_per_beat / 2)
                        note_list.append((-1, -1, last_bar_line_ticks           \
                                          / midi.ticks_per_beat))
                        
                    note_list.append((
                            msg.note,
                            current_key_signature,
                            note_last_on_time[msg.note]/midi.ticks_per_beat,
                            accum_ticks/midi.ticks_per_beat))
                    
                elif(i == time_sig_track and msg.type == "time_signature"):
                    current_8ths_per_bar = msg.numerator * 8 / msg.denominator
                    
                elif(msg.type == "key_signature"):
                    current_key_signature = msg.key
                    
    return(note_list)

def sort_notes(note_list):
    """Returns a sorted copy of note_list with duplicates removed."""
    return sorted(list(dict.fromkeys(note_list)), key=lambda x:x[2]*1000+x[0])

def calculate_note_numbers(note_list, key_override = None):
    """
    Takes in a list of notes, and replaces the key signature (second
    element of each note tuple) with the note's jianpu number.
    
    Parameters
    ----------
    note_list : list of tuples
        List of notes to calculate jianpu numbers for.
    key_override : str
        If this is provided, all notes will be assumed to be in the
        given key.
    """
    note_list_numbered = []
    
    for note in note_list:
        if note[0] != -1:
            
            if(note[1] == 'C' or key_override == 'C'):
                offset = 0
            elif(note[1] == 'C#' or key_override == 'C#'
                     or note[1] == 'Db' or key_override == 'Db'):
                offset = 1
            elif(note[1] == 'D' or key_override == 'D'):
                offset = 2
            elif(note[1] == 'D#' or key_override == 'D#'
                     or note[1] == 'Eb' or key_override == 'Eb'):
                offset = 3
            elif(note[1] == 'E' or key_override == 'E'):
                offset = 4
            elif(note[1] == 'F' or key_override == 'F'):
                offset = 5
            elif(note[1] == 'F#' or key_override == 'F#'
                     or note[1] == 'Gb' or key_override == 'Gb'):
                offset = 6
            elif(note[1] == 'G' or key_override == 'G'):
                offset = 7
            elif(note[1] == 'G#' or key_override == 'G#'
                     or note[1] == 'Ab' or key_override == 'Ab'):
                offset = 8
            elif(note[1] == 'A' or key_override == 'A'):
                offset = 9
            elif(note[1] == 'A#' or key_override == 'A#'
                     or note[1] == 'Bb' or key_override == 'Bb'):
                offset = 10
            elif(note[1] == 'B' or key_override == 'B'):
                offset = 11
                
            num = (note[0]-offset) - ((note[0]-offset)//12)*12
            
            num_to_jianpu = { 0:1,
                              1:1.5,
                              2:2,
                              3:2.5,
                              4:3,
                              5:4,
                              6:4.5,
                              7:5,
                              8:5.5,
                              9:6,
                             10:6.5,
                             11:7}
            jianpu = num_to_jianpu[num]
            
            note_list_numbered.append((note[0], jianpu, note[2], note[3]))
            
        else:
            note_list_numbered.append(note)
            
    return note_list_numbered
    
def group_bars(note_list):
    """
    Returns a list of bars, where each bar is a list of notes. The 
    start and end times of each note are rescaled to units of bars, and
    expressed relative to the beginning of the current bar.
    
    Parameters
    ----------
    note_list : list of tuples
        List of notes to group into bars. 
    """
    bar_list = []
    current_bar = []
    current_bar_start_time = 0
    
    for raw_note in note_list:
        if raw_note[0] != -1:
            current_bar.append(raw_note)
        elif raw_note[0] == -1:
            quarter_notes_per_bar = raw_note[2] - current_bar_start_time
            current_bar_scaled = []
            for note in current_bar:
                current_bar_scaled.append((note[0],
                                           note[1],
                                           min([(note[2]
                                                 - current_bar_start_time)
                                                 / quarter_notes_per_bar, 1]),
                                           min([(note[3]
                                                 - current_bar_start_time)
                                                 / quarter_notes_per_bar, 1])))
                
            bar_list.append(current_bar_scaled)
            current_bar = []
            current_bar_start_time = raw_note[2]
            
    return bar_list

def group_pages(bar_list, bars_per_line, lines_per_page):
    """Groups bar_list into lines and pages."""
    
    page_list = []
    page = []
    line = []
    
    for bar in bar_list:
        if len(line) < bars_per_line:
            line.append(bar)
        else:
            if len(page) < lines_per_page:
                page.append(line)
            else:
                page_list.append(page)
                page = []
            line = []
            line.append(bar)
    return page_list

def calculate_grid_points(size, buffer, bars_per_line, lines_per_page):
    """
    Calculates and returns two lists.
    The first list consists of x-coordinates of all bar lines.
    The second list consists of y-coordinates of all center staff lines.
    
    Parameters
    ----------
    size : 2-tuple of ints
        Pixel size of the output image (X,Y).
    buffer : int
        Size of white space on all sides of the output image, in pixels.
    bars_per_line : int
    lines_per_page : int
    """
    x_list = []
    y_list = []
    for i in range(bars_per_line + 1):
        x_list.append(buffer + i * (size[0]-2*buffer) / bars_per_line)
    for i in range(lines_per_page):
        y_list.append(buffer 
                      + ((size[1]-2*buffer) / lines_per_page)/2
                      + i*(size[1]-2*buffer) / lines_per_page)
    return x_list, y_list
    
def generate_blank_page(size, 
                        buffer, 
                        staff_line_spacing, 
                        bar_line_width,
                        staff_line_width,
                        num_staff_lines,
                        bars_per_line, 
                        lines_per_page):
    """
    Generates and returns a blank PIL Image with specified size,
    with bar and staff lines drawn.
    
    Parameters
    ----------
    size : 2-tuple of ints
        Pixel size of the output image (X,Y).
    buffer : int
        Size of white space on all sides of the output image, in pixels.
    staff_line_spacing : int
        Number of pixels between staff lines.
    bar_line_width : int
        Pixel line width of bar lines.
    staff_line_width : int
        Pixel line width of staff lines.
    num_staff_lines : int
        Number of staff lines to draw.
    bars_per_line : int
    lines_per_page : int
    """
    
    num_staff_lines = num_staff_lines - 1
    
    image = Image.new('RGB', size, color = "white")
    draw = ImageDraw.Draw(image)
    
    x_list, y_list = calculate_grid_points(size, 
                                           buffer, 
                                           bars_per_line, 
                                           lines_per_page)
    
    for y in y_list:
        for y_line in range(int(y-(num_staff_lines*staff_line_spacing/2)),
                            int(y+(num_staff_lines*staff_line_spacing/2)) + 1,
                            int(staff_line_spacing)):
            draw.line([(buffer, y_line), (size[0]-buffer, y_line)],
                       fill="#c6c6c6",
                       width=staff_line_width)
            
    for x in x_list:
        draw.line([(x, buffer), (x, size[1]-buffer)],
                   fill="black",
                   width=bar_line_width)

    return image

def draw_bar(size, 
             buffer, 
             staff_line_spacing, 
             bars_per_line, 
             image,
             bar,
             x, 
             y,
             higher_higher, 
             center=60):
    """
    Draws notes for a single bar.
    
    Parameters
    ----------
    size : 2-tuple of ints
        Pixel size of the output image (X,Y).
    buffer : int
        Size of white space on all sides of the output image, in pixels.
    staff_line_spacing : int
        Number of pixels between staff lines.
    bars_per_line : int
    image : PIL Image
        Image to draw on.
    bar : list of notes
        Bar to draw.
    x : int
        x-coordinate which marks the horizontal beginning of the bar.
    y : int
        y-coordinate which marks the vertical center of the bar.
    higher_higher : bool
        If higher notes are higher on the staff.
    
    Keyword Parameters
    ------------------
    center=60 : int
        MIDI note number at the center of the staff.
    """
    draw = ImageDraw.Draw(image)
    
    bar_width = (size[0] - 2*buffer) / bars_per_line
    direction = 2*higher_higher - 1
    
    color_dict = {
            1 : "DodgerBlue",
            2 : "Green",
            3 : "Yellow",
            4 : "Orange",
            5 : "Red",
            6 : "Magenta",
            7 : "Purple",
            1.5 : "Teal",
            2.5 : "GreenYellow",
            4.5 : "OrangeRed",
            5.5 : "Crimson",
            6.5 : "DarkViolet"}
    
    for note in bar:
        note_y_relative = (
                direction 
                * (center - note[0]) 
                * staff_line_spacing / 2)
        note_y = note_y_relative + y
        note_x_start = x + bar_width * note[2]
        note_x_end = x + bar_width * note[3]
        color = color_dict[note[1]]
        draw.line(
                [(note_x_start, note_y), (note_x_end, note_y)],
                fill = color,
                width = staff_line_spacing)
    return image
    
def draw_page_bars(
        size, 
        buffer, 
        staff_line_spacing, 
        bars_per_line, 
        lines_per_page, 
        image,
        page,
        higher_higher, 
        center=60):
    """
    Draws all bars on a page.
    """
    x_list, y_list = calculate_grid_points(size, 
                                           buffer, 
                                           bars_per_line, 
                                           lines_per_page)
    for x in range(len(x_list) - 1):
        for y in range(len(y_list)):
            image = draw_bar(
                    size, 
                    buffer, 
                    staff_line_spacing, 
                    bars_per_line, 
                    image, 
                    page[y][x], 
                    x_list[x], 
                    y_list[y], 
                    higher_higher)
    
    return image

def create_page(size, buffer, staff_line_spacing, bar_line_width, staff_line_width, num_staff_lines, bars_per_line, lines_per_page, page, higher_higher):
    image = generate_blank_page(size, buffer, staff_line_spacing*6, bar_line_width, staff_line_width, num_staff_lines, bars_per_line, lines_per_page)
    image = draw_page_bars(size, buffer, staff_line_spacing, bars_per_line, lines_per_page, image, page, higher_higher)
    return image

if __name__ == "__main__":
    output_str = "flowerdance_"
    note_list = parse_midi("flowerdance.mid")
    note_list = sort_notes(note_list)
    note_list = calculate_note_numbers(note_list)
    bar_list = group_bars(note_list)
    page_list = group_pages(bar_list, 4, 5)
    for i in range(len(page_list)):
        page = page_list[i]
        image = create_page((2550,3300), 150, 15, 7, 4, 5, 4, 5, page, True)
        image.save(output_str + str(i) + ".PNG", "PNG")
    









