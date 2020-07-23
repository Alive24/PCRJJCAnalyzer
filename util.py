import cv2
import numpy as np
import win32gui
import numpy as np
from matplotlib import pyplot as plt
import config
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import *
import win32gui
import sys
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

    totalWidth = config.refImg['Width']
    totalHeight = config.refImg['Height']
    singleWidth = totalWidth / config.refImg['ColumnCount']
    singleHeight = totalHeight / config.refImg['RowCount']
    index = [int(midPoint[0]/singleWidth)+1, int(midPoint[1]/singleHeight)+1]
    return index


def gui_get_all_hwnd(hwnd,mouse):
    # 用于获取所有窗口的句柄
    if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
        hwnd_title.update({hwnd:win32gui.GetWindowText(hwnd)})

def gui_promtHandle():
    # 打印出所有窗口句柄和标题
    win32gui.EnumWindows(gui_get_all_hwnd, 0)
    for h,t in hwnd_title.items():
        if t is not "":
            print(h, t)

def gui_getScreenshotByHandle(handle:int):
    # 使用QT获取截图
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    img = screen.grabWindow(handle).toImage()
    return img



def query_gen_quick_key(true_id:str, user_id:int) -> str:
    qkey = int(true_id[-6:], 16)
    while qkey in quick_key_dic and quick_key_dic[qkey] != true_id:
        qkey = (qkey + 1) & 0xffffff
    quick_key_dic[qkey] = true_id
    mask = user_id & 0xffffff
    qkey ^= mask
    return base64.b32encode(qkey.to_bytes(3, 'little')).decode()[:5]

def query_parse_result(result):
    plan = {
        'id': result['id'],
        'planCharList' : [],
        'planPickList': [],
        'updated': '',
        'up': 0,
        'down': 0,
    }
