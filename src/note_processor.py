#!/user/bin/env python3 -tt
# -*- coding: utf-8 -*-
"""
Module documentation.
"""

# Imports
import sys
import regex
import os
import bisect
import logging
from datetime import datetime
import css_inline
from collections import OrderedDict
import uuid
import chardet

from markdown_utils import markdown_processor, uniqe_name
from clipboard_utils import clipboard_util
from text_normalizer import py_text_normalizer
from markdown_normalizer import py_markdown_normalizer


def is_filename_untitled(filename):
    return filename == "untitled"


def detect_file_encoding(filepath):
    with open(filepath, 'rb') as f:
        result = chardet.detect(f.read())
        if result['confidence'] > 0.8:
            return result['encoding']

    return None


def read_file_lines(filepath):
    raw_lines = None
    encoding = detect_file_encoding(filepath)
    if encoding:
        try:
            with open(filepath, 'r', encoding=encoding) as notes:
                raw_lines = notes.readlines()
        except:
            pass

    if not raw_lines:
        for encoding in ["utf-8", "utf_8_sig", "utf-16", "utf-16be"]:
            try:
                with open(filepath, 'r', encoding=encoding) as notes:
                    raw_lines = notes.readlines()
            except:
                pass

            if raw_lines:
                break

    return raw_lines

    
class NoteBlock:
    replacement_re = regex.compile(r'^\[(?P<placeholder>[^]]+)\]:\.$')
    placeholder_re = regex.compile(r'^\[(?P<placeholder>[^]]+)\](:-)?$')

    follow_marker = "[]:+"
    stick_marker = "[]:."
    delete_marker = "[]:-"

    def __init__(self, timestamp:float=0, filename:str=None, phy_page_number:str=None):
        self.timestamp = timestamp

        if is_filename_untitled(filename):
            self.filename = str(uuid.uuid4())
        else:
            self.filename = filename

        if phy_page_number == "0":
            self.phy_page_number = str(uuid.uuid4())
        else:
            self.phy_page_number = phy_page_number

        self.sort_key_generated = False
        self._sort_key = None

        self.lines : list[str] = []
        self.next : NoteBlock = None

        self.is_cache_block = False
        self.is_reordered = False
        self.is_follower = False
        self.is_replacement = False

    def is_dummy_block(self):
        return self.timestamp == 0 and self.filename is None and self.phy_page_number is None

    def get_sort_key(self):
        if self.sort_key_generated:
            return self._sort_key

        if self.filename and self.phy_page_number:
            self._sort_key = self.filename + self.phy_page_number
            
        self.sort_key_generated = True
        return self._sort_key

    def random_sort_key(self):
        self._sort_key = str(uuid.uuid4())
        self.sort_key_generated = True

    def make_cache_block(self):
        block = NoteBlock(self.timestamp, self.filename, self.phy_page_number)
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
    DEFAULT_BLOCK_HEADER_RE = regex.compile(
        r"(?P<year>[0-9]{4})年(?P<month>[0-9]{2})月(?P<day>[0-9]{2})日\s*(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})\s*摘自<<(?P<filename>.*?)>>\s*第(?P<page_number>[0-9]+)页")
    DEFAULT_BLOCK_HEADER_DATETIME_RE = regex.compile(
        r"(?P<year>[0-9]{4})年(?P<month>[0-9]{2})月(?P<day>[0-9]{2})日\s*(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})")
    DEFAULT_HAND_NOTES_HEADER_RE = regex.compile(
        r"(?P<year>[0-9]{4})\.(?P<month>[0-9]{1,2})\.(?P<day>[0-9]{1,2})-(?P<hour>[0-9]{1,2}):(?P<minute>[0-9]{1,2})")
    BAIDU_INPUT_DATETIME_RE = regex.compile(
        r"(?P<month>[0-9]{1,2})月(?P<day>[0-9]{1,2})日\s*(?P<hour>[0-9]{1,2}):(?P<minute>[0-9]{1,2}):(?P<second>[0-9]{1,2})")

    def __init__(self):
        self.block_list = []
        self.replacement_dict: dict[str, NoteBlock] = {}
        self.filename_dict: dict[str, str] = {}

        self._prev_block: NoteBlock = None
        self._cur_block: NoteBlock = None
        self.ordered_block_dict: OrderedDict[str, list[NoteBlock]] = OrderedDict()
        self.datetime_ordered_list: list[NoteBlock] = []

    def need_add_file_info(self):
        return True

    def check_filename(self, filename):
        if not filename:
            return

        if is_filename_untitled(filename):
            return

        if filename not in self.filename_dict:
            num_filenames = len(self.filename_dict.keys())
            self.filename_dict[filename] = str(num_filenames + 1)

    def get_filename_seqno(self, filename):
        if filename in self.filename_dict:
            return '[' + self.filename_dict[filename] + ']'
        else:
            return ''

    def check_cur_block_special_markers(self):
        if not self._cur_block.lines:
            return False

        first_line = self._cur_block.lines[0].strip()
        if first_line == NoteBlock.delete_marker:
            self._cur_block.lines.clear()
        if first_line == NoteBlock.stick_marker:
            del self._cur_block.lines[0]
            self._cur_block.random_sort_key()
        elif first_line == NoteBlock.follow_marker:
            del self._cur_block.lines[0]
            if self._prev_block:
                self._prev_block.next = self._cur_block
            self._cur_block.is_follower = True
            return True
        else:
            m = NoteBlock.replacement_re.match(first_line)
            if m:
                del self._cur_block.lines[0]
                placeholder = m.group('placeholder')
                self._cur_block.is_replacement = True
                self.replacement_dict[placeholder] = self._cur_block

        return False

    def add_cur_block_to_ordered_dict(self):
        sort_key = self._cur_block.get_sort_key()
        if not sort_key:
            return

        finished = self.check_cur_block_special_markers()
        if finished:
            return

        if sort_key in self.ordered_block_dict:
            owner_page_blocks = self.ordered_block_dict[sort_key]
            if owner_page_blocks[-1] is not self._prev_block:
                self._cur_block.is_reordered = True
            owner_page_blocks.append(self._cur_block)
        else:
            self.ordered_block_dict[sort_key] = [self._cur_block]

    def finish_current_block(self):
        self.add_cur_block_to_ordered_dict()
        bisect.insort(self.datetime_ordered_list,
                      self._cur_block, key=lambda b: b.timestamp)
        self._prev_block = self._cur_block

    def new_block(self, timestamp:float, filename:str=None, phy_page_number:str=None):
        discard_cur_block = False
        if self._cur_block.is_dummy_block():
            if self._cur_block.lines:
                has_front_matter = py_markdown_normalizer().has_front_matter(self._cur_block.lines)
                if not has_front_matter:
                    self._cur_block.timestamp = timestamp - 0.1

                if filename and phy_page_number:
                    self._cur_block.random_sort_key()
            else:
                discard_cur_block = True

        if not discard_cur_block:
            self.finish_current_block()
        
        if filename:
            filename, extension = os.path.splitext(filename)
            filename = py_markdown_normalizer.normalize_line(filename, add_newline_char=False)
            filename += extension
            self.check_filename(filename)

        self._cur_block = NoteBlock(timestamp, filename, phy_page_number)

    def add_line_to_cur_block(self, line:str):
        self._cur_block.add_line(line)

    def add_multi_line_to_cur_block(self, lines:list):
        self._cur_block.add_multi_line(lines)

    def begin_process_file(self):
        self._prev_block = None
        self._cur_block = NoteBlock()

    def end_process_file(self):
        if self._cur_block.is_dummy_block():
            # dummy block is the only block of this file
            if not self._cur_block.lines:
                return

            self._cur_block.timestamp = datetime(3000, 1, 1).timestamp()
            

        self.finish_current_block()

    def parse_block_header_info(self, line):
        ts = None
        filename = None
        page_number = None
        datetime_items = None

        m = NoteProcessStage1.DEFAULT_BLOCK_HEADER_RE.match(line)
        if m:
            filename = m.group("filename")
            page_number = m.group("page_number")
            datetime_items = [int(i) for i in m.group(
                "year", "month", "day", "hour", "minute", "second")]
        else:
            m = NoteProcessStage1.DEFAULT_BLOCK_HEADER_DATETIME_RE.match(line)
            if m:
                datetime_items = [int(i) for i in m.group(
                    "year", "month", "day", "hour", "minute", "second")]
            else:
                m = NoteProcessStage1.DEFAULT_HAND_NOTES_HEADER_RE.match(line.strip())
                if m:
                    datetime_items = [int(i) for i in m.group(
                        "year", "month", "day", "hour", "minute")]
                else:
                    m = NoteProcessStage1.BAIDU_INPUT_DATETIME_RE.match(line)
                    if m:
                        now = datetime.now()
                        datetime_items = [int(i) for i in m.group(
                            "month", "day", "hour", "minute", "second")]
                        datetime_items.insert(0, now.year)

        if datetime_items:
            datetime_obj = datetime(*datetime_items)
            ts = datetime_obj.timestamp()
 
        return (ts, filename, page_number)

    def process_block_header(self, line):
        ts, filename, page_number = self.parse_block_header_info(line)
        if not ts:
            return False

        self.new_block(ts, filename, page_number)
        return True

    def process_normal_line(self, line):
        self.add_line_to_cur_block(line)

    def process_file(self, filepath):
        raw_lines = read_file_lines(filepath)
        if not raw_lines:
            return

        self.begin_process_file()

        for line in raw_lines:
            if not self.process_block_header(line):
                self.process_normal_line(line)

        self.end_process_file()

    def process(self):
        self.do_process()

        host_block = None
        for block in self.datetime_ordered_list:
            sort_key = block.get_sort_key()
            if not sort_key:
                if host_block:
                    while host_block.next:
                        host_block = host_block.next

                    host_block.next = block
                    host_block = block
                else:
                    self.block_list.append(block)
            elif not block.is_replacement and not block.is_follower and not block.is_reordered:
                host_block = block

        for block_list in self.ordered_block_dict.values():
            for block in block_list:
                self.block_list.append(block)

    def do_process(self):
        pass

class N10NoteProcessStage1(NoteProcessStage1):
    def __init__(self, note_dir,  *note_files):
        super().__init__()
        self.note_dir = note_dir
        self.note_files = note_files

    def get_images_in_directory(self):
        curdir = self.note_dir
        if curdir == "":
            curdir = "."

        # curdir = os.path.abspath(curdir)
        self.begin_process_file()
        for image in os.listdir(curdir):
            # check if the image ends with png
            if image.endswith(".png"):
                fullpath = os.path.join(curdir, image)

                # url in <> to allow space in path names
                self.new_block(os.path.getmtime(fullpath))
                self.add_line_to_cur_block("")
                self.add_line_to_cur_block("![x](<" + image + ">)")
                self.add_line_to_cur_block("")

        self.end_process_file()
    
    def do_process(self):
        self.get_images_in_directory()
        for f in self.note_files:
            self.process_file(f)


class RawNoteProcessStage1(NoteProcessStage1):
    def __init__(self, raw_text):
        super().__init__()
        self.raw_text = raw_text

    def need_add_file_info(self):
        return False

    def process(self):
        block = NoteBlock()
        block.lines = self.raw_text.splitlines(keepends=True)
        self.block_list.append(block)


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
        self.cache_mode = mode
        self.cache_block = ref_block.make_cache_block()
        self.cache_block.add_line(line)

    def end_cache_mode(self):
        if self.cache_mode == NoteProcessStage2.CACHE_MODE_NONE:
            return

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
            self.end_cache_mode()
            return False
        else:
            self.cache_block.add_line(rstriped_line)
            return True

    def process_normal_line(self, line:str, owner_block:NoteBlock):
        # trim tailing spaces if not literal line
        rstriped_line = line.rstrip()
        line_type = self.markdown_normalizer.check_line(rstriped_line)
        is_literal_text = False
        if line_type == py_markdown_normalizer.FENCED_CODE_LINE:
            info_string = self.markdown_normalizer.code_fence_info_string
            if info_string == "delete":
                return

            is_literal_text = True
        elif line_type == py_markdown_normalizer.FRONT_MATTER_LINE:
            self.title_line_pos += 1
            is_literal_text = True
        elif line_type == py_markdown_normalizer.MATH_LINE:
            is_literal_text = True

        if is_literal_text:
            self.add_literal_line(line)
            return

        if line_type:
            if line_type == '#':
                self.add_title_line(rstriped_line)
                self.add_empty_line()
            elif not owner_block.is_cache_block and line_type == py_markdown_normalizer.TABLE_LINE:
                self.begin_cache_mode(self.CACHE_MODE_TABLE, rstriped_line, owner_block)
            else:
                self.new_line(rstriped_line)
        elif not rstriped_line:
            self.add_empty_line()
        else:
            self.concat_line(rstriped_line)

    def add_filename_page_number_info(self, ref_block:NoteBlock):
        if not self.stage1.need_add_file_info():
            return

        if ref_block.filename != self.last_filename or ref_block.phy_page_number != self.last_page_number:
            if self.last_filename and self.last_page_number:
                self.add_empty_line()
                seqno = self.stage1.get_filename_seqno(self.last_filename)
                self.add_literal_line("(" + seqno + "p" + self.last_page_number + "e)\n")
                self.add_empty_line()
            
            if ref_block.filename and ref_block.phy_page_number:
                self.add_empty_line()
                seqno = self.stage1.get_filename_seqno(ref_block.filename)
                self.add_literal_line("(" + seqno + "p" + ref_block.phy_page_number + "s)\n")
                self.add_empty_line()
            
            self.last_filename = ref_block.filename
            self.last_page_number = ref_block.phy_page_number

    def _get_block_lines(self, lines, owner_block:NoteBlock):
        if not lines:
            return

        may_need_filename_page_number_info = True
        line_number = 0
        for line in lines:
            line_number += 1
            replace_block, delete_block = self.get_replacement_block(line, line_number)
            if replace_block:
                self.end_cache_mode()
                self.get_block_lines(replace_block)
                if delete_block:
                    break
                
                may_need_filename_page_number_info = True
            else:
                if may_need_filename_page_number_info:
                    self.add_filename_page_number_info(owner_block)
                    may_need_filename_page_number_info = False
                if not self.cache_line(line):
                    self.process_normal_line(line, owner_block)

    def get_block_lines(self, block:NoteBlock):
        lines = block.lines
        followers = block.next
        block.clear()

        self._get_block_lines(lines, owner_block=block)
        self.end_cache_mode()

        while followers:
            self.get_block_lines(followers)
            followers = followers.next

    def process(self):
        for block in self.stage1.block_list:
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
    def write(title, markdown_lines, notes_dir):
        markdown_filepath = uniqe_name(os.path.join(notes_dir, "notes.md"))
        cue_filepath = uniqe_name(os.path.join(notes_dir, "cue.md"))
        summary_filepath = uniqe_name(os.path.join(notes_dir, "summary.md"))
        qa_filepath = uniqe_name(os.path.join(notes_dir, "qa.md"))
        html_filepath = uniqe_name(os.path.join(notes_dir, "notes.html"))

        NotesWriter.write(markdown_lines, markdown_filepath, html_filepath)

        with open(cue_filepath, 'w', encoding="utf-8") as f:
            f.write(title)

        with open(summary_filepath, 'w', encoding="utf-8") as f:
            f.write(title)

        with open(qa_filepath, 'w', encoding="utf-8") as f:
            f.write(title)


class N10NoteProcessor:
    def __init__(self, n10_notes_filepath, *extra_files):
        self.title = None
        self.markdown_lines = None
        self.notes_dir = os.path.dirname(n10_notes_filepath)
        self.note_files = (n10_notes_filepath, ) + extra_files

    def process(self):
        stage1 = N10NoteProcessStage1(self.notes_dir, *self.note_files)
        stage1.process()
        stage2 = NoteProcessStage2(stage1)
        stage2.process()
        self.title = stage2.title
        self.markdown_lines = stage2.get_markdown_lines()

    def write(self):
        CornellNotesWriter.write(self.title, self.markdown_lines, self.notes_dir)


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
    print("process files: ")
    print(fullpaths)
    none_markdown_files = []
    for fullpath in fullpaths:
        filename = os.path.basename(fullpath)
        if filename.endswith(".md"):
            markdown_processor().markdown_file_to_html_file(fullpath)
            continue
        else:
            none_markdown_files.append(fullpath)

    if not none_markdown_files:
        return

    try:
        processor = N10NoteProcessor(*none_markdown_files)
        processor.process()
        processor.write()
    except Exception as e:
        logging.error(str(e))


def main():
    args = sys.argv[1:]

    if not args:
        print('usage: python3 -m note_processor <txt or md files>')
        sys.exit(1)

    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    #logging.basicConfig(level=logging.DEBUG)

    process_files(args)


# Main body
if __name__ == '__main__':
    main()
