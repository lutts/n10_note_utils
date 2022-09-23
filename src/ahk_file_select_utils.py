#!/user/bin/env python3 -tt
# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import os
import logging

def get_file_list(file_args):
    file_args = file_args.split("\n")

    dirname = file_args[0]
    
    file_list = []

    for filename in file_args[1:]:
        file_list.append(os.path.join(dirname, filename))
    
    return file_list
