# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import regex
import logging

from text_normalizer import py_text_normalizer


class py_markdown_normalizer:
    heading_whitespaces_re = regex.compile(r" +")
    emphasis_normalizer_re = regex.compile(
        r'(?P<asterisks>\*{1,2})\s*(?P<word1>[\u4e00-\u9fd5]+?)\s*(?P<punc1>\(|（|\[|【|<|《)\s*(?P<word2>.*?)\s*(?P<punc2>\)|）|\]|】|>|》)\s*(?P=asterisks)(?=[\u4e00-\u9fd5])')
    # regular expression to match markdown link ang image link
    # (?P<text_group>
    #   \[
    #     (?>
    #       [^\[\]]+
    #       |(?&text_group)
    #     )*
    #   \]
    # )
    # (?P<left_paren>\()
    # (?P<left_angle><)?
    # (?:
    #   (?P<url>
    #    (?(left_angle)
    #     .*?>
    # 	|\S*?
    #     )
    #   )
    #     (?:
    #       (?P<title_begin>[ ]")
    #         (?P<title>
    #           (?:[^"]|(?<=\\)")*?
    #         )
    #       (?P<title_end>")
    #     )?
    # (?P<right_paren>\))
    # )
    img_link_re = regex.compile(
        r'(!?)(?P<text_group>\[(?>[^\[\]]+|(?&text_group))*\])(?P<left_paren>\()(?P<left_angle><)?(?:(?P<url>(?(left_angle).*?>|\S*?))(?:(?P<title_begin>[ ]")(?P<title>(?:[^"]|(?<=\\)")*?)(?P<title_end>"))?(?P<right_paren>\)))')
    double_brace_re = regex.compile(r'(?P<b>\{|\})')

    code_fence_re = regex.compile(r' {,3}(`{3,}|~{3,})(.*)')
    front_matter_re = regex.compile(r'-{3,}')

    list_markers_re = regex.compile(r'(?P<markdown_marker>[-*+]|[0-9]+\.|Q:|q:|A:|a:)[ ]')
    table_re = regex.compile(r'^[|] .*? [|]$')
    blockquote_re = regex.compile(r'(?P<quote_marker>>(?:$|[> ]*))')
    markdown_header_re = regex.compile(r'[ ]{,3}(?P<header_marker>#{1,6})[ ]')

    FRONT_MATTER_LINE = "front matter"
    FENCED_CODE_LINE = "fenced code"
    MATH_LINE = "math"
    TABLE_LINE = "table"
    
    def __init__(self):
        self.seq_number = 0
        self.front_matter = None
        self.code_fence = None
        self.code_fence_info_string = None
        self.in_math_context = False
    
    def check_line(self, line: str) -> str:
        self.seq_number += 1

        line = line.rstrip()
        
        if self._is_in_front_matter(line):
            return py_markdown_normalizer.FRONT_MATTER_LINE

        if self._is_in_code_fence(line):
            return py_markdown_normalizer.FENCED_CODE_LINE

        if self._is_in_math_context(line):
            return py_markdown_normalizer.MATH_LINE

        m = py_markdown_normalizer.markdown_header_re.match(line)
        if m:
            return m.group(1)
        
        line = line.strip()
        # check if is markdown lists and blockquotes
        
        m = py_markdown_normalizer.list_markers_re.match(line)
        if m:
            return m.group(1)

        if py_markdown_normalizer.table_re.match(line):
            return py_markdown_normalizer.TABLE_LINE
        
        m = py_markdown_normalizer.blockquote_re.match(line)
        if m:
            return ">"

        return None

    def is_literal_text(self, line_type) -> bool:
        if not line_type:
            return False

        return line_type in [py_markdown_normalizer.MATH_LINE,
                             py_markdown_normalizer.FENCED_CODE_LINE,
                             py_markdown_normalizer.FRONT_MATTER_LINE]

    def _is_in_front_matter(self, line):
        if self.seq_number == 1:
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

    def _is_in_math_context(self, line):
        if '$$' in line:
            if self.in_math_context:
                # end of math context
                self.in_math_context = False
            else:
                # start of math context
                self.in_math_context = True
            return True
        else:
            return self.in_math_context

    def _is_in_code_fence(self, line):
        m = self.code_fence_re.match(line)
        if m:
            tmp_code_fence = m.group(1)
            info_string = m.group(2).strip()
            if self.code_fence:
                if self.code_fence in tmp_code_fence and not info_string:
                    # end of fenced code block
                    self.code_fence = None
                    # self.code_fence_info_string = None
            else:
                # a new fenced block start
                self.code_fence = tmp_code_fence
                self.code_fence_info_string = info_string

            return True
        elif self.code_fence:
            return True

        return False

    @staticmethod
    def normalize_line(line: str, add_newline_char=True):
        logging.debug("normalize line: " + line)

        line = line.replace('\0', '')

        heading_spaces = ""
        m = py_markdown_normalizer.heading_whitespaces_re.match(line)
        if m:
            heading_spaces = m.group()

        # indented code block, return the orignal line
        logging.debug("heading space len: " + str(len(heading_spaces)))

        # 避免随后的处理误伤link/img link
        image_or_links = py_markdown_normalizer.img_link_re.findall(line)
        if image_or_links:
            image_or_links = ["".join(i) for i in image_or_links]
            logging.debug("found img or links: " + str(image_or_links))
            line = py_markdown_normalizer.double_brace_re.sub(r'\1\1', line)
            line = py_markdown_normalizer.img_link_re.sub('{}', line)

        line = py_text_normalizer.normalize_text_line(line)

        # logging.debug("after normalize_text_line: " + line)

        line = py_markdown_normalizer.emphasis_normalizer_re.sub(
            r'\g<asterisks>\g<word1>\g<asterisks>\g<punc1>\g<asterisks>\g<word2>\g<asterisks>\g<punc2>', line)

        if image_or_links:
            line = line.format(*image_or_links)

        if add_newline_char:
            normalized_line = heading_spaces + line + "\n"
        else:
            normalized_line = heading_spaces + line
        logging.debug("normalized result: " + normalized_line)
        return normalized_line