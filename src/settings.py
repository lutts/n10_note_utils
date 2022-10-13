# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import os
import json


def get_webroot():
    script_path = os.path.dirname( __file__ )
    settings_file = os.path.join(script_path, "settings.json")
    
    try:
        with open(settings_file, 'r') as f:
            setting_json = json.load(f)
            return setting_json.get("webroot")
    except:
        pass
    
    return None


def get_imgroot(img_dir):
    settings_file = os.path.join(img_dir, "settings.json")

    if not os.path.exists(settings_file):
        return None

    try:
        with open(settings_file, 'r') as f:
            settings_json = json.load(f)
            return settings_json.get("imgroot")
    except:
        pass
    
    return None


def save_imgroot(img_dir, imgroot):
    settings_file = os.path.join(img_dir, "settings.json")

    if not os.path.exists(settings_file):
        settings_json = { "imgroot" : imgroot}
        with open(settings_file, 'w') as f:
            json.dump(settings_json, f)
    else:
        settings_json = None

        with open(settings_file, 'r') as f:
            settings_json = json.load(f)
        
        setting_json["imgroot"] = imgroot

        with open(settings_file, 'w') as f:
            json.dump(setting_json, f)
