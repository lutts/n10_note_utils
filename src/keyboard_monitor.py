# -*- coding: utf-8 -*-

import os
import logging
import time
import subprocess
import threading
import queue
import ctypes
import tkinter as tk
from tkinter import filedialog
import traceback
import keyboard
from markdown2clipboard import markdown_to_clipboard
from clipboard_utils import clipboard_util, cf_html_helper
from clipboard_monitor import py_clipboard_monitor
from normalize_clipboard import do_normlize_clipboard, clipboard_html_to_markdown
from normalize_clipboard_thebrain import do_normlize_clipboard_thebrain
from note_processor import process_files
from markdown_to_other_app import send_markdown
from markdown_utils import markdown_processor, markdown_processor_mode, uniqe_name
import settings
from supermemo_qa_generator import generate_qa_file
from send_markdown_to_thebrain_from_ahk import do_send_markdown_to_the_brain
from cue_extractor import generate_cornell_cue
from playsound import play_success_sound


worker_queue = queue.Queue()

def delay_to_worker_thread(callback):
    def delay_to_worker():
        global worker_queue
        worker_queue.put(callback)
        return False
    
    return delay_to_worker


def get_dir_file_from_clipboard():
    initial_file = clipboard_util.get_text()
    if not initial_file:
        return (None, None)

    if initial_file.startswith('"') and initial_file.endswith('"'):
        initial_file = initial_file[1:-1]
    if not os.path.exists(initial_file):
        initial_dir = None
        initial_file = None
    elif os.path.isdir(initial_file):
        initial_dir = initial_file
        initial_file = None
    else:
        initial_dir = os.path.dirname(initial_file)
        initial_file = os.path.basename(initial_file)

    return (initial_dir, initial_file) 


def ask_open_filename(multiple=False, filetypes:list=["md"]):
    def get_filetype_tuple(extension):
        if "md" == extension:
            return ("markdown files", "*.md")
        elif "txt" == extension:
            return ("text files", "*.txt")
        elif "*.*" == extension:
            return ("all files", "*.*")

    initial_dir, initial_file = get_dir_file_from_clipboard()
    if initial_file:
        _, ext = os.path.splitext(initial_file)
        ext = ext[1:]

        if ext not in filetypes:
            initial_file = None
            initial_dir = None
        else:
            filetypes.remove(ext)
            filetypes.insert(0, ext)

    filetypes.append("*.*")
    filetypes_opts = tuple([get_filetype_tuple(ext) for ext in filetypes])
    
    filepaths = filedialog.askopenfilename(title="Select file",
                                      multiple=multiple,
                                      filetypes=filetypes_opts,
                                      initialdir=initial_dir,
                                      initialfile=initial_file)
    print("user selected files:")
    print(str(filepaths))

    return filepaths


def ask_directory(title):
    initial_dir, _ = get_dir_file_from_clipboard()
    return filedialog.askdirectory(title=title, initialdir=initial_dir)


http_server_dict:dict[str, subprocess.Popen] = {}


def run_http_server(rootdir, port):
    global http_server_dict

    if port in http_server_dict:
        popen_proc = http_server_dict[port]
        if popen_proc.poll() is None:
            print("http server on port " + port + " already exist!")
            return
        else:
            del http_server_dict[port]

    print("start http server on port " + port)
    popen_proc = subprocess.Popen(['python', '-m', 'http.server', '-d', rootdir, port],
                                  creationflags=subprocess.CREATE_NEW_CONSOLE)
    http_server_dict[port] = popen_proc


def start_http_server_for_supermemo():
    print("start http server for supermemo")
    webroot = settings.get_webroot()
    if webroot:
        run_http_server(rootdir=webroot, port="9999")


def show_msgbox(msg):
    def target_func(m): return tk.messagebox.showinfo(title="info", message=m)

    threading.Thread(target=target_func, args=[msg]).start()

@delay_to_worker_thread
def supermemo_component_to_plain():
    print("supermemo component to plain")
    keyboard.send("ctrl+shift+f12")


@delay_to_worker_thread
def copy_plain_text():
    print("copy plain text")
    success = clipboard_util.put_text("")
    keyboard.send("ctrl+c")
    if success:
        text = py_clipboard_monitor.wait_for_change(1)
    else:
        time.sleep(0.1)
        text = clipboard_util.get_text()
    clipboard_util.put_text(text)


def copy_as_markdown_header(header_marker):
    print("copy as markdown header: " + header_marker)
    success = clipboard_util.put_text(header_marker)
    if success:
        py_clipboard_monitor.wait_for_text(header_marker, 1)
    else:
        time.sleep(0.1)
    keyboard.send("ctrl+c")


@delay_to_worker_thread
def copy_as_markdown_header1():
    copy_as_markdown_header('#')


@delay_to_worker_thread
def copy_as_markdown_header2():
    copy_as_markdown_header('##')


@delay_to_worker_thread
def copy_as_markdown_header3():
    copy_as_markdown_header('###')


@delay_to_worker_thread
def copy_as_markdown_header4():
    copy_as_markdown_header('####')


@delay_to_worker_thread
def copy_as_markdown_header5():
    copy_as_markdown_header('#####')


@delay_to_worker_thread
def copy_as_markdown_header6():
    copy_as_markdown_header('######')


@delay_to_worker_thread
def look_up_dictionary():
    print("look up dictionary")
    marker = "{{LookupGoldenDictionary}}"
    success = clipboard_util.put_text(marker)
    if not success:
        return
    else:
        py_clipboard_monitor.wait_for_text(marker, 1)
    keyboard.send("ctrl+c")
    #time.sleep(0.6)
    py_clipboard_monitor.wait_for_change(2, marker)
    keyboard.send("ctrl+alt+shift+c")


@delay_to_worker_thread
def clipboard_markdown_to_html():
    print("clipboard markdown to html")
    markdown_to_clipboard()


@delay_to_worker_thread
def n10notes_process():
    print("n10 note process")
    fullpaths = ask_open_filename(multiple=True, filetypes=["txt", "md"])
    if not fullpaths:
        return

    process_files(fullpaths)


@delay_to_worker_thread
def send_markdown_to_onenote():
    print("send markdown to onenote")
    filename = ask_open_filename()
    if not filename:
        return

    send_markdown(filename, markdown_processor_mode.ONENOTE)
    dirname = os.path.dirname(filename)
    run_http_server(rootdir=dirname, port="8888")


@delay_to_worker_thread
def list_markdown_latex_equations():
    print("list markdown latex equations")
    filename = ask_open_filename()
    if not filename:
        return

    print("list latex equatioins from " + filename)

    try:
        processor = markdown_processor(markdown_processor_mode.LIST_EQUATION)
        processor.list_latex_equations(filename)
        dirname = os.path.dirname(filename)
        latex_equations_path = os.path.join(dirname, "latex_equations.txt")
        show_msgbox("latex equations saved to " + latex_equations_path)
    except Exception as e:
        traceback.print_exc()


@delay_to_worker_thread
def send_markdown_to_supermemo():
    print("send markdown to supermemo")
    filename = ask_open_filename()
    if not filename:
        return

    print("send " + filename + " to supermemo")
    send_markdown(filename, markdown_processor_mode.SUPERMEMO)
    start_http_server_for_supermemo()



@delay_to_worker_thread
def send_markdown_to_the_brain():
    print("send markdown to the brain")
    filename = ask_open_filename()
    if not filename:
        return

    do_send_markdown_to_the_brain(filename)
    run_http_server(os.path.dirname(filename), "8888")


@delay_to_worker_thread
def normalized_paste():
    print("normalized paste")
    do_normlize_clipboard()
    keyboard.send("ctrl+v")


@delay_to_worker_thread
def normalized_paste_the_brain():
    print("normalized paste to thebrain")
    do_normlize_clipboard_thebrain()
    keyboard.send("ctrl+v")


def is_supermemo_running():
    output = os.popen("wmic process get description").read()
    if 'sm18.exe' in output:
        return True
    else:
        return False


@delay_to_worker_thread
def run_supermemo():
    print("run supermemo")
    if not is_supermemo_running():
        print("supermemo is not running")
        subprocess.Popen(["C:\SuperMemo\sm18.exe"])

    start_http_server_for_supermemo()


notes_monitor_proc = None

@delay_to_worker_thread
def start_note_monitor():
    print("start note monitor")
    global notes_monitor_proc
    script_path = os.path.dirname(__file__)
    is_running = notes_monitor_proc is not None and notes_monitor_proc.poll() is None

    if not is_running:
        notes_dir = ask_directory(title="Select Notes Directory")
        if not notes_dir:
            print("no notes dir selected, do nothing")
            return

        args = ['python',
                os.path.join(script_path, "notes_monitor.py"),
                notes_dir]
        creationflags = subprocess.CREATE_NEW_CONSOLE

        notes_monitor_proc = subprocess.Popen(args, creationflags=creationflags)
    else:
        show_msgbox("notes monitor is already running")


@delay_to_worker_thread
def generate_supermemo_qa():
    print("generate supermemo_qa")
    filename = ask_open_filename()
    if not filename:
        return

    generate_qa_file(filename)


@delay_to_worker_thread
def triggle_italic():
    print("triggle italic")
    keyboard.send("ctrl+i")


@delay_to_worker_thread
def insert_date_time():
    print("insert date time")
    cur_time = time.strftime('%Y年%m月%d日 %H:%M:%S', time.localtime())
    clipboard_util.put_text(cur_time)
    py_clipboard_monitor.wait_for_text(cur_time, 2)
    keyboard.send("ctrl+v")


@delay_to_worker_thread
def extract_questions():
    print("extract questions to cue")
    filename = ask_open_filename()
    if not filename:
        return

    generate_cornell_cue(filename)


@delay_to_worker_thread
def generate_vocabulary_flashcard():
    print("generate vocabulary card")
    filename = ask_open_filename()
    if not filename:
        return

    generate_qa_file(filename,  add_audio=True)


@delay_to_worker_thread
def do_paste_html_as_markdown():
    print("copy html as markdown")
    clipboard_html_to_markdown()
    keyboard.send("ctrl+v")


def get_capslock_state():
    hllDll = ctypes.WinDLL ("User32.dll")
    VK_CAPITAL = 0x14
    return hllDll.GetKeyState(VK_CAPITAL)


def toggle_capslock():
    capslock_state = get_capslock_state()
    print("capslock_state: " + hex(capslock_state))
    capslock_on = capslock_state & 0x1
    if capslock_on:
        keyboard.send('caps lock')


def worker():
    while True:
        callback = worker_queue.get()

        try:
            toggle_capslock()
            callback()
        except:
            print("failed do work in worker")
            traceback.print_exc()

        worker_queue.task_done()

threading.Thread(target=worker, daemon=True).start()

hotkeys = {
    'b': normalized_paste_the_brain,
    'c': copy_plain_text,
    'd': look_up_dictionary,
    'e': triggle_italic,
    'f': generate_vocabulary_flashcard,
    'h': insert_date_time,
    'i': send_markdown_to_the_brain,
    'l': list_markdown_latex_equations,
    'm': clipboard_markdown_to_html,
    'n': start_note_monitor,
    'o': send_markdown_to_onenote,
    'p': n10notes_process,
    'q': generate_supermemo_qa,
    'r': extract_questions,
    's': run_supermemo,
    't': supermemo_component_to_plain,
    'u': send_markdown_to_supermemo,
    'v': normalized_paste,
    'w': do_paste_html_as_markdown,
    '1': copy_as_markdown_header1,
    '2': copy_as_markdown_header2,
    '3': copy_as_markdown_header3,
    '4': copy_as_markdown_header4,
    '5': copy_as_markdown_header5,
    '6': copy_as_markdown_header6
}

def do_hotkey(key_name):
    # print("do hotkey " + key_name)
    try:
        hotkeys[key_name]()
    except Exception as e:
        print("do hotkey failed for " + key_name)
        traceback.print_exc()


#caps_lock_name = "caps lock"
caps_lock_scan_code = 58
#print(keyboard.key_to_scan_codes(caps_lock_name))

class State(object):
    def on_event(self, event: keyboard.KeyboardEvent):
        pass

    def should_continue(self):
        return True


class InitState(State):
    def on_event(self, event: keyboard.KeyboardEvent):
        #if event.event_type == keyboard.KEY_DOWN and event.name == caps_lock_name:
        if event.event_type == keyboard.KEY_DOWN and event.scan_code == caps_lock_scan_code:
            return CapsLockDownState()
        else:
            return self


class TimeoutState(State):
    def __init__(self):
        self.start_time = time.time()

    def on_event(self, event: keyboard.KeyboardEvent):
        if time.time() - self.start_time > 0.5:
            #print("timeout")
            return InitState().on_event(event)
        else:
            return self.handle_event(event)

    def handle_event(self, event: keyboard.KeyboardEvent):
        return None


class CapsLockDownState(TimeoutState):
    def handle_event(self, event: keyboard.KeyboardEvent):
        if event.event_type == keyboard.KEY_DOWN:
            if event.scan_code == caps_lock_scan_code:
                return self

            key_name = event.name.lower()
            if key_name in hotkeys:
                return HotKeyDownState(key_name)

        return InitState()


class HotKeyDownState(TimeoutState):
    def __init__(self, key_name):
        super().__init__()
        self.name = key_name

    def handle_event(self, event: keyboard.KeyboardEvent):
        key_name = event.name.lower()
        if key_name == self.name:
            if event.event_type == keyboard.KEY_DOWN:
                return self
            else:
                return HotKeyUpState(self.name)
        elif event.event_type == keyboard.KEY_UP and event.scan_code == caps_lock_scan_code:
            return CapsLockUpState(self.name)
        else:
            return InitState()

    def should_continue(self):
        return False


class HotKeyUpState(TimeoutState):
    def __init__(self, key_name):
        super().__init__()
        self.name = key_name

    def handle_event(self, event: keyboard.KeyboardEvent):
        if event.event_type == keyboard.KEY_UP and event.scan_code == caps_lock_scan_code:
            do_hotkey(self.name)
        
        return InitState()

    def should_continue(self):
        return False


class CapsLockUpState(TimeoutState):
    def __init__(self, key_name):
        super().__init__()
        self.name = key_name

    def handle_event(self, event: keyboard.KeyboardEvent):
        if event.event_type == keyboard.KEY_UP and event.name.lower() == self.name:
            do_hotkey(self.name)
        
        return InitState()


cur_state = InitState()

def do_keyboard_hook(event: keyboard.KeyboardEvent):
    global cur_state
    cur_state = cur_state.on_event(event)
    return cur_state.should_continue()

def start_keyboard_hook():
    keyboard.hook(callback=do_keyboard_hook, suppress=True)

if __name__ == '__main__':
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    #logging.basicConfig(level=logging.DEBUG)
    
    start_keyboard_hook()

    print("close the console to stop.")
    #keyboard.wait()

    root = tk.Tk()
    root.withdraw()
    #print("use tk mainloop")
    tk.mainloop()
