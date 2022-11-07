# -*- coding: utf-8 -*-

import sys
import os
import re
import logging
from markdown_utils import markdown_processor, markdown_processor_mode, uniqe_name
from markdown_to_other_app import add_prefix_to_local_images


class Block:
    def __init__(self):
        self.lines = []

    def add_line(self, line):
        self.lines.append(line)

    def generate_qa_markdown(self):
        if self.lines[1].startswith('q: '):
            return self.lines

        qa_lines = []

        self.lines[1] = 'q: ' + self.lines[1]
        joined_lines = ''.join(self.lines)

        double_brace_re = re.compile(r'(?P<b>\{|\})')
        joined_lines = double_brace_re.sub(r'\1\1', joined_lines)
            
        cloze_re = re.compile(r'{{{{(.*?)}}}}')

        clozes = cloze_re.findall(joined_lines)
        joined_lines = cloze_re.sub(r'{}', joined_lines)

        supermemo_cloze = '<span class=cloze>[...]</span>'

        for i in range(len(clozes)):
            if i > 0:
                qa_lines.append('\n')
                qa_lines.append('---\n')
                qa_lines.append('\n')

            sup_clozes = clozes.copy()
            sup_clozes[i] = supermemo_cloze
            answer = 'a: ' + clozes[i] + '\n'

            question = joined_lines.format(*sup_clozes)
            question_lines = question.splitlines(keepends=True)

            qa_lines.extend(question_lines)
            qa_lines.append('\n')
            qa_lines.append(answer)
            qa_lines.append('\n')

        return qa_lines


def generate_qa_markdown(filename):
    title = ""
    qa_markdown_lines = []

    cur_block = Block()
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            #print(line)
            if line.startswith('#'):
                title = line[2:].strip()
                continue

            if line.startswith('---'):
                qa_lines = cur_block.generate_qa_markdown()
                qa_markdown_lines.extend(qa_lines)
                
                qa_markdown_lines.append(line)
                cur_block = Block()
            else:
                cur_block.add_line(line)

    qa_lines = cur_block.generate_qa_markdown()
    qa_markdown_lines.extend(qa_lines)

    return (title, qa_markdown_lines)


def convert_html_to_qa_text(title, html_body):
    qa_text = []

    q_re = re.compile(r'<p>q: ')
    a_re = re.compile(r'<p>a: ')
    hr_re = re.compile('<hr\s*/?>')
    fenced_code_begin_re = re.compile(r'<pre><code')

    if title:
        title = '<strong><font color=blue>' + title + ' : </font></strong>'

    qa_line = None
    in_fenced_code = False
    for line in html_body.splitlines():
        if in_fenced_code:
            qa_line += '\u0002' + line

            if '</code></pre>' in line:
                in_fenced_code = False
        elif hr_re.match(line):
            qa_text.append(qa_line)
            qa_line = None
            qa_text.append('')
        elif q_re.match(line):
            if qa_line:
                qa_text.append(qa_line)
            qa_line = q_re.sub(r'<p>', line, count=1)
            qa_line = 'q: ' + title + qa_line
        elif a_re.match(line):
            if qa_line:
                qa_text.append(qa_line)
            qa_line = a_re.sub(r'a: <p>', line,  count=1)
        elif '<pre><code' in line:
            qa_line += line
            in_fenced_code = True
        elif qa_line:
            qa_line += line
    
    if qa_line:
        qa_text.append(qa_line)
        qa_text.append('')
    
    return '\n'.join(qa_text)


def main():
    #logging.basicConfig(filename='D:\\logs\\n10.log', filemode='w', level=logging.DEBUG)
    #logging.basicConfig(level=logging.DEBUG)
    args = sys.argv[1:]

    if not args:
        logging.debug('no file selected\n')
        sys.exit(1)

    filename = args[0]

    title, qa_markdown_lines = generate_qa_markdown(filename)
    if not qa_markdown_lines:
        logging.debug('empty file')
        return

    # print(qa_markdown_lines)
    processor = markdown_processor(markdown_processor_mode.SUPERMEMO, filename)
    html_body = processor.markdown_to_html_with_inline_style(qa_markdown_lines)
    html_body = add_prefix_to_local_images(
        html_body, markdown_processor_mode.SUPERMEMO, os.path.dirname(filename))
    # print(html_body)
    qa_text = convert_html_to_qa_text(title, html_body)

    split_filepath = os.path.splitext(filename)
    qa_text_file = uniqe_name(split_filepath[0] + ".html")
    
    with open(qa_text_file, 'w', encoding="utf-8") as f:
        f.write(qa_text)

# Main body
if __name__ == '__main__':
    main()