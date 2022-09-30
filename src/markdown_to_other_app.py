#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import re
import logging

from markdown_utils import markdown_processor, markdown_processor_mode
from HTMLClipboard import PutHtml


def add_prefix_to_local_images(html, img_prefix='http://localhost:8000/'):
    if not img_prefix:
        return html

    #img1 = '<p><img src="test_image.jpg" alt="x" /></p>'
    #img2 = '<p><img src="./test%20%20%20%20image.jpeg" alt="x" /></p>'
    #img3 = '<p><img src="https://www.ncl.ucar.edu/Images/NCL_NCAR_NSF_banner.png" alt="x" /></p>'
    #img4 = '<p>one <img src="1.png" /> two <img src="2.png" /> not <img src="https://g.com/3.png" /> end</p>'
    img_re = re.compile(r'(?P<prefix><img[ ].*?src="(?!(?:http|ftp)s?://))(?P<imgurl>.*?)(?P<suffix>".*?>)')

    html = "\n".join([img_re.sub(
        r'\1' + img_prefix + r'\2\3', l) for l in html.splitlines()])

    # html_lines = []
    # for line in html.splitlines():
    #     line = img_re.sub(r'\1' + img_prefix + r'\2\3', line)

    #     if 'style="' not in line:
    #         line = line.replace('<img', '<img style="' + img_style + '" ')

    #     html_lines.append(line)

    # html = "\n".join(html_lines)

    return html


def send_markdown(filename: str, mode: markdown_processor_mode):
    try:
        html_body = ""
        markdown_lines = None
        with open(filename, 'r', encoding="utf-8") as f:
            markdown_lines = f.readlines()

        if not markdown_lines:
            return

        processor = markdown_processor(mode, filename)
        html_body = processor.markdown_to_html_with_inline_style(markdown_lines)

        html_body = add_prefix_to_local_images(html_body)
        
        PutHtml(html_body, "".join(markdown_lines))
    except Exception as e:
        logging.debug("exception: " + str(e))
