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
                print("设备检查错误，在操作步骤{}中，母线设备名错误".format(set.step_number))
                    
    return

def NLP_check(checking_tickets):
    for line in checking_tickets:
        correct_sent, err = pycorrector.correct(line.step)
    # 接口：返回错误信息
        if len(err) != 0:
            print("NLP模型检查错误,在操作步骤{}中，{} => {} {}".format(line.step_number,line.step, correct_sent, err))

# 规则匹配
def RuleMacth(checking_tickets):
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
                    print("规则检查错误，在操作步骤{}中，出现\"{}\"时缺少\"{}\"".format(set.step_number,key,val))
                    break
    
    return

if __name__ == '__main__':
    
    # 操作票接口处
    # 例：
    error_sentences = [
        '核对相关设备的运运行方式',
        '在后台监控机检查500kV#2M母线电压显示正常',
        '在后台监控机检查500kV#1M母线电压显示为零',
        '在在220kV母差保护屏Ⅱ（55P）将1QK Ⅰ母 Ⅱ母切换开关切换至“双母”位置',
        '在220kV #1电压互感器221PT端子箱合上交流电机电源1DK空气开关',
        '合上220kV #1电压互感器1M母线侧221PT刀闸',
        '检查220kV #1电压互感器1M母线侧221PT刀闸三相确在合上位置', 
    ]

    checking_tickets = []
    i = 0

    for sent in error_sentences:
        i += 1
        checking_ticket = ticket()

        sent = sent.replace(' ','')
        checking_ticket.add_newticket('将220kV1M母线由冷备用转运行，220kV 1M母线、2M母线方式倒为正常并列运行方式',i,sent)
        checking_tickets.append(checking_ticket)

    # 去空格
    checking_ticket.task = checking_ticket.task.replace(' ','')

    DeviceMacth(checking_tickets)
    NLP_check(checking_tickets)
    RuleMacth(checking_tickets)