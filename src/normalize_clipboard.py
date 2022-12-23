#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import logging
from note_processor import normalize_markdown_text
from clipboard_utils import clipboard_util

def do_normlize_clipboard():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    raw_text = clipboard_util.get_text()

    if not raw_text:
        return

    norm_text = normalize_markdown_text(raw_text)
    clipboard_util.put_text(norm_text)


if __name__ == "__main__":
    do_normlize_clipboard()