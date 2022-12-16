# -*- coding: utf-8 -*-
"""
Module documentation.
"""

import re
import hanzi
import unicodedata
import string
import logging


NULL_CHAR = '\0'
LINE_END_CHAR = '\n'
NONE_CONTEXT = 0
FULL_WIDTH_CONTEXT = 1
HALF_WIDTH_CONTEXT = 2


############### half width chars #######################
basic_latin = '[0-9A-Za-z]'
latin1_supplement = '[\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u00FF]'
latin_extendedA = '[\\u0100-\\u017F]'
latin_extendedB = '[\\u0180-\\u01BF\\u01C4-\\u024F]'
half_width_chars = '|'.join(
    [basic_latin, latin1_supplement, latin_extendedA, latin_extendedB])
half_width_re = re.compile(half_width_chars)


def is_half_width_char(c):
    return half_width_re.match(c)


def char_is_number(c):
    return '0' <= c and c <= '9'


def char_is_letter(c):
    return ('A' <= c and c <= 'Z') or ('a' <= c and c <= 'z')


############### full width chars #######################
hiragana = '[\\u3040-\\u309F]'
katakana = '[\\u30A0-\\u30FF]'
cjk_unified_ideographs = '[\\u4E00-\\u9FFF]'
cjk_unified_ideographsA = '[\\u3400-\\u4DBF]'
cjk_unified_ideographsB = '[\\ud840-\\ud868][\\udc00-\\udfff]|\\ud869[\\udc00-\\uded6]'
full_width_chars = '|'.join([hiragana, katakana, cjk_unified_ideographs,
                             cjk_unified_ideographsA, cjk_unified_ideographsB])
full_width_re = re.compile(full_width_chars)


def is_full_width_char(c):
    return full_width_re.match(c)


############### punctuations #######################
all_punctuations = string.punctuation + hanzi.punctuation
regular_space = ' '

left_parens = '([{<'
right_parens = ')]}>'

left_smart_quotes = "\u2018\u201c"
right_smart_quotes = "\u2019\u201d"
all_smart_quotes = left_smart_quotes + right_smart_quotes
right_single_quote = '\u2019'
all_quotes = all_smart_quotes + "'\""

stops = hanzi.stops + '.?!'
extra_stops = '」﹂”』’》）］｝〕〗〙〛〉】' + right_parens + regular_space
all_stops = stops + extra_stops

puncs_need_space_after = '.?!,;:'
number_delimiters = ',:.'
puncs_unaware_space = '"#$%&\'*+-/=@\\^`|~'

contraction_suffix_re = re.compile(r'\s*(d|m|s|t|re|ve|ll)(\s+|$)')
o_clock_re = re.compile(r"o\s*’\s*clock(\s+|$)", re.IGNORECASE)
blank_line_re = re.compile(r'^\s*$')


def char_is_punctuation(c):
    return c in all_punctuations


def punc_is_half_width(punc):
    return punc in string.punctuation


def punc_is_full_width(punc):
    return punc in hanzi.punctuation


############### punctuation convertions #######################
half_punc_to_full = {
    ',': '\uFF0C',
    ':': '\uFF1A',
    ';': '\uFF1B',
    '_': '\uFF3F',

    '!': '\uFF01',
    '?': '\uFF1F',
    '.': '\u3002',
}

full_punc_to_half = {
    '\uFF0C': ',',
    '\uFF1A': ':',
    '\uFF1B': ';',
    '\uFF3F': '_',

    '\uFF01': '!',
    '\uFF1F': '?',
    '\uFF61': '.',
    '\u3002': '.',
}

# 用于连续中文标点时进行挤压
cn_full_to_half = {
    '\uFF0C': ',',
    '\uFF1A': ':',
    '\uFF1B': ';',
    '\uFF3F': '_',
    '\uFF5E': '~',

    '\u300C': '\uFF62',
    '\u300D': '\uFF63',
    '\u3001': '\uFF64',

    '\uFF01': '!',
    '\uFF1F': '?',
    '\u3002': '\uff61',
}

foreced_to_half_punc = {
    '\uFF08': '(',
    '\uFF3B': '[',
    '\uFF5B': '{',
    '\uFF09': ')',
    '\uFF3D': ']',
    '\uFF5D': '}',
    '\uFF1C': '<',
    '\uFF1E': '>',

    '\uFF0F': '/',
    '\uFF5C': '|',
}


def char_is_full_width(c):
    return is_full_width_char(c) or c in hanzi.punctuation


def is_blank_line(line):
    if blank_line_re.match(line):
        return True
    return False


class py_text_normalizer:
    def pre_process_text_line(self, line:str):
        # test string: 'a.string,has;no:space?after   punctuation!another, string; has: space? after puctuation! ok!'
        # 多个连续的空格只保留一个，同时也保证后续的处理不会碰到连续的空格
        # 这一操作还有几个副作用:
        # 1. 行首和行尾的空白字符会被去掉
        # 2. tab等空白字符都会被去掉，整个字符串中的空白字符就只剩下英文空格了
        line = regular_space.join(line.split())

        chars = []
        for char in line:
            if '\ufb00' < char and char < '\ufb12':
                # Alphabetic Presentation Forms is a Unicode block containing standard ligatures
                ligature_chars = unicodedata.normalize('NFKD', char)
                chars.extend(list(ligature_chars))
            elif '\uff10' <= char and char <= '\uff19':
                chars.append(str(int(char)))
            elif char in foreced_to_half_punc:
                chars.append(foreced_to_half_punc[char])
            else:
                chars.append(char)

        return "".join(chars)

    def space_allowed(self, is_punc):
        if not self.normalized_chars:
            return False
        elif self.prev_char == regular_space:
            return False
        elif self.prev_is_punc:
            if is_punc:
                # space is not allowed between puctuations
                return False
            elif self.prev_char in hanzi.punctuation:
                if self.prev_char in all_smart_quotes:
                    return True
                else:
                    return False
            elif self.prev_char in left_parens:
                return False

        return True

    def add_space(self):
        allowed = self.space_allowed(False)
        if not allowed:
            next_char = self.line[self.idx + 1]
            if self.prev_char == '[' and next_char == ']':
                # github markdown task list
                allowed = True

        if not allowed:
            #logging.debug("add_space: ignore")
            if self.prev_char == regular_space:
                #logging.debug("but change auto_added to false")
                self.prev_space_is_auto_added = False
            return

        self.normalized_chars.append(regular_space)
        self.prev_char = regular_space
        self.prev_space_is_auto_added = False
        #logging.debug("cur norm line: |{}|".format("".join(self.normalized_chars)))

    def char_is_in_abbr(self, c):
        if not char_is_letter(c):
            return False

        if self.idx + 1 < self.line_len:
            next_char = self.line[self.idx + 1]
            if char_is_letter(next_char):
                return False
        
        prev_prev_char = self.normalized_chars[-2]
        if prev_prev_char != '.':
            return False

        num_norm_chars = len(self.normalized_chars)
        if num_norm_chars < 3:
            return False

        ppp_char = self.normalized_chars[-3]
        if not char_is_letter(ppp_char):
            return False

        if num_norm_chars == 3:
            return True

        pppp_char = self.normalized_chars[-4]
        if char_is_letter(pppp_char):
            return False

        return True

    def add_char(self, c, is_punc=True, is_full_char=False, add_space_before=False, add_space_after=False):
        #logging.debug("self.add_char, c:{}, is_punc:{}, is_full_char:{}, add_space_before:{}, add_space_after:{}".format(
        #    c, is_punc, is_full_char, add_space_before, add_space_after))
        #logging.debug("self.add_char, self.prev_char:{}, prev_is_func:{}, self.prev_is_full_width:{}".format(
        #    self.prev_char, self.prev_is_punc, self.prev_is_full_width))

        if add_space_before and self.space_allowed(is_punc):
            #logging.debug("add space before")
            self.normalized_chars.append(regular_space)
            self.prev_char = regular_space
            self.prev_space_is_auto_added = True

        if is_punc:
            cur_is_full_width = punc_is_full_width(c)
        else:
            cur_is_full_width = is_full_char

        if self.prev_char == regular_space:
            pop_space = False
            if self.prev_is_full_width and cur_is_full_width:
                #logging.debug("remove whitespapce between full width chars")
                pop_space = True
            if is_punc and cur_is_full_width:
                pop_space = True

                if c in all_smart_quotes:
                    pop_space = self.prev_space_is_auto_added

                    if c in right_smart_quotes and not self.prev_is_punc:
                        pop_space = True
            elif is_punc and self.prev_is_punc:
                pop_space = True

                prev_prev_char = self.normalized_chars[-2]
                if c == '\\':
                    pop_space = self.prev_space_is_auto_added
                elif prev_prev_char == '[' and c == ']':
                    pop_space = False
                elif c in left_parens or c in all_quotes:
                    pop_space = self.prev_space_is_auto_added
                # elif c in '+-':
                #     prev_prev_char = self.normalized_chars[-2]
                #     if prev_prev_char == '|':
                #         # markdown table delimiter
                #         pop_space = self.prev_space_is_auto_added
                #     elif self.idx + 1 < self.line_len:
                #         next_char = self.line[self.idx + 1]
                #         if char_is_number(next_char):
                #             pop_space = False
                elif c in puncs_unaware_space:
                    pop_space = self.prev_space_is_auto_added
            elif is_punc and self.prev_is_full_width:
                if c in puncs_unaware_space:
                    pop_space = self.prev_space_is_auto_added
            elif not self.prev_is_full_width and not cur_is_full_width:
                pop_space = self.prev_space_is_auto_added

                if c in left_parens:
                    pop_space = False
                elif c in puncs_need_space_after or c in right_parens:
                    pop_space = True
                elif not self.char_is_in_abbr(c):
                    prev_prev_char = self.normalized_chars[-2]
                    if prev_prev_char in puncs_need_space_after:
                        pop_space = False
                        if self.prev_space_is_auto_added and prev_prev_char in number_delimiters and len(self.normalized_chars) >= 3:
                            ppp_char = self.normalized_chars[-3]
                            if char_is_number(ppp_char) and char_is_number(c):
                                pop_space = True
            elif not is_punc:
                prev_prev_char = self.normalized_chars[-2]
                if prev_prev_char in left_smart_quotes:
                    pop_space = True
                elif is_full_char and prev_prev_char in puncs_unaware_space:
                    pop_space = self.prev_space_is_auto_added

            #logging.debug("remove space before puncs, pop_space={}".format(pop_space))
            if pop_space:
                self.normalized_chars.pop()

        self.normalized_chars.append(c)

        if add_space_after:
            #logging.debug("add space after")
            self.normalized_chars.append(regular_space)
            self.prev_char = regular_space
            self.prev_space_is_auto_added = True
        else:
            self.prev_char = c
        
        self.prev_is_punc = is_punc
        self.prev_is_full_width = cur_is_full_width

        #logging.debug("cur norm line: |{}|".format("".join(self.normalized_chars)))

    def process_full_width_char(self):
        #logging.debug("is full width")
        context_changed = (self.cur_context != FULL_WIDTH_CONTEXT)
        if context_changed:
            self.prev_context = self.cur_context
        self.cur_context = FULL_WIDTH_CONTEXT
        self.add_char(self.cur_char, is_punc=False, is_full_char=True,
                add_space_before=context_changed)

    def process_half_width_char(self):
        #logging.debug("is half width")
        context_changed = (self.cur_context != HALF_WIDTH_CONTEXT)
        if context_changed:
            self.prev_context = self.cur_context
        self.cur_context = HALF_WIDTH_CONTEXT
        self.add_char(self.cur_char, is_punc=False, add_space_before=context_changed)

    def process_punctuation(self):
        #logging.debug("is punc")
        if self.cur_char in left_parens:
            self.add_char(self.cur_char, add_space_before=True)
            return

        if self.cur_char in right_parens:
            self.add_char(self.cur_char, add_space_after=True)
            return

        if self.cur_char == right_single_quote and not self.sentence_end_context and self.cur_context == HALF_WIDTH_CONTEXT:
            is_contraction = False
            if self.idx + 1 < self.line_len:
                m = contraction_suffix_re.match(self.line, self.idx + 1)
                if m:
                    is_contraction = True
            if not is_contraction:
                start_pos = self.idx - 1
                if start_pos >= 0:
                    if self.line[start_pos] == regular_space:
                        start_pos -= 1
                if start_pos >= 0:
                    m = o_clock_re.match(self.line, start_pos)
                    if m:
                        is_contraction = True
            if is_contraction:
                self.add_char("'")
                return
            # else, pass through
        
        if not self.cur_context:
            #logging.debug("env not determinied")
            search_pos = self.idx + 1
            while search_pos < self.line_len:
                c = self.line[search_pos]
                search_pos += 1
                if is_full_width_char(c):
                    self.cur_context = FULL_WIDTH_CONTEXT
                    break
                elif c == regular_space or char_is_punctuation(c):
                    continue
                else:
                    self.cur_context = HALF_WIDTH_CONTEXT
                    break
            
            #logging.debug("env searched: {}".format(self.cur_context))
            if not self.cur_context:
                #logging.debug("using prev dev: {}".format(self.prev_context))
                self.cur_context = self.prev_context

            if not self.cur_context:
                #logging.debug("env not found until end, finish!")
                while self.idx < self.line_len:
                    self.add_char(self.line[self.idx])
                    self.idx += 1
                # finished!
                return
            # else, pass through

        # stops are only considered stops if they are in half or full env
        if self.cur_char in stops:
            #logging.debug("stops found")
            self.sentence_end_context = True
            if self.cur_char == '.' and self.idx + 1 < self.line_len:
                next_char = self.line[self.idx + 1]
                if char_is_number(self.prev_char) and char_is_number(next_char):
                    self.sentence_end_context = False

        if self.cur_context == FULL_WIDTH_CONTEXT:
            if self.normalized_chars:
                if self.prev_char in cn_full_to_half:
                    #logging.debug("标点挤压")
                    self.prev_char = cn_full_to_half[self.prev_char]
                    self.normalized_chars[-1] = self.prev_char

            if self.cur_char in half_punc_to_full:
                self.cur_char = half_punc_to_full[self.cur_char]

            self.add_char(self.cur_char)
        elif self.cur_context == HALF_WIDTH_CONTEXT:
            if self.cur_char in full_punc_to_half:
                self.cur_char = full_punc_to_half[self.cur_char]

            add_space_after = (self.cur_char in puncs_need_space_after)
            self.add_char(self.cur_char, add_space_after=add_space_after)

    def normalize_text_line(self, orig_line:str):
        #logging.debug("normalize line: " + orig_line)
        self.line = self.pre_process_text_line(orig_line)
        self.line_len = len(self.line)

        self.normalized_chars = []

        self.prev_char = NULL_CHAR
        self.prev_is_punc = False
        self.prev_is_full_width = False
        self.prev_space_is_auto_added = False

        self.prev_context = NONE_CONTEXT
        self.cur_context = NONE_CONTEXT
        self.sentence_end_context = False

        self.idx = 0
        while self.idx < self.line_len:
            self.cur_char = self.line[self.idx]
            #logging.debug("norm char: {}({})".format(self.cur_char, hex(ord(self.cur_char))))

            if self.sentence_end_context and self.cur_char not in all_stops:
                #logging.debug("sentence end")
                self.sentence_end_context = False
                self.prev_context = self.cur_context
                self.cur_context = NONE_CONTEXT

            if self.cur_char == regular_space:
                self.add_space()
            elif is_full_width_char(self.cur_char):
                self.process_full_width_char()
            elif char_is_punctuation(self.cur_char):
                self.process_punctuation()
            else:
                self.process_half_width_char()
            
            self.idx += 1

        if self.prev_char == regular_space:
            self.normalized_chars.pop()

        return ''.join(self.normalized_chars)


def py_concat_line(line1, line2):
    if not line1:
        return line2

    last_char = line1[-1]
    if last_char == "-":
        line1 = line1[:-1]
    elif last_char == '\u2019' or last_char == '\u201d' or ord(last_char) < 128:
        # use space to join english lines
        line1 += " "

    return line1 + line2


def py_normalize_text_line(line: str):
    return py_text_normalizer().normalize_text_line(line)


def test():
    testcase_dict = {
        '中 .':
        '中。',

        'english .':
        'english.',

        '亚里士多德（   Aristotle    ）如何如何':
        '亚里士多德 (Aristotle) 如何如何',

        '功利主义的功利译自英文词utility，大致就是useful（有用）的意思。':
        '功利主义的功利译自英文词 utility, 大致就是 useful (有用) 的意思。',

        'Hey Jane, 周 末 要 不要一起 吃早茶，叫上Jennie和Jone, 预计花费100元':
        'Hey Jane, 周末要不要一起吃早茶，叫上 Jennie 和 Jone, 预计花费 100 元',

        "$: 不确定环境测试":
        "$：不确定环境测试",

        "不确定环境测试。_中文。＿english._中文":
        "不确定环境测试｡＿中文。_english.＿中文",

        ".。？！!()":
        ".。？！!()",

        "连续中文标点？    ！    ！":
        "连续中文标点?!！",

        "a.string,has;no:space?after   punctuation!another, string; has: space? after      puctuation! ok!":
        "a. string, has; no: space? after punctuation! another, string; has: space? after puctuation! ok!",

        "中文:【不要加空格】": "中文:【不要加空格】",

        "english:[english]": "english:[english]",

        "全角数字:０１２３４５６７８９要转为半角":
        "全角数字：0123456789 要转为半角",

        "中文  ，  标点前后都不需要空格":
        "中文，标点前后都不需要空格",

        "中文句子,里的标点;转为中文.english，text；convert to english。":
        "中文句子，里的标点；转为中文。english, text; convert to english.",

        "some punc allow space around it: 1 + 2 * 3 / 4 - 5 = -2.5":
        "some punc allow space around it: 1 + 2 * 3 / 4 - 5 = -2.5",

        "Am Not  Ain’t We Have  We’ve Are Not  Aren’t We Will  We’ll Let Us  Let’s What Are  What’re Can Not  Can’t Might Have  Might’ve Could Have  Could’ve Might Not  Mightn’t What Is  What’s Could Not  Couldn’t Must Have  Must’ve What Have  What’ve Do Not  Don’t Must Not  Mustn’t What Will  What’ll Does Not  Doesn’t Need Not  Needn’t When Is  When’s Of the Clock  O’clock When Will  When’ll Ought Not  Oughtn’t Where Are  Where’re Where Is  Where’s She Is  She’s Where Have  Where’ve She Will  She’ll Where Will  Where’ll Should Have  Should’ve Why Are  Why’re Has Not  Hasn’t Should Not  Shouldn’t Why Is  Why’s Have Not  Haven’t Why Have  Why’ve He Is  He’s That Is  That’s Why Will  Why’ll He Will  He’ll That Will  That’ll Who Is  Who’s How Are  How’re That Would  That’d Who Have  Who’ve How Is  How’s There Is  There’s Who Will  Who’ll How Have  How’ve They Are  They’re Will Not  Won’t I Am  I’m They Have  They’ve I Had  I’d They Will  They’ll Would Not  Wouldn’t I Have  I’ve I Will  I’ll We Are  We’re You Are  You’re Is Not  Isn’t It Is  It’s You Have  You’ve It Will  It’ll You Will  You’ll are not	aren’t cannot	can’t could not	couldn’t did not	didn’t do not	don’t does not	doesn’t had not	hadn’t have not	haven’t he is	he’s he has	he’s he will	he’ll he would	he’d here is	here’s I am	I’m I have	I’ve I will	I’ll I would	I’d I had	I’d is not	isn’t it is	it’s it has	it’s it has	it’s it will	it’ll must not	mustn’t she is	she’s she has	she’s she will	she’ll she would	she’d she had	she’d should not	shouldn’t that is	that’s there is	there’s they are	they’re they have	they’ve they will	they’ll they would	they’d they had	they’d was not	wasn’t we are	we’re we have	we’ve we will	we’ll we would	we’d we had	we’d were not	weren’t what is	what’s where is	where’s who is	who’s who will	who’ll will not	won’t would not	wouldn’t you are	you’re you have	you’ve you will	you’ll you would	you’d you had	you’d":
        "Am Not Ain't We Have We've Are Not Aren't We Will We'll Let Us Let's What Are What're Can Not Can't Might Have Might've Could Have Could've Might Not Mightn't What Is What's Could Not Couldn't Must Have Must've What Have What've Do Not Don't Must Not Mustn't What Will What'll Does Not Doesn't Need Not Needn't When Is When's Of the Clock O'clock When Will When'll Ought Not Oughtn't Where Are Where're Where Is Where's She Is She's Where Have Where've She Will She'll Where Will Where'll Should Have Should've Why Are Why're Has Not Hasn't Should Not Shouldn't Why Is Why's Have Not Haven't Why Have Why've He Is He's That Is That's Why Will Why'll He Will He'll That Will That'll Who Is Who's How Are How're That Would That'd Who Have Who've How Is How's There Is There's Who Will Who'll How Have How've They Are They're Will Not Won't I Am I'm They Have They've I Had I'd They Will They'll Would Not Wouldn't I Have I've I Will I'll We Are We're You Are You're Is Not Isn't It Is It's You Have You've It Will It'll You Will You'll are not aren't cannot can't could not couldn't did not didn't do not don't does not doesn't had not hadn't have not haven't he is he's he has he's he will he'll he would he'd here is here's I am I'm I have I've I will I'll I would I'd I had I'd is not isn't it is it's it has it's it has it's it will it'll must not mustn't she is she's she has she's she will she'll she would she'd she had she'd should not shouldn't that is that's there is there's they are they're they have they've they will they'll they would they'd they had they'd was not wasn't we are we're we have we've we will we'll we would we'd we had we'd were not weren't what is what's where is where's who is who's who will who'll will not won't would not wouldn't you are you're you have you've you will you'll you would you'd you had you'd",
        
        "something’is wrong": "something’is wrong",

        'some    "   text   "    in quotes':
        'some " text " in quotes',

        'some    “   text   ”    in quotes':
        'some “text” in quotes',

        'some  ‘  “   text   ” ’   in quotes':
        'some ‘ “text” ’ in quotes',

        'some "text" in quotes':
        'some "text" in quotes',

        'some “text” in quotes':
        'some “text” in quotes',

        'Parse ~~strikethrough~~ formatting':
        'Parse ~~strikethrough~~ formatting',

        'Parse **bold** formatting':
        'Parse **bold** formatting',

        'Parse *italic* formatting':
        'Parse *italic* formatting',

        '# level1 header':
        '# level1 header',

        '# 中文标题1':
        "# 中文标题 1",

        '## level2 header':
        '## level2 header',

        '| 中文 | 表格 |':
        '| 中文 | 表格 |',

        '**测试**(**test**)一下':
        '**测试**(**test**) 一下',

        '**心理学**(**psychology**)是':
        '**心理学**(**psychology**) 是',

        'd. “what” psy':
        'd. “what” psy',

        'this is: \d':
        'this is: \d',

        'this is:\d':
        'this is:\d',

        '| --- | --- | --- |':
        '| --- | --- | --- |',

        'e.g. in U.S.A there (a.m)':
        'e.g. in U.S.A there (a.m)',

        'e. g. in U. S.A there (a.m)':
        'e. g. in U. S.A there (a.m)'
    }

    testcase_dict2 = {
        'e.g. in U.S.A there (a.m)':
        'e.g. in U.S.A there (a.m)'
    }

    for test_line, expect_result in testcase_dict.items():
        norm_result = py_normalize_text_line(test_line)    
        if norm_result == expect_result:
            print("PASSED")
        else:
            print("FAILED")
            print('normalize: ' + test_line)
            print('normalize result: |' + norm_result + '|')
            print('expected  result: |' + expect_result + '|')
        

# Main body
if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    test()