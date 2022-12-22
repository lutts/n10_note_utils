# -*- coding: utf-8 -*-

import sys
import os
import re
import logging
from markdown_utils import markdown_processor, markdown_processor_mode, uniqe_name
from markdown_to_other_app import add_prefix_to_local_images


md_q_re = re.compile(r'^(q|Q): ')
md_a_re = re.compile(r'^(a|A): ')
seperator_re = re.compile(r'^[ ]{0,3}([-*_])([ ]*\1){2,}[ \t]*$')
double_brace_re = re.compile(r'(?P<b>\{|\})')
cloze_re = re.compile(r'{{{{(.*?)}}}}((?:\([^)]*?\))?)')
qid_re = re.compile(r'{#q[0-9]{1,4}}$')
qid_len = len("{#q0000}\n")


class Block:
    def __init__(self):
        self.question_lines = []
        self.answer_lines = []
        self._lines = self.question_lines

    def add_line(self, line):
        if md_q_re.match(line):
            if self.question_lines:
                return False
            self._lines.append(line)
        elif md_a_re.match(line):
            # TODO: multiple answer is not supported, how to warnning the user?
            self._lines = self.answer_lines
            self._lines.append(line)
        elif not self.question_lines:
            if line:
                self.question_lines.append('Q: ' + line)
        else:
            self._lines.append(line)

        return True

    def generate_qa_markdown(self):
        for idx in range(len(self.question_lines)):
            line = self.question_lines[idx]
            line_len = len(line)
            if line_len > qid_len:
                if qid_re.match(line, line_len - qid_len):
                    line = line[:line_len - qid_len] + '\n'
                    self.question_lines[idx] = line
        if self.answer_lines:
            qa_lines = self.question_lines
            qa_lines.append('\n')
            qa_lines.extend(self.answer_lines)
            qa_lines.append('\n')

            return qa_lines

        qa_lines = []

        joined_question  = ''.join(self.question_lines)
        joined_question = double_brace_re.sub(r'\1\1', joined_question)

        clozes_hints = cloze_re.findall(joined_question)
        joined_question = cloze_re.sub(r'{}', joined_question)

        clozes = [i[0] for i in clozes_hints]
        hints = ['<span>' + i[1] + '</span>' if i[1] else i[1] for i in clozes_hints]

        supermemo_cloze = '<span style="background-color:#ffff00;color:red;font-weight:bold">[...]</span>'

        for i in range(len(clozes)):
            if i > 0:
                qa_lines.append('\n')

            sup_clozes = clozes.copy()
            sup_clozes[i] = supermemo_cloze + hints[i]
            answer = 'A: ' + clozes[i] + '\n'

            question = joined_question.format(*sup_clozes)
            question_lines = question.splitlines(keepends=True)

            qa_lines.extend(question_lines)
            qa_lines.append('\n')
            qa_lines.append(answer)
            qa_lines.append('\n')

        return qa_lines


def generate_qa_markdown(filename):
    title = ""
    qa_markdown_lines = []

    block_list = []

    cur_block = Block()

    def new_block():
        nonlocal cur_block
        block_list.append(cur_block)
        cur_block = Block()

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            #print(line)
            if line.startswith('#'):
                title = line[2:].strip()
                continue

            if seperator_re.match(line):
                new_block()
            elif not cur_block.add_line(line):
                new_block()
                cur_block.add_line(line)

    block_list.append(cur_block)

    for block in block_list:
        qa_markdown_lines.extend(block.generate_qa_markdown())

    return (title, qa_markdown_lines)


def convert_html_to_qa_text(title, html_body):
    qa_text = []

    q_re = re.compile(r'<p>(q|Q): *')
    a_re = re.compile(r'<p>(a|A): *')
    hr_re = re.compile('<hr\s*/?>')

    if title:
        title = '<strong><font color="blue">' + title + ' : </font></strong>'

    qa_line = ''
    in_fenced_code = False
    for line in html_body.splitlines():
        if in_fenced_code:
            qa_line += '\u0002' + line

            if '</code></pre>' in line:
                in_fenced_code = False
        elif q_re.match(line):
            if qa_line:
                qa_text.append(qa_line)
                qa_text.append('')

            qa_line = q_re.sub(r'<p>', line, count=1)
            qa_line = 'Q: ' + title + qa_line
        elif a_re.match(line):
            if qa_line:
                qa_text.append(qa_line)
            qa_line = a_re.sub(r'A: <p>', line,  count=1)
        elif qa_line:
            qa_line += line
            if '<pre><code' in line:
                in_fenced_code = True
    
    if qa_line:
        qa_text.append(qa_line)
        qa_text.append('')
    
    return '\n'.join(qa_text)


def generate_qa_file(filename):
    title, qa_markdown_lines = generate_qa_markdown(filename)
    if not qa_markdown_lines:
        return

    #print(qa_markdown_lines)
    try:
        processor = markdown_processor(markdown_processor_mode.SUPERMEMO, filename)
        html_body = processor.markdown_to_html_body(qa_markdown_lines)
        html_body = add_prefix_to_local_images(
            html_body, markdown_processor_mode.SUPERMEMO, os.path.dirname(filename))
        #print(html_body)
        qa_text = convert_html_to_qa_text(title, html_body)

        split_filepath = os.path.splitext(filename)
        qa_text_file = uniqe_name(split_filepath[0] + ".html")
        
        with open(qa_text_file, 'w', encoding="utf-8") as f:
            f.write(qa_text)
    except:
        logging.exception("some exception occured", exc_info=True)


def main():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    #logging.basicConfig(level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        sys.exit(1)

    filename = args[0]
    generate_qa_file(filename)
    

# Main body
if __name__ == '__main__':
    main()