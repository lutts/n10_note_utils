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
from clipboard_monitor import py_clipboard_monitor
from playsound import play_success_sound


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
    logging.debug("window title: " + str(cur_filename))

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
    logging.debug("page number ocr: " + page_number_ocr)
    m = page_number_re.search(page_number_ocr)
    if m:
        page_number = m.group(1)
    else:
        m = page_number_fallback_re.search(page_number_ocr)
        if m:
            page_number = m.group(1)
        else:
            page_number = None

    logging.debug("page number: " + str(page_number))

    return page_number


filename_re = re.compile(r'(.*?)\s+-\s+(福\s*昕\s*阅\s*读\s*器|Adobe\s*Acrobat\s*Pro\s*DC\s*\(\s*64\s*-\s*bit\s*\))')


def extract_filename(filename_ocr):
    logging.debug("extract_filename: " + filename_ocr)
    filename = filename_ocr.strip()
    m = filename_re.search(filename)
    if m:
        filename = m.group(1).strip()

    if filename:
        set_current_filename(filename)

    logging.debug("filename: " + str(filename))

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


def append_note(seq_no, note, filename_caps, page_number_caps):
    note_header = get_note_header(filename_caps, page_number_caps)
    notes_filepath = os.path.join(monitor_notes_dir, 'notes.txt')
    with open(notes_filepath, 'a', encoding='utf_8_sig') as f:
        f.write('\n\n')
        f.write(note_header)
        f.write('\n'.join(note.splitlines()))


class LookupDictionaryDecorator:
    def decorate(self, text):
        return None


lookup_dictionary_decorator = LookupDictionaryDecorator()


class MarkdownHeaderDecorator:
    def __init__(self, marker):
        self.marker = marker

    def decorate(self, text):
        return self.marker + ' ' + text


class DecoratorWraper:
    def __init__(self):
        self.cur_decorator = None
        self.last_text = None
        self.last_decorator_removed_text = None
        self.last_timestamp = 0

    def decorate(self, timestamp, text):
        deco_result = text
        if self.cur_decorator:
            deco_result = self.cur_decorator.decorate(text)
            if not deco_result:
                self.last_decorator_removed_text = text
            else:
                self.last_decorator_removed_text = None
            self.cur_decorator = None
        elif text == '{{LookupGoldenDictionary}}':
            self.cur_decorator = lookup_dictionary_decorator
            return None
        elif text in ['#', '##', '###', '####', '#####', '######']:
            self.cur_decorator = MarkdownHeaderDecorator(text)
            return None

        if deco_result:
            if deco_result == self.last_text:
                logging.debug("duplicate text, ignore")
                deco_result = None
            elif timestamp - self.last_timestamp < 0.5 and text == self.last_decorator_removed_text:
                deco_result = None
            else:
                self.last_text = deco_result

        self.last_timestamp = timestamp

        return deco_result


decorator = DecoratorWraper()


def on_text(timestamp, seq_no, text):
    logging.debug("on text, seq_no: " + str(seq_no))

    text = decorator.decorate(timestamp, text)
    if not text:
        return

    filename_caps, page_number_caps = grab_page_number_and_filename_image()
    global q
    q.put(('text', seq_no, text, filename_caps, page_number_caps))


def save_image(seq_no, img):
    img_filename = str(seq_no) + '.png'
    img_filepath = os.path.join(monitor_notes_dir, img_filename)
    img.save(img_filepath, 'PNG')

    #append_note(seq_no, '![x](' + img_filename + ')')


def on_image(timestamp, seq_no, img):
    logging.debug("on image, seq_no: " + str(seq_no))
    global q
    q.put(('image', seq_no, img))


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

    monitor = py_clipboard_monitor(
        on_text=on_text,
        on_image=on_image)
    monitor.listen()


if __name__ == '__main__':
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    #logging.basicConfig(level=logging.DEBUG)

    notes_dir = None
    if len(sys.argv) > 1:
        notes_dir = sys.argv[1]
    start_notes_monitor(notes_dir)
