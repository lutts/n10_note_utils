# -*- coding: utf-8 -*-

import re
import time
import random
import win32clipboard
import win32con
from io import BytesIO
from PIL import ImageGrab


class cf_html_helper:
    _CF_HTML = None

    MARKER_BLOCK_START_HTML = \
        "Version:(\S+)\s+" \
        "StartHTML:(\d+)\s+"

    START_HTML_RE = re.compile(MARKER_BLOCK_START_HTML)

    BASIC_HTML_FORMAT_HEADER = \
        "Version:0.9\r\n" \
        "StartHTML:{:010d}\r\n" \
        "EndHTML:{:010d}\r\n" \
        "StartFragment:{:010d}\r\n" \
        "EndFragment:{:010d}\r\n"

    BASIC_HTML_FORMAT_HEADER_RE = re.compile(
        "Version:(\S+)\s+"
        "StartHTML:(\d+)\s+"
        "EndHTML:(\d+)\s+"
        "StartFragment:(\d+)\s+"
        "EndFragment:(\d+)\s+")

    def __init__(self):
        self.html = None
        self.fragments = []
        self.extra_info = {}

    def decode(self, clipboard_data):
        dummy_header = cf_html_helper.BASIC_HTML_FORMAT_HEADER.format(0, 0, 0, 0)
        dummy_header_len = len(dummy_header.encode("UTF-8"))

        basic_header = clipboard_data[0:dummy_header_len].decode("UTF-8")

        m = cf_html_helper.START_HTML_RE.match(basic_header)
        if not m:
            print("no recogonizable clip data")
            return

        start_html = int(m.group(2))
        basic_header = clipboard_data[0:start_html].decode("UTF-8")
        #print("basic_header: " + basic_header)
        matches = self.BASIC_HTML_FORMAT_HEADER_RE.match(basic_header)
        if matches:
            self.cf_html_version = matches.group(1)
            start_html = int(matches.group(2))
            end_html = int(matches.group(3))
            start_frag = int(matches.group(4))
            end_frag = int(matches.group(5))

            self.cf_html_header = clipboard_data[0:start_html].decode("UTF-8")

            self.html = clipboard_data[start_html:end_html].decode("UTF-8")
            self.html = self.html.replace(r'<!--StartFragment-->', '')
            self.html = self.html.replace(r'<!--EndFragment-->', '')
            # print("html:" + self.html)
            self.fragments.append(
                clipboard_data[start_frag:end_frag].decode("UTF-8"))
            # print("fragment:###" + self.fragments[0] + "###")

            start_frag = 0
            end_frag = 0

            end_pos = start_html
            start_pos = matches.end()

            header_field_re = re.compile(r'([^:]+):([^\r\n]+)\s+')
            while end_pos > start_pos:
                m = header_field_re.match(self.cf_html_header, start_pos)
                if not m:
                    break

                start_pos = m.end()

                key = m.group(1)
                value = m.group(2)
                #print("key: " + key + ", value: " + value)

                if key == 'StartFragment':
                    start_frag = int(value)
                    continue

                if key == 'EndFragment':
                    end_frag = int(value)
                    frag = clipboard_data[start_frag:end_frag].decode("UTF-8")
                    # print("frag: " + frag)
                    self.fragments.append(frag)
                    continue

                self.extra_info[key] = value
        else:
            print("no recogonizable clip data")

    @staticmethod
    def encode(fragments:list, html_start:str=None, html_end:str=None, source:str=None):
        if not html_start:
            html_start = '<html><body>\n'

        if not html_end:
            html_end = '\n</body></html>'

        cf_html_header = \
            "Version:0.9\n" \
            "StartHTML:{:010d}\n" \
            "EndHTML:{:010d}\n"

        full_html = html_start.encode("UTF-8")

        positions = [0, 0]

        for frag in fragments:
            cf_html_header += "StartFragment:{:010d}\nEndFragment:{:010d}\n"

            full_html += '<!--StartFragment-->\n'.encode("UTF-8")

            start_frag = len(full_html)
            positions.append(start_frag)

            frag = frag.encode("UTF-8")
            end_frag = start_frag + len(frag)
            positions.append(end_frag)

            full_html += frag
            full_html += '\n<!--EndFragment-->'.encode("UTF-8")

        full_html += html_end.encode("UTF-8")
        positions[1] = len(full_html)

        if source:
            cf_html_header += "SourceURL:" + source + "\n"

        dummy_header = cf_html_header.format(*positions)
        positions[0] = len(dummy_header.encode("UTF-8"))

        cf_html_header = cf_html_header.format(*positions)
        cf_html_header = cf_html_header.encode("UTF-8")

        return cf_html_header + full_html

    @staticmethod
    def get_cf_html():
        if cf_html_helper._CF_HTML:
            return cf_html_helper._CF_HTML

        cf_html_helper._CF_HTML = win32clipboard.RegisterClipboardFormat("HTML Format")
        return cf_html_helper._CF_HTML

    @staticmethod
    def is_html_available():
        cf_html = cf_html_helper.get_cf_html()
        if not cf_html:
            return False

        return win32clipboard.IsClipboardFormatAvailable(cf_html)


class clipboard_util:
    @staticmethod
    def _get_data(format):
        cb_opened = False
        clipboard_data = None
        try:
            win32clipboard.OpenClipboard(0)
            cb_opened = True
            clipboard_data = win32clipboard.GetClipboardData(format)
            #print('clipboard_data: ' + clipboard_data)
        except Exception as err:
            clipboard_data = None
            #print(err)
            # If access is denied, that means that the clipboard is in use.
            # Keep trying until it's available.
            # if err.winerror == 5:  # Access Denied
            #     pass
            #     # wait on clipboard because something else has it. we're waiting a
            #     # random amount of time before we try again so we don't collide again
            #     time.sleep(random.random()/50)
            # elif err.winerror == 1418:  # doesn't have board open
            #     pass
            # elif err.winerror == 0:  # open failure
            #     pass
            # else:
            #     print('ERROR in Clipboard section of readcomments: %s' % err)
            #     pass
        finally:
            if cb_opened:
                win32clipboard.CloseClipboard()

        return clipboard_data

    @staticmethod
    def get_data(format):
        data = clipboard_util._get_data(format)
        if data is None:
            for _ in range(2):
                time.sleep(0.02)
                data = clipboard_util._get_data(format)
                if data is not None:
                    return data
        return data

    @staticmethod
    def get_text():
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            return clipboard_util.get_data(win32con.CF_UNICODETEXT)
        else:
            return None

    @staticmethod
    def get_html():
        if not cf_html_helper.is_html_available():
            return None

        cf_html = cf_html_helper.get_cf_html()
        clipboard_data = clipboard_util.get_data(cf_html)
        html_helper = cf_html_helper()
        html_helper.decode(clipboard_data)

        return html_helper.html

    @staticmethod
    def get_image():
        return ImageGrab.grabclipboard()

    @staticmethod
    def _put_data(data_list) -> bool:
        cb_opened = False
        try:
            win32clipboard.OpenClipboard(0)
            cb_opened = True
            win32clipboard.EmptyClipboard()

            for cf_format, cf_content in data_list:
                # print('cf_format: ' + str(cf_format))
                # print('cf_content: ' + str(cf_content))
                win32clipboard.SetClipboardData(cf_format, cf_content)

            return True
        except:
            return False
        finally:
            if cb_opened:
                win32clipboard.CloseClipboard()

    def put_data(data_list) -> bool:
        success = clipboard_util._put_data(data_list)
        if not success:
            for _ in range(2):
                time.sleep(0.02)
                success = clipboard_util._put_data(data_list)
                if success:
                    return success
        return success

    @staticmethod
    def put_text(text):
        if text is None:
            return False
        return clipboard_util.put_data([(win32con.CF_UNICODETEXT, text)])

    @staticmethod
    def put_html_fragements(fragments:list, html_start:str=None, html_end:str=None, source:str=None, text:str=None):
        if not fragments:
            return False

        cf_html = cf_html_helper.get_cf_html()
        if not cf_html:
            return False

        encoded_html = cf_html_helper.encode(
            fragments=fragments, html_start=html_start, html_end=html_end, source=source)
        data_list = [(cf_html, encoded_html)]
        if text:
            data_list.append((win32con.CF_UNICODETEXT, text))
        return clipboard_util.put_data(data_list)

    @staticmethod
    def put_html(html:str, text:str=None):
        if not html:
            return False

        return clipboard_util.put_html_fragements(fragments=[html], text=text)

    @staticmethod
    def put_img(image):
        if not image:
            return False
            
        output = BytesIO()
        image.convert('RGB').save(output, 'BMP')
        data = output.getvalue()[14:]
        output.close()

        return clipboard_util.put_data([(win32con.CF_DIB, data)])


if __name__ == '__main__':
    print(clipboard_util.get_html())
    clipboard_util.put_html(r'<span style="font-weight:bold;">test</span>', 'test')

    img = ImageGrab.grab(bbox=(0, 0, 500, 500))
    clipboard_util.put_img(img)
