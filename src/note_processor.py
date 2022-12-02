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
from clipboard_utils import clipboard_util
from text_normalizer import py_text_normalizer
from markdown_normalizer import py_markdown_normalizer


# Global variables

# Class declarations

class NoteBlock:
    replacement_re = regex.compile(r'^\[(?P<placeholder>[^]]+)\]:\.$')
    placeholder_re = regex.compile(r'^\[(?P<placeholder>[^]]+)\](:-)?$')

    follow_marker = "[]:+"
    stick_marker = "[]:."
    delete_marker = "[]:-"

    def __init__(self, filename:str=None, phy_page_number:str=None):
        if filename is None and phy_page_number is None:
            self.is_dummy = True
        else:
            self.is_dummy = False
        
        if not filename or filename == "untitled":
            self.filename = str(uuid.uuid4())
        else:
            self.filename = filename

        if phy_page_number:
            self.phy_page_number = phy_page_number
        else:
            self.phy_page_number = str(uuid.uuid4())

        self.sort_key: str = self.filename + self.phy_page_number

        self.lines : list[str] = []
        self.next : NoteBlock = None

        self.is_cache_block = False

    def make_cache_block(self):
        block = NoteBlock(self.filename, self.phy_page_number)
        block.is_dummy = self.is_dummy
        block.is_cache_block = True
        return block

    def clear(self):
        self.lines = None
        self.next = None

    def add_line(self, line):
        self.lines.append(line)

    def add_multi_line(self, lines:list):
        self.lines.extend(lines)

class NoteProcessStage1:
    def __init__(self):
        self._prev_block : NoteBlock = None
        self._cur_block : NoteBlock = NoteBlock()

        self.ordered_block_dict: OrderedDict[str, list[NoteBlock]] = OrderedDict()
        self.replacement_dict: dict[str, NoteBlock] = {}
        self.filename_dict: dict[str, str] = {}

    def need_add_file_info(self):
        return True

    def check_filename(self, filename):
        if filename not in self.filename_dict:
            num_filenames = len(self.filename_dict.keys())
            self.filename_dict[filename] = str(num_filenames + 1)

    def get_filename_seqno(self, filename):
        if filename in self.filename_dict:
            return '[' + self.filename_dict[filename] + ']'
        else:
            return ''

    def add_cur_block_to_ordered_dict(self):
        sort_key = self._cur_block.sort_key
        if sort_key in self.ordered_block_dict:
            self.ordered_block_dict[sort_key].append(self._cur_block)
        else:
            self.ordered_block_dict[sort_key] = [self._cur_block]
    
    def finish_current_block(self):
        if not self._cur_block.lines:
            self.add_cur_block_to_ordered_dict()
            return

        first_line = self._cur_block.lines[0].strip()
        if first_line == NoteBlock.delete_marker:
            self._cur_block.lines.clear()
        if first_line == NoteBlock.stick_marker:
            del self._cur_block.lines[0]
            self._cur_block.sort_key = self._cur_block.filename + str(uuid.uuid4())
        elif first_line == NoteBlock.follow_marker:
            del self._cur_block.lines[0]
            if self._prev_block:
                self._prev_block.next = self._cur_block
            return
        else:
            m = NoteBlock.replacement_re.match(first_line)
            if m:
                del self._cur_block.lines[0]
                placeholder = m.group('placeholder')
                self.replacement_dict[placeholder] = self._cur_block

        self.add_cur_block_to_ordered_dict()

    def new_block(self, filename:str, phy_page_number:str):
        self.finish_current_block()
        self._prev_block = self._cur_block
        filename, extension = os.path.splitext(filename)
        filename = py_markdown_normalizer.normalize_line(filename, add_newline_char=False)
        filename += extension
        self.check_filename(filename)
        self._cur_block = NoteBlock(filename, phy_page_number)

    def add_line_to_cur_block(self, line:str):
        self._cur_block.add_line(line)

    def add_multi_line_to_cur_block(self, lines:list):
        self._cur_block.add_multi_line(lines)


class N10NoteProcessStage1(NoteProcessStage1):
    def __init__(self, notes_filepath, hand_notes_filepath=None):
        super().__init__()
        self.notes_filepath = notes_filepath
        self.hand_notes_filepath = hand_notes_filepath
        logging.debug("n10 notes_filepath: ")
        logging.debug(notes_filepath)
        logging.debug("n10 hand_note_filepath:")
        logging.debug(hand_notes_filepath)

        self.image_list = []
        self.hand_note_list = []

    def get_images_in_directory(self):
        if not self.notes_filepath:
            return

        curdir = os.path.dirname(self.notes_filepath)
        if curdir == "":
            curdir = "."

        logging.debug("get images in dir: " + curdir)
        # curdir = os.path.abspath(curdir)
        for image in os.listdir(curdir):
            # check if the image ends with png
            if (image.endswith(".png")):
                fullpath = os.path.join(curdir, image)
                try:
                    logging.debug(image + " mtime:" +
                                  str(os.path.getmtime(fullpath)))
                    logging.debug(
                        image + " mtime:" + str(datetime.fromtimestamp(os.path.getmtime(fullpath))))
                except Exception as e:
                    logging.debug(e)

                # url in <> to allow space in path names
                self.image_list.append(
                    (os.path.getmtime(fullpath), "![x](<" + image + ">)"))

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
        r"(?P<year>[0-9]{4})年(?P<month>[0-9]{2})月(?P<day>[0-9]{2})日\s+(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})\s+摘自<<(?P<filename>.*?)>>\s+第(?P<page_number>[0-9]+)页")

    def process_head_line(self, notes_header):
        datetime_obj = datetime(*[int(i) for i in
                                notes_header.group("year", "month", "day", "hour", "minute", "second")])
        logging.debug(datetime_obj)
        ts = datetime_obj.timestamp()

        while self.image_list:
            img_ts, img_md = self.image_list[0]
            logging.debug("cur ts: " + str(ts) +
                          ", first img ts: " + str(img_ts))
            if ts > img_ts:
                self.add_multi_line_to_cur_block(["", img_md, ""])
                del self.image_list[0]
            else:
                break

        while self.hand_note_list:
            hand_ts, hand_notes = self.hand_note_list[0]
            logging.debug("cur ts: " + str(ts) +
                          ", first hand note ts: " + str(hand_ts))
            if ts > hand_ts:
                self.add_line_to_cur_block("")
                self.add_multi_line_to_cur_block(hand_notes)
                self.add_line_to_cur_block("")
                del self.hand_note_list[0]
            else:
                break

        self.new_block(notes_header.group("filename"), notes_header.group("page_number"))
    
    def process(self):
        self.get_images_in_directory()
        self.read_hand_notes()

        with open(self.notes_filepath, 'r', encoding='utf_8_sig') as n10notes:
            for line in n10notes:
                logging.debug("process line: " + line)
                # check if is header line
                notes_header = self.HW_NOTES_HEADER_RE.match(line)
                if notes_header:
                    logging.debug("header line: " + line)
                    self.process_head_line(notes_header)
                else:
                    logging.debug("normal line: " + line)
                    self.add_line_to_cur_block(line)

        if self.image_list:
            left_image_blocks = [""]
            for _, img in self.image_list:
                left_image_blocks.append(img)
                left_image_blocks.append("")
            self.add_multi_line_to_cur_block(left_image_blocks)

        if self.hand_note_list:
            left_hand_blocks = [""]
            for _, note in self.hand_note_list:
                left_hand_blocks.extend(note)
                left_hand_blocks.append("")
            self.add_multi_line_to_cur_block(left_hand_blocks)

        self.finish_current_block()


class RawNoteProcessStage1(NoteProcessStage1):
    def __init__(self, raw_text):
        super().__init__()
        self.raw_text = raw_text

    def need_add_file_info(self):
        return False

    def process(self):
        block = NoteBlock()
        block.lines = self.raw_text.splitlines(keepends=True)
        self.ordered_block_dict["untitled"] = [block]


class NoteProcessStage2:
    CACHE_MODE_NONE:int = 0
    CACHE_MODE_TABLE:int = 1

    def __init__(self, stage1: NoteProcessStage1):
        self.stage1 : NoteProcessStage1 = stage1
        self.title = "# untitled"
        self.markdown_lines : list[str] = []
        self.markdown_normalizer = py_markdown_normalizer()

        self.title_line_pos = 0
        self.cur_line:str = ""
        self.last_line_is_empty = False
        self.last_filename:str = None
        self.last_page_number:str = None

        self.cache_block:NoteBlock = None
        self.cache_mode:int = NoteProcessStage2.CACHE_MODE_NONE

    def get_markdown_lines(self):
        return self.markdown_lines

    def get_replacement_block(self, line:str, line_number:int):
        m = NoteBlock.placeholder_re.match(line.strip())
        if m:
            delete_block = m.group().endswith(':-')
            if delete_block and line_number != 1:
                return (None, False)

            placeholder = m.group('placeholder')
            if placeholder in self.stage1.replacement_dict:
                block = self.stage1.replacement_dict[placeholder]
                return (block, delete_block)
        
        return (None, False)

    def finish_cur_line(self):
        if not self.cur_line:
            return

        self.last_line_is_empty = False
        self.markdown_lines.append(py_markdown_normalizer.normalize_line(self.cur_line))
        self.cur_line = ""

    def add_title_line(self, title):
        self.finish_cur_line()
        self.title = py_markdown_normalizer.normalize_line(title)
        self.markdown_lines.insert(self.title_line_pos, self.title)
        self.last_line_is_empty = False

    def add_literal_line(self, line):
        self.finish_cur_line()
        self.markdown_lines.append(line)
        self.last_line_is_empty = False

    def add_empty_line(self):
        self.finish_cur_line()
        if not self.last_line_is_empty:
            self.markdown_lines.append("\n")    
            self.last_line_is_empty = True

    def new_line(self, line):
        self.finish_cur_line()
        self.cur_line = line

    def concat_line(self, line):
        self.cur_line = py_text_normalizer.concat_line(self.cur_line, line)

    def begin_cache_mode(self, mode, line, ref_block):
        self.finish_cur_line()
        logging.debug("begin cache mode: " + str(mode))
        self.cache_mode = mode
        self.cache_block = ref_block.make_cache_block()
        self.cache_block.add_line(line)

    def end_cache_mode(self):
        if self.cache_mode == NoteProcessStage2.CACHE_MODE_NONE:
            return

        logging.debug("end cache mode: " + str(self.cache_mode))
        last_cache_mode = self.cache_mode
        self.cache_mode = NoteProcessStage2.CACHE_MODE_NONE
        processed = False
        if last_cache_mode == NoteProcessStage2.CACHE_MODE_TABLE:
            processed, lines = py_markdown_normalizer.normalize_table(self.cache_block.lines, strict_mode=True)
            if processed:
                self.last_line_is_empty = False
                self.markdown_lines.extend(lines)
                self.cur_line = ""

        if not processed:
            self.get_block_lines(self.cache_block)
        self.cache_block = None

    def cache_line(self, line:str):
        if self.cache_mode == self.CACHE_MODE_NONE:
            return False

        rstriped_line = line.rstrip()
        if not rstriped_line:
            logging.debug("blank line, end cache mode")
            self.end_cache_mode()
            return False
        else:
            logging.debug("cache line: " + line)
            self.cache_block.add_line(rstriped_line)
            return True

    def process_normal_line(self, line:str, owner_block:NoteBlock):
        logging.debug("process normal line: " + line)
        # trim tailing spaces if not literal line
        rstriped_line = line.rstrip()
        line_type = self.markdown_normalizer.check_line(rstriped_line)
        is_literal_text = False
        if line_type == py_markdown_normalizer.FENCED_CODE_LINE:
            info_string = self.markdown_normalizer.code_fence_info_string
            if info_string == "delete":
                logging.debug("fenced code marked as deleted")
                return

            is_literal_text = True
        elif line_type == py_markdown_normalizer.FRONT_MATTER_LINE:
            self.title_line_pos += 1
            is_literal_text = True
        elif line_type == py_markdown_normalizer.MATH_LINE:
            is_literal_text = True

        if is_literal_text:
            logging.debug("literal text")
            self.add_literal_line(line)
            return

        if line_type:
            if line_type == '#':
                logging.debug("title line")
                self.add_title_line(rstriped_line)
                self.add_empty_line()
            elif not owner_block.is_cache_block and line_type == py_markdown_normalizer.TABLE_LINE:
                self.begin_cache_mode(self.CACHE_MODE_TABLE, rstriped_line, owner_block)
            else:
                logging.debug("markdown line")
                self.new_line(rstriped_line)
        elif not rstriped_line:
            logging.debug("empty line")
            self.add_empty_line()
        else:
            logging.debug("concat line")
            self.concat_line(rstriped_line)

    def add_filename_page_number_info(self, ref_block:NoteBlock):
        if not self.stage1.need_add_file_info():
            return

        if ref_block.filename != self.last_filename or ref_block.phy_page_number != self.last_page_number:
            if self.last_filename:
                self.add_empty_line()
                seqno = self.stage1.get_filename_seqno(self.last_filename)
                self.add_literal_line("(" + seqno + "p" + self.last_page_number + "e)\n")
                self.add_empty_line()
            
            if not ref_block.is_dummy:
                self.add_empty_line()
                seqno = self.stage1.get_filename_seqno(ref_block.filename)
                self.add_literal_line("(" + seqno + "p" + ref_block.phy_page_number + "s)\n")
                self.add_empty_line()
            
                self.last_filename = ref_block.filename
                self.last_page_number = ref_block.phy_page_number

    def get_block_lines(self, block:NoteBlock):
        if not block.lines:
            return

        may_need_filename_page_number_info = True

        lines = block.lines
        followers = block.next
        block.clear()

        line_number = 0
        for line in lines:
            line_number += 1
            replace_block, delete_block = self.get_replacement_block(line, line_number)
            if replace_block:
                logging.debug("replace block fond, end cache mode")
                self.end_cache_mode()
                self.get_block_lines(replace_block)
                if delete_block:
                    break
                
                may_need_filename_page_number_info = True
            else:
                if may_need_filename_page_number_info:
                    self.add_filename_page_number_info(block)
                    may_need_filename_page_number_info = False
                logging.debug("check line: " + line)
                if not self.cache_line(line):
                    self.process_normal_line(line, block)
        
        logging.debug("finished cur block, end cache mode")
        self.end_cache_mode()

        while followers:
            self.get_block_lines(followers)
            followers = followers.next

    def process(self):
        for block_list in self.stage1.ordered_block_dict.values():
            for block in block_list:
                self.get_block_lines(block)

        self.finish_cur_line()

        if self.stage1.need_add_file_info() and self.last_filename:
            self.add_empty_line()
            seqno = self.stage1.get_filename_seqno(self.last_filename)
            self.add_literal_line("(" + seqno + "p" + self.last_page_number + "e)\n")
        
        if self.stage1.filename_dict:
            self.add_empty_line()
            for filename, seqno in self.stage1.filename_dict.items():
                self.add_literal_line('[' + seqno + ']: <' + filename + ">\n")
        else:
            # markdownlint: markdown file should end with a single new line
            logging.debug("last step, check if last_line_is_empty=" + str(self.last_line_is_empty))
            if self.last_line_is_empty:
                self.markdown_lines.pop()


class NotesWriter:
    @staticmethod
    def write_markdown(markdown_lines, markdown_filepath):
        if not markdown_lines:
            return None

        joined_markdown_text = "".join(markdown_lines)

        if markdown_filepath:
            with open(markdown_filepath, "w", encoding="utf-8") as notes_markdown:
                notes_markdown.write(joined_markdown_text)

        return joined_markdown_text

    @staticmethod
    def write_html(markdown_lines, html_filepath):
        if not markdown_lines:
            return None

        full_html = markdown_processor().markdown_to_full_html(markdown_lines)

        if html_filepath:
            with open(html_filepath, 'w', encoding="utf-8") as html_file:
                html_file.write(full_html)

        return full_html

    @staticmethod
    def copy_to_clipboard(markdown_lines, full_html):
        if markdown_lines:
            if isinstance(markdown_lines,  str):
                joined_markdown_text = markdown_lines
            else:
                joined_markdown_text = "".join(markdown_lines)
        else:
            joined_markdown_text = None

        if full_html:
            inliner = css_inline.CSSInliner(remove_style_tags=True)
            inlined_html = inliner.inline(full_html)
        else:
            inlined_html = None

        if inlined_html:
            clipboard_util.put_html(inlined_html, joined_markdown_text)
        elif joined_markdown_text:
            clipboard_util.put_text(joined_markdown_text)

    @staticmethod
    def write(markdown_lines, markdown_filepath, html_filepath=None, copy_to_clipboard=True):
        joined_markdown_text = NotesWriter.write_markdown(markdown_lines, markdown_filepath)
        full_html = NotesWriter.write_html(markdown_lines, html_filepath)
        if copy_to_clipboard:
            NotesWriter.copy_to_clipboard(joined_markdown_text, full_html)


class CornellNotesWriter:
    @staticmethod
    def write(title, markdown_lines, notes_filepath):
        # root, _ = os.path.splitext(notes_filepath)

        # markdown_filepath = uniqe_name(root + ".md")
        # html_filepath = uniqe_name(root + ".html")
        # review_filepath = uniqe_name(root + "_review.md")
        # summary_filepath = uniqe_name(root + "_summary.md")
        # qa_filepath = uniqe_name(root + "_qa.md")

        rootdir = os.path.dirname(notes_filepath)
        markdown_filepath = uniqe_name(os.path.join(rootdir, "notes.md"))
        cue_filepath = uniqe_name(os.path.join(rootdir, "cue.md"))
        summary_filepath = uniqe_name(os.path.join(rootdir, "summary.md"))
        qa_filepath = uniqe_name(os.path.join(rootdir, "qa.md"))
        html_filepath = uniqe_name(os.path.join(rootdir, "notes.html"))

        NotesWriter.write(markdown_lines, markdown_filepath, html_filepath)

        with open(cue_filepath, 'w', encoding="utf-8") as f:
            f.write(title)

        with open(summary_filepath, 'w', encoding="utf-8") as f:
            f.write(title)

        with open(qa_filepath, 'w', encoding="utf-8") as f:
            f.write(title)


class N10NoteProcessor:
    def __init__(self, n10_notes_filepath, hand_notes_filepath=None):
        self.title = None
        self.markdown_lines = None
        self.n10_notes_filepath = n10_notes_filepath
        self.hand_notes_filepath = hand_notes_filepath

    def process(self):
        stage1 = N10NoteProcessStage1(self.n10_notes_filepath, self.hand_notes_filepath)
        stage1.process()
        stage2 = NoteProcessStage2(stage1)
        stage2.process()
        self.title = stage2.title
        self.markdown_lines = stage2.get_markdown_lines()

    def write(self):
        CornellNotesWriter.write(self.title, self.markdown_lines, self.n10_notes_filepath)


class RawNoteProcessor:
    def __init__(self, raw_text):
        self.raw_text = raw_text
        self.markdown_lines = None

    def process(self):
        stage1 = RawNoteProcessStage1(self.raw_text)
        stage1.process()
        stage2 = NoteProcessStage2(stage1)
        stage2.process()

        self.markdown_lines = stage2.get_markdown_lines()


def process_files(fullpaths):
    notes_filepath = None
    hand_notes_filepath = None
    for fullpath in fullpaths:
        logging.debug("file: " + fullpath)
        filename = os.path.basename(fullpath)
        if filename.endswith(".md"):
            markdown_processor().markdown_file_to_html_file(fullpath)
            continue
        elif '摘抄' in filename:
            notes_filepath = fullpath
        else:
            if not notes_filepath:
                notes_filepath = fullpath
            else:
                hand_notes_filepath = fullpath

    if notes_filepath:
        # only one file, it must be notes file
        if notes_filepath == hand_notes_filepath:
            hand_notes_filepath = None
        
        logging.debug("notes_filepath: " + notes_filepath)
        if hand_notes_filepath:
            logging.debug("hand_notes_filepath: " + hand_notes_filepath)

        try:
            processor = N10NoteProcessor(n10_notes_filepath=notes_filepath,
                                     hand_notes_filepath=hand_notes_filepath)
            processor.process()
            processor.write()
        except Exception as e:
            logging.error(str(e))

        logging.debug("process done")


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
        processor.write()


# Main body
if __name__ == '__main__':
    main()
