#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import re
import logging
import shutil
import uuid
import urllib.parse

from PIL import Image
from markdown_utils import markdown_processor, markdown_processor_mode
from HTMLClipboard import PutHtml
import settings


def add_prefix_to_local_images(html, mode, img_dir, img_prefix='http://localhost:9999/'):
    if not img_prefix:
        return html

    #img1 = '<p><img src="./test_image.jpg" alt="x" /></p>'
    #img2 = '<p><img src="./test%20%20%20%20image.jpeg" alt="x" /></p>'
    #img3 = '<p><img src="https://www.ncl.ucar.edu/Images/NCL_NCAR_NSF_banner.png" alt="x" /></p>'
    #img4 = '<p>one <img src="1.png" /> two <img src="2.png" /> not <img src="https://g.com/3.png" /> end</p>'
    img_re = re.compile(r'(?P<tag><img[ ])(?P<src_prefix>.*?src="(?!(?:http|ftp)s?://))(?P<imgurl>.*?)(?P<suffix>".*?>)')

    if mode != markdown_processor_mode.SUPERMEMO:
        return "\n".join([img_re.sub(
            r'\g<tag>\g<src_prefix>' + img_prefix + r'\g<imgurl>\g<suffix>', l) for l in html.splitlines()])
    else:
        webroot = settings.get_webroot()
        imgroot = None
        if webroot:
            imgroot = settings.get_imgroot(img_dir)
            if not imgroot:
                imgroot = str(uuid.uuid4())
                settings.save_imgroot(img_dir, imgroot)

            try:
                join_path = os.path.join(webroot, imgroot)
                if not os.path.exists(join_path):
                    os.mkdir(join_path)
            except:
                imgroot = None
        
        img_idx = 0

        logging.debug("webroot:")
        logging.debug(webroot)
        logging.debug("imgroot:")
        logging.debug(imgroot)

        img_orig_url_to_seq_url = {}

        def modify_image_url(matchobj):
            nonlocal img_idx
            nonlocal img_orig_url_to_seq_url

            img_idx += 1
            tag = matchobj.group("tag")
            src_prefix = matchobj.group("src_prefix")
            imgurl = matchobj.group("imgurl")
            suffix = matchobj.group("suffix")

            if 'style' in suffix or 'style' in src_prefix:
                return matchobj.group()
            else:
                unquoted_imgurl = urllib.parse.unquote(imgurl)
                img_filename = os.path.join(img_dir, unquoted_imgurl)
                img_width = 0
                try:
                    img = Image.open(img_filename)
                    img_width, _ = img.size

                    if imgroot:
                        if img_filename in img_orig_url_to_seq_url:
                            new_basename = img_orig_url_to_seq_url[img_filename]
                        else:
                            old_basename = os.path.basename(img_filename)
                            new_basename = str(img_idx) + "_" + old_basename
                            img_orig_url_to_seq_url[img_filename] = new_basename

                        target_path = os.path.join(webroot, imgroot, new_basename)
                        shutil.copyfile(img_filename, target_path)

                        imgurl = urllib.parse.quote(imgroot + "/" + new_basename)
                except Exception as e:
                    logging.debug(str(e))
                
                if img_width > 400:
                    if img_width <= 600:
                        img_width = img_width * 3 / 4;
                    else:
                        img_width /= 2

                    return tag + 'width="' + str(int(img_width)) + 'px" ' + src_prefix + img_prefix + imgurl + suffix
                else:
                    return tag + src_prefix + img_prefix + imgurl + suffix


        # supermemo has image scale problem, image will be 2x of the original size
        html_lines = []
        for line in html.splitlines():
            line = img_re.sub(modify_image_url, line)
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
