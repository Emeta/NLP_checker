import string
import chardet
from typing import *

import pycorrector
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

    for line in data:
        if stringMacth(checking_tickets[0].task,line) is not None:
            check_info.append("设备检查错误，在操作任务中，母线设备名错误")
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
    pycorrector.set_custom_confusion_path_or_dict('./my_custom_confusion.txt')
    correct_sent, err =  pycorrector.correct(checking_tickets[0].task)
    if err :
        check_info.append("NLP模型检查错误,操作任务中，{} => {} {}".format(checking_tickets[0].task, correct_sent, err))
    for line in checking_tickets:
        correct_sent, err =  pycorrector.correct(line.step)
        if err :
            check_info.append("NLP模型检查错误,在操作顺序{}中，{} => {} {}".format(line.step_number,line.step, correct_sent, err))

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
            val_list = list(val.split(","))
            data[key] = val_list

    #字符串匹配
    for key, val_list in data.items():
        if stringMacth(checking_tickets[0].task,key) is not None:
            tag = 0
            for val in val_list:  
                if stringMacth(checking_tickets[0].task,val) is not None:
                    tag = 1
                    break
            if tag == 0:        
                check_info.append("规则检查错误，在操作任务中，出现‘{}’时缺少{}".format(key,val_list))

    for set in checking_tickets:
        for key, val_list in data.items():
            if stringMacth(set.step,key) is not None:
                tag = 0
                for val in val_list:  
                    if stringMacth(set.step,val) is not None:
                        tag = 1
                        break
                if tag == 0: 
                    #接口：返回错误信息
                    check_info.append("规则检查错误，在操作顺序{}中，出现‘{}’时缺少{}".format(set.step_number,key,val_list))
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

    check_info += DeviceMacth(checking_tickets)
    check_info += NLP_check(checking_tickets)
    check_info += RuleMacth(checking_tickets)

    return check_info

# 应用功能：NLP模型规则更新
def add_new_confusion(err:string,cor:string):
    filename = 'my_custom_confusion.txt'
    
    with open(filename, 'rb') as f:
        result = chardet.detect(f.read())
        encoding = result['encoding']

    with open(filename,'r', encoding=encoding) as f:
        for line in f:
            (key, val) = line.split()
            if key == err and val == cor:
                return "该语义修正已存在"

    with open(filename, 'a',encoding=encoding) as f:
        f.write('\n' + err +' '+ cor)
    
    return "新语义修正添加成功"

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
    print(add_new_confusion('母差','母差'))
    print(check_newtickets('将#2开关主变由运行转冷备用',[1,2,3,4,5,6,7],error_sentences))
