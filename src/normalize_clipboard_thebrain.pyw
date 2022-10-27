#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import logging
import pyperclip
import regex

from n10_note import N10NoteProcessor

def level_of_spaces(spaces, list_markers):
    if not spaces:
        return 0
    
    spaces_len = len(spaces)
    level = 0
    for markers in list_markers:
        spaces_len -= len(markers)
        if spaces_len < 0:
            break
        else:
            level += 1

    return level

def normlize_clipboard():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    logging.debug("normalize clipboard for thebrain")
    raw_text = pyperclip.paste()

    if not raw_text:
        return

    processor = N10NoteProcessor(raw_text = raw_text)
    processor.process()

    list_markers_re = regex.compile(r'(?P<spaces>\s*)(?P<list_marker>(?:[*]|[0-9]+\.)[ ])(?P<item_content>.*)')
    leading_spaces_re = regex.compile(r'(?P<spaces>\s+)(?P<content>[^\s].*)')

    list_markers = []

    logging.debug("normalized_lines")
    logging.debug(processor.normalized_lines)
    if processor.normalized_lines:
        processor.normalized_lines[-1] = processor.normalized_lines[-1].rstrip()

        thebrain_lines = []

        for line in processor.normalized_lines:
            #logging.debug("checking line: " + line)
            m = list_markers_re.match(line)
            if m:
                logging.debug("found list: ")
                logging.debug(line)
                spaces = m.group('spaces')
                list_marker = m.group('list_marker')
                item_content = m.group('item_content')
                level = level_of_spaces(spaces, list_markers)
                logging.debug("level: " + str(level))
                if level != 0:
                    line = '\t' * level + list_marker + item_content + '\n'
                    list_markers = list_markers[0:level]
                
                list_markers.append(list_marker)
                
                thebrain_lines.append(line)
                continue

            m = leading_spaces_re.match(line)
            if m:
                logging.debug("found line with leading spaces:")
                logging.debug(line)
                spaces = m.group('spaces')
                content = m.group('content')
                level = level_of_spaces(spaces, list_markers)
                logging.debug("level: " + str(level))
                if level != 0:
                    line = '\t' * level + content + '\n'
                
                thebrain_lines.append(line)
                continue

            thebrain_lines.append(line)

        pyperclip.copy("".join(thebrain_lines))

if __name__ == "__main__":
    normlize_clipboard()