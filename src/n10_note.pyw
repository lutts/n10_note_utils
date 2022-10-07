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

from markdown_utils import markdown_processor, uniqe_name
from HTMLClipboard import PutHtml
import hanzi



# Global variables

# Class declarations

# Function declarations

class N10NoteProcessor:
    """
    这个类的用途：
    1. 去掉汉王N10摘抄文件中的多余空格和换行
    2. 将读书过程中的截图图片根据时间戳嵌入到笔记中
    3. 将手写笔记按照手工的时间戳加入到笔记中

    注：汉王的手写笔记导出的文件是UTF-16 BE BOM的，需要事先转为UTF-8

    我们将整个摘抄文件分为`块`，每`块`都有特殊的开头，没有特殊开头的文本行
    默认都属于最近的一个`块`，块又分三类：

    * 汉王的摘抄特征行：
        * 将被简化为`(p56)`这样的页码，放在紧接着的`块`的开始，
        方便后续手工整理笔记时很方便地删掉这些页码信息
    * 会去掉多余空格和换行的
        * 缩进至少4个英文空格则视为一块的开始
        * Markdown特殊字符(*, -, +, >, #，|(表格), 数字后面一个点)开始的行也视为一块的开始
    * 保持不变的：
        * 空行可以用来分隔块。单个空行会被保留，但多个连续空行只会保留一个

    建议：自已的想法用markdown的blockquote `> `来写，这样markdown渲染出来的效果最好

    处理后的文件会生成一个标准的Markdown文件，可以用支持Markdown的编辑器打开
    程序还会自动将markdown文件渲染成html文件一并输出，方便用户将带格式的html文本拷贝到诸如OneNote等笔记
    软件中编辑
    """

    SPECIAL_PAGE_NUMBER = "lines_before_note_header"

    def __init__(self, n10_notes_filepath=None,
                 hand_notes_filepath=None,
                 markdown_filepath=None,
                 html_filepath=None,
                 raw_text=None):
        self.block = None
        self.header_block_list = []
        self.cur_page_number = self.SPECIAL_PAGE_NUMBER
        self.page_block_dict = OrderedDict()
        self.replacement_dict = {}
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
        self.front_matter = None
        self.line_number = 0
        self.last_line_is_header = False

    
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

    placeholder_re  = regex.compile(r'^(?P<placeholder>{.+})(?P<line_number>[0-9]*)$')

    def add_header_blocks_to_page(self):
        if not self.header_block_list:
            return

        logging.debug("save header blocks to page" + str(self.cur_page_number))

        block_list = self.header_block_list
        self.header_block_list = []

        placeholder = ""
        m = self.placeholder_re.match(block_list[0].strip())
        if m:
            placeholder = m.group("placeholder")
            logging.debug("found placeholder: " + placeholder)
            self.replacement_dict[placeholder] = [str(self.line_number)] + block_list[1:]
            block_list = [placeholder + str(self.line_number)]
        
        if self.cur_page_number in self.page_block_dict:
            self.page_block_dict[self.cur_page_number].extend(block_list)
        else:
            self.page_block_dict[self.cur_page_number] = block_list

    def add_current_block_to_header(self):
        if self.block is None:
            return
        
        self.header_block_list.append(self.block)
        self.block = None

    def add_raw_blocks_to_header(self, blocks):
        self.add_current_block_to_header()
        logging.debug("save blocks: " + str(blocks))
        self.header_block_list.extend(blocks)

    def keep_line_untouched(self, line):
        self.add_current_block_to_header()
        self.header_block_list.append(line)

    def new_block(self, initial_line):
        self.add_current_block_to_header()
        self.block = initial_line
    
    def concat_to_current_block(self, line):
        if self.block is None:
            self.block = line
            return

        if self.block:
            line = line.strip()
            last_char = self.block[-1]
            if last_char == "-":
                self.block = self.block[:-1]
            elif ord(last_char) < 128:
                # use space to join english lines
                self.block += " "

        self.block += line


    code_fence_re = regex.compile(r' {,3}(`{3,}|~{3,})(.*)')
    front_matter_re = regex.compile(r'-{3,}')

    english_punctuation = r'-!"#$%&\'()*+,./:;<=>?@\[\\\]^_`{|}~'

    heading_whitespaces_re = regex.compile(r" +")
    emphasis_normalizer_re = regex.compile(
        r'(?P<asterisks>\*{1,2})\s*(?P<word1>[^\s].*?[^\s])\s*(?P<punc1>\(|（|\[|【|<|《)\s*(?P<word2>[^\s].*?[^\s])\s*(?P<punc2>\)|）|\]|】|>|》)\s*(?P=asterisks)')
    space_after_punc_re = regex.compile(
        r'(?P<punc>\.|,|;|:|\?|\!)(?P<word>[^' + english_punctuation + hanzi.punctuation + r'0123456789\s]+)')
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

        # 避免随后的处理误伤link/img link
        image_or_links = self.img_link_re.findall(striped_line)
        if image_or_links:
            image_or_links = ["".join(i) for i in image_or_links]
            logging.debug("found img or links: " + str(image_or_links))
            striped_line = self.double_brace_re.sub(r'\1\1', striped_line)
            striped_line = self.img_link_re.sub('{}', striped_line)

        striped_line = striped_line.replace('’', "'")

        # 中文括号转英文括号
        striped_line = striped_line.replace('（', '(')
        striped_line = striped_line.replace('）', ')')
        # 去掉括号前后的空格
        striped_line = self.space_around_left_paren_re.sub(r'\1', striped_line)
        striped_line = self.space_around_right_paren_re.sub(r'\1', striped_line)

        # test string: 'a.string,has;no:space?after   punctuation!another, string; has: space? after puctuation! ok!'
        # 多个连续的空格只保留一个
        striped_line = " ".join(striped_line.split())

        # add a space after some punctuations if there's no one
        striped_line = self.space_after_punc_re.sub(r'\1 \2', striped_line)

        striped_line = self.emphasis_normalizer_re.sub(
            '\g<asterisks>\g<word1>\g<asterisks>\g<punc1>\g<asterisks>\g<word2>\g<asterisks>\g<punc2>', striped_line)

        if image_or_links:
            striped_line = striped_line.format(*image_or_links)

        logging.debug("normalized result: " +
                      heading_spaces + striped_line + "\n")
        return heading_spaces + striped_line + "\n"


    def normalize_markdown_lines(self):
        if self.normalized_lines:
            return self.normalized_lines

        if not self.page_block_dict:
            return None

        self.reinit_state()
        all_block_list = []

        for page_number, block_list in self.page_block_dict.items():
            if page_number != self.SPECIAL_PAGE_NUMBER:
                all_block_list.append("(p" + str(page_number) + "s)")
                all_block_list.append("")

            for block in block_list:
                self.line_number += 1

                m = self.placeholder_re.match(block.strip())
                if m:
                    placeholder = m.group("placeholder")
                    line_number = m.group("line_number")
                    if placeholder in self.replacement_dict:
                        placeholder_content = self.replacement_dict[placeholder]
                        del self.replacement_dict[placeholder]

                        orig_line_number = placeholder_content[0]
                        placeholder_content = placeholder_content[1:]

                        if orig_line_number == line_number:
                            all_block_list.append(placeholder)

                        all_block_list.extend(placeholder_content)
                    elif not line_number:
                        all_block_list.append(block)
                else:
                    all_block_list.append(block)

            if page_number != self.SPECIAL_PAGE_NUMBER:
                all_block_list.append("")
                all_block_list.append("(p" + str(page_number) + "e)")
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

        full_html = markdown_processor().markdown_to_full_html(self.normalized_lines)

        joined_markdown_text = "".join(self.normalized_lines)

        if self.markdown_filepath:
            try:
                with open(self.markdown_filepath, "w", encoding="utf-8") as n10notes_markdown:
                    n10notes_markdown.write(joined_markdown_text)
            except:
                pass

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
                self.add_raw_blocks_to_header(["", self.image_list[0][1], ""])
                del self.image_list[0]

        if self.hand_note_list:
            logging.debug("cur ts: " + str(ts) +
                          ", first hand note ts: " + str(self.hand_note_list[0][0]))
            if ts > self.hand_note_list[0][0]:
                self.add_raw_blocks_to_header([""] + self.hand_note_list[0][1] + [""])
                del self.hand_note_list[0]

        if not self.book_filename:
            self.book_filename = notes_header.group("filename")

        self.add_header_blocks_to_page()
        self.cur_page_number = notes_header.group("page_number")

    def process_normal_line(self, line, orig_line):
        if self.line_is_in_code_fence(line):
            logging.debug("fenced code untouched: " + orig_line)
            self.keep_line_untouched(orig_line)
            return

        markdown_marker = self.line_is_markdown(line)
        if markdown_marker:
            if not self.book_title and markdown_marker == "#":
                # level 1 head, treat it as book title
                self.book_title = line[line.index('# ')+2:]
                # actually TOUCHED, title line is replace with an empty line
                self.keep_line_untouched("")
            else:
                self.new_block(line)
            return
        
        if not line:
            logging.debug("empty line")
            self.keep_line_untouched("")
            return

        logging.debug("normal line: " + line)
        self.concat_to_current_block(line)

    def get_raw_text_lines(self):
        if self.n10_notes_filepath:
            logging.debug("get raw text from file " + self.n10_notes_filepath)
            with open(self.n10_notes_filepath, 'r', encoding='utf_8_sig') as n10notes:
                return n10notes.readlines()

        if self.raw_text:
            return self.raw_text.splitlines(keepends=True)

        return None

    def post_process(self):
        self.add_current_block_to_header()

        if self.image_list:
            left_image_blocks = [""]
            for ts, img in self.image_list:
                left_image_blocks.append(img)
                left_image_blocks.append("")
            self.add_raw_blocks_to_header(left_image_blocks)

        if self.hand_note_list:
            left_hand_blocks = [""]
            for ts, note in self.hand_note_list:
                left_hand_blocks.extend(note)
                left_hand_blocks.append("")
            self.add_raw_blocks_to_header(left_hand_blocks)

        self.add_header_blocks_to_page()
        
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
