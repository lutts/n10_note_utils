# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import re
import hanzi
import unicodedata
import string

class py_text_normalizer:
    punctuation_and_numbers = string.punctuation + hanzi.punctuation + '0123456789'
    blank_line_re = re.compile(r'^\s*$')

    en_to_ch_punc_map = {

    }

    ch_to_en_punc_map = {
        
    }

    @staticmethod
    def is_blank_line(line):
        if py_text_normalizer.blank_line_re.match(line):
            return True
        return False

    @staticmethod
    def is_chinese_char(char):
        if '\u4e00' < char and char < '\u9fd5':
            return True

    @staticmethod
    def normalize_text_line(line):
        # test string: 'a.string,has;no:space?after   punctuation!another, string; has: space? after puctuation! ok!'
        # 多个连续的空格只保留一个，同时也保证后续的处理不会碰到连续的空格
        # 这一操作还有几个副作用:
        # 1. 行首和行尾的空白字符会被去掉
        # 2. tab等空白字符都会被去掉，整个字符串中的空白字符就只剩下英文空格了
        line = " ".join(line.split())

        line_len = len(line)
        if line_len <= 2:
            return line

        chars = []
        skip_next_char = False

        for idx in range(0, line_len):
            if skip_next_char:
                skip_next_char = False
                continue

            if idx == 0:
                prev_char = ' '
            else:
                prev_char = chars[-1]
            cur_char = line[idx]

            if idx + 1 < line_len:
                next_char = line[idx + 1]
            else:
                next_char = ' '

            if idx + 2 < line_len:
                next_next_char = line[idx + 2]
            else:
                next_next_char = ' '

            # 如果是空格，要判断是否需要删掉
            if cur_char == ' ':
                # CJK Unified Ideographs: 4E00 — 9FFF, 但后面有几个没用，只到9fd5
                # 中英文之间需要增加空格: 中 chinese 文
                # 中文与数字之间需要增加空格: 花了 5000 元
                # 基于这两点，只有在中文之间存在空格时才会去掉空格，如果中文字符后面是数字、英文、标点之类的，则不会
                # test string: Hey Jane, 周 末 要 不要一起 吃早茶，叫上 Jennie 和 Jone, 预计花费 100 元
                if py_text_normalizer.is_chinese_char(prev_char) and py_text_normalizer.is_chinese_char(next_char):
                    # 删除
                    continue
            
                # 中文标点前后都不需要空格
                if prev_char in hanzi.punctuation: 
                    continue

                if next_char in hanzi.punctuation:
                    continue

                if prev_char == ' ':
                    continue

                # 英文小括号（暂时不考虑中括号、大括号、尖括号，太复杂了）
                if prev_char == '(':
                    continue
                if next_char == ')':
                    continue

                chars.append(cur_char)
            elif cur_char in ['.', ',', ';', ':', '?', '!']:
                chars.append(cur_char)
                if next_char != ' ' and next_char not in py_text_normalizer.punctuation_and_numbers:
                    chars.append(' ')
            elif cur_char in ['\u2018', '\u201c']:  # left single/double quotation mark
                next_nonspace_char = next_char
                if next_char == ' ':
                    next_nonspace_char = next_next_char
                    skip_next_char = True

                if not py_text_normalizer.is_chinese_char(next_nonspace_char) and next_nonspace_char not in hanzi.punctuation:
                    if prev_char != ' ':
                        chars.append(' ')
                    if cur_char == '\u2018':
                        chars.append("'")
                    else:
                        chars.append('"')
                else:
                    chars.append(cur_char)
            elif cur_char in ['\u2019', '\u201d']: # right single/double quotation mark
                if not py_text_normalizer.is_chinese_char(prev_char) and prev_char not in hanzi.punctuation:
                    if cur_char == '\u2019':
                        chars.append("'")
                    else:
                        chars.append('"')
                else:
                    chars.append(cur_char)
            elif cur_char == '（':  # 中文左括号
                next_nonspace_char = next_char
                if next_char == ' ':
                    next_nonspace_char = next_next_char
                    skip_next_char = True

                if not py_text_normalizer.is_chinese_char(next_nonspace_char) and next_nonspace_char not in hanzi.punctuation:
                    if prev_char != ' ':
                        chars.append(' ')

                    chars.append('(')
                else:
                    chars.append(cur_char)
            elif cur_char == '）': # 中文右括号
                if not py_text_normalizer.is_chinese_char(prev_char) and prev_char not in hanzi.punctuation:
                    chars.append(')')
                else:
                    chars.append(cur_char)
            elif '\ufb00' < cur_char and cur_char < '\ufb12':
                # Alphabetic Presentation Forms is a Unicode block containing standard ligatures
                ligature_chars = unicodedata.normalize('NFKD', cur_char)
                chars.extend(list(ligature_chars))
            else:
                chars.append(cur_char)

        return ''.join(chars)

    @staticmethod
    def concat_line(line1, line2):
        if not line1:
            return line2

        last_char = line1[-1]
        if last_char == "-":
            line1 = line1[:-1]
        elif last_char == '\u2019' or last_char == '\u201d' or ord(last_char) < 128:
            # use space to join english lines
            line1 += " "
        
        return line1 + line2