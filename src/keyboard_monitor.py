import os
import logging
import time
import subprocess
import threading
import queue
import ctypes
from tkinter import filedialog
import keyboard
from markdown2clipboard import markdown_to_clipboard
from clipboard_utils import clipboard_util, cf_html_helper
from clipboard_monitor import py_clipboard_monitor
from normalize_clipboard import do_normlize_clipboard
from normalize_clipboard_thebrain import do_normlize_clipboard_thebrain
from note_processor import process_files
from markdown_to_other_app import send_markdown
from markdown_utils import markdown_processor, markdown_processor_mode, uniqe_name
import settings
from supermemo_qa_generator import generate_qa_file
from send_markdown_to_thebrain_from_ahk import do_send_markdown_to_the_brain


capslock_queue = queue.Queue()


def triggle_capslock_normalizer():
    global capslock_queue
    capslock_queue.put("")


def capslock_normalizer(callback):
    def _normalizer():
        global capslock_queue
        capslock_queue.put(callback)
    
    return _normalizer

    
def ask_open_filename(multiple=False):
    return filedialog.askopenfilename(title="Select file",
                                      multiple=multiple,
                                      filetypes=(("markdown files", "*.md"),
                                                 ("all files", "*.*")))


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


@capslock_normalizer
def supermemo_component_to_plain():
    print("supermemo component to plain")
    keyboard.send("ctrl+shift+f12")


@capslock_normalizer
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


@capslock_normalizer
def copy_as_markdown_header1():
    copy_as_markdown_header('#')


@capslock_normalizer
def copy_as_markdown_header2():
    copy_as_markdown_header('##')


@capslock_normalizer
def copy_as_markdown_header3():
    copy_as_markdown_header('###')


@capslock_normalizer
def copy_as_markdown_header4():
    copy_as_markdown_header('####')


@capslock_normalizer
def copy_as_markdown_header5():
    copy_as_markdown_header('#####')


@capslock_normalizer
def copy_as_markdown_header6():
    copy_as_markdown_header('######')


@capslock_normalizer
def look_up_dictionary():
    print("look up dictionary")
    marker = "{{LookupGoldenDictionary}}"
    success = clipboard_util.put_text(marker)
    if not success:
        return
    else:
        py_clipboard_monitor.wait_for_text(marker, 1)
    keyboard.send("ctrl+c")
    py_clipboard_monitor.wait_for_change(2, marker)
    time.sleep(0.2)
    keyboard.send("ctrl+alt+shift+c")


@capslock_normalizer
def clipboard_markdown_to_html():
    print("clipboard markdown to html")
    markdown_to_clipboard()


@capslock_normalizer
def n10notes_process():
    print("n10 note process")
    fullpaths = ask_open_filename(multiple=True)
    if not fullpaths:
        return

    process_files(fullpaths)


@capslock_normalizer
def send_markdown_to_onenote():
    print("send markdown to onenote")
    filename = ask_open_filename()
    if not filename:
        return

    send_markdown(filename, markdown_processor_mode.ONENOTE)
    dirname = os.path.dirname(filename)
    run_http_server(rootdir=dirname, port="8888")


@capslock_normalizer
def list_markdown_latex_equations():
    print("list markdown latex equations")
    filename = ask_open_filename()
    if not filename:
        return

    logging.debug("list latex equatioins from " + filename)

    try:
        processor = markdown_processor(markdown_processor_mode.LIST_EQUATION)
        processor.list_latex_equations(filename)
        dirname = os.path.dirname()
        latex_equations_path = os.path.join(dirname, "latex_equations.txt")
        print("latex equations saved to " + latex_equations_path)
    except Exception as e:
        logging.debug(str(e))


@capslock_normalizer
def send_markdown_to_supermemo():
    print("send markdown to supermemo")
    filename = ask_open_filename()
    if not filename:
        return

    logging.debug("send " + filename + " to supermemo")
    send_markdown(filename, markdown_processor_mode.SUPERMEMO)
    start_http_server_for_supermemo()



@capslock_normalizer
def send_markdown_to_the_brain():
    print("send markdown to the brain")
    filename = ask_open_filename()
    if not filename:
        return

    do_send_markdown_to_the_brain(filename)
    run_http_server(os.path.dirname(filename), "8888")


@capslock_normalizer
def normalized_paste():
    print("normalized paste")
    do_normlize_clipboard()
    keyboard.send("ctrl+v")


@capslock_normalizer
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


@capslock_normalizer
def run_supermemo():
    print("run supermemo")
    if not is_supermemo_running():
        print("supermemo is not running")
        subprocess.Popen(["C:\SuperMemo\sm18.exe"])

    start_http_server_for_supermemo()


@capslock_normalizer
def start_note_monitor():
    print("start note monitor")
    script_path = os.path.dirname(__file__)
    subprocess.Popen(['python', os.path.join(script_path, "notes_monitor.py")],
                     creationflags=subprocess.CREATE_NEW_CONSOLE)


@capslock_normalizer
def generate_supermemo_qa():
    print("generate supermemo_qa")
    filename = ask_open_filename()
    if not filename:
        return

    generate_qa_file(filename)


keyboard.add_hotkey("caps lock+t",
                    supermemo_component_to_plain,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+c",
                    copy_plain_text,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+1",
                    copy_as_markdown_header1,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+2",
                    copy_as_markdown_header2,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+3",
                    copy_as_markdown_header3,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+4",
                    copy_as_markdown_header4,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+5",
                    copy_as_markdown_header5,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+6",
                    copy_as_markdown_header6,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+d",
                    look_up_dictionary,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+m",
                    clipboard_markdown_to_html,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+p",
                    n10notes_process,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+o",
                    send_markdown_to_onenote,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+l",
                    list_markdown_latex_equations,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+u",
                    send_markdown_to_supermemo,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+i",
                    send_markdown_to_the_brain,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+v",
                    normalized_paste,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+b",
                    normalized_paste_the_brain,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+q",
                    generate_supermemo_qa,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+n",
                    start_note_monitor,
                    suppress=True, trigger_on_release=True)
keyboard.add_hotkey("caps lock+s",
                    run_supermemo,
                    suppress=True, trigger_on_release=True)

def get_capslock_state():
    hllDll = ctypes.WinDLL ("User32.dll")
    VK_CAPITAL = 0x14
    return hllDll.GetKeyState(VK_CAPITAL)
    

def worker():
    while True:
        callback = capslock_queue.get()

        try:
            callback()

            time.sleep(10)

            capslock_state = get_capslock_state()
            print("capslock_state: " + hex(capslock_state))
            capslock_on = capslock_state & 0x1
            capslock_down = capslock_state & 0x8000
            if not capslock_down and capslock_on:
                keyboard.send('caps lock')
        except:
            pass

        capslock_queue.task_done()

threading.Thread(target=worker, daemon=True).start()


print("Press ESC to stop.")
keyboard.wait('esc')
