#!/user/bin/env python3 -tt
# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import sys
import os
import logging

from markdown_utils import markdown_processor
from n10_note import N10NoteProcessor

def main():
    # logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        logging.debug('no file selected\n')
        sys.exit(1)

    args = "".join(args)
    args = args.split("\n")

    logging.debug("###".join(args))

    if len(args) < 2:
        logging.debug("args len < 2")
        sys.exit(1)

    dirname = args[0]
    notes_filepath = None
    hand_notes_filepath = None

    logging.debug("dirname: " + dirname)
    
    for filename in args[1:]:
        logging.debug("filename: " + filename)
        fullpath = os.path.join(dirname, filename)
        if filename.endswith(".md"):
            markdown_processor().markdown_file_to_html_file(fullpath)
            continue
        elif '摘抄' in filename:
            notes_filepath = fullpath
        else:
            if not notes_filepath:
                notes_filepath = fullpath
            else:
                hand_notes_filepath = fullpath

    if notes_filepath:
        # only one file, it must be notes file
        if notes_filepath == hand_notes_filepath:
            hand_notes_filepath = None
        
        logging.debug("notes_filepath: " + notes_filepath)
        if hand_notes_filepath:
            logging.debug("hand_notes_filepath: " + hand_notes_filepath)

        try:
            processor = N10NoteProcessor(n10_notes_filepath=notes_filepath,
                                     hand_notes_filepath=hand_notes_filepath)
            processor.process()
            processor.write_block_list()
        except Exception as e:
            logging.error(str(e))

        logging.debug("process done")

# Main body
if __name__ == '__main__':
    main()
