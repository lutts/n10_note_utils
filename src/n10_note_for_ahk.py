#!/user/bin/env python3 -tt
# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import sys
import os
import logging

from note_processor import process_files

def main():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        logging.debug('no file selected\n')
        sys.exit(1)

    args = "".join(args)
    args = args.split("\n")

    logging.debug("###".join(args))

    if len(args) < 2:
        logging.debug("args len < 2")
        sys.exit(1)

    dirname = args[0]

    logging.debug("dirname: " + dirname)

    fullpaths = []
    for filename in args[1:]:
        fullpaths.append(os.path.join(dirname, filename))
    
    process_files(fullpaths)

# Main body
if __name__ == '__main__':
    main()
