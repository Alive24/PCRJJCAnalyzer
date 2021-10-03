#! /usr/bin/env python
#-*- coding: utf-8 -*-
import os
from pcrdapi import sign
import numpy as np
import json
import copy
import time
import cv2
import sys
import httpx
import requests
import win32gui
import asyncio
import quamash
import logging
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QApplication, QMainWindow, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QLabel, QWidget, QTextBrowser, QMessageBox, QButtonGroup, QCheckBox, QDialog, QMenu, QAction, QPlainTextEdit
from PyQt5 import QtGui, QtCore, QtNetwork
from PyQt5.QtCore import QProcess, QRunnable, QThreadPool, pyqtSlot, QThread, QMetaObject, Qt, Q_ARG, QObject, pyqtSignal

## Version Info
global globalVersion
globalVersion = 'PCRJJCAnalyzer-v0.2.2-beta2'

## PrepareInitialPaths
if not os.path.exists(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer")):
        os.makedirs(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer"))
if not os.path.exists(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData")):
    os.makedirs(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData"))
if not os.path.exists(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "characterIndexList.json")):
    with open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "characterIndexList.json"),'w',encoding='utf-8') as file:
        file.write("[]")
        file.close()

## PrepareGlobalVariables
global characterIndexListJsonFile
global characterIndexList
characterIndexListJsonFile = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "characterIndexList.json"),'r',encoding='utf-8')
characterIndexList = json.load(characterIndexListJsonFile)

## Prepare Local Modules
import util
import OTA
from gui import Ui_PCRJJCAnalyzerGUI
from solutionWidget import Ui_solutionWidget
from configDialog import Ui_configDialog
from exceptHookHandler import ExceptHookHandler


## Prepare Logging
global_logger = logging.getLogger()

class LogHandler(QObject, logging.Handler):
    new_record = pyqtSignal(object)
    def __init__(self, parent):
        super().__init__(parent)
        super(logging.Handler).__init__()
        formatter = LogFormatter('%(asctime)s|%(levelname)s|%(message)s', '%d/%m/%Y %H:%M:%S')
        self.setFormatter(formatter)
    def emit(self, record):
        msg = self.format(record)
        self.new_record.emit(msg) # <---- emit signal here
class LogFormatter(logging.Formatter):
    def formatException(self, ei):
        result = super(LogFormatter, self).formatException(ei)
        return result
    def format(self, record):
        s = super(LogFormatter, self).format(record)
        if record.exc_text:
            s = s.replace('\n', '')
        return s


class GUIConfigDialogWidget(QDialog, Ui_configDialog):
    def __init__(self, parent=None, mainGUI=None):
        super(GUIConfigDialogWidget, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("设定")
        self.closeConfigDialogButton.clicked.connect(self.closeConfigDialog)
        self.customizedApiUrlLineEdit.setText(config_dict['customizedApiUrl'])
        if config_dict['customizedApi'] == False:
            self.defaultApiUrlRadioButton.setChecked(True)
            self.customizedApiUrlLineEdit.setDisabled(True)
        else:
            self.customizedApiUrlRadioButton.setChecked(True)
        self.defaultApiUrlRadioButton.clicked.connect(self.setApiModeOnClicked)
        self.HimariApiUrlRadioButton.clicked.connect(self.setApiModeOnClicked)
        self.customizedApiUrlRadioButton.clicked.connect(self.setApiModeOnClicked)
        self.customizedApiUrlLineEdit.textChanged.connect(self.customizedApirUrlLineEditHandler)
        self.updateFromCNSourceButton.clicked.connect(self.updateFromCNSourceOnClicked)
        self.updateFromJPSourceButton.clicked.connect(self.updateFromJPSourceOnClicked)
        self.updateStatusTag.setText(config_dict['lastDatabaseUpdate'])
        logHandler = LogHandler(self)
        logTextBox = QPlainTextEdit(self)
        self.logTextBoxLayout.addWidget(logTextBox)
        logging.getLogger().addHandler(logHandler)
        logging.getLogger().setLevel(logging.WARNING)
        logHandler.new_record.connect(logTextBox.appendPlainText)
        loggingLevelList = ["Warning", "Info", "Debug"]
        self.loggingLevelDropbox.addItems(loggingLevelList)
        self.loggingLevelDropbox.activated[str].connect(lambda loggingLevel: self.onLoggingLevelDropboxSelect(loggingLevel))
        self.openConfigFolderButton.clicked.connect(self.onOpenConfigFolderButtonClicked)
        self.resetSettingsButton.clicked.connect(self.onResetSettingsButton)
        self.QRafdian.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "afdian", "afdian-Alive24.png")))
        self.QRalipay.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "afdian", "tips-alipay.png")))
        self.QRwechat.setPixmap(QtGui.QPixmap(os.path.join(os.getcwd(), "afdian", "tips-wechat.png")))
    def onOpenConfigFolderButtonClicked(self):
        os.startfile(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer"))
    def onResetSettingsButton(self):
        global config_dict
        util.config_writeConfig(util.default_dict)
        config_dict = util.default_dict
        self.customizedApiUrlLineEdit.setDisabled(True)
        self.defaultApiUrlRadioButton.setChecked(True)
        global_logger.warning("已重置设定。")
    def onLoggingLevelDropboxSelect(self, loggingLevel):
        if loggingLevel == "Warning":
            logging.getLogger().setLevel(logging.WARNING)
        if loggingLevel == "Info":
            logging.getLogger().setLevel(logging.INFO)
        if loggingLevel == "Debug":
            logging.getLogger().setLevel(logging.DEBUG)

    def emitLog(self, record):
        msg = self.format(record)
        self.loggingPlainTextEdit.appendPlainText(msg)
    def updateFromJPSourceOnClicked(self):
        url = "https://redive.estertion.win/db/redive_jp.db.br"
        updateFromJPSourceRunnable = updateRunnable(url, self, "JP")
        try:
            QThreadPool.globalInstance().start(updateFromJPSourceRunnable)
        except Exception as e:
            self.updateStatusTag.setText("更新失败")
            self.updateStatusTag.setStyleSheet("color:red")
    def updateFromCNSourceOnClicked(self):
        url = "https://redive.estertion.win/db/redive_cn.db.br"
        updateFromJPSourceRunnable = updateRunnable(url, self, "CN")
        try:
            QThreadPool.globalInstance().start(updateFromJPSourceRunnable)
        except Exception as e:
            self.updateStatusTag.setText("更新失败")
            self.updateStatusTag.setStyleSheet("color:red")
    def setApiModeOnClicked(self):
        clickedRadioButton = self.sender()
        if clickedRadioButton.isChecked():
            if clickedRadioButton.objectName() == "defaultApiUrlRadioButton":
                config_dict['customizedApi'] = False
                self.customizedApiUrlLineEdit.setDisabled(True)
            if clickedRadioButton.objectName() == "HimariApiUrlRadioButton":
                config_dict['customizedApi'] = True
                self.customizedApiUrlLineEdit.setDisabled(True)
                config_dict['customizedApiUrl'] = "https://pcr.himaribot.com/himari_api/pcrdproxy"
                util.config_writeConfig(config_dict)
            if clickedRadioButton.objectName() == "customizedApiUrlRadioButton":
                config_dict['customizedApi'] = True
                self.customizedApiUrlLineEdit.setDisabled(False)
        try:
            util.config_writeConfig(config_dict)
            util.config_loadConfig()
        except Exception as e:
            global_logger.exception("Failed to write config", e)
    def customizedApirUrlLineEditHandler(self,customizedApiUrl):
        config_dict['customizedApiUrl'] = customizedApiUrl
        util.config_writeConfig(config_dict)
    def closeConfigDialog(self):
        self.close()

class updateRunnable(QRunnable):
    def __init__(self, url, parentWidget, source):
        QRunnable.__init__(self)
        self.url = url
        self.parentWidget = parentWidget
        self.source = source
    def run(self):
        OTA.updateCharacterIndexListByURL(self.url)
        characterIndexListJsonFile = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "characterIndexList.json"),'r',encoding='utf-8')
        characterIndexList = json.load(characterIndexListJsonFile)
        OTA.updateAssetsByCharacterIndexList(characterIndexList)
        OTA.generateRefImageByCharacterIndexList(characterIndexList)
        config_dict['lastDatabaseUpdate'] = "%s from %s" % (str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())), self.source)
        util.config_writeConfig(config_dict)
        self.parentWidget.updateStatusTag.setText(config_dict['lastDatabaseUpdate'])

class generateCharCandidateRunnable(QRunnable):
    def __init__(self, charImageList, mainGUI, i, ):
        QRunnable.__init__(self)
        self.charImageList = charImageList
        self.w = mainGUI
        self.i = i
    def run(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        # 尝试修正可能出现的中文路径编码问题
        refImagePath = refImageParams['refImagePath']
        refImage = cv2.imdecode(np.fromfile(refImagePath,dtype=np.uint8),cv2.IMREAD_COLOR) # 读取参考图
        charIndexCandidateList = [[],[],[],[],[],[]]
        charCandidateList = [
                {'name': '未知角色', 'id': 1000},
                {'name': '未知角色', 'id': 1000},
                {'name': '未知角色', 'id': 1000},
                {'name': '未知角色', 'id': 1000},
                {'name': '未知角色', 'id': 1000},
                {'name': '未知角色', 'id': 1000},
        ]
        charIndexCandidateList[0] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_CCOEFF")), refImageParams))
        charIndexCandidateList[1] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_CCOEFF_NORMED")), refImageParams))
        charIndexCandidateList[2] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_CCORR")), refImageParams))
        charIndexCandidateList[3] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_CCORR_NORMED")),refImageParams))
        charIndexCandidateList[4] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_SQDIFF")), refImageParams))
        charIndexCandidateList[5] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_SQDIFF_NORMED")), refImageParams))
        for j in range(6):
            charName = characterIndexList[charIndexCandidateList[j][0]]["unit_name"]
            charId = characterIndexList[charIndexCandidateList[j][0]]["unit_id"]
            charCandidate = {"name": charName, "id": charId}
            charCandidateList[j] = charCandidate
        charDropboxItemList = []
        for j in range(6):
            charDropboxItemList.append(charCandidateList[j]['name'])
        if self.i == 0:
            self.w.char1CandidateList = charCandidateList
            if self.w.activeTeamNum ==1:
                self.w.queryResultStorageTeam1['char1CandidateList'] = charCandidateList
            if self.w.activeTeamNum ==2:
                self.w.queryResultStorageTeam2['char1CandidateList'] = charCandidateList
            if self.w.activeTeamNum ==3:
                self.w.queryResultStorageTeam3['char1CandidateList'] = charCandidateList
            self.w.char1Dropbox.addItems(charDropboxItemList)
        if self.i == 1:
            self.w.char2CandidateList = charCandidateList
            if self.w.activeTeamNum ==1:
                self.w.queryResultStorageTeam1['char2CandidateList'] = charCandidateList
            if self.w.activeTeamNum ==2:
                self.w.queryResultStorageTeam2['char2CandidateList'] = charCandidateList
            if self.w.activeTeamNum ==3:
                self.w.queryResultStorageTeam3['char2CandidateList'] = charCandidateList
            self.w.char2Dropbox.addItems(charDropboxItemList)
        if self.i == 2:
            self.w.char3CandidateList = charCandidateList
            if self.w.activeTeamNum ==1:
                self.w.queryResultStorageTeam1['char3CandidateList'] = charCandidateList
            if self.w.activeTeamNum ==2:
                self.w.queryResultStorageTeam2['char3CandidateList'] = charCandidateList
            if self.w.activeTeamNum ==3:
                self.w.queryResultStorageTeam3['char3CandidateList'] = charCandidateList
            self.w.char3Dropbox.addItems(charDropboxItemList)
        if self.i == 3:
            self.w.char4CandidateList = charCandidateList
            if self.w.activeTeamNum ==1:
                self.w.queryResultStorageTeam1['char4CandidateList'] = charCandidateList
            if self.w.activeTeamNum ==2:
                self.w.queryResultStorageTeam2['char4CandidateList'] = charCandidateList
            if self.w.activeTeamNum ==3:
                self.w.queryResultStorageTeam3['char4CandidateList'] = charCandidateList
            self.w.char4Dropbox.addItems(charDropboxItemList)
        if self.i == 4:
            self.w.char5CandidateList = charCandidateList
            if self.w.activeTeamNum ==1:
                self.w.queryResultStorageTeam1['char5CandidateList'] = charCandidateList
            if self.w.activeTeamNum ==2:
                self.w.queryResultStorageTeam2['char5CandidateList'] = charCandidateList
            if self.w.activeTeamNum ==3:
                self.w.queryResultStorageTeam3['char5CandidateList'] = charCandidateList
            self.w.char5Dropbox.addItems(charDropboxItemList)
        

class RequestRunnable(QRunnable):
    def __init__(self, url, json, mainGUI, apiKey):
        QRunnable.__init__(self)
        self.mUrl = url
        self.mJson = json
        self.w = mainGUI
        self.wApiKey = apiKey
    
    def getIsInRuleOutList(self, solution, mainGUI):
        for ruledOutSolution in mainGUI.ruleOutList:
            if solution['id'] == ruledOutSolution['id']:
                return True
        return False
    
    @staticmethod
    def _dumps(x):
        return json.dumps(x, ensure_ascii=False).replace(' ', '')

    def run(self):
        self.w.queryStatusTag.setText('查询中')
        self.w.queryStatusTag.setStyleSheet("color:black")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66",
            "Referer": "https://pcrdfans.com/",
            "Origin": "https://pcrdfans.com",
            "Accept": "*/*",
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "",
            "Host": "api.pcrdfans.com",
        }
        r = requests.post(self.mUrl, data=RequestRunnable._dumps(self.mJson).encode('utf8'), headers=headers) or None
        QThread.msleep(500)
        try:
            if self.w.activeTeamNum == 1:
                self.w.queryResultStorageTeam1['rjson'] = r.json()
                self.w.queryResultStorageTeam1['charDataList'] = self.w.charDataList
            if self.w.activeTeamNum == 2:
                self.w.queryResultStorageTeam2['rjson'] = r.json()
                self.w.queryResultStorageTeam2['charDataList'] = self.w.charDataList
            if self.w.activeTeamNum == 3:
                self.w.queryResultStorageTeam3['rjson'] = r.json()
                self.w.queryResultStorageTeam3['charDataList'] = self.w.charDataList
            if len(r.json()['data']['result']) == 0:
                self.w.queryStatusTag.setText('无结果！等待查询')
                self.w.queryStatusTag.setStyleSheet("color:green")
                return
            for solution in r.json()['data']['result']:
                if config_dict['globalHideExclusionRuledOutSwitch'] == True:
                    if self.getIsInRuleOutList(solution, self.w):
                        continue                
                    __solutionPickIDSet = set([item['id'] for item in solution['atk']])
                    __intersection = set(config_dict['globalExclusionList']) & __solutionPickIDSet
                    if len(__intersection) != 0:
                        continue
                QMetaObject.invokeMethod(self.w, "addSolution",
                                        Qt.QueuedConnection,
                                        Q_ARG(dict, solution))
            self.w.queryStatusTag.setText('等待查询')
            self.w.queryStatusTag.setStyleSheet("color:green")
        except Exception as e:
            global_logger.exception("查询失败\n")
            global_logger.exception("self.mJson: %s\n" % self.mJson)
            try:
                global_logger.exception("r.json(): %s\n" % r.json())
                self.w.queryStatusTag.setText('查询失败(%s)' % r.json()['code'])
                self.w.queryStatusTag.setStyleSheet("color:red")
            except:
                global_logger.exception("没有获取到返回结果，请检查接口URL。\n" )
                self.w.queryStatusTag.setText('查询失败(%s)' % "N/A URL")
                self.w.queryStatusTag.setStyleSheet("color:red")
            return

class GUIsolutionWidget(QWidget, Ui_solutionWidget):
    def __init__(self, parent=None, solution=None, mainGUI=None, buttonGroup=None):
        super(GUIsolutionWidget, self).__init__(parent)
        self.setupUi(self)
        self.teamNum = mainGUI.activeTeamNum
        self.pick1Avatar.setObjectName('pick1Avatar_%s' % solution['id'])
        self.pick2Avatar.setObjectName('pick2Avatar_%s' % solution['id'])
        self.pick3Avatar.setObjectName('pick3Avatar_%s' % solution['id'])
        self.pick4Avatar.setObjectName('pick4Avatar_%s' % solution['id'])
        self.pick5Avatar.setObjectName('pick5Avatar_%s' % solution['id'])
        self.pick1Star.setObjectName('pick1Star_%s' % solution['id'])
        self.pick2Star.setObjectName('pick2Star_%s' % solution['id'])
        self.pick3Star.setObjectName('pick3Star_%s' % solution['id'])
        self.pick4Star.setObjectName('pick4Star_%s' % solution['id'])
        self.pick5Star.setObjectName('pick5Star_%s' % solution['id'])
        self.upCount.setObjectName('upCount_%s' % solution['id'])
        self.downCount.setObjectName('downCount_%s' % solution['id'])
        self.likeDislikeRatioValue.setObjectName('likeDislikeRatioValue_%s' % solution['id'])
        self.commentBrowser.setObjectName('commentBrowser_%s' % solution['id'])
        self.lockSolutionCheckBox.stateChanged.connect(lambda: mainGUI.addToExclusionList(self, self.lockSolutionCheckBox, solution, self.teamNum))
        self.lockSolutionCheckBox.setObjectName('lockSolutionCheckBox_%s' % solution['id'])
        if self.getIsInBookmarkList(solution, mainGUI):
            self.bookmarkSolutionCheckBox.setChecked(True)
            self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            self.setStyleSheet('background-color: aquamarine')
        self.bookmarkSolutionCheckBox.stateChanged.connect(lambda: self.bookmarkSolutionCheckBoxHandler(self.bookmarkSolutionCheckBox, solution, mainGUI))
        self.bookmarkSolutionCheckBox.setObjectName('bookmarkSolutionCheckBox_%s' % solution['id'])
        if self.getIsInRuleOutList(solution, mainGUI):
            self.ruleOutSolutionCheckBox.setChecked(True)
            self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            self.setStyleSheet('background-color: pink')
        self.ruleOutSolutionCheckBox.stateChanged.connect(lambda: self.ruleOutSolutionCheckBoxHandler(self.ruleOutSolutionCheckBox, solution, mainGUI))
        self.ruleOutSolutionCheckBox.setObjectName('ruleOutSolutionCheckBox_%s' % solution['id'])
        buttonGroup.addButton(self.lockSolutionCheckBox)
        self.renderSolution(solution, mainGUI, buttonGroup)
        for i in range(5):
            self.createContextMenu(solution, i+1, mainGUI)
    def createContextMenu(self, solution, pickIndex, mainGUI):
        def showContextMenu(self):
            __contextMenu.move(QtGui.QCursor().pos())
            __contextMenu.show()
        def actionHandler(checked, __pickID, mainGUI):
            if checked:
                mainGUI.exclusionList[0].append(__pickID)
                config_dict['globalExclusionList'] == mainGUI.exclusionList[0]
                util.config_writeConfig(config_dict)
                __targetAvartar.setStyleSheet('background-color: orange')
            else:
                for i in range(len(mainGUI.exclusionList[0])):
                    if mainGUI.exclusionList[0][i] == __pickID:
                        mainGUI.exclusionList[0].pop(i)
                        config_dict['globalExclusionList'] == mainGUI.exclusionList[0]
                        util.config_writeConfig(config_dict)
                __targetAvartar.setStyleSheet('background-color: None')
        __targetAvartar = self.findChild(QGraphicsView, 'pick%sAvatar_%s' % (pickIndex, solution['id']))
        __targetAvartar.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        __targetAvartar.customContextMenuRequested.connect(showContextMenu)
        # 创建QMenu
        __contextMenu = QMenu(self)
        __pickID = solution['atk'][pickIndex-1]['id']
        __pickName = util.refData_getNameByRawID(__pickID)
        __addToLockedListAction = QAction('添加%s到未解锁角色列表' % __pickName, __contextMenu, checkable=True)
        if __pickID in mainGUI.exclusionList[0]:
            __addToLockedListAction.setChecked(True)
        __addToLockedListAction.triggered.connect(lambda checked, __pickID=__pickID, mainGUI=mainGUI: actionHandler(checked, __pickID, mainGUI))
        __contextMenu.addAction(__addToLockedListAction)
    def getIsInBookmarkList(self, solution, mainGUI):
        for bookmarkedSolution in mainGUI.bookmarkList:
            if solution['id'] == bookmarkedSolution['id']:
                return True
        return False
    def getIsInRuleOutList(self, solution, mainGUI):
        for ruledOutSolution in mainGUI.ruleOutList:
            if solution['id'] == ruledOutSolution['id']:
                return True
        return False

    def bookmarkSolutionCheckBoxHandler(self, bookmarkSolutionCheckBox, solution, mainGUI):
        if bookmarkSolutionCheckBox.isChecked():
            self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            self.setStyleSheet('background-color: aquamarine')
            util.solution_appendToBookmarkList(solution, mainGUI)
        else:
            self.setAttribute(QtCore.Qt.WA_StyledBackground, False)
            self.setStyleSheet('background-color: None')
            util.solution_removeFromBookmarkList(solution, mainGUI)
    def ruleOutSolutionCheckBoxHandler(self, ruleOutSolutionCheckBox, solution, mainGUI):
        if ruleOutSolutionCheckBox.isChecked():
            self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
            self.setStyleSheet('background-color: pink')
            util.solution_appendToRuleOutList(solution, mainGUI)
        else:
            self.setAttribute(QtCore.Qt.WA_StyledBackground, False)
            self.setStyleSheet('background-color: None')
            util.solution_removeFromRuleOutList(solution, mainGUI)
    def renderSolution(self, solution, mainGUI, buttonGroup):
        __pickImageList = []
        __pixPickImageList = []
        __itemPickImageList = []
        __scenePickImageList = [QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene()]
        __scenePickStarList = [QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene()]
        if solution['id'] == mainGUI.excludingSolutionIDList[self.teamNum-1]:
            self.findChild(QCheckBox, 'lockSolutionCheckBox_%s' % solution['id']).setChecked(True)
        for i in range(5):
            if solution["atk"][i]['star'] == 1:
                __scenePickStarList[i].addText("一星")
            if solution["atk"][i]['star'] == 2:
                __scenePickStarList[i].addText("二星")
            if solution["atk"][i]['star'] == 3:
                __scenePickStarList[i].addText("三星")
            if solution["atk"][i]['star'] == 4:
                __scenePickStarList[i].addText("四星")
            if solution["atk"][i]['star'] == 5:
                __scenePickStarList[i].addText("五星")
            if solution["atk"][i]['star'] == 6:
                __scenePickStarList[i].addText("六星")
        for pick in solution["atk"]:
            __pickImageList.append(util.query_getPickAvatar(pick['id'], refImageParams))
        __pixPickImageList = [QtGui.QPixmap.fromImage(pickImage) for pickImage in __pickImageList]
        __itemPickImageList = [QGraphicsPixmapItem(pix) for pix in __pixPickImageList]
        for i in range(len(__scenePickImageList)):
            __scenePickImageList[i].addItem(__itemPickImageList[i])
            for j in range(4):
                if self.teamNum == j:
                    continue
                if j == 0:
                    for k in range(len(mainGUI.exclusionList[j])):
                        if solution["atk"][i]['id'] == mainGUI.exclusionList[j][k]:
                            self.findChild(QGraphicsView, 'pick%sAvatar_%s' % (i+1, solution['id'])).setStyleSheet('background-color: orange')
                else:
                    for k in range(5):
                        if j == 0:
                            continue
                        if solution["atk"][i]['id'] == mainGUI.exclusionList[j][k]:
                            __scenePickImageList[i].setBackgroundBrush(QtGui.QBrush(Qt.red))
        try:
            self.findChild(QGraphicsView, 'pick1Avatar_%s' % solution['id']).setScene(__scenePickImageList[0])
            self.findChild(QGraphicsView, 'pick2Avatar_%s' % solution['id']).setScene(__scenePickImageList[1])
            self.findChild(QGraphicsView, 'pick3Avatar_%s' % solution['id']).setScene(__scenePickImageList[2])
            self.findChild(QGraphicsView, 'pick4Avatar_%s' % solution['id']).setScene(__scenePickImageList[3])
            self.findChild(QGraphicsView, 'pick5Avatar_%s' % solution['id']).setScene(__scenePickImageList[4])
            self.findChild(QGraphicsView, 'pick1Star_%s' % solution['id']).setScene(__scenePickStarList[0])
            self.findChild(QGraphicsView, 'pick2Star_%s' % solution['id']).setScene(__scenePickStarList[1])
            self.findChild(QGraphicsView, 'pick3Star_%s' % solution['id']).setScene(__scenePickStarList[2])
            self.findChild(QGraphicsView, 'pick4Star_%s' % solution['id']).setScene(__scenePickStarList[3])
            self.findChild(QGraphicsView, 'pick5Star_%s' % solution['id']).setScene(__scenePickStarList[4])
            self.findChild(QLabel, 'upCount_%s' % solution['id']).setText(str(solution['up']))
            self.findChild(QLabel, 'upCount_%s' % solution['id']).setStyleSheet("color:green")
            self.findChild(QLabel, 'downCount_%s' % solution['id']).setText(str(solution['down']))
            self.findChild(QLabel, 'downCount_%s' % solution['id']).setStyleSheet("color:red")
            if solution['down'] != 0:
                __likeDislikeRatioValue_Text = str(solution['up']/solution['down'])[:4]
            else:
                __likeDislikeRatioValue_Text = "N/A"
            self.findChild(QLabel, 'likeDislikeRatioValue_%s' % solution['id']).setText(__likeDislikeRatioValue_Text)
            if solution['comment']:
                for comment in list(reversed(solution['comment'])):
                    self.findChild(QTextBrowser, 'commentBrowser_%s' % solution['id']).append("(%s) %s" % (comment['date'][:10], comment['msg'])) 
        except Exception as e:
            global_logger.exception("renderSolution()渲染错误")
            global_logger.exception("渲染用solution: %s" % solution)
            global_logger.exception("Exception %s" % e)


class GUIMainWin(QMainWindow, Ui_PCRJJCAnalyzerGUI):
    def __init__(self, parent=None):
        super(GUIMainWin, self).__init__(parent)
        self.setupUi(self)
        self.appExceptionHandler = ExceptHookHandler(self, logFile=os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "log.txt"))
        self.setWindowTitle(globalVersion)
        self.exclusionList  = [[], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
        self.excludingSolutionIDList = ['','','']
        self.exclusionCheckBoxButtonGroup = QButtonGroup()
        self.resetExclusionCurrentTeamButton.clicked.connect(lambda: self.resetExclusionList(self.activeTeamNum))
        self.resetExclusionAllTeamButton.clicked.connect(lambda: self.resetExclusionList(-1))
        self.sceneCharImageList = [QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene()]
        self.recognizeAndSolveButton.clicked.connect(lambda: self.recognizeAndSolve(0))
        self.recognizeAndSolveButton_TeamOneFromHisotry.clicked.connect(lambda: self.recognizeAndSolve(1))
        self.recognizeAndSolveButton_TeamTwoFromHisotry.clicked.connect(lambda: self.recognizeAndSolve(2))
        self.recognizeAndSolveButton_TeamThreeFromHisotry.clicked.connect(lambda: self.recognizeAndSolve(3))
        self.recognizeAndSolveButton_OwnTeam.clicked.connect(lambda: self.recognizeAndSolve(-1))
        self.resetAllButton.clicked.connect(self.resetAll)
        self.setRegion1.clicked.connect(self.setRegionOnClicked)
        self.setRegion2.clicked.connect(self.setRegionOnClicked)
        self.setRegion3.clicked.connect(self.setRegionOnClicked)
        self.setRegion4.clicked.connect(self.setRegionOnClicked)
        if config_dict['algorithm'] == "cv2.TM_CCOEFF":
            self.TM_CCOEFF.setChecked(True)
        if config_dict['algorithm'] == "cv2.TM_CCOEFF_NORMED":
            self.TM_CCOEFF_NORMED.setChecked(True)
        if config_dict['algorithm'] == "cv2.TM_CCORR":
            self.TM_CCORR.setChecked(True)
        if config_dict['algorithm'] == "cv2.TM_CCORR_NORMED":
            self.TM_CCORR_NORMED.setChecked(True)
        if config_dict['algorithm'] == "cv2.TM_SQDIFF":
            self.TM_SQDIFF.setChecked(True)
        if config_dict['algorithm'] == "cv2.TM_SQDIFF_NORMED":
            self.TM_SQDIFF_NORMED.setChecked(True)
        self.TM_CCOEFF.clicked.connect(self.setTMAlgorithmOnClicked)
        self.TM_CCOEFF_NORMED.clicked.connect(self.setTMAlgorithmOnClicked)
        self.TM_CCORR.clicked.connect(self.setTMAlgorithmOnClicked)
        self.TM_CCORR_NORMED.clicked.connect(self.setTMAlgorithmOnClicked)
        self.TM_SQDIFF.clicked.connect(self.setTMAlgorithmOnClicked)
        self.TM_SQDIFF_NORMED.clicked.connect(self.setTMAlgorithmOnClicked)
        self.team1RadioButton.clicked.connect(lambda: self.switchActiveTeam(1))
        self.team2RadioButton.clicked.connect(lambda: self.switchActiveTeam(2))
        self.team3RadioButton.clicked.connect(lambda: self.switchActiveTeam(3))
        self.apiKeylineEdit.textChanged.connect(self.setApiKey)
        self.apiKey = config_dict['apiKey']
        self.apiKeylineEdit.setText(self.apiKey)
        self.activeTeamNum = 1
        self.queryResultStorageTeam1 = {
            'def': [], 
            'rjson': {}, 
            'itemCharImageList':[], 
            'charDataList': [], 
            'char1CandidateList': [],
            'char2CandidateList': [], 
            'char3CandidateList': [], 
            'char4CandidateList': [], 
            'char5CandidateList': [], 
        }
        self.queryResultStorageTeam2 = {
            'def': [], 
            'rjson': {}, 
            'itemCharImageList':[], 
            'charDataList': [], 
            'char1CandidateList': [],
            'char2CandidateList': [], 
            'char3CandidateList': [], 
            'char4CandidateList': [], 
            'char5CandidateList': [], 
        }
        self.queryResultStorageTeam3 = {
            'def': [], 
            'rjson': {}, 
            'itemCharImageList':[], 
            'charDataList': [], 
            'char1CandidateList': [],
            'char2CandidateList': [], 
            'char3CandidateList': [], 
            'char4CandidateList': [], 
            'char5CandidateList': [], 
        }
        self.team1RadioButton.setChecked(True)
        self.bookmarkList = util.solution_loadLists()[0]
        self.ruleOutList = util.solution_loadLists()[1]
        if config_dict['region'] == 1:
            self.setRegion1.setChecked(True)
        if config_dict['region'] == 2:
            self.setRegion2.setChecked(True)
        if config_dict['region'] == 3:
            self.setRegion3.setChecked(True)
        if config_dict['region'] == 4:
            self.setRegion3.setChecked(True)
        self.updateHandleSelectorListButton.clicked.connect(self.initializeHandleSelector)
        self.handleSelectorComboBox.activated[str].connect(self.onHandleSelect)
        self.handle = 0
        self.initializeHandleSelector()
        self.char1Dropbox.activated[str].connect(lambda candidateName, charNum=1: self.onCharCandidateSelect(candidateName, charNum))
        self.char2Dropbox.activated[str].connect(lambda candidateName, charNum=2: self.onCharCandidateSelect(candidateName, charNum))
        self.char3Dropbox.activated[str].connect(lambda candidateName, charNum=3: self.onCharCandidateSelect(candidateName, charNum))
        self.char4Dropbox.activated[str].connect(lambda candidateName, charNum=4: self.onCharCandidateSelect(candidateName, charNum))
        self.char5Dropbox.activated[str].connect(lambda candidateName, charNum=5: self.onCharCandidateSelect(candidateName, charNum))
        self.configDialogButton.clicked.connect(self.showConfigDialog)
        self.exclusionList[0] = config_dict['globalExclusionList']
        self.globalHideExclusionRuledOutSwitchCheckBox.setChecked(config_dict['globalHideExclusionRuledOutSwitch'])
        self.globalHideExclusionRuledOutSwitchCheckBox.stateChanged.connect(self.globalHideExclusionRuledOutSwitchCheckBoxHandler)
    def getIsInRuleOutList(self, solution):
        for ruledOutSolution in self.ruleOutList:
            if solution['id'] == ruledOutSolution['id']:
                return True
        return False
    def globalHideExclusionRuledOutSwitchCheckBoxHandler(self, globalHideExclusionRuledOutSwitchCheckBox):
        config_dict['globalHideExclusionRuledOutSwitch'] = self.globalHideExclusionRuledOutSwitchCheckBox.isChecked()
        util.config_writeConfig(config_dict)
        self.switchActiveTeam(targetTeamNum=self.activeTeamNum, forced=True)
    def initializeHandleSelector(self):
        emulator_lst = dict()
        emulator_hwnd = ["subWin", "canvasWin", "BlueStacksApp"] # subWin: nox, ldplayer | canvasWin: mumu
        def check_emulator_window(hwnd, p):
            if win32gui.GetClassName(hwnd) in emulator_hwnd and hwnd not in emulator_lst:
                emulator_lst.update({hwnd: p})
            else:
                win32gui.EnumChildWindows(hwnd, check_emulator_window, p)
        def gui_get_all_hwnd(hwnd, mouse):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
                if win32gui.GetClassName(hwnd) == "UnityWndClass" and win32gui.GetWindowText(hwnd) == "PrincessConnectReDive": # DMM Game Player
                    emulator_lst.update({hwnd: "DMM_PrincessConnectReDive"})
                else:
                    win32gui.EnumChildWindows(hwnd, check_emulator_window, win32gui.GetWindowText(hwnd))
        win32gui.EnumWindows(gui_get_all_hwnd, 0)
        self.handleList = []
        for h,t in emulator_lst.items():
            if t is not "":
                self.handleList.append([h, t])
        self.titleList = [handle[1] for handle in self.handleList]
        self.handleSelectorComboBox.clear()
        self.handleSelectorComboBox.addItems(self.titleList)
        if len(self.titleList) == 1:
            self.handle = list(emulator_lst.keys())[0]
            self.queryStatusTag.setText('等待查询')
            self.queryStatusTag.setStyleSheet("color:green")
        else:
            self.queryStatusTag.setText("请选择句柄")
            self.queryStatusTag.setStyleSheet("color:red")
    def showConfigDialog(self):
        self.configDialog = GUIConfigDialogWidget(mainGUI=self)
        self.configDialog.show()
        self.configDialog.exec_()
    def resetAll(self):
        self.activeTeamNum = 1
        self.team1RadioButton.setChecked(True)
        self.queryResultStorageTeam1 = {
            'def': [], 
            'rjson': {}, 
            'itemCharImageList':[], 
            'charDataList': [], 
            'char1CandidateList': [],
            'char2CandidateList': [], 
            'char3CandidateList': [], 
            'char4CandidateList': [], 
            'char5CandidateList': [], 
        }
        self.queryResultStorageTeam2 = {
            'def': [], 
            'rjson': {}, 
            'itemCharImageList':[], 
            'charDataList': [], 
            'char1CandidateList': [],
            'char2CandidateList': [], 
            'char3CandidateList': [], 
            'char4CandidateList': [], 
            'char5CandidateList': [], 
        }
        self.queryResultStorageTeam3 = {
            'def': [], 
            'rjson': {}, 
            'itemCharImageList':[], 
            'charDataList': [], 
            'char1CandidateList': [],
            'char2CandidateList': [], 
            'char3CandidateList': [], 
            'char4CandidateList': [], 
            'char5CandidateList': [], 
        }
        self.exclusionList  = [[], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
        self.exclusionList[0] = config_dict['globalExclusionList']
        self.excludingSolutionIDList = ['','','']
        self.char1Dropbox.clear()
        self.char2Dropbox.clear()
        self.char3Dropbox.clear()
        self.char4Dropbox.clear()
        self.char5Dropbox.clear()
        self.switchActiveTeam(targetTeamNum=self.activeTeamNum, forced=True)
    def resetExclusionList(self, teamNumToReset:[-1, 0, 1, 2, 3]):
        if teamNumToReset == -1:
            self.exclusionList  = [[], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
            self.excludingSolutionIDList = ['','','']
        if teamNumToReset in [1, 2, 3]:
            self.exclusionList[teamNumToReset] = [0, 0, 0, 0, 0]
            self.excludingSolutionIDList[teamNumToReset-1] = ''
        self.switchActiveTeam(targetTeamNum=self.activeTeamNum, forced=True)
    def addToExclusionList(self, GUIsolutionWidget, lockSolutionCheckBox, solution, ExcludedByTeamNum:[0,1,2,3]):
        if lockSolutionCheckBox.isChecked():
            self.excludingSolutionIDList[ExcludedByTeamNum-1] = solution['id']
            for i in range(5):
                self.exclusionList[GUIsolutionWidget.teamNum][i] = solution['atk'][i]['id']
        
    def switchActiveTeam(self, targetTeamNum, forced:bool = False):
        if not forced:
            if self.activeTeamNum == targetTeamNum:
                return
            self.char1Dropbox.clear()
            self.char2Dropbox.clear()
            self.char3Dropbox.clear()
            self.char4Dropbox.clear()
            self.char5Dropbox.clear()
        self.exclusionCheckBoxButtonGroup = QButtonGroup()
        self.activeTeamNum = targetTeamNum
        for i in range(self.solutionListLayout.count()):
            self.solutionListLayout.itemAt(i).widget().deleteLater()
        self.sceneCharImageList = [QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene()]
        for scene in self.sceneCharImageList:
            scene.clear()
        targetQueryResultStorageRJson = {}
        try:
            char1DropboxItemList = []
            char2DropboxItemList = []
            char3DropboxItemList = []
            char4DropboxItemList = []
            char5DropboxItemList = []
            if targetTeamNum == 1:
                self.charDataList = self.queryResultStorageTeam1['charDataList']
                self.itemCharImageList = self.queryResultStorageTeam1['itemCharImageList']
                self.char1CandidateList = self.queryResultStorageTeam1['char1CandidateList']
                self.char2CandidateList = self.queryResultStorageTeam1['char2CandidateList']
                self.char3CandidateList = self.queryResultStorageTeam1['char3CandidateList']
                self.char4CandidateList = self.queryResultStorageTeam1['char4CandidateList']
                self.char5CandidateList = self.queryResultStorageTeam1['char5CandidateList']
                targetQueryResultStorageRJson = self.queryResultStorageTeam1['rjson']
                if len(self.charDataList) != 0:
                    for j in range(6):
                        char1DropboxItemList.append(self.queryResultStorageTeam1['char1CandidateList'][j]['name'])
                        char2DropboxItemList.append(self.queryResultStorageTeam1['char2CandidateList'][j]['name'])
                        char3DropboxItemList.append(self.queryResultStorageTeam1['char3CandidateList'][j]['name'])
                        char4DropboxItemList.append(self.queryResultStorageTeam1['char4CandidateList'][j]['name'])
                        char5DropboxItemList.append(self.queryResultStorageTeam1['char5CandidateList'][j]['name'])
            if targetTeamNum == 2:
                self.charDataList = self.queryResultStorageTeam2['charDataList']
                self.itemCharImageList = self.queryResultStorageTeam2['itemCharImageList']
                self.char1CandidateList = self.queryResultStorageTeam2['char1CandidateList']
                self.char2CandidateList = self.queryResultStorageTeam2['char2CandidateList']
                self.char3CandidateList = self.queryResultStorageTeam2['char3CandidateList']
                self.char4CandidateList = self.queryResultStorageTeam2['char4CandidateList']
                self.char5CandidateList = self.queryResultStorageTeam2['char5CandidateList']
                targetQueryResultStorageRJson = self.queryResultStorageTeam2['rjson']
                if len(self.charDataList) != 0:
                    for j in range(6):
                        char1DropboxItemList.append(self.queryResultStorageTeam2['char1CandidateList'][j]['name'])
                        char2DropboxItemList.append(self.queryResultStorageTeam2['char2CandidateList'][j]['name'])
                        char3DropboxItemList.append(self.queryResultStorageTeam2['char3CandidateList'][j]['name'])
                        char4DropboxItemList.append(self.queryResultStorageTeam2['char4CandidateList'][j]['name'])
                        char5DropboxItemList.append(self.queryResultStorageTeam2['char5CandidateList'][j]['name'])
            if targetTeamNum == 3:
                self.charDataList = self.queryResultStorageTeam3['charDataList']
                self.itemCharImageList = self.queryResultStorageTeam3['itemCharImageList']
                self.char1CandidateList = self.queryResultStorageTeam3['char1CandidateList']
                self.char2CandidateList = self.queryResultStorageTeam3['char2CandidateList']
                self.char3CandidateList = self.queryResultStorageTeam3['char3CandidateList']
                self.char4CandidateList = self.queryResultStorageTeam3['char4CandidateList']
                self.char5CandidateList = self.queryResultStorageTeam3['char5CandidateList']
                targetQueryResultStorageRJson = self.queryResultStorageTeam3['rjson']
                if len(self.charDataList) != 0:
                    for j in range(6):
                        char1DropboxItemList.append(self.queryResultStorageTeam3['char1CandidateList'][j]['name'])
                        char2DropboxItemList.append(self.queryResultStorageTeam3['char2CandidateList'][j]['name'])
                        char3DropboxItemList.append(self.queryResultStorageTeam3['char3CandidateList'][j]['name'])
                        char4DropboxItemList.append(self.queryResultStorageTeam3['char4CandidateList'][j]['name'])
                        char5DropboxItemList.append(self.queryResultStorageTeam3['char5CandidateList'][j]['name'])
            if len(self.charDataList) != 0:
                self.showChars(targetTeamNum)
                self.char1Dropbox.addItem(self.charDataList[0]['name'])
                self.char2Dropbox.addItem(self.charDataList[1]['name'])
                self.char3Dropbox.addItem(self.charDataList[2]['name'])
                self.char4Dropbox.addItem(self.charDataList[3]['name'])
                self.char5Dropbox.addItem(self.charDataList[4]['name'])
                self.char1Dropbox.addItems(char1DropboxItemList)
                self.char2Dropbox.addItems(char2DropboxItemList)
                self.char3Dropbox.addItems(char3DropboxItemList)
                self.char4Dropbox.addItems(char4DropboxItemList)
                self.char5Dropbox.addItems(char5DropboxItemList)
        except Exception as e:
            global_logger.exception("switchActiveTeam()生成dropboxlist错误")
            global_logger.exception("Exception %s" % e)
        try:
            self.char1Avatar.setScene(self.sceneCharImageList[0])
            self.char2Avatar.setScene(self.sceneCharImageList[1])
            self.char3Avatar.setScene(self.sceneCharImageList[2])
            self.char4Avatar.setScene(self.sceneCharImageList[3])
            self.char5Avatar.setScene(self.sceneCharImageList[4])
        except Exception as e:
            print(e)
        try:
            if not targetQueryResultStorageRJson:
                return
            if targetQueryResultStorageRJson['data']['result'] == 0:
                self.queryStatusTag.setText('无结果！等待查询')
                self.queryStatusTag.setStyleSheet("color:green")
                return
            for solution in targetQueryResultStorageRJson['data']['result']:
                if config_dict['globalHideExclusionRuledOutSwitch'] == True:
                    if self.getIsInRuleOutList(solution):
                        continue                
                    __solutionPickIDSet = set([item['id'] for item in solution['atk']])
                    __intersection = list(set(config_dict['globalExclusionList']) & __solutionPickIDSet)
                    if len(__intersection) != 0:
                        continue
                QMetaObject.invokeMethod(self, "addSolution",
                                        Qt.QueuedConnection,
                                        Q_ARG(dict, solution))
                self.queryStatusTag.setText('等待查询')
                self.queryStatusTag.setStyleSheet("color:green")
            if solution['comment']:
                for comment in list(reversed(solution['comment'])):
                    self.findChild(QTextBrowser, 'commentBrowser_%s' % solution['id']).append("(%s) %s" % (comment['date'][:10], comment['msg'])) 
        except Exception as e:
            global_logger.exception("switchActiveTeam()渲染globalExclusion错误")
            global_logger.exception("Exception %s" % e)
        

    def setApiKey(self, apiKey):
        self.apiKey = apiKey
        config_dict['apiKey'] = apiKey
        util.config_writeConfig(config_dict)
    def onCharCandidateSelect(self, candidateName, charNum:[1,2,3,4,5]):
        if charNum == 1:
            for i in range(6):
                if self.char1CandidateList[i]['name'] == candidateName:
                    self.charDataList[0] = self.char1CandidateList[i]
        if charNum == 2:
            for i in range(6):
                if self.char2CandidateList[i]['name'] == candidateName:
                    self.charDataList[1] = self.char2CandidateList[i]
        if charNum == 3:
            for i in range(6):
                if self.char3CandidateList[i]['name'] == candidateName:
                    self.charDataList[2] = self.char3CandidateList[i]
        if charNum == 4:
            for i in range(6):
                if self.char4CandidateList[i]['name'] == candidateName:
                    self.charDataList[3] = self.char4CandidateList[i]
        if charNum == 5:
            for i in range(6):
                if self.char5CandidateList[i]['name'] == candidateName:
                    self.charDataList[4] = self.char5CandidateList[i]
        raw_id_list = [charData['id'] for charData in self.charDataList]
        id_list = list(set([ x for x in raw_id_list ]))
        payload = {
            "def": id_list, 
            "nonce": "a", 
            "page": 1, 
            "region": config_dict['region'], 
            "sort": 1, 
            "ts": int(time.time())
        }
        sign(payload)
        apiUrl = "https://api.pcrdfans.com/x/v1/search"
        if config_dict['customizedApi'] == True:
            apiUrl = config_dict['customizedApiUrl']
        queryRunnable = RequestRunnable(apiUrl, payload, self, self.apiKey)
        QThreadPool.globalInstance().start(queryRunnable)

    def onHandleSelect(self, handleTitle):
        def getHandle(handleTitle):
            for handle in self.handleList:
                if handle[1] == handleTitle:
                    return handle
        targetHandle = getHandle(handleTitle)
        self.handle = targetHandle[0]
        self.queryStatusTag.setText("等待查询")
        self.queryStatusTag.setStyleSheet("color:green")
    def setTMAlgorithmOnClicked(self):
        clickedRadioButton = self.sender()
        if clickedRadioButton.isChecked():
            if clickedRadioButton.objectName() == "TM_CCOEFF":
                config_dict['algorithm'] = "cv2.TM_CCOEFF"
                util.config_writeConfig(config_dict)
            if clickedRadioButton.objectName() == "TM_CCOEFF_NORMED":
                config_dict['algorithm'] = "cv2.TM_CCOEFF_NORMED"
                util.config_writeConfig(config_dict)
            if clickedRadioButton.objectName() == "TM_CCORR":
                config_dict['algorithm'] = "cv2.TM_CCORR"
                util.config_writeConfig(config_dict)
            if clickedRadioButton.objectName() == "TM_CCORR_NORMED":
                config_dict['algorithm'] = "cv2.TM_CCORR_NORMED"
                util.config_writeConfig(config_dict)
            if clickedRadioButton.objectName() == "TM_SQDIFF":
                config_dict['algorithm'] = "cv2.TM_SQDIFF"
                util.config_writeConfig(config_dict)
            if clickedRadioButton.objectName() == "TM_SQDIFF_NORMED":
                config_dict['algorithm'] = "cv2.TM_SQDIFF_NORMED"
                util.config_writeConfig(config_dict)

    def setRegionOnClicked(self):
        clickedRadioButton = self.sender()
        if clickedRadioButton.isChecked():
            if clickedRadioButton.objectName() == "setRegion1":
                config_dict['region'] = 1
            if clickedRadioButton.objectName() == "setRegion2":
                config_dict['region'] = 2
            if clickedRadioButton.objectName() == "setRegion3":
                config_dict['region'] = 3
            if clickedRadioButton.objectName() == "setRegion4":
                config_dict['region'] = 4
        try:
            util.config_writeConfig(config_dict)
        except Exception as e:
            global_logger.exception("setRegionOnClicked()错误")
            global_logger.exception("Exception %s" % e)
    def recognizeAndSolve(self, teamNum:[0, 1, 2, 3, 4]):
        characterIndexListJsonFile = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "characterIndexList.json"),'r',encoding='utf-8')
        characterIndexList = json.load(characterIndexListJsonFile)
        self.exclusionCheckBoxButtonGroup = QButtonGroup()
        self.char1Dropbox.clear()
        self.char2Dropbox.clear()
        self.char3Dropbox.clear()
        self.char4Dropbox.clear()
        self.char5Dropbox.clear()
        if self.handle == 0:
            QMessageBox.information(self, "No Handle", "No Handle")
            self.queryStatusTag.setText("请选择句柄")
            self.queryStatusTag.setStyleSheet("color:red")
            return
        self.sceneCharImageList = [QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene(), QGraphicsScene()]
        for scene in self.sceneCharImageList:
            scene.clear()
        for i in range(self.solutionListLayout.count()):
            self.solutionListLayout.itemAt(i).widget().deleteLater()
        gameImage = screen.grabWindow(self.handle).toImage() # 直接截取vbox子窗口和DMM的UnityWnd
        #gameImage.save('gameImage.png', 'PNG')
        if teamNum==0:
            # 当前目标队，右上
            translatedCharY = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_CurrentEnemyTeam']['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            translatedCharH = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_CurrentEnemyTeam']['h']
            translatedCharW = gameImage.width()*config_dict['matchTemplateParams']['charLocationRatioConfig_CurrentEnemyTeam']['w']
            if self.activeTeamNum == 1:
                self.queryResultStorageTeam1['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_CurrentEnemyTeam']['x'] ]
            if self.activeTeamNum == 2:
                self.queryResultStorageTeam2['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_CurrentEnemyTeam']['x'] ]
            if self.activeTeamNum == 3:
                self.queryResultStorageTeam3['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_CurrentEnemyTeam']['x'] ]
            self.charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_CurrentEnemyTeam']['x']] 
        if teamNum==1:
            # 履历一队
            translatedCharY = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamOne']['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            if config_dict['region'] in [3,4]:
                translatedCharY = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamOne_WithTitleBanner']['y']
            translatedCharH = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamOne']['h']
            translatedCharW = gameImage.width()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamOne']['w']
            if self.activeTeamNum == 1:
                self.queryResultStorageTeam1['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamOne']['x']]
            if self.activeTeamNum == 2:
                self.queryResultStorageTeam2['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamOne']['x']]
            if self.activeTeamNum == 3:
                self.queryResultStorageTeam3['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamOne']['x']]
            self.charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamOne']['x']]
        if teamNum==2:
            #履历二队
            translatedCharY = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamTwo']['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            if config_dict['region'] in [3,4]:
                translatedCharY = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamTwo_WithTitleBanner']['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            translatedCharH = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamTwo']['h']
            translatedCharW = gameImage.width()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamTwo']['w']
            if self.activeTeamNum == 1:
                self.queryResultStorageTeam1['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamTwo']['x']]
            if self.activeTeamNum == 2:
                self.queryResultStorageTeam2['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamTwo']['x']]
            if self.activeTeamNum == 3:
                self.queryResultStorageTeam3['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamTwo']['x']]
            self.charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamTwo']['x']]
        if teamNum==3:
            #履历三队
            translatedCharY = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamThree']['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            if config_dict['region'] in [3,4]:
                translatedCharY = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamThree_WithTitleBanner']['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            translatedCharH = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamThree']['h']
            translatedCharW = gameImage.width()*config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamThree']['w']
            if self.activeTeamNum == 1:
                self.queryResultStorageTeam1['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamThree']['x']]
            if self.activeTeamNum == 2:
                self.queryResultStorageTeam2['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamThree']['x']]
            if self.activeTeamNum == 3:
                self.queryResultStorageTeam3['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamThree']['x']]
            self.charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_HistoryTeamThree']['x']]
        if teamNum==-1:
            # 当前防守队
            translatedCharY = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_OwnTeam']['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            translatedCharH = gameImage.height()*config_dict['matchTemplateParams']['charLocationRatioConfig_OwnTeam']['h']
            translatedCharW = gameImage.width()*config_dict['matchTemplateParams']['charLocationRatioConfig_OwnTeam']['w']
            if self.activeTeamNum == 1:
                self.queryResultStorageTeam1['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_OwnTeam']['x']]
            if self.activeTeamNum == 2:
                self.queryResultStorageTeam2['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_OwnTeam']['x']]
            if self.activeTeamNum == 3:
                self.queryResultStorageTeam3['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_OwnTeam']['x']]
            self.charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config_dict['matchTemplateParams']['charLocationRatioConfig_OwnTeam']['x']]
        self.charDataList = [
            {'name': '未知角色', 'id': 1000},
            {'name': '未知角色', 'id': 1000},
            {'name': '未知角色', 'id': 1000},
            {'name': '未知角色', 'id': 1000},
            {'name': '未知角色', 'id': 1000},
        ]
        # self.sceneCharImageList = [QGraphicsScene().addItem(item) for item in self.itemCharImageList]
        self.showChars(0)
        self.parseChars()
        id_list = list(set([charData['id'] for charData in self.charDataList]))
        payload = {
            "def": id_list, 
            "nonce": "a", 
            "page": 1, 
            "region": config_dict['region'], 
            "sort": 1, 
            "ts": int(time.time())
        }        
        sign(payload)
        apiUrl = "https://api.pcrdfans.com/x/v1/search"
        if config_dict['customizedApi'] == True:
            apiUrl = config_dict['customizedApiUrl']
        queryRunnable = RequestRunnable(apiUrl, payload, self, self.apiKey)
        QThreadPool.globalInstance().start(queryRunnable)
        for i in range(5):
            completeDropboxRunnable = generateCharCandidateRunnable(self.charImageList, self, i)
            QThreadPool.globalInstance().start(completeDropboxRunnable)
    @pyqtSlot(dict)
    def addSolution(self, solution):
        self.solutionListLayout.addWidget(GUIsolutionWidget(solution=solution, mainGUI=self, buttonGroup=self.exclusionCheckBoxButtonGroup))
        self.solutionListScrollAreaScrollAreaWidgetContents.setLayout(self.solutionListLayout)
    def showChars(self, targetTeamNum:[0,1,2,3]):
        if targetTeamNum == 0:
            self.pixCharImageList = [QtGui.QPixmap.fromImage(charImage) for charImage in self.charImageList]
            self.itemCharImageList = [QGraphicsPixmapItem(pix) for pix in self.pixCharImageList]
        if targetTeamNum == 1:
            self.pixCharImageList = [QtGui.QPixmap.fromImage(charImage) for charImage in self.queryResultStorageTeam1['charImageList']]
            self.itemCharImageList = [QGraphicsPixmapItem(pix) for pix in self.pixCharImageList]
        if targetTeamNum == 2:
            self.pixCharImageList = [QtGui.QPixmap.fromImage(charImage) for charImage in self.queryResultStorageTeam2['charImageList']]
            self.itemCharImageList = [QGraphicsPixmapItem(pix) for pix in self.pixCharImageList]
        if targetTeamNum == 3:
            self.pixCharImageList = [QtGui.QPixmap.fromImage(charImage) for charImage in self.queryResultStorageTeam3['charImageList']]
            self.itemCharImageList = [QGraphicsPixmapItem(pix) for pix in self.pixCharImageList]
        for i in range(len(self.sceneCharImageList)):
            self.sceneCharImageList[i].addItem(self.itemCharImageList[i])
        self.char1Avatar.setScene(self.sceneCharImageList[0])
        self.char2Avatar.setScene(self.sceneCharImageList[1])
        self.char3Avatar.setScene(self.sceneCharImageList[2])
        self.char4Avatar.setScene(self.sceneCharImageList[3])
        self.char5Avatar.setScene(self.sceneCharImageList[4])
    def parseChars(self):
        characterIndexListJsonFile = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "characterIndexList.json"),'r',encoding='utf-8')
        characterIndexList = json.load(characterIndexListJsonFile)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        # 尝试修正可能出现的中文路径编码问题
        refImagePath = refImageParams['refImagePath']
        refImage = cv2.imdecode(np.fromfile(refImagePath,dtype=np.uint8),cv2.IMREAD_COLOR) # 读取参考图
        for i in range(len(self.charImageList)):
            charNum = i+1
            charIndex = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[i], refImage, eval("%s" % config_dict['algorithm'] )), refImageParams)) # 计算出目标角色在参考图中的坐标位置（行与列）
            charName = characterIndexList[charIndex[0]]["unit_name"]
            charId = characterIndexList[(charIndex[0])]["unit_id"]
            self.charDataList[i] = {"name": charName, "id": charId}
            charName = self.charDataList[i]['name']
            print(charNum, charName, charIndex)
        self.char1Dropbox.addItem(self.charDataList[0]['name'])
        self.char2Dropbox.addItem(self.charDataList[1]['name'])
        self.char3Dropbox.addItem(self.charDataList[2]['name'])
        self.char4Dropbox.addItem(self.charDataList[3]['name'])
        self.char5Dropbox.addItem(self.charDataList[4]['name'])

if __name__ == '__main__':
    # ### CLI测试部分
    global config_dict 
    config_dict = util.config_loadConfig()
    refImageParams = util.config_getRefImageParams()
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    loop = quamash.QEventLoop(app)
    asyncio.set_event_loop(loop)  # NEW must set the event loop

    with loop:
        mainWin = GUIMainWin()
        mainWin.show()
        loop.run_forever()
    