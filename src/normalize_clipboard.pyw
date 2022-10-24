#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import logging
import pyperclip

from n10_note import N10NoteProcessor

def normlize_clipboard():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    logging.debug("normalize clipboard")
    raw_text = pyperclip.paste()

    if not raw_text:
        return

    processor = N10NoteProcessor(raw_text = raw_text)
    processor.process()

    if processor.normalized_lines:
        processor.normalized_lines[-1] = processor.normalized_lines[-1].rstrip()
        pyperclip.copy("".join(processor.normalized_lines))


if __name__ == "__main__":
    normlize_clipboard()