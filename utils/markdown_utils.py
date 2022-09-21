# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import sys
import os
import logging
import re
#import markdown
#import markdown2
#from markdown_checklist.extension import ChecklistExtension
#import mistletoe
from markdown_it import MarkdownIt
from mdit_py_plugins.tasklists import tasklists_plugin
import hanzi
import css_inline


def uniqe_name(expect_path):
    filename, extension = os.path.splitext(expect_path)
    counter = 1

    while os.path.exists(expect_path):
        expect_path = filename + "(" + str(counter) + ")" + extension
        counter += 1

    return expect_path


# def render_markdown_with_py_markdown(markdown_text):
#    return markdown.markdown("".join(markdown_text), encoding='utf-8',
#                             extensions=['tables', ChecklistExtension()])


# def render_markdown_with_mistletoe(markdown_text):
#    return mistletoe.markdown(markdown_text)

class markdown_processor:
    """
    standard commonmark parser with some additional features

    additinal features
    ------------------
    * remove unneeded whitespaces
    * emphasis normalizer
    * add a space after some punctuations if there's no one
    """

    css_style = """
        <style>
        blockquote {
            margin-top: 10px;
            margin-bottom: 10px;
            margin-left: 15px;
            padding-left: 15px;
            border-left: 3px solid #ccc;
            }
        table {
            display: table;
            margin-bottom: 1em;
            border-collapse: collapse;
        }
        th, td {
            padding: 5px 10px;
        }
        table thead th {
            font-weight: bold;
            border: 1px solid;
        }
        table tbody td {
            border: 1px solid;
        }
        </style>
    """

    english_punctuation = r'!"#$%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~'

    heading_whitespaces_re = re.compile(r" +")
    emphasis_normalizer_re = re.compile(
        r'(?P<left>\*{1,2})(?P<word1>.+?)(?P<punc1>\(|（|\[|【|<|《)(?P<word2>.+?)(?P<punc2>\)|）|\]|】|>|》)(?P<right>\*{1,2})')
    space_after_punc_re = re.compile(
        r'(?P<punc>\.|,|;|:|\?|\!)(?P<word>[^' + english_punctuation + hanzi.punctuation + r'\s]+)')
    img_link_re = re.compile(r'(?P<linkhead>!{,1}\[.*\]\(<{,1})(?P<linkurl>.*?)(?P<linktail>>{,1}\)|>{,1} ".*?"\))')
    double_brace_re = re.compile(r'(?P<b>\{|\})')
    code_fence_re = re.compile(r' {,3}(`{3,}|~{3,})(.*)')

    def __init__(self):
        pass

    def render_markdown_with_parser(self, markdown_lines):
        """
        convert markdown to html with a parser

        Parameters
        -----------
        markdown_lines : iterable of markdown lines **with line breaks**
        """

        md = (
            MarkdownIt()
            .use(tasklists_plugin)
            .enable('strikethrough')
            .enable('table'))
        logging.debug(md.get_all_rules())

        return md.render("".join(markdown_lines))


    def normalize_markdown_line(self, line):
        heading_spaces = ""
        m = self.heading_whitespaces_re.match(line)
        if m:
            heading_spaces = m.group()

        # indented code block, return the orignal line
        if len(heading_spaces) >= 4:
            return line

        # markdownlint: no trailing spaces
        striped_line = line.rstrip()

        image_or_links = self.img_link_re.findall(striped_line)
        if image_or_links:
            image_or_links = ["".join(i) for i in image_or_links]
            striped_line = self.double_brace_re.sub(r'\1\1', striped_line)
            striped_line = self.img_link_re.sub('{}', striped_line)

        # test string: 'a.string,has;no:space?after   punctuation!another, string; has: space? after puctuation! ok!'
        # multiple space between word reduce to one only
        reduced_line = " ".join(striped_line.split())
        striped_line = heading_spaces + reduced_line

        # add a space after some punctuations if there's no one
        striped_line = self.space_after_punc_re.sub(r'\1 \2', striped_line)

        striped_line = self.emphasis_normalizer_re.sub(
                    '\g<left>\g<word1>\g<left>\g<punc1>\g<left>\g<word2>\g<right>\g<punc2>', striped_line)

        if image_or_links:
            striped_line = striped_line.format(*image_or_links)

        return heading_spaces + striped_line + "\n"


    def process_newline_in_table_cell(self, markdown_line):
        if markdown_line.startswith("| "):
            table_cells = markdown_line.split('|')
            #logging.debug("table cells: " + str(table_cells))
            markdown_cells = []
            for cell in table_cells:
                if not cell:
                    markdown_cells.append(cell)
                    continue

                if "{nl}" in cell:
                    logging.debug(
                        "custom new line in table cell found: " + cell)
                    cell = cell.strip()
                    inline_lines = cell.split("{nl}")
                    cell = self.render_markdown_with_parser(
                        [l + "\n" for l in inline_lines])

                    cell = cell.replace("\n", "")
                    markdown_cells.append(" " + cell + " ")
                else:
                    markdown_cells.append(cell)

            return "|".join(markdown_cells)
        else:
            return markdown_line
            

    def markdown_to_raw_html(self, markdown_lines):
        """
        convert markdown to html with my own extenstions

        Parameters
        -----------
        markdown_lines : iterable of markdown lines

        My extenstions
        --------------
        {nl} : allow multiline in table cell, use {nl} as line break
        """

        if not markdown_lines:
            return None

        normalized_markdown_lines = []
        processed_markdown_lines = []
        last_line_is_empty = False
        code_fence = None

        for line in markdown_lines:
            m = self.code_fence_re.match(line)
            if m:
                tmp_code_fence = m.group(1)
                info_string = m.group(2).strip()
                if code_fence:
                    if code_fence in tmp_code_fence and not info_string:
                        # end of fenced code block
                        code_fence = None
                else:
                    # a new fenced block start
                    code_fence = tmp_code_fence

                normalized_markdown_lines.append(line)
                processed_markdown_lines.append(line)
                continue
            elif code_fence:
                normalized_markdown_lines.append(line)
                processed_markdown_lines.append(line)
                continue
            
            striped_line = line.strip()
            if not striped_line:
                # markdownlint: no multiple consecutive blank lines
                if not last_line_is_empty:
                    # markdownlint: no trailing spaces
                    normalized_markdown_lines.append("\n")
                    processed_markdown_lines.append("\n")
                    last_line_is_empty = True
                
                continue
            else:
                last_line_is_empty = False

            line = self.normalize_markdown_line(line)
 
            normalized_markdown_lines.append(line)

            line = self.process_newline_in_table_cell(line)
            processed_markdown_lines.append(line)

        # markdownlint: markdown file should end with a single new line
        if not last_line_is_empty:
            normalized_markdown_lines.append("\n")
            processed_markdown_lines.append("\n")

        raw_html = self.render_markdown_with_parser(processed_markdown_lines)

        return (normalized_markdown_lines, raw_html)


    def markdown_to_full_html(self, markdown_lines):
        if not markdown_lines:
            return None

        normalized_markdown_lines, html_body = self.markdown_to_raw_html(markdown_lines)
        if not html_body:
            return None

        full_html = '<html><head><meta charset="UTF-8">'
        full_html += self.css_style
        full_html += "</head><body>\n" + html_body + "\n</body></html>"

        return (normalized_markdown_lines, full_html)


    def markdown_to_html_with_inline_style(self, markdown_lines):
        normalized_markdown_lines, html_body = self.markdown_to_full_html(markdown_lines)
        if not html_body:
            return None

        inliner = css_inline.CSSInliner(remove_style_tags=True)
        html_body = inliner.inline(html_body)

        return (normalized_markdown_lines, html_body)

    def markdown_to_html_file(self, markdown_lines, html_filepath):
        if not html_filepath:
            return

        full_html = self.markdown_to_full_html(markdown_lines)[1]
        if not full_html:
            return

        with open(html_filepath, "w", encoding="utf-8") as html_file:
            html_file.write(full_html)


    def markdown_file_to_html_file(self, markdown_filepath, html_filepath=None):
        if not html_filepath:
            split_filepath = os.path.splitext(markdown_filepath)
            html_filepath = uniqe_name(split_filepath[0] + ".html")

        with open(markdown_filepath, 'r', encoding='utf-8') as m:
            self.markdown_to_html_file(m.readlines(), html_filepath)