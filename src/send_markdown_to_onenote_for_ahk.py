#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import re
import logging

from markdown_to_other_app import send_markdown
from markdown_utils import markdown_processor_mode


def main():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        logging.debug('no file selected\n')
        sys.exit(1)

    filename = args[0]

    logging.debug("send " + filename + " to onenote")
    send_markdown(filename, markdown_processor_mode.ONENOTE)


# Main body
if __name__ == '__main__':
    main()


