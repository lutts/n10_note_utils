#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import re
import logging

from markdown_utils import markdown_processor, markdown_processor_mode
from HTMLClipboard import PutHtml


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

        #img1 = '<p><img src="test_image.jpg" alt="x" /></p>'
        #img2 = '<p><img src="./test%20%20%20%20image.jpeg" alt="x" /></p>'
        #img3 = '<p><img src="https://www.ncl.ucar.edu/Images/NCL_NCAR_NSF_banner.png" alt="x" /></p>'
        #img4 = '<p>one <img src="1.png" /> two <img src="2.png" /> not <img src="https://g.com/3.png" /> end</p>'
        img_re = re.compile(r'(?P<prefix><img[ ].*?src="(?!(?:http|ftp)s?://))(?P<imgurl>.*?)(?P<suffix>".*?>)')

        html_body = "\n".join([img_re.sub(
            r'\1http://localhost:8000/\2\3', l) for l in html_body.splitlines()])

        #localhost_lines = []
        #for line in html_body.splitlines():
        #    logging.debug("pre localhost line: " + line)
        #    line = img_re.sub(r'\1http://localhost:8000\2\3', line)
        #    logging.debug("after localhost line: " + line)
        #    localhost_lines.append(line)

        #html_body = "\n".join(localhost_lines)
        
        PutHtml(html_body, "".join(markdown_lines))
    except Exception as e:
        logging.debug("exception: " + str(e))
