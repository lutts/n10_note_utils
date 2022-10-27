#!/user/bin/env python3 -tt
# -*- coding: utf-8 -*-
"""
Module documentation.
"""

# Imports
import sys
import regex
import os
import logging
from datetime import datetime
import css_inline
from collections import OrderedDict
import uuid

from markdown_utils import markdown_processor, uniqe_name
from HTMLClipboard import PutHtml
import hanzi


# Global variables

# Class declarations

class NoteBlock:
    def __init__(self, phy_page_number):
        self.phy_page_number = phy_page_number
        self.logic_page_number = phy_page_number
        self.cur_line = None
        self.lines = []
        self.next = None
    
    def is_empty(self):
        if not self.lines:
            return True
        
        for line in self.lines:
            if line:
                return False
        
        return True

    def get_next_list_tail(self):
        if not self.next:
            return None
        
        next_block = self.next
        while next_block.next:
            next_block = next_block.next

        return next_block

    def finish_current_line(self):
        if self.cur_line is None:
            return

        self.lines.append(self.cur_line)
        self.cur_line = None

    def concat_to_current_line(self, line):
        if self.cur_line is None:
            self.cur_line = line
            return

        line = line.strip()
        last_char = self.cur_line[-1]
        if last_char == "-":
            self.cur_line = self.cur_line[:-1]
        elif last_char == '’' or last_char == '”' or ord(last_char) < 128:
            # use space to join english lines
            self.cur_line += " "
        
        self.cur_line += line

    def new_line(self, line):
        self.finish_current_line()
        self.cur_line = line

    def add_single_raw_line(self, line):
        self.finish_current_line()
        self.lines.append(line)

    def add_multi_raw_line(self, lines):
        self.finish_current_line()
        self.lines.extend(lines)


class N10NoteProcessor:
    def __init__(self, n10_notes_filepath=None,
                 hand_notes_filepath=None,
                 markdown_filepath=None,
                 html_filepath=None,
                 raw_text=None):
        self.prev_block = None
        self.cur_block = NoteBlock("0")
        self.page_block_dict = OrderedDict()
        
        self.replacement_dict = {}
        self.old_placeholder_dict = {}

        self.normalized_lines = []

        self.image_list = []
        self.hand_note_list = []
        self.n10_notes_filepath = n10_notes_filepath
        self.hand_notes_filepath = hand_notes_filepath
        self.raw_text = raw_text

        self.book_title = None
        self.book_filename = None

        self.markdown_filepath = None
        self.html_filepath = None

        if markdown_filepath:
            self.markdown_filepath = markdown_filepath
        elif self.n10_notes_filepath:
            split_filepath = os.path.splitext(n10_notes_filepath)
            self.markdown_filepath = uniqe_name(split_filepath[0] + ".md")

        if self.markdown_filepath:
            logging.debug("markdown text will write to " + self.markdown_filepath)
        
        if html_filepath:
            self.html_filepath = html_filepath
        elif self.n10_notes_filepath:
            split_filepath = os.path.splitext(n10_notes_filepath)
            self.html_filepath = uniqe_name(split_filepath[0] + ".html")

        if self.html_filepath:
            logging.debug("rendered html file will write to " + self.html_filepath)

    def reinit_state(self):
        self.code_fence = None
        self.code_fence_info_string = None
        self.front_matter = None
        self.line_number = 0
        self.last_line_is_header = False
        self.in_math_context = False
    
    list_table_markers_re = regex.compile(r'(?P<markdown_marker>[-*+|]|[0-9]+\.)[ ]')
    blockquote_re = regex.compile(r'>([ ]|$)')
    markdown_header_re = regex.compile(r'[ ]{,3}(?P<header_marker>#{1,6})[ ]')

    def line_is_markdown(self, line):
        if not line:
            return None

        m = self.markdown_header_re.match(line)
        if m:
            logging.debug("markdown header line: " + line)
            return m.group(1)
        
        line = line.strip()
        # check if is markdown lists and blockquotes
        
        m = self.list_table_markers_re.match(line)
        if m:
            logging.debug("line with markdown list or table: " + line)
            return m.group(1)
        
        m = self.blockquote_re.match(line)
        if m:
            logging.debug("markdown blockquote: " + line)
            return ">"

        return None

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

    def line_is_in_math_context(self, line):
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
                self.code_fence_info_string = info_string

            return True
        elif self.code_fence:
            return True
        elif self.line_is_in_math_context(line):
            return True

        return False

    old_placeholder_re  = regex.compile(r'^{(?P<placeholder>.+)}$')
    sticker_re = regex.compile(r'\[(?P<placeholder>[^]]*?)\](:[.+-])?$')

    def scan_block_for_book_title(self):
        idx = 0
        for line in self.cur_block.lines:
            m = self.markdown_header_re.match(line)
            if m:
                markdown_marker = m.group(1)
                if markdown_marker == "#":
                    # level 1 head, treat it as book title
                    self.book_title = line[line.index('# ')+2:]
                    self.cur_block.lines[idx] = ""
                    break
            idx += 1

    def convert_old_placeholder(self, block):
        # 兼容以前的{placeholder}方案
        converted_lines = []
        first_line = block.lines[0].strip()
        idx = 0
        for line in block.lines:
            m = self.old_placeholder_re.match(line.strip())
            if m:
                placeholder = m.group(1)

                if placeholder in self.old_placeholder_dict:
                    # 第二次碰到
                    converted_lines.append(line)
                    if idx == 0:
                        first_line = '[' + placeholder + ']:.'
                else:
                    self.old_placeholder_dict[placeholder] = line
                    # 第一次碰到
                    if idx == 0:
                        # 第一行
                        converted_lines.append('[' + placeholder + ']:-')
                    else:
                        converted_lines.append('[' + placeholder + ']')
            else:
                converted_lines.append(line)
            
            idx += 1
        
        block.lines =  converted_lines
        return first_line

    def finish_current_block(self):
        self.cur_block.finish_current_line()

        if self.cur_block.is_empty():
            return

        if not self.book_title:
            self.scan_block_for_book_title()

        # check again
        if self.cur_block.is_empty():
            return

        first_line = self.convert_old_placeholder(self.cur_block)
        #first_line = self.cur_block.lines[0].strip()
        m = self.sticker_re.match(first_line)
        if m:
            if first_line == '[]:.':
                # stick to current position
                del self.cur_block.lines[0]
                self.cur_block.logic_page_number = str(uuid.uuid4())
            elif first_line == '[]:+':
                # stick to previous block
                del self.cur_block.lines[0]
                if self.prev_block:
                    self.cur_block.logic_page_number = self.prev_block.logic_page_number
                    self.prev_block.next = self.cur_block
                    return
            else:
                placeholder = m.group(1)
                suffix = m.group(2)
                if placeholder and suffix == ":.":
                    #logging.debug("------------>" + (" | ".join(self.cur_block.lines)))
                    self.replacement_dict[placeholder] = self.cur_block

        logic_page_number = self.cur_block.logic_page_number
        if logic_page_number in self.page_block_dict:
            self.page_block_dict[logic_page_number].append(self.cur_block)
        else:
            self.page_block_dict[logic_page_number] = [self.cur_block]

    def new_block(self, phy_page_number):
        self.finish_current_block()
        self.prev_block = self.cur_block
        self.cur_block = NoteBlock(phy_page_number)

    def concat_to_current_line(self, line):
        self.cur_block.concat_to_current_line(line)

    def new_line(self, line):
        self.cur_block.new_line(line)

    def add_single_raw_line(self, line):
        self.cur_block.add_single_raw_line(line)

    def add_multi_raw_line(self, lines):
        self.cur_block.add_multi_raw_line(lines)

    code_fence_re = regex.compile(r' {,3}(`{3,}|~{3,})(.*)')
    front_matter_re = regex.compile(r'-{3,}')

    english_punctuation = r'-!"#$%&\'()*+,./:;<=>?@\[\\\]^_`{|}~'

    heading_whitespaces_re = regex.compile(r" +")
    emphasis_normalizer_re = regex.compile(
        r'(?P<asterisks>\*{1,2})\s*(?P<word1>[\u4e00-\u9fd5]+?)\s*(?P<punc1>\(|（|\[|【|<|《)\s*(?P<word2>.*?)\s*(?P<punc2>\)|）|\]|】|>|》)\s*(?P=asterisks)(?=[\u4e00-\u9fd5])')
    space_after_punc_re = regex.compile(
        r'(?P<punc>\.|,|;|:|\?|\!)(?P<word>[^' + english_punctuation + hanzi.punctuation + r'0123456789\s]+)')
    # CJK Unified Ideographs: 4E00 — 9FFF, 但后面有几个没用，只到9fd5
    # 中英文之间需要增加空格: 中 chinese 文
    # 中文与数字之间需要增加空格: 花了 5000 元
    # 基于这两点，下面的正则表达式只有在中文之间存在空格时才会去掉空格，如果中文字符后面是数字、英文、标点之类的，则不会
    space_around_chinese_char_re = regex.compile(r'(?P<zhchar>[\u4e00-\u9fd5])(?:\s+)(?=[\u4e00-\u9fd5])')
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
    space_around_left_paren_re = regex.compile(r'(?:\s*?)(\s?[(])(?:\s*)')
    space_around_right_paren_re = regex.compile(r'(?:\s*)([)]\s?)(?:\s*?)')

    def normalize_line(self, line):
        logging.debug("normalize line: " + line)
        heading_spaces = ""
        m = self.heading_whitespaces_re.match(line)
        if m:
            heading_spaces = m.group()

        # indented code block, return the orignal line
        logging.debug("heading space len: " + str(len(heading_spaces)))

        # markdownlint: no trailing spaces
        # 行首的空格在heading_spaces里保存着
        striped_line = line.strip()
        
        striped_line = striped_line.replace('\0', '')

        # 避免随后的处理误伤link/img link
        image_or_links = self.img_link_re.findall(striped_line)
        if image_or_links:
            image_or_links = ["".join(i) for i in image_or_links]
            logging.debug("found img or links: " + str(image_or_links))
            striped_line = self.double_brace_re.sub(r'\1\1', striped_line)
            striped_line = self.img_link_re.sub('{}', striped_line)

        # Replaces all curly quotes(‘, ’, “, ”) in a document with straight quotes(', ").
        striped_line = regex.sub(r'‘(?=[^\u4e00-\u9fd5])', "'", striped_line)
        striped_line = regex.sub(r'(?<=[^\u4e00-\u9fd5])’', "'", striped_line)
        striped_line = regex.sub(r'“(?=[^\u4e00-\u9fd5])', '"', striped_line)
        striped_line = regex.sub(r'(?<=[^\u4e00-\u9fd5])”', '"', striped_line)

        # 中文括号转英文括号
        striped_line = regex.sub(r'（(?=[^\u4e00-\u9fd5])', '(', striped_line)
        striped_line = regex.sub(r'(?<=[^\u4e00-\u9fd5])）', ')', striped_line)
        # 去掉括号前或后面的空格
        striped_line = self.space_around_left_paren_re.sub(r'\1', striped_line)
        striped_line = self.space_around_right_paren_re.sub(r'\1', striped_line)

        # 去掉中文字符之间的空格
        # test string: Hey Jane, 周 末 要 不要一起 吃早茶，叫上 Jennie 和 Jone, 预计花费 100 元
        striped_line = self.space_around_chinese_char_re.sub(r'\g<zhchar>', striped_line)

        # test string: 'a.string,has;no:space?after   punctuation!another, string; has: space? after puctuation! ok!'
        # 多个连续的空格只保留一个
        striped_line = " ".join(striped_line.split())

        # add a space after some punctuations if there's no one
        striped_line = self.space_after_punc_re.sub(r'\1 \2', striped_line)

        striped_line = self.emphasis_normalizer_re.sub(
            r'\g<asterisks>\g<word1>\g<asterisks>\g<punc1>\g<asterisks>\g<word2>\g<asterisks>\g<punc2>', striped_line)

        if image_or_links:
            striped_line = striped_line.format(*image_or_links)

        logging.debug("normalized result: " +
                      heading_spaces + striped_line + "\n")
        return heading_spaces + striped_line + "\n"


    def get_block_lines(self, block):
        if block.is_empty():
            if block.next:
                return self.get_block_lines(block.next)
            else:
                return []

        # logging.debug("get_block_lines: " + (" | ".join(block.lines)))

        lines = block.lines
        block.lines = None

        first_line = lines[0]
        m = self.sticker_re.match(first_line.strip())
        if m:
            placeholder = m.group(1)
            suffix = m.group(2)
            if placeholder and suffix == ":-":
                if placeholder in self.replacement_dict:
                    replace_block = self.replacement_dict[placeholder]
                    if not replace_block.is_empty():
                        replace_block.lines[0] = ""
                        lines = replace_block.lines

                        if replace_block.next:
                            tmp_next = block.next
                            block.next = replace_block.next
                            replace_block.get_next_list_tail().next = tmp_next
                            replace_block.next = None
                    else:
                        lines = []
                    replace_block.lines = None
                elif placeholder in self.old_placeholder_dict:
                    lines[0] = self.old_placeholder_dict[placeholder]
                    del self.old_placeholder_dict[placeholder]

        result_list = []

        phy_page_number = int(block.phy_page_number)
        if phy_page_number != self.prev_phy_page_number:
            if self.prev_phy_page_number != 0:
                result_list.append("")
                result_list.append("(p" + str(self.prev_phy_page_number) + "e)")
                result_list.append("")

            result_list.append("(p" + block.phy_page_number + "s)")
            result_list.append("")

            self.prev_phy_page_number = phy_page_number

        for line in lines:
            stripped_line = line.strip()
            m = self.sticker_re.match(stripped_line)
            if m:
                placeholder = m.group(1)
                suffix = m.group(2)

                if placeholder and not suffix:
                    if placeholder in self.replacement_dict:
                        replace_block = self.replacement_dict[placeholder]

                        if replace_block.next:
                            if block.next:
                                block.get_next_list_tail().next = replace_block.next
                            else:
                                block.next = replace_block.next
                            
                            replace_block.next = None

                        if not replace_block.is_empty():
                            replace_block.lines[0] = ""
                            result_list.extend(self.get_block_lines(replace_block))
                        else:
                            result_list.append("")
                    elif placeholder in self.old_placeholder_dict:
                        result_list.append(self.old_placeholder_dict[placeholder])
                        del self.old_placeholder_dict[placeholder]
                    else:
                        result_list.append(line)
                else:
                    result_list.append(line)
            else:
                result_list.append(line)

        if block.next:
            result_list.extend(self.get_block_lines(block.next))
        
        # logging.debug("get_block_lines: return_list: " + (" | ".join(result_list)))
        return result_list

    def normalize_markdown_lines(self):
        if self.normalized_lines:
            return self.normalized_lines

        if not self.page_block_dict:
            return None

        all_block_list = []
        self.prev_phy_page_number = 0

        for _, block_list in self.page_block_dict.items():
            for block in block_list:
                all_block_list.extend(self.get_block_lines(block))

        if self.prev_phy_page_number != 0:
            all_block_list.append("")
            all_block_list.append("(p" + str(self.prev_phy_page_number) + "e)")
            all_block_list.append("")

        self.reinit_state()
        last_line_is_empty = False
        title_added = False

        for line in all_block_list:
            logging.debug("check line before write disk: " + line)
            self.line_number += 1

            if self.line_is_in_code_fence(line):
                logging.debug("fenced code remained: " + line)
                # fenced code line already has '\n', so do not append another '\n'
                self.normalized_lines.append(line)
                last_line_is_empty = False
                continue

            if not title_added:
                title_added = True

                if self.book_title:
                    self.normalized_lines.append("# " + self.book_title + "\n")
                    self.normalized_lines.append("\n")
                elif self.book_filename:
                    self.normalized_lines.append("# 摘自: " + self.book_filename + "\n")
                    self.normalized_lines.append("\n")

            striped_line = line.strip()
            if not striped_line:
                logging.debug("empty line, last_line_is_empty: " + str(last_line_is_empty))
                # markdownlint: no multiple consecutive blank lines
                if not last_line_is_empty:
                    # markdownlint: no trailing spaces
                    self.normalized_lines.append("\n")
                    last_line_is_empty = True

                continue
            else:
                last_line_is_empty = False

            line = self.normalize_line(line)
            self.normalized_lines.append(line)

        # markdownlint: markdown file should end with a single new line
        logging.debug("last step, check if last_line_is_empty=" + str(last_line_is_empty))
        if last_line_is_empty:
            self.normalized_lines.pop()

    def write_block_list(self):
        self.normalize_markdown_lines()

        if not self.normalized_lines:
            return

        joined_markdown_text = "".join(self.normalized_lines)

        if self.markdown_filepath:
            try:
                with open(self.markdown_filepath, "w", encoding="utf-8") as n10notes_markdown:
                    n10notes_markdown.write(joined_markdown_text)
            except:
                pass

        full_html = markdown_processor().markdown_to_full_html(self.normalized_lines)
        
        if self.html_filepath:
            try:
                with open(self.html_filepath, 'w', encoding="utf-8") as html_file:
                    html_file.write(full_html)
            except:
                pass

        inliner = css_inline.CSSInliner(remove_style_tags=True)
        inlined_html = inliner.inline(full_html)
        PutHtml(inlined_html, joined_markdown_text)

    def get_images_in_directory(self):
        if not self.n10_notes_filepath:
            return

        curdir = os.path.dirname(self.n10_notes_filepath)
        if curdir == "":
            curdir = "."

        logging.debug("get images in dir: " + curdir)
        # curdir = os.path.abspath(curdir)
        for image in os.listdir(curdir):
            # check if the image ends with png
            if (image.endswith(".png")):
                fullpath = os.path.join(curdir, image)
                try:
                    logging.debug(image + " ctime:" +
                                  str(os.path.getctime(fullpath)))
                    logging.debug(
                        image + " ctime:" + str(datetime.fromtimestamp(os.path.getctime(fullpath))))
                except Exception as e:
                    logging.debug(e)

                # url in <> to allow space in path names
                self.image_list.append(
                    (os.path.getctime(fullpath), "![x](<" + image + ">)"))

        self.image_list.sort()
        logging.debug("images: " + str(self.image_list))


    HAND_NOTES_HEADER_RE = regex.compile(
        r"([0-9]{4})\.([0-9]{1,2})\.([0-9]{1,2})-([0-9]{1,2}):([0-9]{1,2})")

    def read_hand_notes(self):
        if not self.hand_notes_filepath:
            return

        last_ts = 0
        cur_notes = []

        with open(self.hand_notes_filepath, 'r', encoding="utf-16be") as hand_notes:
            for line in hand_notes:
                logging.debug("hand note: " + line)
                line = line.strip()
                m = self.HAND_NOTES_HEADER_RE.match(line)
                if m:
                    datetime_obj = datetime(*[int(i) for i in
                                            m.group(1, 2, 3, 4, 5)])
                    logging.debug(datetime_obj)
                    if cur_notes:
                        self.hand_note_list.append((last_ts, cur_notes))
                        cur_notes = []

                    last_ts = datetime_obj.timestamp()
                else:
                    # 手写笔迹不会合并行，用户写的一行就是一行
                    if line:
                        cur_notes.append("> " + line)
                    else:  # avoid trailing space
                        cur_notes.append(">")

        if cur_notes:
            self.hand_note_list.append((last_ts, cur_notes))

        self.hand_note_list.sort()
        logging.debug(self.hand_note_list)

    
    HW_NOTES_HEADER_RE = regex.compile(
        r"(?P<year>[0-9]{4})年(?P<month>[0-9]{2})月(?P<day>[0-9]{2})日 (?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})  摘自<<(?P<filename>.*?)>> 第(?P<page_number>[0-9]+)页")

    def process_head_line(self, notes_header, line, orig_line):
        logging.debug("header line: " + line)
        datetime_obj = datetime(*[int(i) for i in
                                notes_header.group("year", "month", "day", "hour", "minute", "second")])
        logging.debug(datetime_obj)
        ts = datetime_obj.timestamp()
        if self.image_list:
            logging.debug("cur ts: " + str(ts) +
                          ", first img ts: " + str(self.image_list[0][0]))
            if ts > self.image_list[0][0]:
                self.add_multi_raw_line(["", self.image_list[0][1], ""])
                del self.image_list[0]

        if self.hand_note_list:
            logging.debug("cur ts: " + str(ts) +
                          ", first hand note ts: " + str(self.hand_note_list[0][0]))
            if ts > self.hand_note_list[0][0]:
                self.add_multi_raw_line([""] + self.hand_note_list[0][1] + [""])
                del self.hand_note_list[0]

        if not self.book_filename:
            self.book_filename = notes_header.group("filename")

        self.new_block(notes_header.group("page_number"))

    def process_normal_line(self, line, orig_line):
        if self.line_is_in_code_fence(line):
            if self.code_fence_info_string and self.code_fence_info_string == "delete":
                logging.debug("fenced code marked as deleted: " + orig_line)
                return

            logging.debug("fenced code untouched: " + orig_line)
            self.add_single_raw_line(orig_line)
            return

        stripped_line = line.strip()
        m = self.sticker_re.match(stripped_line)
        if m:
            logging.debug("found sticker: " + stripped_line)
            self.add_single_raw_line(line)
            return

        markdown_marker = self.line_is_markdown(line)
        if markdown_marker:
            self.new_line(line)
            return
        
        if not line:
            logging.debug("empty line")
            self.add_single_raw_line("")
            return

        logging.debug("normal line: " + line)
        self.concat_to_current_line(line)

    def get_raw_text_lines(self):
        if self.n10_notes_filepath:
            logging.debug("get raw text from file " + self.n10_notes_filepath)
            with open(self.n10_notes_filepath, 'r', encoding='utf_8_sig') as n10notes:
                return n10notes.readlines()

        if self.raw_text:
            return self.raw_text.splitlines(keepends=True)

        return None

    def post_process(self):
        if self.image_list:
            left_image_blocks = [""]
            for ts, img in self.image_list:
                left_image_blocks.append(img)
                left_image_blocks.append("")
            self.add_multi_raw_line(left_image_blocks)

        if self.hand_note_list:
            left_hand_blocks = [""]
            for ts, note in self.hand_note_list:
                left_hand_blocks.extend(note)
                left_hand_blocks.append("")
            self.add_multi_raw_line(left_hand_blocks)

        self.finish_current_block()
        self.cur_block = None
        
        self.normalize_markdown_lines()

    def process(self):
        raw_text_lines = self.get_raw_text_lines()
        if not raw_text_lines:
            return

        self.get_images_in_directory()
        self.read_hand_notes()

        self.reinit_state()

        last_line_is_header = False

        for line in raw_text_lines:
            self.line_number += 1

            logging.debug("process line: " + line)
            orig_line = line

            # only remove trailing whitespaces
            line = line.rstrip()
            # check if is header line
            notes_header = self.HW_NOTES_HEADER_RE.match(line)
            if notes_header:
                self.last_line_is_header = True
                self.process_head_line(notes_header, line, orig_line)
            else:
                self.process_normal_line(line, orig_line)
                self.last_line_is_header = False

        self.post_process()

def main():
    args = sys.argv[1:]

    if not args:
        print('usage: python3 -m n10_note_processor <摘抄文件> [手写笔记导出文本文件]')
        sys.exit(1)

    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    #logging.basicConfig(level=logging.DEBUG)

    if args[0].endswith(".md"):
        logging.debug("process markdown file: " + args[0])
        markdown_processor().markdown_file_to_html_file(args[0])
    else:
        processor = N10NoteProcessor(*args)
        processor.process()
        processor.write_block_list()


# Main body
if __name__ == '__main__':
    main()
