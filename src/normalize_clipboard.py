#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import logging
import re
from note_processor import normalize_markdown_text
from clipboard_utils import clipboard_util
import css_inline


def do_normlize_clipboard(keep_last_end=False):
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    raw_text = clipboard_util.get_text()
    if not raw_text:
        return

    norm_text = normalize_markdown_text(raw_text, keep_last_end=keep_last_end)
    clipboard_util.put_text(norm_text)


def markdownify_convert(html):
    #md = markdownify(html, heading_style="ATX", strip=['a', 'style'])
    from markdownify import MarkdownConverter
    from bs4 import BeautifulSoup

    inliner = css_inline.CSSInliner()
    html = inliner.inline(html)

    soup = BeautifulSoup(html, "html.parser")
    els = soup.find_all(style=re.compile('font-style\s*:\s*italic'))
    if els:
        for node in els:
            node.name = "em"
    
    els = soup.find_all(style=re.compile('font-weight\s*:\s*(bold|[789][0-9]{2})'))
    if els:
        for node in els:
            node.name = "strong"
    
    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()
  
    return MarkdownConverter(heading_style="ATX", strip=['a']).convert_soup(soup)


def clipboard_html_to_markdown():
    html = clipboard_util.get_html()
    if not html:
        return

    md = markdownify_convert(html)
    md = normalize_markdown_text(md, no_bold_in_header=True)
    if md:
        clipboard_util.put_text(md)


if __name__ == "__main__":
    do_normlize_clipboard()