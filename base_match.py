import string
import chardet
from typing import *

import pycorrector
import sys

from flask import Flask

sys.path.append("..")

ATTR = {"step":"操作步骤",
        "task":"操作任务",
        "unit":"发令单位",
        "place":"地点名称"}

err_cor = {}
# 操作票数据结构
# 只需要操作任务，操作步骤，操作顺序三项
class ticket:
    def __init__(self):
        self.task = ''          # 操作任务
        self.step_number = 0    # 操作顺序
        self.step = ''          # 操作步骤
        self.place = ''         # 地点名称
        self.unit = ''          # 发令单位
    def add_newticket(self,Task,Step_number,Step,Place,Unit):
        self.task = Task        
        self.step_number = Step_number 
        self.step = Step
        self.place = Place
        self.unit = Unit
    def add_newtickets(self,Task,Step_number_list,Step_list,Place,Unit):
        for i in range(len(Step_number_list)):
            self.add_newticket(Task,Step_number_list[i],Step_list[i],Place,Unit)

class ticketrule:
    def __init__(self):
        self.en = ''
        self.co = ''
        self.key = ''
        self.val = []
    def add_newrule(self,en,co,key,val):
        if en == '操作任务':
            self.en = 'task'
        elif en == '操作步骤':
            self.en = 'step'       
        elif en == '地点名称':
            self.en = 'place' 
        elif en == '发令单位':
            self.en = 'unit'
        if co == '操作任务':
            self.co = 'task'
        elif co == '操作步骤':
            self.co = 'step'       
        elif co == '地点名称':
            self.en = 'place' 
        elif co == '发令单位':
            self.co = 'unit'       
        self.key = key
        self.val = val

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
            err_cor[str(line.step_number)] = [err[0][0],err[0][1]]
    # 接口：返回错误信息

    return check_info

# 规则匹配
def RuleMacth(checking_tickets):
    check_info = []
    filename = 'rule.txt'

    with open(filename, 'rb') as f:
        result = chardet.detect(f.read())
        encoding = result['encoding']

    with open(filename,'r', encoding=encoding) as f:
        res = None
        rules = []
        for line in f:
            newrule = ticketrule()
            en, co, key, val = line.split()
            val_list = list(val.split(","))
            newrule.add_newrule(en, co, key, val_list)
            rules.append(newrule)

    #字符串匹配
    for sen in checking_tickets:
        for rule in rules:
            res = eval('stringMacth(sen.{},rule.key)'.format(rule.en))
            if res is not None:
                tag = 0
                for val in rule.val:  
                    res = eval('stringMacth(sen.{},val)'.format(rule.co))
                    if res is not None:
                        tag = 1
                        break
                if tag == 0:        
                    check_info.append("规则检查错误，在操作顺序{},在{}中出现‘{}’时,{}缺少{}".format(sen.step_number,ATTR[rule.en],rule.key,ATTR[rule.co],rule.val))

    return check_info

def check_newtickets(Task:string,Step_number_list:list,Step_list:list,Place:string,Unit:string) ->list:
    checking_tickets = []
    check_info = []

    Task = Task.replace(' ','')

    for i in range(len(Step_number_list)):
        checking_ticket = ticket()
        Step_list[i] = Step_list[i].replace(' ','')
        checking_ticket.add_newticket(Task,Step_number_list[i],Step_list[i],Place,Unit)
        checking_tickets.append(checking_ticket)

    #check_info += DeviceMacth(checking_tickets)
    check_info += NLP_check(checking_tickets)
    #check_info += RuleMacth(checking_tickets)

    return check_info,err_cor

# 应用功能：NLP模型规则更新
def add_new_confusion(err:string,cor:string) ->string: 
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

# 应用功能：规则更新
def add_new_rule(en:string,co:string,key:string,val:list) ->string:
    filename = 'rule.txt'
    l = ['操作任务','操作步骤','地点名称','发令单位']
    if en in l and co in l:
        with open(filename, 'rb') as f:
            result = chardet.detect(f.read())
            encoding = result['encoding']

        with open(filename, 'a',encoding=encoding) as f:
            f.write('\n' + en +' '+ co + ' ' + key+ ' ' + val)
   
        return "新规则添加成功"
    else:
        return "规则格式错误"

def show_rules() ->list:
    filename = 'rule.txt'

    with open(filename, 'rb') as f:
        result = chardet.detect(f.read())
        encoding = result['encoding']

    with open(filename,'r', encoding=encoding) as f:
        info = []
        for line in f:
            en, co, key, val = line.split()
            info.append('在{}中，出现{}时，{}中不能出现{}'.format(en,key,co,val))
        return info

def show_device() ->list:
    filename = 'device.txt'
    with open(filename, 'rb') as f:
        result = chardet.detect(f.read())
        encoding = result['encoding']

    with open(filename,'r', encoding=encoding) as f:
        info = []
        for line in f:
            line = line.strip("\n")
            info.append(line)
        return info

if __name__ == '__main__':
    # 操作票接口处
    # 例：
    error_sentences = [
        '合对相关在分闸位置设备的运行方式；',
        '确认220kV#1电压互感器111PT 在冷备用状态；',
        '确认220kV母线并列运行；',
        '确认#3主变220kV中性点113000接地刀闸在拉开位置；',
        '在220kV #1电压互感器111PT端子箱：',
        '确认Ⅰ母PT计量表计用A相电压1MCBa空气开关在分闸位置；',
        '确认Ⅰ母保护1用A相电压2MCBa空气开关在分闸位置；',
        '确认110kV#1电压互感器111PT 二次开口三角电压二次接线已临时解开，并用绝缘胶布保好；',
        '确认上述一、二次设备在规定状态，启动范围内所有临时接地线均已拆除，接地刀闸均已拉开。',
    ]
    #print(show_rules())
    print(check_newtickets('220kV #1电压互感器119PT启动前操作',[1,2,3,4,5,6,7,8,9],error_sentences,'1','自调'))