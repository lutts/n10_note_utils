# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import shutil
import os

imgs = """1\\13\\440.png
2\\4\\648.png
2\\5\\655.png
2\\5\\656.png
2\\5\\657.png
2\\5\\658.png
2\\5\\659.png
2\\5\\660.png
2\\6\\661.png
2\\6\\662.png
2\\6\\663.png
2\\6\\665.png
2\\6\\666.png
2\\6\\667.png
2\\6\\662.png
2\\6\\668.png
2\\6\\670.png
2\\7\\671.png
2\\6\\667.png
1\\14\\450.png
1\\13\\440.png
2\\5\\657.png
1\\14\\450.png
2\\5\\659.png
2\\7\\671.png
2\\6\\669.png
2\\12\\730.png
3\\15\\1058.png
3\\15\\1059.png
2\\5\\660.png
2\\6\\661.png
2\\6\\662.png
2\\6\\666.png
2\\6\\668.png
23\\240.png
2\\12\\730.png
3\\15\\1058.png
4\\10\\1306.png
4\\11\\1315.png
3\\15\\1059.png
3\\15\\1060.png
3\\16\\1061.png
"""

def main():
    src_dir = r'D:\Data\supermemo\collections\Lutts\elements'
    dst_dir = r'D:\Data\supermemo\collections\webroot\supermemoimages'
    for img in imgs.splitlines():
        img = img.strip()
        if not img:
            continue

        dst_filename = img.replace("\\", '_')
        dst_path = os.path.join(dst_dir, dst_filename)
        src_path = os.path.join(src_dir, img)

        shutil.copyfile(src_path, dst_path)
        print(img)

# Main body
if __name__ == '__main__':
    main()