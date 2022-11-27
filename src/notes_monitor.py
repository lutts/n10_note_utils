# -*- coding: utf-8 -*-

import re
import time
import os
import threading
import queue
import json
import uuid
import pytesseract
import win32ui
from PIL import ImageGrab, Image
import settings
from clipboard_monitor import py_clipboard_monitor


saved_text = None
last_text = ""

lookup_dictionary_seq_begin = False
ignore_seqno = 0

q = queue.Queue()

single_book_mode : bool = False
ebook_filename = None
ebook_filename_lock = threading.Lock()

foxit_filename_bbox  = settings.get_foxit_filename_region()
foxit_pagenumber_bbox = settings.get_foxit_pagenumber_region()
adobe_filename_bbox = settings.get_adobe_filename_region()
adobe_pagenumber_bbox = settings.get_adobe_pagenumber_region()


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


def should_seqno_ignored(seqno):
    global ignore_seqno
    if seqno == ignore_seqno:
        return True
    else:
        ignore_seqno = 0
        return False


def grab_page_number_and_filename_image():
    page_number_caps = []
    if foxit_pagenumber_bbox:
        page_number_caps.append(ImageGrab.grab(bbox=foxit_pagenumber_bbox))

    if adobe_pagenumber_bbox:
        page_number_caps.append(ImageGrab.grab(bbox=adobe_pagenumber_bbox))

    fw = win32ui.GetForegroundWindow()
    cur_filename = fw.GetWindowText()
    print("window title: " + str(cur_filename))

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

    print('page number and filename image grabed.')

    return (filename_caps, page_number_caps)


page_number_re = re.compile(r'\(\s*(\d+)\s+[^\s]*\s+\d+\s*\)')
page_number_fallback_re = re.compile(r'(\d+)\s+[^\s]*\s+\d+')


def get_page_number(page_number_cap):
    if isinstance(page_number_cap, str):
        return page_number_cap

    page_number_ocr = pytesseract.image_to_string(
        page_number_cap, lang='eng')
    print("page number ocr: " + page_number_ocr)
    m = page_number_re.search(page_number_ocr)
    if m:
        page_number = m.group(1)
    else:
        m = page_number_fallback_re.search(page_number_ocr)
        if m:
            page_number = m.group(1)
        else:
            page_number = None

    print("page number: " + str(page_number))

    return page_number


filename_re = re.compile(r'(.*?)\s+-\s+(福\s*昕\s*阅\s*读\s*器|Adobe\s*Acrobat\s*Pro\s*DC\s*\(\s*64\s*-\s*bit\s*\))')


def extract_filename(filename_ocr):
    print("extract_filename: " + filename_ocr)
    m = filename_re.search(filename_ocr)
    if m:
        filename = m.group(1).strip()

        set_current_filename(filename)
    else:
        filename = None

    print("filename: " + str(filename))

    return filename


def get_filename(filename_cap):
    if isinstance(filename_cap, str):
        print("str cap: " + filename_cap)
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
    print("get note header")
    filename = None
    for cap in filename_caps:
        filename = get_filename(cap)
        if filename:
            break

    if not filename:
        print("failed OCR file name")
        filename = "untitled"

    page_number = None
    for cap in page_number_caps:
        page_number = get_page_number(cap)
        if page_number:
            break

    if not page_number:
        print("failed OCR page number")
        page_number = 0

    cur_time = time.strftime('%Y年%m月%d日 %H:%M:%S', time.localtime())

    return cur_time + ' 摘自<<' + filename + '>> 第' + str(page_number) + '页\n'


def append_note(seq_no, note, filename_caps, page_number_caps):
    temp_notes_dir = settings.get_temp_notes_dir()
    if not temp_notes_dir:
        return

    note_header = get_note_header(filename_caps, page_number_caps)
    notes_filepath = os.path.join(temp_notes_dir, 'notes.txt')
    with open(notes_filepath, 'a', encoding='utf_8_sig') as f:
        f.write('\n\n')
        f.write(note_header)
        f.write('\n'.join(note.splitlines()))


def on_text(seq_no, text):
    if should_seqno_ignored(seq_no):
        print('ignore seqno ' + str(seq_no))
        return

    print("on text, seq_no: " + str(seq_no))

    global last_text
    if last_text == text:
        print('duplicate text, ignore')
        return
    else:
        last_text = text

    global lookup_dictionary_seq_begin
    global ignore_seqno
    if text == '{{LookupGoldenDictionary}}':
        lookup_dictionary_seq_begin = True
        return
    elif lookup_dictionary_seq_begin:
        lookup_dictionary_seq_begin = False
        ignore_seqno = seq_no
        return
    
    global saved_text
    if text in ['#', '##', '###', '####', '#####', '######']:
        saved_text = text
        return
    elif saved_text:
        text = saved_text + ' ' + text
        saved_text = None

    filename_caps, page_number_caps = grab_page_number_and_filename_image()
    global q
    q.put(('text', seq_no, text, filename_caps, page_number_caps))


def save_image(seq_no, img):
    temp_notes_dir = settings.get_temp_notes_dir()
    if not temp_notes_dir:
        return

    img_filename = str(seq_no) + '.png'
    img_filepath = os.path.join(temp_notes_dir, img_filename)
    img.save(img_filepath, 'PNG')

    #append_note(seq_no, '![x](' + img_filename + ')')


def on_image(seq_no, img):
    if should_seqno_ignored(seq_no):
        print('ignore seqno ' + str(seq_no))
        return

    print("on image, seq_no: " + str(seq_no))
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
        except:
            pass

        q.task_done()


if __name__ == '__main__':
    temp_notes_dir = settings.get_temp_notes_dir()
    settings_file = os.path.join(temp_notes_dir, 'notes_monitor_settings.json')
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            setting_json = json.load(f)
            single_book_mode = setting_json.get('single_book_mode')

     # Path of tesseract executable
    pytesseract.pytesseract.tesseract_cmd = settings.get_tesseract_cmd()

    print('start notes monitor(pid: ' + str(os.getpid()) + ')')
    print('temp notes directory: ' + str(temp_notes_dir))
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
