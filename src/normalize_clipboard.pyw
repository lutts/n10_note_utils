#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import logging
from n10_note import N10NoteProcessor
from clipboard_utils import clipboard_util

def normlize_clipboard():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    logging.debug("normalize clipboard")
    raw_text = clipboard_util.get_text()

    if not raw_text:
        return

    processor = N10NoteProcessor(raw_text = raw_text)
    processor.process()

    if processor.normalized_lines:
        processor.normalized_lines[-1] = processor.normalized_lines[-1].rstrip()
        clipboard_util.put_text("".join(processor.normalized_lines))


if __name__ == "__main__":
    normlize_clipboard()