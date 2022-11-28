#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import logging

from markdown_utils import markdown_processor, markdown_processor_mode, uniqe_name
from markdown_to_other_app import add_prefix_to_local_images
import webbrowser


def do_send_markdown_to_the_brain(filename):
    logging.debug("send " + filename + " to thebrain")
    processor = markdown_processor(markdown_processor_mode.THEBRAIN, filename)
    full_html = None
    with open(filename, 'r', encoding='utf-8') as m:
        full_html = processor.markdown_to_full_html(m.readlines())

    if not full_html:
        return

    full_html = add_prefix_to_local_images(
        full_html, markdown_processor_mode.THEBRAIN, os.path.dirname(filename))

    split_filepath = os.path.splitext(filename)
    html_filepath = uniqe_name(split_filepath[0] + ".html")

    with open(html_filepath, "w", encoding="utf-8") as html_file:
        html_file.write(full_html)

    return html_filepath


def main():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        logging.debug('no file selected\n')
        sys.exit(1)

    filename = args[0]

    html_filepath = do_send_markdown_to_the_brain(filename)

    webbrowser.open_new_tab(html_filepath)


# Main body
if __name__ == '__main__':
    main()


