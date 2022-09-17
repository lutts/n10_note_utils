#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import re
import logging

from markdown2clipboard import markdown_to_clipboard

def main():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        logging.debug('no file selected\n')
        sys.exit(1)

    filename = args[0]

    logging.debug("send " + filename + "to onenote")

    try:
        img_re = re.compile(r'(?P<linkhead>!\[.*?\]\(<{,1})(?P<linkurl>.*?)(?P<linktail>>{,1}\)|>{,1} ".*?"\))')
        lines = []
        with open(filename, 'r', encoding="utf-8") as f:
            for line in f:
                line = img_re.sub(r'\1http://localhost:8000/\2\3', line)
                lines.append(line)

        markdown_to_clipboard(lines)
    except Exception as e:
        logging(str(e))

# Main body
if __name__ == '__main__':
    main()


