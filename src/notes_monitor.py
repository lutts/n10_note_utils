# -*- coding: utf-8 -*-

import re
import time
import os
import threading
import queue
import json
import pytesseract
from PIL import ImageGrab, Image
from settings import get_temp_notes_dir, get_tesseract_cmd
from clipboard_monitor import py_clipboard_monitor


last_page_number = 0
saved_text = None
last_text = ""

lookup_dictionary_seq_begin = False
ignore_seqno = 0

q = queue.Queue()

single_book_mode : bool = False
ebook_filename = None
ebook_filename_lock = threading.Lock()


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
    foxit_page_number_cap = ImageGrab.grab(bbox=(104, 1858, 299, 1896))
    adobe_page_number_cap = ImageGrab.grab(bbox=(782, 183, 1021, 223))

    cur_filename = get_current_filename()

    if not cur_filename:
        # filename_cap = ImageGrab.grab(bbox=(586, 0, 2641, 57))
        filename_cap = ImageGrab.grab(bbox=(34, 0, 2641, 48))
    else:
        filename_cap = None

    print('page number and filename image grabed.')

    return (foxit_page_number_cap, adobe_page_number_cap, filename_cap)


def get_page_number(page_number_cap):
    if isinstance(page_number_cap, str):
        return page_number_cap

    global last_page_number

    page_number_ocr = pytesseract.image_to_string(
        page_number_cap, lang='eng')
    # print("page number ocr: " + page_number_ocr)
    r = re.compile(r'\(\s*(\d+)\s+[^\s]*\s+\d+\s*\)')
    m = r.search(page_number_ocr)
    if m:
        page_number = m.group(1)
        last_page_number = page_number
        return page_number
    else:
        return None

    return page_number


def get_filename(filename_cap):
    if isinstance(filename_cap, str):
        return filename_cap
        
    filename = get_current_filename()

    if not filename:
        filename_ocr = pytesseract.image_to_string(
            filename_cap, lang='eng+chi_sim')
        print("filename_ocr: " + filename_ocr)
        r = re.compile(r'(.*?)\s+-\s+(福\s*昕\s*阅\s*读\s*器|Adobe\s*Acrobat\s*Pro\s*DC\s*\(\s*64\s*-\s*bit\s*\))')
        m = r.search(filename_ocr)
        if m:
            filename = m.group(1).strip()

            set_current_filename(filename)
        else:
            filename = "untitled"
        print("filename: " + filename)

    return filename


def get_note_header(foxit_page_number_cap, adobe_page_number_cap, filename_cap):
    page_number = get_page_number(foxit_page_number_cap)
    if not page_number:
        page_number = get_page_number(adobe_page_number_cap)
    else:
        if isinstance(filename_cap, Image.Image):
            filename_cap = filename_cap.crop((552, 0, 2607, 48))
    if not page_number:
        print("failed OCR page number")
        page_number = last_page_number
    print("page_number: " + str(page_number))
    filename = get_filename(filename_cap)
    cur_time = time.strftime('%Y年%m月%d日 %H:%M:%S', time.localtime())

    return cur_time + ' 摘自<<' + filename + '>> 第' + str(page_number) + '页\n'


def append_note(seq_no, note, foxit_page_number_cap, adobe_page_number_capp, filename_cap):
    temp_notes_dir = get_temp_notes_dir()
    if not temp_notes_dir:
        return

    note_header = get_note_header(foxit_page_number_cap, adobe_page_number_capp, filename_cap)
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

    foxit_page_number_cap, adobe_page_number_cap, filename_cap = grab_page_number_and_filename_image()
    global q
    q.put(('text', seq_no, text, foxit_page_number_cap, adobe_page_number_cap, filename_cap))


def save_image(seq_no, img):
    temp_notes_dir = get_temp_notes_dir()
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
    temp_notes_dir = get_temp_notes_dir()
    settings_file = os.path.join(temp_notes_dir, 'notes_monitor_settings.json')
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            setting_json = json.load(f)
            single_book_mode = setting_json.get('single_book_mode')

     # Path of tesseract executable
    pytesseract.pytesseract.tesseract_cmd = get_tesseract_cmd()

    print('start notes monitor(pid: ' + str(os.getpid()) + ')')
    print('temp notes directory: ' + str(temp_notes_dir))
    print('single_book_mode: ' + str(single_book_mode))
    # Turn-on the worker thread.
    threading.Thread(target=worker, daemon=True).start()

    monitor = py_clipboard_monitor(
        on_text=on_text,
        on_image=on_image)
    monitor.listen()
