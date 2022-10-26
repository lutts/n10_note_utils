# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import sys
import os
import logging
#import re
import regex
#import markdown
#import markdown2
#from markdown_checklist.extension import ChecklistExtension
#import mistletoe
from markdown_it import MarkdownIt
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
import css_inline
from markdown_it.common.utils import escapeHtml
from katex_wrapper import tex2html
from enum import Enum, auto
import hashlib


def uniqe_name(expect_path):
    filename, extension = os.path.splitext(expect_path)
    counter = 1

    while os.path.exists(expect_path):
        expect_path = filename + "(" + str(counter) + ")" + extension
        counter += 1

    return expect_path


latex_cmd_args_space_re = regex.compile(r'(?P<prev>[\]}])\s+(?P<next>[\[{])')


def multiline_tex_to_one_line(tex, display_mode):
    one_line_tex = "".join(tex.splitlines())
    one_line_tex = latex_cmd_args_space_re.sub(r'\1\2', one_line_tex)

    if display_mode:
        return '$$' + one_line_tex + '$$'
    else:
        return '$' + one_line_tex + '$'


# def render_markdown_with_py_markdown(markdown_text):
#    return markdown.markdown("".join(markdown_text), encoding='utf-8',
#                             extensions=['tables', ChecklistExtension()])


# def render_markdown_with_mistletoe(markdown_text):
#    return mistletoe.markdown(markdown_text)

class markdown_processor_mode(Enum):
    NORMAL = auto()
    ONENOTE = auto()
    SUPERMEMO = auto()
    THEBRAIN = auto()
    LIST_EQUATION = auto()


class markdown_processor:
    """
    standard commonmark parser with some additional features

    additinal features
    ------------------
    * remove unneeded whitespaces
    * emphasis normalizer
    * add a space after some punctuations if there's no one
    """

    code_fence_re = regex.compile(r' {,3}(`{3,}|~{3,})(.*)')
    front_matter_re = regex.compile(r'-{3,}')

    def __init__(self, mode: markdown_processor_mode = markdown_processor_mode.NORMAL,
                 markdown_filepath: str = None):
        self.mode = mode
        self.inline_latex_equations = []
        self.block_latex_equations = []
        self.markdown_filepath = markdown_filepath
        self.images_dict = {}
        self.reinit_state()

    def reinit_state(self):
        self.code_fence = None
        self.front_matter = None
        self.line_number = 0
        self.has_latex_equations = False

    def get_images_in_directory(self):
        if self.images_dict:
            return

        if not self.markdown_filepath:
            return

        curdir = os.path.dirname(self.markdown_filepath)
        if curdir == "":
            curdir = "."

        logging.debug("get images in dir: " + curdir)
        # curdir = os.path.abspath(curdir)
        for image in os.listdir(curdir):
            # check if the image ends with png or jpg
            if image.endswith(".png") or img.endswith(".jpg"):
                hashdigest = os.path.splitext(image)[0]
                logging.debug("found image file: " + image)
                self.images_dict[hashdigest] = image

    def katex_renderer(self, content, display_mode):
        logging.debug("katex render coontent " + content +
                      " with  display_mode " + str(display_mode))
        logging.debug("render mode: " + str(self.mode))

        is_display_mode = display_mode['display_mode']

        one_line_tex = ""
        hexdigest = ""

        if self.mode != markdown_processor_mode.NORMAL:
            one_line_tex = multiline_tex_to_one_line(content, is_display_mode)
            hash_object = hashlib.md5(one_line_tex.encode())
            hexdigest = hash_object.hexdigest()
            logging.debug("equation digest: " + hexdigest)

        if self.mode is markdown_processor_mode.ONENOTE:
            if not is_display_mode:
                return one_line_tex

            self.get_images_in_directory()

            if hexdigest in self.images_dict:
                return '<img src="' + self.images_dict[hexdigest] + '" />'
            else:
                return one_line_tex
        elif self.mode in [markdown_processor_mode.SUPERMEMO, markdown_processor_mode.THEBRAIN]:
            self.get_images_in_directory()

            if hexdigest in self.images_dict:
                if is_display_mode:
                    return '<img src="' + self.images_dict[hexdigest] + '" />'
                else:
                    return '<img src="' + self.images_dict[hexdigest] + '" style="height:12pt; width:auto" />'
            else:
                return one_line_tex
        elif self.mode is markdown_processor_mode.LIST_EQUATION:
            if is_display_mode:
                if hexdigest not in self.block_latex_equations:
                    self.block_latex_equations.append('$$' + content + '$$')
                    self.block_latex_equations.append(hexdigest)
            else:
                if hexdigest not in self.inline_latex_equations:
                    self.inline_latex_equations.append('$' + content + "$")
                    self.inline_latex_equations.append(hexdigest)

            return ""

        options = {}

        if is_display_mode:
            options['display-mode'] = True

        html = tex2html(content, options)
        logging.debug("tex " + content + " render to " + html)

        self.has_latex_equations = True
        return html

    def render_markdown_with_parser(self, markdown_lines):
        """
        convert markdown to html with a parser

        Parameters
        -----------
        markdown_lines : iterable of markdown lines **with line breaks**
        """

        # md = MarkdownIt("commonmark", {"typographer": True})
        # md.enable(["replacements", "smartquotes"])
        # md.render("'single quotes' (c)")

        md = (
            MarkdownIt()
            .use(tasklists_plugin)
            .use(front_matter_plugin)
            .use(dollarmath_plugin, renderer=self.katex_renderer)
            .enable('strikethrough')
            .enable('table'))
        logging.debug(md.get_all_rules())

        return md.render("".join(markdown_lines))

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

    def line_is_in_front_matter(self, line):
        if self.line_number == 1:
            m = self.front_matter_re.match(line)
            if m:
                self.front_matter = m.group()
                return True
        elif self.front_matter:
            m = self.front_matter_re.match(line)
            if m:
                if self.front_matter == m.group():
                    # end of front matter
                    self.front_matter = None

            return True

        return False

    def line_is_in_code_fence(self, line):
        if self.line_is_in_front_matter(line):
            return True

        m = self.code_fence_re.match(line)
        if m:
            tmp_code_fence = m.group(1)
            info_string = m.group(2).strip()
            if self.code_fence:
                if self.code_fence in tmp_code_fence and not info_string:
                    # end of fenced code block
                    self.code_fence = None
            else:
                # a new fenced block start
                self.code_fence = tmp_code_fence

            return True
        elif self.code_fence:
            return True

        return False

    thebrain_text_color_re = regex.compile(r':[{](?P<text>.*?):[(]style=&quot;(?P<style>.*?)&quot;[)]:[}]:')

    def process_html_body_extras(self, raw_html):
        processed_html = []

        for line in raw_html.splitlines():
            processed_html.append(self.thebrain_text_color_re.sub(r'<span style="\2">\1</span>', line))
        
        return "\n".join(processed_html)

    def markdown_to_html_body(self, markdown_lines):
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

        processed_markdown_lines = []
        self.reinit_state()

        for line in markdown_lines:
            self.line_number += 1

            if self.line_is_in_code_fence(line):
                logging.debug("fenced code remained: " + line)
                processed_markdown_lines.append(line)
                continue

            line = line.replace('[x]', '[]')

            line = self.process_newline_in_table_cell(line)
            processed_markdown_lines.append(line)

        raw_html = self.render_markdown_with_parser(processed_markdown_lines)
        return self.process_html_body_extras(raw_html)

    common_css_style = """
        body {
            font-size: 12pt;
        }
        /*
        img {
			width:100%;
		}
        */
        table {
            display: table;
            /* margin-bottom: 1em; */
            border-collapse: collapse;
        }
        th, td {
            padding: 5px 8px;
        }
        table thead th {
            font-weight: bold;
            text-align: left;
            /* border: 1px solid; */
			border-top: 2px solid #000; /* 表头首行上方粗线 */
			border-bottom: 1px solid #000; /* 表头首行下方细线 */
        }
		/*
        table tbody td {
            border: 1px solid;
        }
		*/
		table > tbody > tr:last-child {
            border-bottom: 2px solid #000; /* 表体末行下方粗线 */
        }
    """

    common_blockquote_css_style = """
        blockquote {
            margin-top: 10px;
            margin-bottom: 10px;
            margin-left: 15px;
            padding-left: 15px;
            border-left: 3px solid #ccc;
            }
    """

    onenote_css_style = """
        blockquote {
            margin-left: .375in;
            background-color: #ececec;
        }
    """

    katex_stylesheet='<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.2/dist/katex.min.css" integrity="sha384-bYdxxUwYipFNohQlHt0bjN/LCpueqWz13HufFEV1SUatKs1cm4L6fFgCi1jT643X" crossorigin="anonymous">'

    def markdown_to_full_html(self, markdown_lines):
        if not markdown_lines:
            return None

        html_body = self.markdown_to_html_body(markdown_lines)
        if not html_body:
            return None

        full_html = '<html><head><meta charset="UTF-8">\n'
        
        if self.has_latex_equations:
            full_html += "\n" + self.katex_stylesheet + "\n"

        full_html += "<style>\n"
        full_html += self.common_css_style
        if self.mode == markdown_processor_mode.ONENOTE:
            full_html += self.onenote_css_style
        else:
            full_html += self.common_blockquote_css_style
        full_html += "</style>\n"
        full_html += "</head><body>\n"
        full_html += '<!-- <div  style="margin:0 auto;width:18.46cm;"> -->\n'
        full_html += html_body
        full_html += '\n<!-- </div> -->\n'
        full_html += "</body></html>"

        return full_html

    def markdown_to_html_with_inline_style(self, markdown_lines):
        html_body = self.markdown_to_full_html(markdown_lines)
        if not html_body:
            return None

        inliner = css_inline.CSSInliner(remove_style_tags=True)
        html_body = inliner.inline(html_body)

        return html_body

    def markdown_to_html_file(self, markdown_lines, html_filepath):
        if not html_filepath:
            return

        full_html = self.markdown_to_full_html(markdown_lines)
        if not full_html:
            return

        with open(html_filepath, "w", encoding="utf-8") as html_file:
            html_file.write(full_html)

    def markdown_file_to_html_file(self, markdown_filepath, html_filepath=None):
        if not self.markdown_filepath:
            self.markdown_filepath = markdown_filepath

        if not html_filepath:
            split_filepath = os.path.splitext(markdown_filepath)
            html_filepath = uniqe_name(split_filepath[0] + ".html")

        with open(markdown_filepath, 'r', encoding='utf-8') as m:
            self.markdown_to_html_file(m.readlines(), html_filepath)

    def list_latex_equations(self, markdown_filepath):
        if not self.markdown_filepath:
            self.markdown_filepath = markdown_filepath

        with open(markdown_filepath, 'r', encoding='utf-8') as m:
            self.markdown_to_html_body(m.readlines())

        if not self.inline_latex_equations and not self.block_latex_equations:
            return

        curdir = os.path.dirname(markdown_filepath)

        latex_equations_filepath = os.path.join(curdir, 'latex_euqations.txt')
        with open(latex_equations_filepath, 'w', encoding='utf-8') as equations:
            if self.inline_latex_equations:
                equations.write(
                    "------------inline equations-------------\n\n")
                equations.write("\n\n".join(self.inline_latex_equations))
            if self.block_latex_equations:
                equations.write(
                    "\n\n------------block equations-------------\n\n")
                equations.write("\n\n".join(self.block_latex_equations))
