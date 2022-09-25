#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import logging

from markdown_utils import markdown_processor, markdown_processor_mode


def main():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        logging.debug('no file selected\n')
        sys.exit(1)

    filename = args[0]

    logging.debug("send " + filename + " to thebrain")
    processor = markdown_processor(markdown_processor_mode.SUPERMEMO)
    processor.markdown_file_to_html_file(filename)


# Main body
if __name__ == '__main__':
    main()


