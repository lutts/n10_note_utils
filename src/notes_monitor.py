# -*- coding: utf-8 -*-

import re
import time
import os
import sys
import threading
import queue
import json
import uuid
import logging
import pytesseract
import win32ui
from PIL import ImageGrab, Image
import settings
from clipboard_utils import cf_html_helper
from clipboard_monitor import py_clipboard_monitor
from playsound import play_success_sound
from normalize_clipboard import markdownify_convert
from markdown_normalizer import py_markdown_normalizer


q = queue.Queue()

single_book_mode : bool = False
ebook_filename = None
ebook_filename_lock = threading.Lock()

foxit_filename_bbox  = settings.get_foxit_filename_region()
foxit_pagenumber_bbox = settings.get_foxit_pagenumber_region()
adobe_filename_bbox = settings.get_adobe_filename_region()
adobe_pagenumber_bbox = settings.get_adobe_pagenumber_region()


monitor_notes_dir = None


def get_current_filename():
    global ebook_filename
    global ebook_filename_lock

    if single_book_mode:
        ebook_filename_lock.acquire()
        cur_filename = ebook_filename
        ebook_filename_lock.release()
    else:
        cur_filename = None

    return cur_filename


def set_current_filename(filename):
    global ebook_filename
    global ebook_filename_lock

    if single_book_mode:
        ebook_filename_lock.acquire()
        ebook_filename = filename
        ebook_filename_lock.release()


def grab_page_number_and_filename_image():
    page_number_caps = []
    if foxit_pagenumber_bbox:
        page_number_caps.append(ImageGrab.grab(bbox=foxit_pagenumber_bbox))

    if adobe_pagenumber_bbox:
        page_number_caps.append(ImageGrab.grab(bbox=adobe_pagenumber_bbox))

    fw = win32ui.GetForegroundWindow()
    cur_filename = fw.GetWindowText()
    logging.debug("window title: %s", str(cur_filename))

    if not cur_filename:
        cur_filename = get_current_filename()

    if not cur_filename:
        filename_caps = []
        if foxit_filename_bbox:
            filename_caps.append(ImageGrab.grab(bbox=foxit_filename_bbox))

        if adobe_filename_bbox:
            filename_caps.append(ImageGrab.grab(bbox=adobe_filename_bbox))
    else:
        filename_caps = [cur_filename]

    logging.debug('page number and filename image grabed.')

    return (filename_caps, page_number_caps)


page_number_re = re.compile(r'\(\s*(\d+)\s+[^\s]*\s+\d+\s*\)')
page_number_fallback_re = re.compile(r'(\d+)\s+[^\s]*\s+\d+')


def get_page_number(page_number_cap):
    if isinstance(page_number_cap, str):
        return page_number_cap

    page_number_ocr = pytesseract.image_to_string(
        page_number_cap, lang='eng')
    logging.debug("page number ocr: %s", str(page_number_ocr))
    m = page_number_re.search(page_number_ocr)
    if m:
        page_number = m.group(1)
    else:
        m = page_number_fallback_re.search(page_number_ocr)
        if m:
            page_number = m.group(1)
        else:
            page_number = None

    logging.debug("page number: %s", str(page_number))

    return page_number


filename_re = re.compile(r'(.*?)\s+-\s+(福\s*昕\s*阅\s*读\s*器|Adobe\s*Acrobat\s*Pro\s*DC\s*\(\s*64\s*-\s*bit\s*\))')


def extract_filename(filename_ocr):
    logging.debug("extract_filename: %s", filename_ocr)
    filename = filename_ocr.strip()
    m = filename_re.search(filename)
    if m:
        filename = m.group(1).strip()

    if filename:
        set_current_filename(filename)

    logging.debug("filename: %s", str(filename))

    return filename


def get_filename(filename_cap):
    if isinstance(filename_cap, str):
        # logging.debug("str cap: " + filename_cap)
        filename = extract_filename(filename_cap)
        if filename:
            return filename

    filename = get_current_filename()

    if not filename:
        filename_ocr = pytesseract.image_to_string(
            filename_cap, lang='eng+chi_sim')
        filename = extract_filename(filename_ocr)

    return filename


def get_note_header(filename_caps, page_number_caps):
    filename = None
    for cap in filename_caps:
        filename = get_filename(cap)
        if filename:
            break

    if not filename:
        logging.debug("failed OCR file name")
        filename = "untitled"

    page_number = None
    for cap in page_number_caps:
        page_number = get_page_number(cap)
        if page_number:
            break

    if not page_number:
        logging.debug("failed OCR page number")
        page_number = 0

    cur_time = time.strftime('%Y年%m月%d日 %H:%M:%S', time.localtime())

    return cur_time + ' 摘自<<' + filename + '>> 第' + str(page_number) + '页\n'


def append_note(note, filename_caps, page_number_caps):
    note_header = get_note_header(filename_caps, page_number_caps)
    notes_filepath = os.path.join(monitor_notes_dir, 'notes.txt')
    with open(notes_filepath, 'a', encoding='utf_8_sig') as f:
        f.write('\n\n')
        f.write(note_header)
        f.write('\n'.join(note.splitlines()))


last_note = None

def on_text(text):
    global last_note
    if last_note:
        if text == last_note:
            return
        else:
            last_note = text

    filename_caps, page_number_caps = grab_page_number_and_filename_image()
    global q
    q.put(('text', text, filename_caps, page_number_caps))


def save_image(seq_no, img):
    img_filename = str(seq_no) + '.png'
    img_filepath = os.path.join(monitor_notes_dir, img_filename)
    img.save(img_filepath, 'PNG')

    #append_note(seq_no, '![x](' + img_filename + ')')


def on_image(seq_no, img):
    logging.debug("on image, seq_no: %s", str(seq_no))
    global q
    q.put(('image', seq_no, img))


class LookupDictionaryDecorator:
    def decorate(self, text):
        return None


lookup_dictionary_decorator = LookupDictionaryDecorator()


class MarkdownHeaderDecorator:
    def __init__(self, marker):
        self.marker = marker

    def decorate(self, text):
        return self.marker + ' ' + text


list_markers_re = re.compile(r'(?P<leading_space>[ ]*)(\*{1,2})(?P<marker>[0-9]+\.|Q:|q:|A:|a:)\2')

def decode_html_to_markdown(clip_html):
    md = None
    try:
        html_helper = cf_html_helper()
        html_helper.decode(clip_html)
        md = markdownify_convert(html_helper.html)
    except:
        pass

    if md:
        md_lines = md.splitlines(keepends=True)
        while not md_lines[0].strip():
            md_lines.pop(0)

        if not md_lines:
            return None

        while not md_lines[-1].strip():
            md_lines.pop()

        if not md_lines:
            return None

        for idx in range(len(md_lines)):
            line = md_lines[idx]
            m = list_markers_re.match(line)
            if m:
                leading_space = m.group('leading_space')
                marker = m.group('marker')
                line = leading_space + marker + line[m.end():]
                md_lines[idx] = line
            
            if py_markdown_normalizer.atx_header_re.match(line):
                md_lines[idx] = py_markdown_normalizer.asterisk_bold_re.sub(r'\2\3', line)

        return ''.join(md_lines)
    else:
        return None
        

class ClipSession:
    def __init__(self, decorator=None):
        self.lock = threading.Lock()
        self.timestamp = None
        self.decorator = decorator
        self.html = None
        self.markdown = None
        self.text = None
        self.finished = False

        self.timer = threading.Timer(0.5, self.finish)

    def cancel_timer(self):
        self.timer.cancel()

    def update(self, timestamp, seq_no, clips):
        if not self.timestamp:
            self.timestamp =  timestamp
            self.timer.start()
        elif timestamp - self.timestamp > 1:
            return True

        clip_html = clips.get_html()
        clip_markdown = None
        if clip_html:
            clip_markdown = decode_html_to_markdown(clip_html)
            #logging.debug("decode |%s| got |%s|", clip_html, clip_markdown)
        clip_text = clips.get_text()

        if self.content_changed(clip_html, clip_text):
            #logging.debug("content changed, finish cur session")
            self.finish()
            return True

        with self.lock:
            self.html = clip_html
            self.markdown = clip_markdown
            self.text = clip_text

            if self.markdown:
                #logging.debug("markdown found, finish cur session")
                self.finish_locked()

    def content_changed(self, clip_html, clip_text):
        if self.html is not None and self.text is not None:
            if self.html == clip_html and self.text == clip_text:
                return False
            else:
                return True
        elif self.html is not None:
            if self.html == clip_html:
                return False
            else:
                return True
        elif self.text is not None:
            if self.text == clip_text:
                return False
            else:
                return True
        else:
            return False

    def finish_locked(self):
        if self.finished:
            return
        self.finished = True

        note = self.markdown
        if not note:
            if self.text:
                note = self.text
            elif self.html:
                note = self.html

        if not note:
            return

        if self.decorator:
            note = self.decorator.decorate(note)

        if note:
            on_text(note)

        self.timer.cancel()

    def finish(self):
        with self.lock:
            self.finish_locked()


def detect_decorator(clips):
    text = clips.get_text()
    if not text:
        return None

    if text == '{{LookupGoldenDictionary}}':
        return lookup_dictionary_decorator
    elif text in ['#', '##', '###', '####', '#####', '######']:
        return MarkdownHeaderDecorator(text)
    
    return None


cur_session = None


def on_update(timestamp, seq_no, clips):
    global cur_session

    if not clips.clips:
        return

    decorator = detect_decorator(clips)
    if decorator:
        if cur_session:
            #logging.debug("decorator found, finish cur session")
            cur_session.finish()
        cur_session = ClipSession(decorator)
        return

    image = clips.get_image()
    if image:
        if cur_session:
            #logging.debug("image found, finish current sesion")
            cur_session.finish()
        cur_session = ClipSession()
        on_image(seq_no, image)
        return
    
    session_changed = True
    if cur_session:
        session_changed = cur_session.update(timestamp, seq_no, clips)

    if session_changed:
        cur_session = ClipSession()
        cur_session.update(timestamp, seq_no,  clips)


def worker():
    while True:
        item = q.get()

        try:
            if item[0] == 'text':
                append_note(*item[1:])
            elif item[0] == 'image':
                save_image(*item[1:])
            threading.Thread(target=play_success_sound).start()
        except:
            pass

        q.task_done()


def start_notes_monitor(notes_dir: str = None):
    global single_book_mode
    global monitor_notes_dir

    monitor_notes_dir = notes_dir

    if monitor_notes_dir:
        try:
            if not os.path.exists(monitor_notes_dir):
                print(monitor_notes_dir + " not exist, create")
                os.makedirs(monitor_notes_dir)
        except:
            print("ERROR: make directory " + monitor_notes_dir + " failed!")
            monitor_notes_dir = None

    if not monitor_notes_dir:
        monitor_notes_dir = settings.get_temp_notes_dir()
    if not monitor_notes_dir:
        print("ERROR: notes directory not specified")
        return

    # Path of tesseract executable
    ocr_cmd = settings.get_tesseract_cmd()
    if ocr_cmd:
        pytesseract.pytesseract.tesseract_cmd = ocr_cmd

    settings_file = os.path.join(monitor_notes_dir, 'notes_monitor_settings.json')
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                setting_json = json.load(f)
                single_book_mode = setting_json.get('single_book_mode')
        except:
            print("ERROR: read notes_monitor_settings.json failed")

    print('start notes monitor(pid: ' + str(os.getpid()) + ')')
    print('temp notes directory: ' + str(monitor_notes_dir))
    print('single_book_mode: ' + str(single_book_mode))
    print('foxit_filename_bbox: ' + str(foxit_filename_bbox))
    print('foxit_pagenumber_bbox: ' + str(foxit_pagenumber_bbox))
    print('adobe_filename_bbox: ' + str(adobe_filename_bbox))
    print('adobe_pagenumber_bbox: ' + str(adobe_pagenumber_bbox))
    # Turn-on the worker thread.
    threading.Thread(target=worker, daemon=True).start()

    monitor = py_clipboard_monitor(on_update=on_update)
    monitor.listen()


if __name__ == '__main__':
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    #logging.basicConfig(level=logging.DEBUG)

    notes_dir = None
    if len(sys.argv) > 1:
        notes_dir = sys.argv[1]
    start_notes_monitor(notes_dir)
