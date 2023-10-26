import string
import chardet
from typing import *
from pycorrector.macbert.macbert_corrector import MacBertCorrector
from pycorrector import ConfusionCorrector
import sys

from flask import Flask

sys.path.append("..")

# 操作票数据结构
# 只需要操作任务，操作步骤，操作顺序三项
class ticket:
    def __init__(self):
        self.task = ''          # 操作任务
        self.step_number = 0    # 操作顺序
        self.step = ''          # 操作步骤
    def add_newticket(self,Task,Step_number,Step):
        self.task = Task        
        self.step_number = Step_number 
        self.step = Step
    def add_newtickets(self,Task,Step_number_list,Step_list):
        for i in range(len(Step_number_list)):
            self.add_newticket(Task,Step_number_list[i],Step_list[i])

def stringMacth(S:string,T:string):

    lens=len(S)
    lent=len(T)
    i=0
    j=-1

    Next=[0]*(lent) 
    Next[0]=-1
    while i<lent-1:
        if j==-1 or T[i]==T[j]:
            i+=1
            j+=1
            Next[i]=j
        else:
            j=Next[j]
    i=0
    j=0
    while i<lens and j<lent:
        if j==-1 or S[i]==T[j]:
            i+=1
            j+=1
        else:
            j=Next[j]
    if j==lent:
        return i-j
    else:
        return None

# 设备匹配
def DeviceMacth(checking_tickets):
    #读取设备库文件
    filename = 'device.txt'
    data = []
    check_info = []
    with open(filename, 'rb') as f:
        result = chardet.detect(f.read())
        encoding = result['encoding']

    with open(filename,'r', encoding=encoding) as f:
        for line in f:
            line = line.strip('\n')
            data.append(line)

    #字符串匹配
    for set in checking_tickets:
        if stringMacth(set.step,'母线') is not None:
            tag = 0
            for line in data:
                if stringMacth(set.step,line) is not None:
                    tag = 1
                    break
                    
            if tag == 0:
                #接口：返回错误信息
                check_info.append("设备检查错误，在操作顺序{}中，母线设备名错误".format(set.step_number))
                    
    return check_info

def NLP_check(checking_tickets):
    check_info = []
    m = MacBertCorrector()
    confusion_dict = {"喝小明同学": "喝小茗同学", "老人让坐": "老人让座", "平净": "平静", "却在": "确在"}
    cm = ConfusionCorrector(custom_confusion_path_or_dict=confusion_dict)
    for line in checking_tickets:
        correct_sent, err = m.macbert_correct(line.step)
        if err :
            check_info.append("NLP模型检查错误,在操作顺序{}中，{} => {} {}".format(line.step_number,line.step, correct_sent, err))
        correct_sent, err = cm.confusion_correct(correct_sent)
        if err :
            check_info.append("NLP模型投喂库检查错误,在操作顺序{}中，{} => {} {}".format(line.step_number,line.step, correct_sent, err))
    # 接口：返回错误信息

    return check_info

# 规则匹配
def RuleMacth(checking_tickets):
    check_info = []
    filename = 'rule.txt'
    data = {}

    with open(filename, 'rb') as f:
        result = chardet.detect(f.read())
        encoding = result['encoding']

    with open(filename,'r', encoding=encoding) as f:
        for line in f:
            (key, val) = line.split()
            data[key] = val

    #字符串匹配
    for set in checking_tickets:
        for key, val in data.items():
            if stringMacth(set.step,key) is not None:
                if stringMacth(set.step,val) is None:
                    #接口：返回错误信息
                    check_info.append("规则检查错误，在操作顺序{}中，出现\"{}\"时缺少\"{}\"".format(set.step_number,key,val))
                    break
    
    return check_info

def check_newtickets(Task:string,Step_number_list:list,Step_list:list) ->list:
    checking_tickets = []
    check_info = []

    Task = Task.replace(' ','')

    for i in range(len(Step_number_list)):
        checking_ticket = ticket()
        Step_list[i] = Step_list[i].replace(' ','')
        checking_ticket.add_newticket(Task,Step_number_list[i],Step_list[i])
        checking_tickets.append(checking_ticket)

    #check_info += DeviceMacth(checking_tickets)
    check_info += NLP_check(checking_tickets)
    #check_info += RuleMacth(checking_tickets)

    return check_info
if __name__ == '__main__':
    
    # 操作票接口处
    # 例：
    error_sentences = [
        '老是较书',
        '在后台监控机检查500kV#2M母线电压因该显示正长',
        '在后台监控机检查500kV#1M母线电压显示为零',
        '在在220kV母差保护屏Ⅱ（55P）将1QK Ⅰ母 Ⅱ母切换开关切换至“双母”位制',
        '在220kV #1电压互感器221PT端子箱合上交流电机电源1DK空气开关',
        '合商220kV #1电压互感器1M母线侧221PT刀闸',
        '检插220kV #1电压互感器1M母线侧221PT刀闸三相却在合上位置', 
    ]

    print(check_newtickets('Task',[1,2,3,4,5,6,7],error_sentences))
