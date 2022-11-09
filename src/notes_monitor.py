# -*- coding: utf-8 -*-

import re
import time
import os
import threading
import queue
import pytesseract
from PIL import ImageGrab
from settings import get_temp_notes_dir, get_tesseract_cmd
from clipboard_monitor import py_clipboard_monitor


last_page_number = 0
last_filename = "untitled"
ignore_next_clip = False
ignore_seqno = 0


q = queue.Queue()


def on_clipboard_update(seq_no, clips, retcode):
    global ignore_next_clip

    if retcode != 0:
        return

    if len(clips) == 0:
        ignore_next_clip = True


def should_seqno_ignored(seqno):
    global ignore_next_clip
    global ignore_seqno

    if ignore_next_clip:
        ignore_seqno = seqno
        ignore_next_clip = False
        return True

    return seqno == ignore_seqno


def grab_page_number_and_filename_image():
    page_number_cap = ImageGrab.grab(bbox=(104, 1858, 299, 1896))
    filename_cap = ImageGrab.grab(bbox=(586, 0, 2641, 57))
    print('page number and filename image grabed.')

    return (page_number_cap, filename_cap)


def get_note_header(page_number_cap, filename_cap):
    global last_page_number
    global last_filename

    # Path of tesseract executable
    pytesseract.pytesseract.tesseract_cmd = get_tesseract_cmd()

    page_number_ocr = pytesseract.image_to_string(
        page_number_cap, lang='eng+chi_sim')
    r = re.compile(r'(\d+)\s*\(\d+\s*/\s*\d+\s*\)')
    m = r.search(page_number_ocr)
    if m:
        page_number = m.group(1)
        last_page_number = page_number
    else:
        page_number = last_page_number
    print("page_number: " + str(page_number))

    filename_ocr = pytesseract.image_to_string(
        filename_cap, lang='eng+chi_sim')
    r = re.compile(r'(.*?)\s*-\s*福\s*昕\s*阅\s*读\s*器')
    m = r.search(filename_ocr)
    if m:
        filename = m.group(1).strip()
    else:
        filename = last_filename
    print("filename: " + filename)

    cur_time = time.strftime('%Y年%m月%d日 %H:%M:%S', time.localtime())

    return cur_time + ' 摘自<<' + filename + '>> 第' + str(page_number) + '页\n'


def append_note(seq_no, note, page_number_cap, filename_cap):
    temp_notes_dir = get_temp_notes_dir()
    if not temp_notes_dir:
        return

    note_header = get_note_header(page_number_cap, filename_cap)
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

    page_number_cap, filename_cap = grab_page_number_and_filename_image()
    global q
    q.put(('text', seq_no, text, page_number_cap, filename_cap))


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
                _, seq_no, note, page_number_cap, filename_cap = item
                append_note(seq_no, note, page_number_cap, filename_cap)
            elif item[0] == 'image':
                _, seq_no, img = item
                save_image(seq_no, img)
        except:
            pass

        q.task_done()


if __name__ == '__main__':
    temp_notes_dir = get_temp_notes_dir()
    print('start notes monitor(' + str(os.getpid()) + ') on temp notes directory: ' + str(temp_notes_dir))
    # Turn-on the worker thread.
    threading.Thread(target=worker, daemon=True).start()

    monitor = py_clipboard_monitor(
        on_text=on_text,
        on_image=on_image,
        on_update=on_clipboard_update)
    monitor.listen()
