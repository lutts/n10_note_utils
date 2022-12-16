# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import regex
import logging

from text_normalizer import py_normalize_text_line, py_concat_line


class py_markdown_normalizer:
    leading_whitespaces_re = regex.compile(r" +")
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
    IMG_LINK_PLACEHOLDER_PREFIX = "md_image_links"
    img_link_restore_re = regex.compile(r'{' + IMG_LINK_PLACEHOLDER_PREFIX + r'_(?P<idx>\d+)}')

    autolinks_re = regex.compile("<(((http|https)://)(www\\.)?|www\\.)" +
                                 "[a-zA-Z0-9@:%._\\+~#?&//=]" +
                                 "{2,256}\\.[a-z]" +
                                 "{2,6}\\b([-a-zA-Z0-9@:%" +
                                 "._\\+~#?&//=]*)>")
    AUTO_LINKS_PLACEHOLDER_PREFIX = "md_github_auto_links"
    autolinks_restore_re = regex.compile(r'{' + AUTO_LINKS_PLACEHOLDER_PREFIX + r'_(?P<idx>\d+)}')

    code_span_re = regex.compile("(`+)((?:[^`]|(?!(?<!`)\\1(?!`))`)*+)(\\1)")
    CODE_SPANS_PLACEHOLDER_PREFIX = "md_code_spans"
    code_span_restore_re = regex.compile(r'{' + CODE_SPANS_PLACEHOLDER_PREFIX + r'_(?P<idx>\d+)}')
    code_fence_re = regex.compile(r' {,3}(`{3,}|~{3,})(.*)')
    front_matter_re = regex.compile(r'-{3,}')

    list_markers_re = regex.compile(r'[ ]*(?P<markdown_marker>[-*+]|[0-9]+\.|Q:|q:|A:|a:)[ ]')
    blockquote_re = regex.compile(r'[ ]{,3}(?P<quote_marker>>(?:$|[> ]*))')
    markdown_header_re = regex.compile(r'[ ]{,3}(?P<header_marker>#{1,6})[ ]')
    level_1_header_re = regex.compile(r'[ ]{,3}#[ ]')
    maybe_table_re = regex.compile(r'[ ]{,3}\|')
    table_line_re = regex.compile(r'^[ ]{,3}\|[ ]*|[ ]*(?<=[^\\])\|[ ]*')
    table_delimiter_row_cell_re = regex.compile(r'^:?-+:?$')

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
        self.last_markdown_prefix = None
    
    def check_line(self, line: str) -> str:
        self.seq_number += 1

        if self._is_in_front_matter(line):
            return py_markdown_normalizer.FRONT_MATTER_LINE

        if self._is_in_code_fence(line):
            return py_markdown_normalizer.FENCED_CODE_LINE

        if self._is_in_math_context(line):
            return py_markdown_normalizer.MATH_LINE

        m = py_markdown_normalizer.markdown_header_re.match(line)
        if m:
            self.last_markdown_prefix = m.group(0)
            return m.group(1)

        m = py_markdown_normalizer.blockquote_re.match(line)
        if m:
            self.last_markdown_prefix = m.group(0)
            return ">"

        m = py_markdown_normalizer.list_markers_re.match(line)
        if m:
            self.last_markdown_prefix = m.group(0)
            return m.group(1)

        m = py_markdown_normalizer.maybe_table_re.match(line)
        if m:
            _, _, cells = py_markdown_normalizer.parse_table_line(line)
            if cells:
                return py_markdown_normalizer.TABLE_LINE
        
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

    def has_front_matter(self, lines):
        if not lines:
            return False

        self.seq_number = 1

        if not self._is_in_front_matter(lines[0]):
            return False
        
        for i in range(1, len(lines)):
            self.seq_number += 1
            fm = self._is_in_front_matter(lines[i])
            if not fm:
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
    def _reserve_special_inlines(line:str, matcher, placeholder_prefix):
        reserves = []

        def replace_func(matchobj):
            placeholder = "{" + placeholder_prefix + "_" + str(len(reserves)) + "}"
            reserves.append(matchobj.group())
            return placeholder
            
        new_line = matcher.sub(replace_func, line)
        return (new_line, reserves)


    @staticmethod
    def _restore_special_inlines(line:str, matcher, reserves):
        restored_num = 0
        def restore_func(matchobj):
            nonlocal restored_num

            idx = int(matchobj.group('idx'))
            if idx < len(reserves):
                restored_num += 1
                return reserves[idx]
            else:
                return matchobj.group()

        orig_line = matcher.sub(restore_func, line)
        return (orig_line, restored_num)

    @staticmethod
    def normalize_line(line: str, add_newline_char=True, markdown_prefix=None):
        line = line.replace('\0', '')

        if not markdown_prefix:
            # res = [py_markdown_normalizer.list_markers_re,
            #        py_markdown_normalizer.blockquote_re,
            #        py_markdown_normalizer.markdown_header_re,
            #        py_markdown_normalizer.leading_whitespaces_re]
            # for r in res:
            #     m = r.match(line)
            #     if m:
            #         markdown_prefix = m.group()
            #         break
            m = py_markdown_normalizer.leading_whitespaces_re.match(line)
            if m:
                markdown_prefix = m.group()

        if markdown_prefix:
            line = line[len(markdown_prefix):]
        else:
            markdown_prefix = ""

        # indented code block, return the orignal line

        # 避免随后的处理误伤code span, link/img link
        line, code_spans = py_markdown_normalizer._reserve_special_inlines(line,
                                                                           py_markdown_normalizer.code_span_re,
                                                                           py_markdown_normalizer.CODE_SPANS_PLACEHOLDER_PREFIX)
        line, image_or_links = py_markdown_normalizer._reserve_special_inlines(line,
                                                                               py_markdown_normalizer.img_link_re,
                                                                               py_markdown_normalizer.IMG_LINK_PLACEHOLDER_PREFIX)
        line, github_autolinks = py_markdown_normalizer._reserve_special_inlines(line,
                                                                                 py_markdown_normalizer.autolinks_re,
                                                                                 py_markdown_normalizer.AUTO_LINKS_PLACEHOLDER_PREFIX)

        line = py_normalize_text_line(line)

        line = py_markdown_normalizer.emphasis_normalizer_re.sub(
            r'\g<asterisks>\g<word1>\g<asterisks>\g<punc1>\g<asterisks>\g<word2>\g<asterisks>\g<punc2>', line)

        # restored_code_spans = 0
        if github_autolinks:
            line, _ = py_markdown_normalizer._restore_special_inlines(
                line, py_markdown_normalizer.autolinks_restore_re, github_autolinks)

        if image_or_links:
            line, _ = py_markdown_normalizer._restore_special_inlines(
                line, py_markdown_normalizer.img_link_restore_re, image_or_links)

        if code_spans:
            line, _ = py_markdown_normalizer._restore_special_inlines(
                line, py_markdown_normalizer.code_span_restore_re, code_spans)

        # if code_spans and restored_code_spans < len(code_spans):
        #     line, _ = py_markdown_normalizer._restore_special_inlines(
        #         line, py_markdown_normalizer.code_span_restore_re, code_spans)

        normalized_line = markdown_prefix + line
        if add_newline_char:
            normalized_line = normalized_line + "\n"

        return normalized_line

    # 这里的表格定义和commonmark的不同，因为我们的目的是从错乱的文本中”恢复“表格，
    # 所以一开始的文本很大可能不符合commonmark规范的
    # 
    # * 表格的第一行必须要有pipe，否则不认为表格的开始，pipe可以在任何位置
    # * 第一行可以是delimiter row，在这里的主要作用是指定列数
    # * delimiter row可以出现在任意行
    # * strict_mode时，delimiter row必须要有开头和结尾的pipe
    # * 如果delimiter row在第一行，则紧跟着的N个cell为表头
    # * 如果delimiter row不在第一行，则delimiter前面的N个cell为表头，如果N和delimiter row的cell个数对不上，则不是有效表格
    # * 非strict_mode时，如果没有delimiter row，则表格列数以第一行所表示的列数
    # * strict_mode时，必须要有delimiter row
    # * cell的定义: 两个pipe(|)之间的内容为一个cell，换行不影响cell的判定，如果有多行，会合并成一行
    # * 表格的终止条件: 空行。标准里是允许block level structure来终止表格的，但我们不考虑block level structure

    @staticmethod
    def parse_table_line(line:str):
        cells = py_markdown_normalizer.table_line_re.split(line)
        has_leading_pipe = False
        has_trailing_pipe = False
        if not cells[0]:
            cells.pop(0)
            has_leading_pipe = True
        
        if not cells[-1]:
            cells.pop()
            has_trailing_pipe = True

        return (has_leading_pipe, has_trailing_pipe, cells)

    @staticmethod
    def is_delimiter_row(line:str, parse_result, strict_mode:bool=False) -> bool:
        if line == "-" or line.startswith("- "):
            # is list item, not delimiter row
            return False

        has_leading_pipe, has_trailing_pipe, cells = parse_result
        if strict_mode:
            if not has_leading_pipe or not has_trailing_pipe:
                return False

        for cell in cells:
            m = py_markdown_normalizer.table_delimiter_row_cell_re.match(cell)
            if not m:
                return False

        return True

    @staticmethod
    def normalize_table(table_lines:list[str], strict_mode:bool=False):
        if not table_lines:
            return (False, table_lines)

        first_line = table_lines[0]
        if not first_line:
            return (False, table_lines)

        parse_result = py_markdown_normalizer.parse_table_line(first_line)
        has_leading_pipe, has_trailing_pipe, cells = parse_result
        if not has_leading_pipe and not has_trailing_pipe and len(cells) == 1:
            return (False, table_lines)

        all_cells = []
        delimiter_cells = None
        # default num columns is the number cells of the first line
        num_columns = len(cells)

        if py_markdown_normalizer.is_delimiter_row(first_line, parse_result):
            delimiter_cells = cells
            has_trailing_pipe = True
        else:
            all_cells = cells

        last_line_has_trailing_pipe = has_trailing_pipe

        for line in table_lines[1:]:
            if not line:
                break

            parse_result = py_markdown_normalizer.parse_table_line(line)
            has_leading_pipe, has_trailing_pipe, cells = parse_result
            if not delimiter_cells and py_markdown_normalizer.is_delimiter_row(line, parse_result):
                num_columns = len(cells)
                # if delimiter row is not the first line, column number MUST be the number of cells currently parsed
                if len(all_cells) != num_columns:
                    break

                delimiter_cells = cells
                last_line_has_trailing_pipe = True
            else:
                if not has_leading_pipe and not last_line_has_trailing_pipe:
                    if not all_cells:
                        all_cells.append(cells[0])
                    else:
                        all_cells[-1] = py_concat_line(all_cells[-1], cells[0])
                    cells = cells[1:]
                
                all_cells.extend(cells)

                last_line_has_trailing_pipe = has_trailing_pipe

        if strict_mode and not delimiter_cells:
            return (False, table_lines)

        if len(all_cells) < num_columns:
            return (False, table_lines)

        if len(all_cells) == 1 and not all_cells[0]:
            return (False, table_lines)

        all_cells = [py_markdown_normalizer.normalize_line(
            cell, add_newline_char=False) for cell in all_cells]

        header_line = '| ' + (' | '.join(all_cells[0:num_columns])) + ' |\n'
        table_lines = [header_line]
        if delimiter_cells:
            table_lines.append('| ' + (' | '.join(delimiter_cells)) + ' |\n')
        else:
            delimiter_cells = [""]
            for _ in range(num_columns):
                delimiter_cells.append(' --- ')
            delimiter_cells.append("")
            table_lines.append('|'.join(delimiter_cells) + "\n")

        for i in range(num_columns, len(all_cells), num_columns):
            cells = all_cells[i:i+num_columns]
            table_lines.append('| ' + (' | '.join(cells)) + ' |\n')

        return (True, table_lines)


def test():
    logging.basicConfig(level=logging.DEBUG)
    table = """| --- | --- | --- |
| Variable | | |
| Encodings | The way you categorize information about yourself,
other people, events, and situations
| As soon as Bob meets someone, he tries to figure out
how wealthy he or she is.
| Expectancies
and beliefs
| Your beliefs about the social world and likely outcomes
for given actions in particular situations; your beliefs
about your ability to bring outcomes about
| Greg invites friends to the movies, but he never expects
them to say “yes.”
| Affects | Your feelings and emotions, including physiological
responses
| Cindy blushes very easily.
| Goals and values | The outcomes and affective states you do and do not
value; your goals and life projects
| Peter wants to be president of his
college class.
| Competencies
and self-regulatory plans
| The behaviors you can accomplish and plans for
generating cognitive and behavioral outcomes
| Jan can speak English, French, Russian, and Japanese
and expects to work for the United Nations.
    """
    table_lines = table.splitlines()
    _, normalized_lines = py_markdown_normalizer.normalize_table(table_lines)
    print("".join(normalized_lines))
    print("-----------------------------")


if __name__ == '__main__':
    test()
