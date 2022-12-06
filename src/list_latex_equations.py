#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import logging

from markdown_utils import markdown_processor, markdown_processor_mode

def main():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        sys.exit(1)

    filename = args[0]
    try:
        processor = markdown_processor(markdown_processor_mode.LIST_EQUATION)
        processor.list_latex_equations(filename)
    except Exception as e:
        logging.debug(str(e))

# Main body
if __name__ == '__main__':
    main()


