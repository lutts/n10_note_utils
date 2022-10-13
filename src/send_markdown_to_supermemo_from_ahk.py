#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import re
import logging

from markdown_to_other_app import send_markdown
from markdown_utils import markdown_processor_mode
import settings
from simple_http_server import start_http_server


def main():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    #logging.basicConfig(level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        logging.debug('no file selected\n')
        sys.exit(1)

    filename = args[0]

    logging.debug("send " + filename + " to supermemo")
    send_markdown(filename, markdown_processor_mode.SUPERMEMO)

    webroot = settings.get_webroot()
    if not webroot:
        webroot = os.path.dirname(filename)

    start_http_server(root_directory=webroot)


# Main body
if __name__ == '__main__':
    main()


