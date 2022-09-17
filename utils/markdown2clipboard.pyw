#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import codecs
import pyperclip
import unicodedata
from markdown_it import MarkdownIt
from mdit_py_plugins.tasklists import tasklists_plugin
from HTMLClipboard import GetHtml, PutHtml, DumpHtml

def markdown_to_html(markdown_text):
    md = (
        MarkdownIt()
        .use(tasklists_plugin)
        .enable('strikethrough')
        .enable('table'))
    # print(md.get_all_rules())
    return md.render("".join(markdown_text))


def markdown_to_clipboard(markdown_lines):
    pre_render_lines = []
    for line in markdown_lines:
        if line[0:2] == "| ":
            table_cells = line.split('|')
            markdown_cells = []
            for cell in table_cells:
                if not cell:
                    markdown_cells.append(cell)
                    continue

                if "{nl}" in cell:
                    #print("new line")
                    cell = cell.strip()
                    # cell = cell.replace("{nl}", "\n")
                    inline_lines = cell.split("{nl}")
                    cell = markdown_to_html(
                        [l + "\n" for l in inline_lines])

                    cell = cell.replace("\n", "")
                    markdown_cells.append(" " + cell + " ")
                else:
                    markdown_cells.append(cell)

            #print('orig line: ' + line)
            line = "|".join(markdown_cells)
            #print("mark line: " + line)

        pre_render_lines.append(line)

    html_body = markdown_to_html(pre_render_lines)

    html_body = html_body.replace(
        '<table style="', 'table style="border-collapse: collapse;')
    html_body = html_body.replace(
        '<td style="', '<td style="padding: 8px;border: 1px solid #dddfe1;')
    html_body = html_body.replace(
        '<th style="', '<th style="font-weight: bold;border: 1px solid #dddfe1;')
    html_body = html_body.replace(
        "<table>", '<table style="border-collapse: collapse;">')
    html_body = html_body.replace(
        "<td>", '<td style="padding: 8px;border: 1px solid #dddfe1;">')
    html_body = html_body.replace(
        "<th>", '<th style="font-weight: bold;border: 1px solid #dddfe1;">')

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

    markdown_text = pyperclip.paste()
    #markdown_text = unicodedata.normalize('NFKD', markdown_text)
    markdown_text = markdown_text.replace(u'\xa0', u' ')

    lines = markdown_text.splitlines(keepends=True)
    markdown_to_clipboard(lines)
    # PutHtml(html_body, markdown_text)
#    DumpHtml()
#    print(GetHtml())
