import os
import re
import random
from collections import OrderedDict
from markdown_utils import uniqe_name


in_paragraph_re = re.compile(r'^(\s*[-=]{3,}\s*$|[ ]{4,}\S)')
level_1_header_re = re.compile(r'[ ]{,3}#[ ]')
qid_re = re.compile(r'{#q[0-9]{,4}}$')
qid_len = len("{#q0000}\n")
q_re = re.compile(r'^(q|Q): ')
a_re = re.compile(r'^(a|A): *')
check_answer_prefix = '[check answer]('
check_answer_template = check_answer_prefix + '{}#L{})\n'


class qa_entity:
    def __init__(self, qid=None):
        self.qid = qid
        self.question = []
        self.recite_answer = []
        self.answer_line_number = 0


def get_qid(line):
    if len(line) <= qid_len:
        return None

    m = qid_re.search(line, len(line) - qid_len)
    if m:
        return m.group()

    return None


def parse_cue(cue_filepath) -> dict[str, qa_entity]:
    qa_dict: dict[str, qa_entity] = {}

    if not os.path.exists(cue_filepath):
        return qa_dict

    q_part_found = False
    a_part_found = False
    cur_qa_entity = None

    with open(cue_filepath, "r", encoding="utf-8") as f:
        for line in f:
            if q_part_found and in_paragraph_re.match(line):
                cur_qa_entity.question.append(line)
                qid = get_qid(line)
                if qid:
                    cur_qa_entity.qid = qid
            elif a_part_found:
                if not line.startswith(check_answer_prefix):
                    cur_qa_entity.recite_answer.append(line)
                else:
                    a_part_found = False
                    qa_dict[cur_qa_entity.qid] = cur_qa_entity
            elif q_re.match(line):
                cur_qa_entity = qa_entity()
                cur_qa_entity.question.append(line)
                q_part_found = True

                qid = get_qid(line)
                if qid:
                    cur_qa_entity.qid = qid
            elif a_re.match(line):
                q_part_found = False
                a_part_found = True
                cur_qa_entity.recite_answer.append(line)

    return qa_dict


def random_qid():
    return "{{#q{}}}".format(int(random.random() * 10000))


def append_qid(line, qid):
    return line.rstrip() + " " + qid + "\n"


def generate_cornell_cue(markdown_filepath):
    if not markdown_filepath:
        return

    filedir = os.path.dirname(markdown_filepath)
    filename = os.path.basename(markdown_filepath)
    cue_file = os.path.join(filedir, "cue.md")

    old_cue_qa_dict = parse_cue(cue_file)

    def gen_qid():
        qid = random_qid()
        while qid in old_cue_qa_dict:
            qid = random_qid()

        return qid

    questions: OrderedDict[str, qa_entity] = OrderedDict()
    cur_qa_entity: qa_entity = None
    orig_lines = []
    title = "# untitled\n"

    line_number = 0
    question_found = False

    with open(markdown_filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line_number += 1
            orig_lines.append(line)

            if line_number == 1 and level_1_header_re.match(line):
                title = line
            elif question_found:
                if in_paragraph_re.match(line):
                    cur_qa_entity.question.append(line)
                    qid = get_qid(line)
                    if qid:
                        cur_qa_entity.qid = qid
                else:
                    question_found = False
                    if not line.strip():
                        cur_qa_entity.answer_line_number = line_number + 1
                    else:
                        cur_qa_entity.answer_line_number = line_number

                    qid = cur_qa_entity.qid
                    if qid and qid in old_cue_qa_dict:
                        old_qa_entity = old_cue_qa_dict[qid]
                        cur_qa_entity.recite_answer = old_qa_entity.recite_answer

                    if not qid:
                        qid = gen_qid()
                        cur_qa_entity.qid = qid
                        orig_lines[-2] = append_qid(orig_lines[-2], qid)
                        cur_qa_entity.question[-1] = append_qid(cur_qa_entity.question[-1], qid)
                    
                    questions[cur_qa_entity.qid] = cur_qa_entity
            elif q_re.match(line):
                cur_qa_entity = qa_entity()
                cur_qa_entity.question.append(line)
                question_found = True

                qid = get_qid(line)
                if qid:
                    cur_qa_entity.qid = qid
            
        with open(cue_file, 'w', encoding='utf-8') as cue:
            cue.write(title)
           
            for entity in questions.values():
                cue.write("\n")
                cue.writelines(entity.question)
                cue.write("\n")
                if entity.recite_answer:
                    cue.writelines(entity.recite_answer)
                else:
                    cue.write("A:\n")
                    cue.write("\n")

                cue.write(check_answer_template.format(filename, entity.answer_line_number))

        with open(markdown_filepath, 'w', encoding="utf-8") as f:
            f.writelines(orig_lines)


                    

