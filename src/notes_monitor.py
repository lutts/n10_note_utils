# -*- coding: utf-8 -*-

import pytesseract
from PIL import ImageGrab
from settings import get_temp_notes_dir, get_tesseract_cmd
from clipboard_monitor import py_clipboard_monitor
import re
import time
import os


last_page_number = 0
last_filename = "untitled"


def get_note_header():
    global last_page_number
    global last_filename
    # Path of tesseract executable
    pytesseract.pytesseract.tesseract_cmd = get_tesseract_cmd()
    page_number_cap = ImageGrab.grab(bbox=(104, 1858, 299, 1896))

    page_number_ocr = pytesseract.image_to_string(
        page_number_cap, lang='eng+chi_sim')
    r = re.compile(r'(\d+)\s*\(\d+\s*/\s*\d+\s*\)')
    m = r.search(page_number_ocr)
    if m:
        page_number = m.group(1)
        last_page_number = page_number
    else:
        page_number = last_page_number
    print("page_number: " + page_number)

    filename_cap = ImageGrab.grab(bbox=(586, 0, 2641, 57))
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

    return cur_time + ' 摘自<<' + filename + '>> 第' + page_number + '页\n'


def append_note(seq_no, note):
    print("append note, seq_no: " + str(seq_no))
    temp_notes_dir = get_temp_notes_dir()
    if not temp_notes_dir:
        return

    note_header = get_note_header()
    notes_filepath = os.path.join(temp_notes_dir, 'notes.txt')
    with open(notes_filepath, 'a', encoding='utf_8_sig') as f:
        f.write('\n\n')
        f.write(note_header)
        f.write('\n'.join(note.splitlines()))


def save_image(seq_no, img):
    print("save image, seq_no: " + str(seq_no))
    temp_notes_dir = get_temp_notes_dir()
    if not temp_notes_dir:
        return

    img_filename = str(seq_no) + '.png'
    img_filepath = os.path.join(temp_notes_dir, img_filename)
    img.save(img_filepath, 'PNG')

    #append_note(seq_no, '![x](' + img_filename + ')')


if __name__ == '__main__':
    temp_notes_dir = get_temp_notes_dir()
    print('start notes monitor on temp notes directory: ' + str(temp_notes_dir))
    monitor = py_clipboard_monitor(
        on_text=append_note,
        on_image=save_image)
    monitor.listen()
