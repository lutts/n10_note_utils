#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import logging
from markdown_utils import markdown_processor, markdown_processor_mode
from clipboard_utils import clipboard_util

def markdown_to_clipboard():
    markdown_text = clipboard_util.get_text()
    #markdown_text = unicodedata.normalize('NFKD', markdown_text)
    markdown_text = markdown_text.replace(u'\xa0', u' ')

    lines = markdown_text.splitlines(keepends=True)
    html_body = markdown_processor().markdown_to_html_with_inline_style(lines)
    clipboard_util.put_html(html_body, "".join(lines))


if __name__ == "__main__":
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    logging.debug("markdown to clipboard")
    markdown_to_clipboard()
