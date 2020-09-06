import cv2
import json
import numpy as np
import win32gui
import os
import numpy as np
from matplotlib import pyplot as plt
import config
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import *
import win32gui
import sys
import data
hwnd_title = dict()

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

def cv_getIndex(midPoint):
# 根据midPoint坐标计算其顺序坐标（行列）
    index = [int(midPoint[0]/config.refImg['UnitWidth'])+1, int(midPoint[1]/config.refImg['UnitWidth'])+1]
    return index


def query_gen_quick_key(true_id:str, user_id:int) -> str:
    qkey = int(true_id[-6:], 16)
    while qkey in quick_key_dic and quick_key_dic[qkey] != true_id:
        qkey = (qkey + 1) & 0xffffff
    quick_key_dic[qkey] = true_id
    mask = user_id & 0xffffff
    qkey ^= mask
    return base64.b32encode(qkey.to_bytes(3, 'little')).decode()[:5]

def query_getPickAvatar(id:int, bigfun:bool) -> QImage:
    def getGridIndex(realId, p2):
        index = [0, 0]
        for i in range(int(p2.height() / config.refImg['UnitWidth'])):
            for j in range(int(p2.width() / config.refImg['UnitWidth'])):
                if bigfun:
                    refGrid = data.bigfunRefGrid
                else:
                    refGrid = data.refGrid
                if isinstance(realId, str):
                    realId = int(realId)
                if refGrid[i][j]['id'] == realId:
                    index[0] = i + 1
                    index[1] = j + 1
                    return index
    if not bigfun:
        id //= 100
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    if not bigfun:
        refImagePath = os.path.join(base_path, 'resource/refImage.png')
    else:
        refImagePath = os.path.join(base_path, 'resource/bigfun.png')
    p2 = QImage(refImagePath)
    pickIndex = getGridIndex(id, p2)
    if not bigfun:
        pickX = (pickIndex[1] - 1) * (config.refImg['UnitWidth'] + config.refImg['GapWidth'])
        pickY = (pickIndex[0] - 1) * (config.refImg['UnitWidth'] + config.refImg['GapWidth'])
    else:
        pickX = (pickIndex[1] - 1) * (config.refImg['UnitWidth'])
        pickY = (pickIndex[0] - 1) * (config.refImg['UnitWidth'])
    pickW = config.refImg['UnitWidth']
    pickH = config.refImg['UnitWidth']
    pickAvatar = p2.copy(pickX, pickY, pickW, pickH)
    return pickAvatar

def config_loadConfig():
    if not os.path.exists(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer")):
        os.makedirs(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer"))
    try:
        config_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "config.json"),'r',encoding='utf-8')
        config_dict = json.load(config_file)
        config_file.close()
    except Exception as e:
        print(e)
        config_dict = {
            'apiKey': '',
            'region': 1,
            'marginOffsetMode': '雷电模拟器',
            'effectiveMarginOffSet': [0, 32, 42, 0]
        }
        config_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "config.json"),'w',encoding='utf-8')
        json.dump(config_dict,config_file,ensure_ascii=False)
        config_file.close()
    return config_dict

def config_writeConfig(config_dict):
    try:
        config_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "config.json"),'w',encoding='utf-8')
        json.dump(config_dict,config_file,ensure_ascii=False)
        config_file.close()
    except Exception as e:
        print(e)
        config_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "config.json"),'w',encoding='utf-8')
        json.dump(config_dict,config_file,ensure_ascii=False)
        config_file.close()
    return

def solution_loadLists():
    try:
        bookmarkList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "bookmarkList.json"),'r',encoding='utf-8')
        bookmarkList = json.load(bookmarkList_file)
        bookmarkList_file.close()
    except Exception as e:
        print(e)
        bookmarkList = []
        bookmarkList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "bookmarkList.json"),'w',encoding='utf-8')
        json.dump(bookmarkList,bookmarkList_file,ensure_ascii=False)
        bookmarkList_file.close()
    try:
        ruleOutList_file = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "ruleOutList.json"),'r',encoding='utf-8')
        ruleOutList = json.load(ruleOutList_file)
        ruleOutList_file.close()
    except Exception as e:
        print(e)
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