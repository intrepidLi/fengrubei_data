import csv
import json
import re

header = ['id', 'url', 'align', 'title', 'question', 'answer', 'content', 'label_content', 'q_a', 'leibie', 'key']
header2 = ['question', 'title', 'answer', 'content-key', 'type']
flag = 0

# strmatch1 = ('0.', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')
# strmatch2 = ('0．', '1．', '2．', '3．', '4．', '5．', '6．', '7．', '8．', '9．', '10．')
# strmatch3 = ('（0）', '（1）', '（2）', '（3）', '（4）', '（5）', '（6）', '（7）', '（8）', '（9）', '（10）',)
# strmatch4 = ('一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '九、', '十、')
# type = 0: 已有qa对
def read_data(file_path):
    data = []
    with open(file_path, encoding='utf-8-sig') as csvfile:
        csv_reader = csv.reader(csvfile)  # 使用csv.reader读取csvfile中的文件
        header = next(csv_reader)  # 读取第一行每一列的标题
        for row in csv_reader:  # 将csv 文件中的数据保存到data中
            data.append(row)  # 选择某一列加入到data数组中
    return data


def count_data(data):
    key_set = set()
    qa_cnt = 0
    for row in data:
        key = row[10]
        q_a = row[8]
        key_set.add(key)
        if q_a.isdigit():
            qa_cnt += int(q_a)

    print(f"data {filename}, total row is {len(data)}, has q_a {qa_cnt}, different content {len(key_set)}")


temp_list = []
pseudo_list = []


def walk_list(ll, path):
    s = ""
    for i, l in enumerate(ll):
        path.append(i)
        if isinstance(l, str):
            if l.endswith('：'):
                if l.find('温馨提示') == -1 and l.find('尊敬的') == -1 \
                        and l.find('注意事项') == -1 and l[-2] != '注':
                    pseudo_list.append(l)
            s += l
            temp_list.append({'path': path.copy(), 'text': s})
        elif isinstance(l, list):
            temp, path = walk_list(l, path)
            s += temp
        elif isinstance(l, dict):
            temp, path = walk_map(l, path)
            s += temp
        path.pop()
    return s, path


def walk_map(map, path):
    s = ""
    title = ""
    for key, value in map.items():
        path.append(key)
        if isinstance(value, str):
            if value.endswith('：'):
                if value.find('温馨提示') == -1 and value.find('尊敬的') == -1 \
                        and value.find('注意事项') == -1 and value[-5:].find('包括') == -1 and value[-2:] != '注：':
                    pseudo_list.append(value)
            if key == 'title':
                title = value
                s += value
                temp_list.append({'path': path.copy(), 'text': s})
            else:
                s += value
                temp_list.append({'path': path.copy(), 'text': s[len(title):]})
        elif isinstance(value, list):
            temp, path = walk_list(value, path)
            s += temp
        elif isinstance(value, dict):
            temp, path = walk_map(value, path)
            s += temp
        path.pop()
    return s, path


def make_new_row(old_row, new_question, new_answer, type):  # 删除序号（不完整），新增种类
    # new_row = old_row.copy()
    new_row = [0, 0, 0, 0, 0]
    new_question1 = re.sub('\d+\.', '', new_question)
    # print(new_question1)
    new_question2 = re.sub('\d+\．', '', new_question1)
    # print(new_question2)
    new_question3 = re.sub('（\d+）', '', new_question2)
    new_question4 = re.sub('[一|二|三|四|五|六|七|八|九|十]+、', '', new_question3)
    new_question5 = re.sub('（[一|二|三|四|五|六|七|八|九|十]+）', '', new_question4)
    new_question6 = re.sub('\d+、', '', new_question5)

    new_row[0] = new_question6
    new_row[1] = old_row[3]
    new_row[2] = new_answer
    new_row[3] = old_row[10]
    new_row[4] = type
    # new_row[8] = 1
    return new_row


if __name__ == "__main__":
    # filename = 'haicontent.csv'
    # filename = 'shandong.csv'
    filename = 'content1_try2.csv'
    out_filename = "new_" + filename

    data = read_data(filename)

    qa_list = []
    new_row_list = []
    content2question = {}
    qa_change_cnt, qa_no_change_cnt = 0, 0
    cnt = 0
    re_cnt, pseudo_cnt, use_title_cnt, use_article_cnt = 0, 0, 0, 0
    for row in data:
        cnt += 1
        # if 173 <= cnt and cnt <= 183:
        #    continue
        # 确定相同content
        content = row[6]
        label_content = row[7]
        key = row[10]
        if content not in content2question.keys():
            question_list = []

        align = row[2]
        title = row[3]
        question = row[4]
        answer = row[5]
        q_a = row[8]
        if content == "":
            continue
        if q_a.isdigit() and int(q_a) == 1:
            if question.find("温馨提示") != -1 and question_list != []:  # "温馨提示"类型，则在统一content中找前一问题进行拼接,该分支暂未使用
                new_question = "关于" + question_list[-1] + '的' + question  # 模板："关于xx的温馨提示"
                qa_list.append({"question": new_question, "answer": answer})
            else:
                last_align = align.split(">")[-1]
                if last_align.find("常见") == -1:  # 非"常见问题"类型，拼接align最后一组
                    # 模板："关于last_align，question的相关规定是？"
                    question = question.replace('?', '？').replace(':', '：')
                    if question.split('、')[0].isdigit():
                        question = ''.join(question.split('、')[1:])
                    if question.endswith('？'):
                        new_question = "关于" + last_align + '，' + question
                    elif question.endswith('：'):
                        new_question = "关于" + last_align + '，' + question.rstrip('：') + '的相关规定是?'

                    else:
                        new_question = "关于" + last_align + '，' + question + '的相关规定是?'
                        # qa_list.append({"question":new_question, "answer":answer})
                    new_row = make_new_row(row, new_question, answer, 1)
                    new_row_list.append(new_row)
                    qa_change_cnt += 1
                else:  # "常见问题"类型，直接使用现有q-a对
                    # qa_list.append({"question":question, "answer":answer})
                    new_row = make_new_row(row, question, answer, 0)
                    new_row_list.append(new_row)
                    qa_no_change_cnt += 1
            question_list.append(question)
            content2question[content] = question_list
        else:
            last_align = align.split(">")[-1]

            result = re.findall(r"([0-9]+、.*?(\？|\?|\：))", content)
            temp_content = re.sub(r"([0-9]+、.*?(\？|\?|\：))", "[QUESTION]", content)
            ans_list = temp_content.split("[QUESTION]")
            if title.isdigit():
                if "通知" in content or "公告" in content or "提示" in content or "说明" in content or "指南" in content or "要求" in content or "政策" in content:  # 通知文章处理
                    temp_content = re.sub(re.compile("(通知|公告|提示|说明|指南|要求|政策)"), "[QUESTION]", content)
                    article_title = temp_content.split("[QUESTION]")[0]
                    if len(article_title) > 50:
                        continue
                    new_question = title + "," + article_title + "通知的内容是？"
                    new_answer = re.sub(re.compile('(' + article_title + ')' + "(通知|公告|提示|说明|指南|要求|政策)"), "",
                                        content)
                    new_row = make_new_row(row, new_question, new_answer, "article")
                    new_row_list.append(new_row)
                    use_article_cnt += 1
                else:
                    continue
            elif result != [] and last_align != "国内机场" and last_align != "国际机场" and last_align != "会员权益":  # 文本中有数字-问题/冒号类型
                for i in range(0, len(result)):
                    group = result[i]
                    # new_question = group[0]
                    if title != last_align:
                        new_question = "关于" + last_align + title + '，' + group[0].rstrip('：')
                    else:
                        new_question = "关于" + title + '，' + group[0].rstrip('：')
                    new_answer = ans_list[i + 1]
                    new_row = make_new_row(row, new_question, new_answer, 2)
                    new_row_list.append(new_row)
                    # qa_list.append({"question":new_question,"answer":new_answer})
                re_cnt += 1
            else:  # 分析文本label_content结构，有text冒号类型内容
                # label_content.replace("\\\\\"", "\"")
                json_content = eval(label_content)
                # if isinstance(json_content,str):
                #     continue
                pseudo_list = []
                content_text, _ = walk_map(json_content, [])
                if pseudo_list != [] and last_align != "国内机场" and last_align != "国际机场" and last_align != "会员权益":
                    pseudo_start_list, pseudo_end_list = [], []
                    for pseudo_question in pseudo_list:
                        pseudo_start_list.append(content_text.find(pseudo_question))
                        pseudo_end_list.append(content_text.find(pseudo_question) + len(pseudo_question))
                    for i in range(len(pseudo_list)):
                        if i < len(pseudo_list) - 1:
                            new_answer = content_text[pseudo_end_list[i]:pseudo_start_list[i + 1]]
                        else:
                            new_answer = content_text[pseudo_end_list[i]:]
                        if len(pseudo_list[i]) > 15:
                            new_question = pseudo_list[i].rstrip('：')
                        else:
                            if title != last_align:
                                new_question = "关于" + last_align + title + '，' + pseudo_list[i].rstrip('：')
                            else:
                                new_question = "关于" + title + '，' + pseudo_list[i].rstrip('：')
                        new_row = make_new_row(row, new_question, new_answer, 3)
                        new_row_list.append(new_row)
                        # qa_list.append({"question":new_question,"answer":new_answer})
                    pseudo_cnt += 1
                else:  # 其他类型，直接使用title作为question，模板："关于last_align，title的相关规定是？"
                    if "机上服务" in align or "机场服务" in align:
                        template_type = 2  # 介绍类
                    else:
                        template_type = 1  # 规定类
                    if "规定" in title or "须知" in title or "预案" in title or "手册" in title or "协议" in title:
                        print(title)
                        new_question = title
                    elif last_align == title:
                        if template_type == 1:
                            new_question = "关于" + last_align + "的相关规定是?"
                        if template_type == 2:
                            new_question = "关于" + last_align + "的相关介绍是?"
                    else:
                        if template_type == 1:
                            new_question = "关于" + last_align + '，' + title + '的相关规定是?'
                        if template_type == 2:
                            new_question = "关于" + last_align + '，' + title + '的相关介绍是?'
                    new_answer = content
                    # qa_list.append({"question":new_question,"answer":new_answer})
                    new_row = make_new_row(row, new_question, new_answer, "pseudo_type2")
                    new_row_list.append(new_row)
                    use_title_cnt += 1

    print(f"old data row: {len(data)}")
    print(f"has qa row:{qa_change_cnt + qa_no_change_cnt}, change {qa_change_cnt}, no change {qa_no_change_cnt}")
    print(
        f"no qa data row :{re_cnt + pseudo_cnt + use_title_cnt + use_article_cnt}, re: {re_cnt}, pseudo: {pseudo_cnt}, title: {use_title_cnt}, article :{use_article_cnt}")
    print(f"new data row: {len(new_row_list)}")

    with open("qa_content1.json", "w", encoding='utf-8-sig') as f:
        json.dump(qa_list, f, ensure_ascii=False)

    with open(out_filename, "w", encoding='utf-8-sig', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header2)
        for row in new_row_list:
            ans = row[2]
            if ans != "" and ans != "[]" and ans is not None:
                writer.writerow(row)
            else:
                continue