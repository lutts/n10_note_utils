#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import logging
import codecs
import pyperclip
import unicodedata

from markdown_utils import markdown_processor
from HTMLClipboard import GetHtml, PutHtml, DumpHtml


def markdown_to_clipboard(markdown_lines, onenote_mode=False):
    html_body = markdown_processor(onenote_mode).markdown_to_html_with_inline_style(markdown_lines)
    PutHtml(html_body, "".join(markdown_lines))


if __name__ == "__main__":
    def test_SimpleGetPutHtml():
        data = "<p>Writing to the clipboard is <strong>太简单了</strong> with this code.</p>"
        PutHtml(data)
        if GetHtml() == data:
            print("passed")
        else:
            print("failed")

    # test_SimpleGetPutHtml()
    # DumpHtml()

    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    logging.debug("markdown to clipboard")
    markdown_text = pyperclip.paste()
    #markdown_text = unicodedata.normalize('NFKD', markdown_text)
    markdown_text = markdown_text.replace(u'\xa0', u' ')

    lines = markdown_text.splitlines(keepends=True)
    markdown_to_clipboard(lines)