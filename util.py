import cv2
import json
import copy
import logging
import numpy as np
import win32gui
import os
import base64
import numpy as np
from matplotlib import pyplot as plt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import *
import sys
import data

global_logger = logging.getLogger()
hwnd_title = dict()
quick_key_dic = {} 
default_refImageParams = {
    'refImagePath': '',
    'totalWidth': 0,
    'totalHeight': 0,
    'columnCount': 0,
    'rowCount': 0,
    'unitWidth': 60,
    'unitHeight': 60,
    'gapWidth': 2
}

default_dict = {
    'globalExclusionList': [],
    'globalHideExclusionRuledOutSwitch': False,
    'apiKey': '',
    'region': 1,
    'marginOffsetMode': '雷电模拟器',
    'effectiveMarginOffSet': [0, 32, 42, 0],
    'customizedApi': False,
    'customizedApiUrl': '',
    'algorithm': 'TM_SQDIFF',
    'matchTemplateParams':
        {
            'charLocationRatioConfig_CurrentEnemyTeam': 
                {
                    'y': 0.138679389,
                    'w': 0.058583784,
                    'h': 0.08859542,
                    'x': [0.610567568, 0.681837838, 0.752027027, 0.821459459, 0.891648649]
                },
            'charLocationRatioConfig_HistoryTeamOne': 
                {
                    'y': 0.265,
                    'w': 0.058583784,
                    'h': 0.09,
                    'x': [0.486625, 0.5571875, 0.628375, 0.69825, 0.7686375]
                },
            'charLocationRatioConfig_HistoryTeamTwo': 
                {
                    'y': 0.4773333333,
                    'w': 0.058583784,
                    'h': 0.09,
                    'x': [0.486625, 0.5571875, 0.628375, 0.69825, 0.7686375]
                },
            'charLocationRatioConfig_HistoryTeamThree':
                {
                    'y': 0.69,
                    'w': 0.058583784,
                    'h': 0.09,
                    'x': [0.486625, 0.5571875, 0.628375, 0.69825, 0.7686375]
                },
            'charLocationRatioConfig_HistoryTeamOne_WithTitleBanner': 
                {
                    'y': 0.277778,
                    'w': 0.058583784,
                    'h': 0.09,
                    'x': [0.486625, 0.5571875, 0.628375, 0.69825, 0.7686375]
                },
            'charLocationRatioConfig_HistoryTeamTwo_WithTitleBanner': 
                {
                    'y': 0.483333,
                    'w': 0.058583784,
                    'h': 0.09,
                    'x': [0.486625, 0.5571875, 0.628375, 0.69825, 0.7686375]
                },
            'charLocationRatioConfig_HistoryTeamThree_WithTitleBanner':
                {
                    'y': 0.683333,
                    'w': 0.058583784,
                    'h': 0.09,
                    'x': [0.486625, 0.5571875, 0.628375, 0.69825, 0.7686375]
                },
            'charLocationRatioConfig_OwnTeam': 
                {
                    'y': 0.76,
                    'w': 0.0936,
                    'h': 0.130,
                    'x': [0.056, 0.16625, 0.28375, 0.394375, 0.506878]
                }
        }
}

def config_getRefImageParams():
    refImageParams = copy.deepcopy(default_refImageParams)
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    refImageParams['refImagePath'] = os.path.join(base_path, 'resource/refImage.png')
    refImageQImage = QImage(refImageParams['refImagePath'])
    refImageParams['totalWidth'] = refImageQImage.width()
    refImageParams['totalHeight'] = refImageQImage.height()
    refImageParams['columnCount'] = len(data.refGrid[0])
    refImageParams['rowCount'] = len(data.refGrid)
    return refImageParams




def cv_getMidPoint(incomingImage, refImage, method):
# 读取目标图像和参考图像，获取目标图像在参考图像中对应的部分的中点
# incomingImage是QImage，需要转换成CV2 MAT RGB(3通道)
# targetImage是转化后的结果，可以用于matchTemplate
# method为methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR','cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED'] 其一
    incomingImage = incomingImage.convertToFormat(4)
    w = incomingImage.width()
    h = incomingImage.height()
    ptr = incomingImage.bits()
    ptr.setsize(incomingImage.byteCount())
    targetImage = np.array(ptr).reshape(h, w, 4) #此处完成转换
    targetImage = cv2.cvtColor(targetImage, cv2.COLOR_BGRA2BGR)


    res = cv2.matchTemplate(refImage,targetImage,method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    
    bottom_right = (top_left[0] + w, top_left[1] + h)

    cv2.rectangle(refImage,top_left, bottom_right, 255, 2)

    ## 以下用于Debug时生成匹配结果对比图
    # plt.subplot(121),plt.imshow(res,cmap = 'gray')
    # plt.title('Matching Result'), plt.xticks([]), plt.yticks([])
    # plt.subplot(122),plt.imshow(refImage,cmap = 'gray')
    # plt.title('Detected Point'), plt.xticks([]), plt.yticks([])
    # plt.suptitle(method)
    # plt.show()

    midPoint = (top_left[0] + 0.5 * w, top_left[1] + 0.5 *h)
    return midPoint

def cv_getIndex(midPoint, refImageParams):
# 根据midPoint坐标计算其顺序坐标（行列）
    index = [int(midPoint[0]/(refImageParams['unitWidth'] + refImageParams['gapWidth']))+1, int(midPoint[1]/(refImageParams['unitHeight'] + refImageParams['gapWidth']))+1]
    return index


def query_gen_quick_key(true_id:str, user_id:int) -> str:
    qkey = int(true_id[-6:], 16)
    while qkey in quick_key_dic and quick_key_dic[qkey] != true_id:
        qkey = (qkey + 1) & 0xffffff
    quick_key_dic[qkey] = true_id
    mask = user_id & 0xffffff
    qkey ^= mask
    return base64.b32encode(qkey.to_bytes(3, 'little')).decode()[:5]

def query_getPickAvatar(id:int, refImageParams:dict) -> QImage:
    def getGridIndex(realId):
        index = [0, 0]
        for i in range(refImageParams['rowCount']):
            for j in range(refImageParams['columnCount']):
                if data.refGrid[i][j]['id'] == realId:
                    index[0] = i + 1
                    index[1] = j + 1
                    return index
    realId = id // 100
    pickIndex = getGridIndex(realId)
    pickX = (pickIndex[1] - 1) * (refImageParams['unitWidth'] + refImageParams['gapWidth'])
    pickY = (pickIndex[0] - 1) * (refImageParams['unitWidth'] + refImageParams['gapWidth'])
    pickW = refImageParams['unitWidth']
    pickH = refImageParams['unitWidth']
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    pickAvatar = QImage(refImageParams['refImagePath']).copy(pickX, pickY, pickW, pickH)
    return pickAvatar

def config_loadConfig():
    if not os.path.exists(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer")):
        os.makedirs(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer"))
    try:
        config_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "config.json"),'r',encoding='utf-8')
        config_dict_toLoad = json.load(config_file)
        config_dict = copy.deepcopy(default_dict)
        for key in list(config_dict_toLoad.keys()):
            config_dict[key] = config_dict_toLoad[key]
        config_file.close()
    except Exception as e:
        global_logger.exception("config_loadConfig()错误")
        config_dict = copy.deepcopy(default_dict)
        config_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "config.json"),'w',encoding='utf-8')
        json.dump(config_dict,config_file,ensure_ascii=False)
        config_file.close()
    return config_dict

def config_loadRefImageParams():
    if not os.path.exists(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer")):
        os.makedirs(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer"))
    try:
        refImageParams_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "refImageParams.json"),'r',encoding='utf-8')
        refImageParams_toLoad = json.load(refImageParams_file)
        refImageParams = copy.deepcopy(default_refImageParams)
        for key in list(refImageParams_toLoad.keys()):
            refImageParams[key] = refImageParams_toLoad[key]
        refImageParams_file.close()
    except Exception as e:
        global_logger.exception("config_loadRefImageParams()错误")
        refImageParams = copy.deepcopy(default_refImageParams)
        refImageParams_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "refImageParams.json"),'w',encoding='utf-8')
        json.dump(refImageParams,refImageParams_file,ensure_ascii=False)
        refImageParams_file.close()
    return refImageParams

def config_writeConfig(config_dict):
    try:
        config_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "config.json"),'w',encoding='utf-8')
        json.dump(config_dict,config_file,ensure_ascii=False)
        config_file.close()
    except Exception as e:
        global_logger.exception("config_writeConfig()错误")
        config_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "config.json"),'w',encoding='utf-8')
        json.dump(config_dict,config_file,ensure_ascii=False)
        config_file.close()
    return

# 暂不开放
# def config_writerefImageParams(config_dict):
#     try:
#         refImageParams_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "refImageParams.json"),'w',encoding='utf-8')
#         json.dump(refImageParams,refImageParams_file,ensure_ascii=False)
#         refImageParams_file.close()
#     except Exception as e:
#         print(e)
#         refImageParams_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "refImageParams.json"),'w',encoding='utf-8')
#         json.dump(refImageParams,refImageParams_file,ensure_ascii=False)
#         refImageParams_file.close()
#     return

def solution_loadLists():
    try:
        bookmarkList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "bookmarkList.json"),'r',encoding='utf-8')
        bookmarkList = json.load(bookmarkList_file)
        bookmarkList_file.close()
    except Exception as e:
        global_logger.exception('solution_loadLists()错误')
        bookmarkList = []
        bookmarkList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "bookmarkList.json"),'w',encoding='utf-8')
        json.dump(bookmarkList,bookmarkList_file,ensure_ascii=False)
        bookmarkList_file.close()
    try:
        ruleOutList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "ruleOutList.json"),'r',encoding='utf-8')
        ruleOutList = json.load(ruleOutList_file)
        ruleOutList_file.close()
    except Exception as e:
        global_logger.exception('solution_loadLists()错误')
        ruleOutList = []
        ruleOutList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "ruleOutList.json"),'w',encoding='utf-8')
        json.dump(ruleOutList,ruleOutList_file,ensure_ascii=False)
        ruleOutList_file.close()
    return [bookmarkList, ruleOutList]

def solution_appendToBookmarkList(solution, mainGUI):
    mainGUI.bookmarkList.append(solution)
    bookmarkList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "bookmarkList.json"),'w',encoding='utf-8')
    json.dump(mainGUI.bookmarkList, bookmarkList_file, ensure_ascii=False)
    bookmarkList_file.close()
    return

def solution_appendToRuleOutList(solution, mainGUI):
    mainGUI.ruleOutList.append(solution)
    ruleOutList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "ruleOutList.json"),'w',encoding='utf-8')
    json.dump(mainGUI.ruleOutList, ruleOutList_file, ensure_ascii=False)
    ruleOutList_file.close()
    return

def solution_removeFromBookmarkList(solution, mainGUI):
    for i in range(len(mainGUI.bookmarkList)):
        if mainGUI.bookmarkList[i]['id'] == solution['id']:
            mainGUI.bookmarkList.pop(i)
            break
    bookmarkList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "bookmarkList.json"),'w',encoding='utf-8')
    json.dump(mainGUI.bookmarkList, bookmarkList_file, ensure_ascii=False)
    bookmarkList_file.close()
    return

def solution_removeFromRuleOutList(solution, mainGUI):
    for i in range(len(mainGUI.ruleOutList)):
        if mainGUI.ruleOutList[i]['id'] == solution['id']:
            mainGUI.ruleOutList.pop(i)
            break
    ruleOutList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "ruleOutList.json"),'w',encoding='utf-8')
    json.dump(mainGUI.ruleOutList, ruleOutList_file, ensure_ascii=False)
    ruleOutList_file.close()
    return

def refData_getNameByRawID(rawID):
    for row in data.refGrid:
        for entry in row:
            if entry['id'] == rawID:
                return entry['name']
    return