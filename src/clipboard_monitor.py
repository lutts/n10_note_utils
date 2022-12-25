# -*- coding: utf-8 -*-

import win32gui
import win32api
import win32con
import win32clipboard
import threading
import ctypes
import time
import logging
from PIL import ImageGrab
from clipboard_utils import cf_html_helper, clipboard_util


class ClipboardContent:
    def __init__(self):
        self.clips = {}

    def get_text(self):
        return self.clips.get('text')

    def set_text(self, text):
        self.clips['text'] = text

    def get_html(self):
        return self.clips.get('html')

    def set_html(self, html):
        self.clips['html'] = html

    def get_image(self):
        if 'image' in self.clips:
            img = self.clips['image']
            if not img:
                try:
                    img = ImageGrab.grabclipboard()
                    self.clips['image'] = img
                except:
                    pass

            return img
        else:
            return None

    def set_image(self, img=None):
        self.clips['image'] = img


class py_clipboard_monitor:
    def __init__(self,
                 on_text=None,
                 on_image=None,
                 on_html=None,
                 on_update=None,
                 on_finished=None):
        self._on_text = on_text
        self._on_image = on_image
        self._on_html = on_html
        self._on_update = on_update
        self._on_finished = on_finished
        self._clipboard_thread = None
        self.last_seq_no = 0

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
        logging.debug(str(time.time()) + ": update message received: " +
                str(win32clipboard.GetClipboardSequenceNumber()))

        timestamp = time.time()

        seq_no, clips, retcode = self._get_clipboard_content()
        if retcode == -1:
            logging.debug("get clipboard content failed")
            return
        
        if seq_no == self.last_seq_no:
            logging.debug("clipboard sequence number not changed, ignore")
            return
        else:
            self.last_seq_no = seq_no

        try:
            if self._on_update:
                self._on_update(timestamp, seq_no, clips)

            if self._on_text:
                text = clips.get_text()
                if text:
                    self._on_text(timestamp, seq_no, text)

            if self._on_html:
                html = clips.get_html()
                if html:
                    self._on_html(timestamp, seq_no, html)

            if self._on_image:
                img = clips.get_image()
                if img:
                    self._on_image(timestamp, seq_no, img)

            if clips and self._on_finished:
                self._on_finished(timestamp, seq_no, clips)
        except:
            logging.exception("error occured when process clipboard content", exc_info=True)

        return 0

    def _process_message(self, hwnd: int, msg: int, wparam: int, lparam: int):
        WM_CLIPBOARDUPDATE = 0x031D
        logging.debug('msg: ' + hex(msg))
        if msg == WM_CLIPBOARDUPDATE:
            self.on_clipboard_update(hwnd, msg, wparam, lparam)

        return 0

    def _get_clipboard_content(self):
        # sleep 0.5 to avoid clipboard not ready for read
        # time.sleep(0.5)

        seq_no = 0
        clips = ClipboardContent()
        retcode = 0

        cb_opened = False
        try:
            win32clipboard.OpenClipboard()
            cb_opened = True

            seq_no = win32clipboard.GetClipboardSequenceNumber()
            if self._on_text or self._on_update:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    text = win32clipboard.GetClipboardData(
                        win32con.CF_UNICODETEXT)
                    clips.set_text(text)
                elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                    text_bytes = win32clipboard.GetClipboardData(
                        win32con.CF_TEXT)
                    text = text_bytes.decode()
                    clips.set_text(text)

            if self._on_html or self._on_update:
                if cf_html_helper.is_html_available():
                    cf_html = cf_html_helper.get_cf_html()
                    clipboard_data = win32clipboard.GetClipboardData(cf_html)
                    clips.set_html(clipboard_data)

            # if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
            #    files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
            #    clips['files'] = files

            if self._on_image or self._on_update:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_BITMAP):
                    clips.set_image()
        except:
            logging.debug("open clipboard failed")
            retcode = -1
        finally:
            if cb_opened:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    logging.debug("close clipboard error")
                    retcode = -1

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

    @staticmethod
    def wait_for_change(timeout=None, prev_text='', content_getter=clipboard_util.get_text):
        start_time = time.time()
        while True:
            clipboard_text = content_getter()
            if clipboard_text is not None and clipboard_text != prev_text:
                return clipboard_text

            if timeout is not None and time.time() > start_time + timeout:
                return None

            time.sleep(0.01)

    @staticmethod
    def wait_for_text(expect_text, timeout=None):
        start_time = time.time()
        while True:
            clipboard_text = clipboard_util.get_text()
            if clipboard_text == expect_text:
                return True

            if timeout is not None and time.time() > start_time + timeout:
                return False

            time.sleep(0.01)


def test():
    def print_text(seqno, text):
        print("seq" + str(seqno) + ": " + text)
    monitor = py_clipboard_monitor(on_text=print_text)
    monitor.listen()


if __name__ == '__main__':
    test()
