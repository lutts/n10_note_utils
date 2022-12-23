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


def markdownify_convert(html, **options):
    #md = markdownify(html, heading_style="ATX", strip=['a', 'style'])

    from markdownify import MarkdownConverter
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()
  
    return MarkdownConverter(**options).convert_soup(soup)


def clipboard_html_to_markdown():
    html = clipboard_util.get_html()
    if not html:
        return

    md = markdownify_convert(html, heading_style="ATX", strip=['a'])
    md = normalize_markdown_text(md, no_bold_in_header=True)
    if md:
        clipboard_util.put_text(md)


if __name__ == "__main__":
    do_normlize_clipboard()