import util
import json
import time
import config
import data
import cv2
import sys
import httpx
import asyncio
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QLabel, QWidget
from PyQt5 import QtGui, QtCore, QtNetwork
from gui import Ui_PCRJJCAnalyzerGUI
from solutionWidget import Ui_solutionWidget
global handle
global charImageList
global charDataList
global apiKey

class GUIsolutionWidget(QWidget, Ui_solutionWidget):
    def __init__(self, parent=None, solution):
        super(GUIsolutionWidget, self).__init__(parent)
        self.setupUi(self)
        

class GUIMainWin(QMainWindow, Ui_PCRJJCAnalyzerGUI):
    def __init__(self, parent=None):
        super(GUIMainWin, self).__init__(parent)
        self.setupUi(self)
        self.Debugger.clicked.connect(self.showChars)
        self.parse.clicked.connect(self.parseChars)
        self.query.clicked.connect(self.do_query)
        self.tryAddSolution.clicked.connect(self.addSolution)
    def addSolution(self, solution):
        self.solutionListLayout.addWidget(GUIsolutionWidget(solution))
        self.solutionListScrollAreaScrollAreaWidgetContents.setLayout(self.solutionListLayout)
    def showChars(self):
        self.pixCharImageList = [QtGui.QPixmap.fromImage(charImage) for charImage in charImageList]
        self.itemCharImageList = [QGraphicsPixmapItem(pix) for pix in self.pixCharImageList]
        # self.sceneCharImageList = [QGraphicsScene().addItem(item) for item in self.itemCharImageList]
        self.sceneCharImageList = [QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene()]
        for i in range(len(self.sceneCharImageList)):
            self.sceneCharImageList[i].addItem(self.itemCharImageList[i])
        self.char1Avatar.setScene(self.sceneCharImageList[0])
        self.char2Avatar.setScene(self.sceneCharImageList[1])
        self.char3Avatar.setScene(self.sceneCharImageList[2])
        self.char4Avatar.setScene(self.sceneCharImageList[3])
        self.char5Avatar.setScene(self.sceneCharImageList[4])
    def parseChars(self):
        refImage = cv2.imread('refImage.png') # 读取参考图
        for i in range(len(charImageList)):
            charNum = i+1
            charIndex = (util.cv_getIndex(util.cv_getMidPoint(charImageList[i], refImage, eval('cv2.TM_CCOEFF' )))) # 计算出目标角色在参考图中的坐标位置（行与列）
            charDataList[i] = data.refGrid[(charIndex[1]-1)][(charIndex[0]-1)]
            charName = charDataList[i]['name']
            print(charNum, charName, charIndex)
    def handleResponse(self, response):
        er = response.error()

        if er == QtNetwork.QNetworkReply.NoError:

            bytes_string = response.readAll()

            json_ar = json.loads(str(bytes_string, 'utf-8'))
            data = json_ar['form']

            print('Name: {0}'.format(data['name']))
            print('Age: {0}'.format(data['age']))

            print()

        else:
            print("Error occurred: ", er)
            print(response.errorString())
    def do_query(self):
        async def request(id_list):
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36',
                'authorization': config.apiKey,
                'Content-Type': 'application/json'
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post('https://api.pcrdfans.com/x/v1/search',json={"_sign": "a", "def": id_list, "nonce": "a", "page": 1, "sort": 1, "ts": int(time.time()), "region": config.region}, headers=headers)
                result = resp.json()
            return result
        raw_id_list = [charData['id'] for charData in charDataList]
        id_list = [ x * 100 + 1 for x in raw_id_list ]
        output=asyncio.run(request(id_list))
        print(output)

        
        # try:
        #     resp = await aiorequests.post('https://api.pcrdfans.com/x/v1/search', headers=header, json=payload, timeout=10)
        #     res = await resp.json()
        #     logger.debug(f'len(res)={len(res)}')
        # except Exception as e:
        #     logger.exception(e)
        #     return None

        # if res['code']:
        #     logger.error(f"Arena query failed.\nResponse={res}\nPayload={payload}")
        #     return None

        # ret = []
        # for entry in res['data']['result']:
        #     eid = entry['id']
        #     likes = get_likes(eid)
        #     dislikes = get_dislikes(eid)
        #     ret.append({
        #         'qkey': gen_quick_key(eid, user_id),
        #         'atk': [ chara.fromid(c['id'] // 100, c['star'], c['equip']) for c in entry['atk'] ],
        #         'up': entry['up'],
        #         'down': entry['down'],
        #         'my_up': len(likes),
        #         'my_down': len(dislikes),
        #         'user_like': 1 if user_id in likes else -1 if user_id in dislikes else 0
        #     })

    
        
    

if __name__ == '__main__':
    # ### CLI测试部分
    util.gui_promtHandle()  # 输出窗口句柄和标题
    handle = int(input(["请输入句柄"]))
    screenshot = util.gui_getScreenshotByHandle(handle)
    copyX = config.simulator['marginOffset'][0]
    copyY = config.simulator['marginOffset'][1]
    copyWidth = screenshot.width() - config.simulator['marginOffset'][0] - config.simulator['marginOffset'][2]
    copyHeight = screenshot.height() - config.simulator['marginOffset'][1] - config.simulator['marginOffset'][3]
    gameImage = screenshot.copy(copyX, copyY, copyWidth, copyHeight) # 根据边框裁剪出游戏图像
    translatedCharY = gameImage.height()*config.charLocationRatioConfig['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
    translatedCharH = gameImage.height()*config.charLocationRatioConfig['h']
    translatedCharW = gameImage.width()*config.charLocationRatioConfig['w']
    charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH) for x in config.charLocationRatioConfig['x'] ] # 裁剪出对方每个角色头像
    charDataList = [
        {'name': '未知角色', 'id': 1000},
        {'name': '未知角色', 'id': 1000},
        {'name': '未知角色', 'id': 1000},
        {'name': '未知角色', 'id': 1000},
        {'name': '未知角色', 'id': 1000},
]
 


    app = QApplication(sys.argv)
    mainWin = GUIMainWin()
    mainWin.show()
    sys.exit(app.exec_())