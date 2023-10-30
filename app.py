from flask import Flask, request, jsonify
import json
import base_match
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)


class InputError(Exception):
    def __init__(self, code, message, show):
        super().__init__(code, message, show)
        self.message = message
        self.code = code
        self.show = show


class CalculateError(Exception):
    def __init__(self, code, message, show):
        super().__init__(code, message, show)
        self.message = message
        self.code = code
        self.show = show


class OutputError(Exception):
    def __init__(self, code, message, show):
        super().__init__(code, message, show)
        self.message = message
        self.code = code
        self.show = show


class ModelFailError(Exception):
    def __init__(self, code, message, show):
        super().__init__(code, message, show)
        self.message = message
        self.code = code
        self.show = show


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = "application/json;charset=utf-8"


#
# 操作票识别 (废弃)
# taskSeq（List）：操作顺序 [1, 2, 3, 4, 5, 6, 7]
# taskName（String）：操作任务 "Task"
# sentencesList（List）：操作步骤 ["核对相关设备的运运行方式",
# 			"在后台监控机检查500kV#2M母线电压显示正常",
# 			"在后台监控机检查500kV#1M母线电压显示为零",
# 			"在在220kV母差保护屏Ⅱ（55P）将1QK Ⅰ母 Ⅱ母切换开关切换至“双母”位置",
# 			"在220kV #1电压互感器221PT端子箱合上交流电机电源1DK空气开关",
# 			"合上220kV #1电压互感器1M母线侧221PT刀闸",
# 			"检查220kV #1电压互感器1M母线侧221PT刀闸三相确在合上位置"],
#
@app.route('/nlpChecker', methods=['POST'])
def flask_api():
    if type(request.json) != str:
        api_json = request.json
    else:
        api_json = json.loads(request.json)

    task_seq = api_json["taskSeq"]
    task_name = api_json["taskName"]
    sentences_list = api_json["sentencesList"]

    result = base_match.check_newtickets_old(task_name, task_seq, sentences_list)

    return jsonify(code=100, data=result)


#
# 操作票识别
# taskSeq（List）：操作顺序 [1, 2, 3, 4, 5, 6, 7]
# taskName（String）：操作任务 "Task"
# sentencesList（List）：操作步骤 ["核对相关设备的运运行方式",
# 			"在后台监控机检查500kV#2M母线电压显示正常",
# 			"在后台监控机检查500kV#1M母线电压显示为零",
# 			"在在220kV母差保护屏Ⅱ（55P）将1QK Ⅰ母 Ⅱ母切换开关切换至“双母”位置",
# 			"在220kV #1电压互感器221PT端子箱合上交流电机电源1DK空气开关",
# 			"合上220kV #1电压互感器1M母线侧221PT刀闸",
# 			"检查220kV #1电压互感器1M母线侧221PT刀闸三相确在合上位置"],
# place 地点名称
# unit  发令单位
#
@app.route('/nlpCheckerV2', methods=['POST'])
def flask_api_v2():
    if type(request.json) != str:
        api_json = request.json
    else:
        api_json = json.loads(request.json)

    task_seq = api_json["taskSeq"]
    task_name = api_json["taskName"]
    sentences_list = api_json["sentencesList"]
    place = api_json["place"]
    unit = api_json["unit"]

    result = base_match.check_newtickets(task_name, task_seq, sentences_list, place, unit)

    return jsonify(code=100, data=result)


#
# 新增操作票语料
# errWord（String）: 错误的字词
# corWord（String）: 需要纠正成的字词
#
@app.route('/addCustomConfusion', methods=['POST'])
def add_custom_confusion():
    if type(request.json) != str:
        api_json = request.json
    else:
        api_json = json.loads(request.json)

    err_word = api_json["errWord"]
    cor_word = api_json["corWord"]

    result = base_match.add_new_confusion(err_word, cor_word)
    return jsonify(code=100, data=result)


#
# 新增规则库: 表示在en中出现key时，在co中需要出现val中的元素
#  en(String): '操作任务','操作步骤','地点名称','发令单位'
#  co(String): '操作任务','操作步骤','地点名称','发令单位'
#  key(String): 柜
#  val(String): T
#
@app.route('/addNewRule', methods=['POST'])
def add_new_rule():
    if type(request.json) != str:
        api_json = request.json
    else:
        api_json = json.loads(request.json)

    en = api_json["en"]
    co = api_json["co"]
    key = api_json["key"]
    val = api_json["val"]

    result = base_match.add_new_rule(en, co, key, val)
    return jsonify(code=100, data=result)


#
# 查询规则库
#
@app.route('/showRules', methods=['POST'])
def show_rules():
    if type(request.json) != str:
        api_json = request.json
    else:
        api_json = json.loads(request.json)

    result = base_match.show_rules()
    return jsonify(code=100, data=result)


#
# 查询设备库
#
@app.route('/showDevice', methods=['POST'])
def show_device():
    if type(request.json) != str:
        api_json = request.json
    else:
        api_json = json.loads(request.json)

    result = base_match.show_device()
    return jsonify(code=100, data=result)


@app.errorhandler(InputError)
def catch_except(e):
    return jsonify(code=e.args[0], data=e.args[1], frontend=e.args[2]), 500


@app.errorhandler(CalculateError)
def catch_except(e):
    return jsonify(code=e.args[0], data=e.args[1], frontend=e.args[2]), 500


@app.errorhandler(OutputError)
def catch_except(e):
    return jsonify(code=e.args[0], data=e.args[1], frontend=e.args[2]), 500


@app.errorhandler(ModelFailError)
def catch_except(e):
    return jsonify(code=e.args[0], data=e.args[1], frontend=e.args[2]), 500


@app.errorhandler(Exception)
def catch_except(e):
    type_name = type(e).__name__
    return jsonify(code=501,
                   data='运行错误，错误类型为%s，报错信息：%s' % (type_name, e.args),
                   frontend=0), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=7076)
    # flask_api()
    # add_custom_confusion()
