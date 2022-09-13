#!/user/bin/env python3 -tt
# -*- coding: utf-8 -*-
"""
Module documentation.
"""

# Imports
import sys
import re
import os
from datetime import datetime
#import markdown
#import markdown2
#from markdown_checklist.extension import ChecklistExtension
#import mistletoe
from markdown_it import MarkdownIt
from mdit_py_plugins.tasklists import tasklists_plugin

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


# def markdown_to_html_with_py_markdown(markdown_text):
#    return markdown.markdown("".join(markdown_text), encoding='utf-8',
#                             extensions=['tables', ChecklistExtension()])


# def markdown_to_html_mistletoe(markdown_text):
#    return mistletoe.markdown(markdown_text)


def markdown_to_html(markdown_text):
    md = (
        MarkdownIt()
        .use(tasklists_plugin)
        .enable('strikethrough')
        .enable('table'))
    # print(md.get_all_rules())
    return md.render("".join(markdown_text))


def convert_markdown_to_html(markdown_filepath, html_filepath=None):
    if not html_filepath:
        split_filepath = os.path.splitext(markdown_filepath)
        html_filepath = uniqe_name(split_filepath[0] + ".html")

    text = []
    with open(markdown_filepath, 'r', encoding='utf-8') as m:
        for line in m:
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

            text.append(line)

    html = markdown_to_html(text)

    html_style = """
    <style>
    blockquote {
        font: 14px/22px;
        margin-top: 10px;
        margin-bottom: 10px;
        margin-left: 15px;
        padding-left: 15px;
        border-left: 3px solid #ccc;
        }
    table {
        border-collapse: collapse;
    }
    table td {
        padding: 8px;
    }
    table thead th {
        font-weight: bold;
        border: 1px solid #dddfe1;
    }
    table tbody td {
        border: 1px solid #dddfe1;
    }
    </style>
    """
    with open(html_filepath, "w", encoding="utf-8") as n10notes_html:
        n10notes_html.write("<html>")
        n10notes_html.write(html_style)
        n10notes_html.write("<body>")
        n10notes_html.write(html)
        n10notes_html.write("</body></html>")


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

    HW_NOTES_HEADER_RE = re.compile(
        r"([0-9]{4})年([0-9]{2})月([0-9]){2}日 ([0-9]{2}):([0-9]{2}):([0-9]{2})  摘自<<(.*?)>> 第([0-9]+)页")
    MARKDOWN_MARKERS = ["* ", "- ", "+ ", "> ", '| ']
    MARKDOWN_ORDERED_LIST_RE = re.compile(r"[0-9]+\. ")
    HAND_NOTES_HEADER_RE = re.compile(
        r"([0-9]{4})\.([0-9]{1,2})\.([0-9]{1,2})-([0-9]{1,2}):([0-9]{1,2})")

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

        if html_filepath:
            self.html_filepath = html_filepath
        else:
            self.html_filepath = uniqe_name(split_filepath[0] + ".html")

    def line_is_markdown(self, line):
        if not line:
            return False

        if line[0] == "#":
            #print("markdown chapter line: " + line)
            return True
        # check if is markdown lists and blockquotes
        elif line[0:2] in self.MARKDOWN_MARKERS:
            #print("line with markdown marker: " + line)
            return True
        elif self.MARKDOWN_ORDERED_LIST_RE.match(line):
            #print("markdown order list: " + line)
            return True

        return False

    def append_prev_block_to_list(self):
        if self.block:
            self.block_list.append(self.block)
            self.block = ""

    def write_block_list(self):
        self.append_prev_block_to_list()

        # append the remained images at the end
        if self.image_list:
            self.block_list.append("")
            for ts, img in self.image_list:
                self.block_list.append(img)
                self.block_list.append("")

        if self.block_list:
            last_line_is_empty = False
            if self.book_title:
                no_duplicate_empty_line_block_list = [
                    "# 摘自:" + self.book_title, ""]
            else:
                no_duplicate_empty_line_block_list = []

            emphasis_normalizer = re.compile(
                r'(?P<left>\*{1,2})(?P<word1>.+?)(?P<punc1>\(|（|\[|【|<|《)(?P<word2>.+?)(?P<punc2>\)|）|\]|】|>|》)(?P<right>\*{1,2})')
            for block in self.block_list:
                if not block:
                    if last_line_is_empty:
                        continue

                    last_line_is_empty = True
                else:
                    last_line_is_empty = False

                if block[0:4] != "![](":
                    # test string: 'a.string,has;no:space?after   punctuation!another, string; has: space? after puctuation! ok!'
                    # multiple space between word reduce to one only
                    block = " ".join(block.split())
                    # add a space after some punctuations if there's no one
                    r = re.compile(
                        r'(?P<punc>\.|,|;|:|\?|\!)(?P<word>[^,;:?!.\s]+)')
                    block = r.sub(r'\1 \2', block)

                block = emphasis_normalizer.sub(
                    '\g<left>\g<word1>\g<left>\g<punc1>\g<left>\g<word2>\g<right>\g<punc2>', block)

                no_duplicate_empty_line_block_list.append(block)

            if not no_duplicate_empty_line_block_list:
                return

            # markdownlint: markdown file should end with a single new line
            if no_duplicate_empty_line_block_list[-1]:
                no_duplicate_empty_line_block_list.append("")

            with open(self.markdown_filepath, "w", encoding="utf-8") as n10notes_markdown:
                n10notes_markdown.write(
                    "\n".join(no_duplicate_empty_line_block_list))

            self.block_list = []

            convert_markdown_to_html(
                self.markdown_filepath, self.html_filepath)

    def get_images_in_directory(self):
        curdir = os.path.dirname(self.n10_notes_filepath)
        if curdir == "":
            curdir = "."

        # curdir = os.path.abspath(curdir)
        for image in os.listdir(curdir):
            # check if the image ends with png
            if (image.endswith(".png")):
                #print(image + ":" + str(os.path.getctime(image)))
                # print(datetime.fromtimestamp(os.path.getctime(image)))
                # url in <> to allow space in path names
                self.image_list.append(
                    (os.path.getctime(image), "![x](<" + image + ">)"))

        self.image_list.sort()
        #print("images: ", self.image_list)

    def read_hand_notes(self):
        if not self.hand_notes_filepath:
            return

        last_ts = 0
        cur_notes = []

        with open(self.hand_notes_filepath, 'r', encoding="utf-8") as hand_notes:
            for line in hand_notes:
                #print("hand note: " + line)
                line = line.strip()
                m = self.HAND_NOTES_HEADER_RE.match(line)
                if m:
                    datetime_obj = datetime(*[int(i) for i in
                                            m.group(1, 2, 3, 4, 5)])
                    # print(datetime_obj)
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
        # print(self.hand_note_list)

    def process(self):
        if not self.n10_notes_filepath:
            return

        self.get_images_in_directory()
        self.read_hand_notes()

        last_line_is_header = False

        with open(self.n10_notes_filepath, 'r', encoding='utf_8_sig') as n10notes:
            for line in n10notes:
                # print(line)

                # only remove trailing whitespaces
                line = line.rstrip()
                # check if is header line
                notes_header = self.HW_NOTES_HEADER_RE.match(line)
                if notes_header:
                    #print("header line: " + line)
                    datetime_obj = datetime(*[int(i) for i in
                                            notes_header.group(1, 2, 3, 4, 5, 6)])
                    # print(datetime_obj)
                    ts = datetime_obj.timestamp()
                    if self.image_list:
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

                    if not self.remove_header_line:
                        #self.block = "<sub>" + line + "</sub>\n"
                        # self.append_prev_block_to_list()
                        self.block = "(p" + notes_header.group(8) + ")"
                        last_line_is_header = True

                else:
                    if self.line_is_markdown(line):
                        self.append_prev_block_to_list()
                        if last_line_is_header:
                            self.block_list.append("")
                        self.block = line
                    elif not line:
                        #print("empty line")
                        self.append_prev_block_to_list()
                        # empty line is remained
                        self.block_list.append("")
                        self.block = ""
                    elif line[0:4] == "    ":
                        #print("indented line: " + line)
                        self.append_prev_block_to_list()
                        self.block = line
                    else:
                        #print("normal line: " + line)

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

    if args[0].endswith(".md"):
        convert_markdown_to_html(args[0])
    else:
        processor = N10NoteProcessor(*args)
        processor.process()


# Main body
if __name__ == '__main__':
    main()
