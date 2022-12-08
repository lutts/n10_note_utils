# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import os
import json
import re


def _get_key_value(key):
    script_path = os.path.dirname( __file__ )
    settings_file = os.path.join(script_path, "settings.json")
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            setting_json = json.load(f)
            return setting_json.get(key)
    except:
        pass
    
    return None


def get_webroot():
    webroot = _get_key_value("webroot")
    if webroot:
        try:
            if not os.path.exists(webroot):
                os.makedirs(webroot)
        except:
            webroot = None
        
    return webroot


def get_temp_notes_dir():
    temp_notes_dir = _get_key_value("temp_notes_dir")
    if temp_notes_dir:
        try:
            if not os.path.exists(temp_notes_dir):
                os.makedirs(temp_notes_dir)
        except:
            temp_notes_dir = None
    
    return temp_notes_dir


def get_tesseract_cmd():
    return _get_key_value("tesseract_cmd")


def get_bbox(key):
    v = _get_key_value(key)
    #print("get bbox for " + key + ", " + v)
    bbox_re = re.compile(r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)')
    m = bbox_re.match(v)
    if m:
        left = int(m.group(1))
        top = int(m.group(2))
        right = int(m.group(3))
        bottom = int(m.group(4))

        return (left, top, right, bottom)
    
    return None


def get_foxit_filename_region():
    return get_bbox("foxit_filename_region")


def get_foxit_pagenumber_region():
    return get_bbox("foxit_page_number_region")


def get_adobe_filename_region():
    return get_bbox("adobe_filename_region")


def get_adobe_pagenumber_region():
    return get_bbox("adobe_page_number_region")


def get_imgroot(img_dir):
    settings_file = os.path.join(img_dir, "settings.json")

    if not os.path.exists(settings_file):
        return None

    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings_json = json.load(f)
            return settings_json.get("imgroot")
    except:
        pass
    
    return None


def save_imgroot(img_dir, imgroot):
    settings_file = os.path.join(img_dir, "settings.json")

    if not os.path.exists(settings_file):
        settings_json = { "imgroot" : imgroot}
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings_json, f)
    else:
        settings_json = {}

        with open(settings_file, 'r') as f:
            settings_json = json.load(f)
        
        settings_json["imgroot"] = imgroot

        with open(settings_file, 'w') as f:
            json.dump(settings_json, f)
