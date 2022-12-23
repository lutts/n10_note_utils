
import time
import re
from clipboard_utils import clipboard_util
import keyboard
from clipboard_monitor import py_clipboard_monitor
from note_processor import normalize_markdown_text


def markdownify_convert(html, **options):
    #md = markdownify(html, heading_style="ATX", strip=['a', 'style'])

    from markdownify import MarkdownConverter
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()
  
    return MarkdownConverter(**options).convert_soup(soup)


def copy_html_as_markdown():
    success = clipboard_util.put_text("")
    keyboard.send("ctrl+c")
    if success:
        html = py_clipboard_monitor.wait_for_change(1, content_getter=clipboard_util.get_html)
    else:
        time.sleep(0.1)
        html = clipboard_util.get_html()

    if html:
        md = markdownify_convert(html, heading_style="ATX", strip=['a'])
        md = normalize_markdown_text(md, no_bold_in_header=True)
        if md:
            clipboard_util.put_text(md)
