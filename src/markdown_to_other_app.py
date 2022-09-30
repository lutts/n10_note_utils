#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import re
import logging

from PIL import Image
from markdown_utils import markdown_processor, markdown_processor_mode
from HTMLClipboard import PutHtml


def add_prefix_to_local_images(html, mode, img_dir, img_prefix='http://localhost:8000/'):
    if not img_prefix:
        return html

    #img1 = '<p><img src="test_image.jpg" alt="x" /></p>'
    #img2 = '<p><img src="./test%20%20%20%20image.jpeg" alt="x" /></p>'
    #img3 = '<p><img src="https://www.ncl.ucar.edu/Images/NCL_NCAR_NSF_banner.png" alt="x" /></p>'
    #img4 = '<p>one <img src="1.png" /> two <img src="2.png" /> not <img src="https://g.com/3.png" /> end</p>'
    img_re = re.compile(r'(?P<tag><img[ ])(?P<src_prefix>.*?src="(?!(?:http|ftp)s?://))(?P<imgurl>.*?)(?P<suffix>".*?>)')

    if mode != markdown_processor_mode.SUPERMEMO:
        return "\n".join([img_re.sub(
            r'\g<tag>\g<src_prefix>' + img_prefix + r'\g<imgurl>\g<suffix>', l) for l in html.splitlines()])
    else:
        # supermemo has image scale problem, image will be 2x of the original size
        html_lines = []
        for line in html.splitlines():
            all_imgs = img_re.findall(line)

            img_width = 0
            if len(all_imgs) == 1:
                img_filename = all_imgs[0][2]
                img_width = 0
                try:
                    img = Image.open(os.path.join(img_dir, img_filename))
                    img_width, _ = img.size
                except:
                    pass

            if img_width > 400:
                if img_width <= 600:
                    img_width = img_width * 3 / 4;
                else:
                    img_width /= 2

                line = img_re.sub(r'\g<tag> width="' + str(int(img_width)) +
                                  r'px" \g<src_prefix>' + img_prefix + r'\g<imgurl>\g<suffix>', line)
            else:
                line = img_re.sub(r'\g<tag>\g<src_prefix>' + img_prefix + r'\g<imgurl>\g<suffix>', line)

            html_lines.append(line)

        return "\n".join(html_lines)


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

        html_body = add_prefix_to_local_images(html_body, mode, os.path.dirname(filename))
        
        PutHtml(html_body, "".join(markdown_lines))
    except Exception as e:
        logging.debug("exception: " + str(e))
