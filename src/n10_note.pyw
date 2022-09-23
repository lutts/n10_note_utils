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
from markdown_utils import markdown_processor
import css_inline
from HTMLClipboard import PutHtml
import hanzi


# Global variables

# Class declarations

# Function declarations


def uniqe_name(expect_path):
    filename, extension = os.path.splitext(expect_path)
    counter = 1

    while os.path.exists(expect_path):
        expect_path = filename + "(" + str(counter) + ")" + extension
        counter += 1

    return expect_path


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

    HW_NOTES_HEADER_RE = regex.compile(
        r"([0-9]{4})年([0-9]{2})月([0-9]{2})日 ([0-9]{2}):([0-9]{2}):([0-9]{2})  摘自<<(.*?)>> 第([0-9]+)页")
    MARKDOWN_MARKERS = ["* ", "- ", "+ ", "> ", '| ']
    MARKDOWN_ORDERED_LIST_RE = regex.compile(r"[0-9]+\. ")
    HAND_NOTES_HEADER_RE = regex.compile(
        r"([0-9]{4})\.([0-9]{1,2})\.([0-9]{1,2})-([0-9]{1,2}):([0-9]{1,2})")
    code_fence_re = regex.compile(r' {,3}(`{3,}|~{3,})(.*)')
    front_matter_re = regex.compile(r'-{3,}')

    english_punctuation = r'!"#$%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~'

    heading_whitespaces_re = regex.compile(r" +")
    emphasis_normalizer_re = regex.compile(
        r'(?P<asterisks>\*{1,2})(?P<word1>[^*]+?)(?P<punc1>\(|（|\[|【|<|《)(?P<word2>.+?)(?P<punc2>\)|）|\]|】|>|》)(?P=asterisks)')
    space_after_punc_re = regex.compile(
        r'(?P<punc>\.|,|;|:|\?|\!)(?P<word>[^' + english_punctuation + hanzi.punctuation + r'\s]+)')
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
    img_link_re = regex.compile(r'(!?)(?P<text_group>\[(?>[^\[\]]+|(?&text_group))*\])(?P<left_paren>\()(?P<left_angle><)?(?:(?P<url>(?(left_angle).*?>|\S*?))(?:(?P<title_begin>[ ]")(?P<title>(?:[^"]|(?<=\\)")*?)(?P<title_end>"))?(?P<right_paren>\)))')
    double_brace_re = regex.compile(r'(?P<b>\{|\})')

    def __init__(self, n10_notes_filepath, hand_notes_filepath=None,
                 remove_header_line=False,
                 markdown_filepath=None, html_filepath=None):
        self.block = ""
        self.block_list = []
        self.image_list = []
        self.hand_note_list = []
        self.n10_notes_filepath = n10_notes_filepath
        self.hand_notes_filepath = hand_notes_filepath
        self.remove_header_line = remove_header_line

        self.book_title = None

        split_filepath = os.path.splitext(n10_notes_filepath)
        if markdown_filepath:
            self.markdown_filepath = markdown_filepath
        else:
            self.markdown_filepath = uniqe_name(split_filepath[0] + ".md")

        logging.debug("markdown text will write to " + self.markdown_filepath)

        if html_filepath:
            self.html_filepath = html_filepath
        else:
            self.html_filepath = uniqe_name(split_filepath[0] + ".html")

        logging.debug("rendered html file will write to " + self.html_filepath)

    
    def reinit_state(self):
        self.code_fence = None
        self.front_matter = None
        self.line_number = 0

    def line_is_markdown(self, line):
        if not line:
            return False

        if line[0] == "#":
            logging.debug("markdown chapter line: " + line)
            return True
        # check if is markdown lists and blockquotes
        elif line[0:2] in self.MARKDOWN_MARKERS:
            logging.debug("line with markdown marker: " + line)
            return True
        elif self.MARKDOWN_ORDERED_LIST_RE.match(line):
            logging.debug("markdown order list: " + line)
            return True

        return False


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


    def append_prev_block_to_list(self):
        if self.block:
            self.block_list.append(self.block)
            self.block = ""


    def normalize_line(self, line):
        logging.debug("normalize line: " + line)
        heading_spaces = ""
        m = self.heading_whitespaces_re.match(line)
        if m:
            heading_spaces = m.group()

        # indented code block, return the orignal line
        logging.debug("heading space len: " + str(len(heading_spaces)))
        if len(heading_spaces) >= 4:
            return line

        # markdownlint: no trailing spaces
        striped_line = line.rstrip()

        image_or_links = self.img_link_re.findall(striped_line)
        if image_or_links:
            image_or_links = ["".join(i) for i in image_or_links]
            logging.debug("found img or links: " + str(image_or_links))
            striped_line = self.double_brace_re.sub(r'\1\1', striped_line)
            striped_line = self.img_link_re.sub('{}', striped_line)

        # test string: 'a.string,has;no:space?after   punctuation!another, string; has: space? after puctuation! ok!'
        # multiple space between word reduce to one only
        reduced_line = " ".join(striped_line.split())
        striped_line = heading_spaces + reduced_line

        # add a space after some punctuations if there's no one
        striped_line = self.space_after_punc_re.sub(r'\1 \2', striped_line)

        striped_line = self.emphasis_normalizer_re.sub(
                    '\g<asterisks>\g<word1>\g<asterisks>\g<punc1>\g<asterisks>\g<word2>\g<asterisks>\g<punc2>', striped_line)

        if image_or_links:
            striped_line = striped_line.format(*image_or_links)

        logging.debug("normalized result: " + heading_spaces + striped_line + "\n")
        return heading_spaces + striped_line + "\n"


    def write_block_list(self):
        self.append_prev_block_to_list()

        # append the remained images at the end
        if self.image_list:
            self.block_list.append("")
            for ts, img in self.image_list:
                self.block_list.append(img)
                self.block_list.append("")

        if self.hand_note_list:
            self.block_list.append("")
            for ts, note in self.hand_note_list:
                self.block_list.extend(note)
                self.block_list.append("")

        if not self.block_list:
            return

        self.reinit_state()
        normalized_markdown_lines = []
        last_line_is_empty = False

        for line in self.block_list:
            self.line_number += 1

            if self.line_is_in_code_fence(line):
                logging.debug("fenced code remained: " + line)
                normalized_markdown_lines.append(line)
                continue
            
            striped_line = line.strip()
            if not striped_line:
                # markdownlint: no multiple consecutive blank lines
                if not last_line_is_empty:
                    # markdownlint: no trailing spaces
                    normalized_markdown_lines.append("\n")
                    last_line_is_empty = True
                
                continue
            else:
                last_line_is_empty = False

            line = self.normalize_line(line)
            normalized_markdown_lines.append(line)

        # markdownlint: markdown file should end with a single new line
        if not last_line_is_empty:
            normalized_markdown_lines.append("\n")

        full_html = markdown_processor().markdown_to_full_html(normalized_markdown_lines)
        #self.block_list = []

        with open(self.markdown_filepath, "w", encoding="utf-8") as n10notes_markdown:
            n10notes_markdown.write(
                "".join(normalized_markdown_lines))

        with open(self.html_filepath, 'w', encoding="utf-8") as html_file:
            html_file.write(full_html)

        inliner = css_inline.CSSInliner(remove_style_tags=True)
        inlined_html = inliner.inline(full_html)
        PutHtml(inlined_html, "".join(normalized_markdown_lines))


    def get_images_in_directory(self):
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
                    logging.debug(image + " ctime:" + str(os.path.getctime(fullpath)))
                    logging.debug(image + " ctime:" + str(datetime.fromtimestamp(os.path.getctime(fullpath))))
                except Exception as e:
                    logging.debug(e)

                # url in <> to allow space in path names
                self.image_list.append(
                    (os.path.getctime(fullpath), "![x](<" + image + ">)"))

        self.image_list.sort()
        logging.debug("images: " + str(self.image_list))

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
                    if line:
                        cur_notes.append("> " + line)
                    else:  # avoid trailing space
                        cur_notes.append(">")

        if cur_notes:
            self.hand_note_list.append((last_ts, cur_notes))

        self.hand_note_list.sort()
        logging.debug(self.hand_note_list)


    def process(self):
        logging.debug("start process notes file: " + self.n10_notes_filepath)
        if not self.n10_notes_filepath:
            return

        self.get_images_in_directory()
        self.read_hand_notes()

        self.reinit_state()

        last_line_is_header = False

        with open(self.n10_notes_filepath, 'r', encoding='utf_8_sig') as n10notes:
            for line in n10notes:
                self.line_number += 1

                logging.debug("read notes line: " + line)
                orig_line = line

                # only remove trailing whitespaces
                line = line.rstrip()
                # check if is header line
                notes_header = self.HW_NOTES_HEADER_RE.match(line)
                if notes_header:
                    logging.debug("header line: " + line)
                    datetime_obj = datetime(*[int(i) for i in
                                            notes_header.group(1, 2, 3, 4, 5, 6)])
                    logging.debug(datetime_obj)
                    ts = datetime_obj.timestamp()
                    if self.image_list:
                        logging.debug("cur ts: " + str(ts) + ", first img ts: " + str(self.image_list[0][0]))
                        if ts > self.image_list[0][0]:
                            self.block_list.append(self.image_list[0][1])
                            self.block_list.append("")
                            del self.image_list[0]

                    if self.hand_note_list:
                        if ts > self.hand_note_list[0][0]:
                            self.block_list.append("")
                            self.block_list.extend(self.hand_note_list[0][1])
                            self.block_list.append("")
                            del self.hand_note_list[0]

                    if not self.book_title:
                        self.book_title = notes_header.group(7)
                        self.block_list.append("# 摘自:" + self.book_title)
                        self.block_list.append("")

                    if not self.remove_header_line:
                        #self.block = "<sub>" + line + "</sub>\n"
                        # self.append_prev_block_to_list()
                        self.block = "(p" + notes_header.group(8) + ")"
                        last_line_is_header = True
                else:
                    if self.line_is_in_code_fence(line):
                        self.append_prev_block_to_list()
                        if last_line_is_header:
                            self.block_list.append("")
                        # fenced code block is untouched
                        logging.debug("fenced code remained: " + orig_line)
                        self.block_list.append(orig_line)
                        self.block = ""
                    elif self.line_is_markdown(line):
                        self.append_prev_block_to_list()
                        if last_line_is_header:
                            self.block_list.append("")
                        # this line is remained, the following lines is append to this line 
                        # if they do not open another block 
                        self.block = line
                    elif not line:
                        logging.debug("empty line")
                        self.append_prev_block_to_list()
                        # empty line is remained
                        self.block_list.append("")
                        self.block = ""
                    elif line[0:4] == "    ":
                        logging.debug("indented line: " + line)
                        # this line is remained, the following lines is append to this line 
                        # if they do not open another block 
                        self.append_prev_block_to_list()
                        self.block = line
                    else:
                        logging.debug("normal line: " + line)

                        if self.block:
                            if self.block[-1] == "-":
                                if len(self.block) > 1:
                                    # remove trailing hyphen
                                    self.block = self.block[:-1]
                            elif ord(self.block[-1]) < 128:
                                # use space to join english lines
                                self.block += " "

                        self.block += line

                    last_line_is_header = False

        self.write_block_list()


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


# Main body
if __name__ == '__main__':
    main()
