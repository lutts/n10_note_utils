
import time
import re
from clipboard_utils import clipboard_util
import keyboard
from clipboard_monitor import py_clipboard_monitor
from note_processor import RawNoteProcessor


def copy_html_to_markdown():
    from markdownify import markdownify

    success = clipboard_util.put_text("")
    keyboard.send("ctrl+c")
    if success:
        html = py_clipboard_monitor.wait_for_change(1, content_getter=clipboard_util.get_html)
    else:
        time.sleep(0.1)
        html = clipboard_util.get_html()

    if html:
        md = markdownify(html, heading_style="ATX", strip=['a'])
        processor = RawNoteProcessor(md)
        processor.process()

        header_re = re.compile(r'^#{1,6} ')
        bold_re = re.compile(r'(\*\*)(.*?)(\*?)\1')

        markdown_lines = [bold_re.sub(r'\2\3', line) if header_re.match(line) else line
                          for line in processor.markdown_lines]

        clipboard_util.put_text(''.join(markdown_lines))
