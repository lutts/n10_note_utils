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

"""
* item0(希望下级缩进2)

     text

* item1(希望下级缩进2)
  * item11(希望下级缩进4)

       item11 content1(希望下级缩进4)

       > item11 blockquote par1
       >
       > item11 blockquote par2

    * item111(希望下级缩进6)

      some text1111(希望下级缩进6)

    * item112(希望下级缩进6)

      * item1121(希望下级缩进8)

        item1121 content(希望下级缩进8)

    item11 content2(希望下级缩进4)

    * item1121

        item1121 content

    * item113
  * item12
    * item121
  * item13
* item2

  item2 content1

  > item2 blockquote par1
  >
  > item2 blockquote par2

  * item21
    * item211
      * item2111
        * item21111
    * item212
  * item22
  
normal text

> blockquote par1
>
>> blockquote par2
>
> blockquote par3

* another list
  * item1
"""

def normlize_clipboard():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    logging.debug("normalize clipboard for thebrain")
    raw_text = pyperclip.paste()

    if not raw_text:
        return

    processor = N10NoteProcessor(raw_text = raw_text)
    processor.process()

    logging.debug("normalized_lines")
    logging.debug(processor.normalized_lines)
    if processor.normalized_lines:
        processor.normalized_lines[-1] = processor.normalized_lines[-1].rstrip()

        list_markers_re = regex.compile(r'(?P<spaces>\s*)(?P<list_marker>(?:[*]|[0-9]+\.)[ ])(?P<item_content>.*)')
        leading_spaces_re = regex.compile(r'(?P<spaces>\s*)(?P<content>[^\s].*)')
        blockquote_re = regex.compile(r'(?P<quote_marker>>(?:$|[> ]*))(?P<content>.*)')

        # used to predict the indention of next level
        list_markers = []
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
                logging.debug("content:" + content)

                q = blockquote_re.match(content)
                if not q:
                    line = '\t' * level + content + '\n'
                else:
                    quote_marker = q.group('quote_marker')
                    quote_marker = quote_marker.replace('>', '> ')
                    quote_marker = ' '.join(quote_marker.split()) + ' '
                    line = '> ' * level + quote_marker + q.group('content') + '\n'
                
                list_marker = list_markers[0:level]
                
                thebrain_lines.append(line)
                continue

            thebrain_lines.append(line)

        pyperclip.copy("".join(thebrain_lines))

if __name__ == "__main__":
    normlize_clipboard()