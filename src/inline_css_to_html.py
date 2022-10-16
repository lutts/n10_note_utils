# -*- coding: utf-8 -*-

import sys
import os
import css_inline

def main():
    full_html = ""
    with open(r"D:\temp\test_output.html", 'r', encoding='utf-8') as fp:
        full_html = fp.read()

    inliner = css_inline.CSSInliner(remove_style_tags=True)
    inlined_html = inliner.inline(full_html)

    with open(r"D:\temp\test_output_inline.html", 'w', encoding="utf-8") as fp:
        fp.write(inlined_html)

# Main body
if __name__ == '__main__':
    main()