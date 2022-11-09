# -*- coding: utf-8 -*-

import win32gui
import win32api
import win32con
import win32clipboard
import threading
import ctypes
import time
from PIL import ImageGrab
from clipboard_utils import cf_html_helper, clipboard_util


class py_clipboard_monitor:
    def __init__(self,
                 on_text=None,
                 on_image=None,
                 on_html=None,
                 on_update=None,
                 cf_html=None):
        self._on_text = on_text
        self._on_image = on_image
        self._on_html = on_html
        self._on_update = on_update
        self._clipboard_thread = None

        if on_html:
            self._cf_html = cf_html_helper.get_cf_html()
        else:
            self._cf_html = None

    def _create_window(self) -> int:
        """
        Create a window for listening to messages
        :return: window hwnd
        """
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = {0x031D: self.on_clipboard_update}
        wc.lpszClassName = self.__class__.__name__
        wc.hInstance = win32api.GetModuleHandle(None)
        class_atom = win32gui.RegisterClass(wc)
        return win32gui.CreateWindow(
            wc.lpszClassName,
            "py clipboard monitor",
            0,
            0, 0, 0, 0,
            win32con.HWND_MESSAGE,
            0,
            wc.hInstance,
            None)

    def on_clipboard_update(self, hwnd: int, msg: int, wparam: int, lparam: int):
        print("update message received: " +
                str(win32clipboard.GetClipboardSequenceNumber()))

        seq_no, clips, retcode = self._get_clipboard_content()
        print("num clips: " + str(len(clips)))

        if self._on_update:
            self._on_update(seq_no, clips, retcode)

        for clip in clips:
            if clip[0] == 'text' and self._on_text:
                self._on_text(seq_no, clip[1])

            if clip[0] == 'image' and self._on_image:
                try:
                    img = ImageGrab.grabclipboard()
                    self._on_image(seq_no, img)
                except:
                    pass

            if clip[0] == 'html' and self._on_html:
                self._on_html(seq_no, clip[1])

        return 0

    def _process_message(self, hwnd: int, msg: int, wparam: int, lparam: int):
        WM_CLIPBOARDUPDATE = 0x031D
        print('msg: ' + hex(msg))
        if msg == WM_CLIPBOARDUPDATE:
            self.on_clipboard_update(hwnd, msg, wparam, lparam)

        return 0

    def _get_clipboard_content(self):
        # sleep 0.5 to avoid clipboard not ready for read
        # time.sleep(0.5)

        seq_no = 0
        clips = []
        retcode = 0

        cb_opened = False
        try:
            win32clipboard.OpenClipboard()
            cb_opened = True

            seq_no = win32clipboard.GetClipboardSequenceNumber()

            if self._on_text:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    text = win32clipboard.GetClipboardData(
                        win32con.CF_UNICODETEXT)
                    clips.append(('text', text))
                elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                    text_bytes = win32clipboard.GetClipboardData(
                        win32con.CF_TEXT)
                    text = text_bytes.decode()
                    clips.append(('text', text))

            if self._on_html:
                if cf_html_helper.is_html_available():
                    cf_html = cf_html_helper.get_cf_html()
                    clipboard_data = win32clipboard.GetClipboardData(cf_html)
                    html_helper = cf_html_helper()
                    html_helper.decode(clipboard_data)
                    clips.append(('html', html_helper.html))

            # if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
            #    files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
            #    clips.append(('files', files))

            if self._on_image:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_BITMAP):
                    clips.append(('image', None))
        except:
            print("open clipboard failed")
            retcode = -1
        finally:
            if cb_opened:
                win32clipboard.CloseClipboard()

        return (seq_no, clips, retcode)

    def listen(self):
        def runner():
            hwnd = self._create_window()
            ctypes.windll.user32.AddClipboardFormatListener(hwnd)
            win32gui.PumpMessages()

        if not self._clipboard_thread:
            self._clipboard_thread = threading.Thread(
                target=runner, daemon=True)
            self._clipboard_thread.start()
            while self._clipboard_thread.is_alive():
                self._clipboard_thread.join(0.25)


def test():
    def print_text(seqno, text):
        print("seq" + str(seqno) + ": " + text)
    monitor = py_clipboard_monitor(on_text=print_text)
    monitor.listen()


if __name__ == '__main__':
    test()
