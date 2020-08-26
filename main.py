#! /usr/bin/env python
#-*- coding: utf-8 -*-

import json
import util
import copy
import time
import config
import data
import cv2
import os
import sys
import httpx
import requests
import win32gui
import asyncio
import quamash
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QLabel, QWidget, QTextBrowser, QMessageBox, QButtonGroup, QCheckBox
from PyQt5 import QtGui, QtCore, QtNetwork
from PyQt5.QtCore import QRunnable, QThreadPool, pyqtSlot, QThread, QMetaObject, Qt, Q_ARG
from gui import Ui_PCRJJCAnalyzerGUI
from solutionWidget import Ui_solutionWidget


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
        refImagePath = os.path.join(base_path, 'resource/refImage.png')
        refImage = cv2.imread(refImagePath) # 读取参考图
        charIndexCandidateList = [[],[],[],[],[],[]]
        charCandidateList = [
                {'name': '未知角色', 'id': 1000},
                {'name': '未知角色', 'id': 1000},
                {'name': '未知角色', 'id': 1000},
                {'name': '未知角色', 'id': 1000},
                {'name': '未知角色', 'id': 1000},
                {'name': '未知角色', 'id': 1000},
        ]
        charIndexCandidateList[0] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_CCOEFF"))))
        charIndexCandidateList[1] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_CCOEFF_NORMED"))))
        charIndexCandidateList[2] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_CCORR"))))
        charIndexCandidateList[3] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_CCORR_NORMED"))))
        charIndexCandidateList[4] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_SQDIFF"))))
        charIndexCandidateList[5] = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[self.i], refImage, eval("cv2.TM_SQDIFF_NORMED"))))
        for j in range(6):
            charCandidateList[j]= data.refGrid[(charIndexCandidateList[j][1]-1)][(charIndexCandidateList[j][0]-1)]
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

    def run(self):
        self.w.queryStatusTag.setText('查询中')
        self.w.queryStatusTag.setStyleSheet("color:black")
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36',
            'authorization': self.wApiKey,
            'Content-Type': 'application/json'
        }
        r = requests.post(self.mUrl, json=self.mJson, headers=headers)
        QThread.msleep(1000)
        print(r)
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
                QMetaObject.invokeMethod(self.w, "addSolution",
                                        Qt.QueuedConnection,
                                        Q_ARG(dict, solution))
            self.w.queryStatusTag.setText('等待查询')
            self.w.queryStatusTag.setStyleSheet("color:green")
        except Exception as e:
            self.w.queryStatusTag.setText('查询失败(%s)' % r.json()['code'])
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
        self.commentBrowser.setObjectName('commentBrowser_%s' % solution['id'])
        self.lockSolutionCheckBox.stateChanged.connect(lambda: mainGUI.addToExclusionList(self, self.lockSolutionCheckBox, solution, self.teamNum))
        self.lockSolutionCheckBox.setObjectName('lockSolutionCheckBox_%s' % solution['id'])
        buttonGroup.addButton(self.lockSolutionCheckBox)
        self.renderSolution(solution, mainGUI, buttonGroup)
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
            __pickImageList.append(util.query_getPickAvatar(pick['id']))
        __pixPickImageList = [QtGui.QPixmap.fromImage(pickImage) for pickImage in __pickImageList]
        __itemPickImageList = [QGraphicsPixmapItem(pix) for pix in __pixPickImageList]
        for i in range(len(__scenePickImageList)):
            __scenePickImageList[i].addItem(__itemPickImageList[i])
            for j in range(4):
                if self.teamNum == j:
                    continue
                for k in range(5):
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
            for comment in list(reversed(solution['comment'])):
                self.findChild(QTextBrowser, 'commentBrowser_%s' % solution['id']).append("(%s) %s" % (comment['date'][:10], comment['msg'])) 
        except Exception as e:
            print(e, solution)
        


        

class GUIMainWin(QMainWindow, Ui_PCRJJCAnalyzerGUI):
    def __init__(self, parent=None):
        super(GUIMainWin, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('PCRJJCAnalyzer-v0.0.7-beta1')
        self.exclusionList  = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
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
        self.region = config.region
        self.algorithm = config.algorithm
        self.apiKey = config.apiKey
        self.activeTeamNum = 1
        self.queryResultStorageTeam1 = {'def': [], 'rjson': {}, 'itemCharImageList':[]}
        self.queryResultStorageTeam2 = {'def': [], 'rjson': {}, 'itemCharImageList':[]}
        self.queryResultStorageTeam3 = {'def': [], 'rjson': {}, 'itemCharImageList':[]}
        self.team1RadioButton.setChecked(True)
        if self.region == 1:
            self.setRegion1.setChecked(True)
        if self.region == 2:
            self.setRegion2.setChecked(True)
        if self.region == 3:
            self.setRegion3.setChecked(True)
        if self.algorithm == "TM_CCOEFF":
            self.TM_CCOEFF.setChecked(True)
        if self.algorithm == "TM_CCOEFF_NORMED":
            self.TM_CCOEFF_NORMED.setChecked(True)
        if self.algorithm == "TM_CCORR":
            self.TM_CCORR.setChecked(True)
        if self.algorithm == "TM_CCORR_NORMED":
            self.TM_CCORR_NORMED.setChecked(True)
        if self.algorithm == "TM_SQDIFF":
            self.TM_SQDIFF.setChecked(True)
        if self.algorithm == "TM_SQDIFF_NORMED":
            self.TM_SQDIFF_NORMED.setChecked(True)
        hwnd_title = dict()
        def gui_get_all_hwnd(hwnd,mouse):
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
                hwnd_title.update({hwnd:win32gui.GetWindowText(hwnd)})
        win32gui.EnumWindows(gui_get_all_hwnd, 0)
        self.handleList = []
        for h,t in hwnd_title.items():
            if t is not "":
                self.handleList.append([h, t])
        self.titleList = [handle[1] for handle in self.handleList]
        self.handleSelectorComboBox.addItems(self.titleList)
        self.handleSelectorComboBox.activated[str].connect(self.onHandleSelect)
        self.char1Dropbox.activated[str].connect(lambda candidateName, charNum=1: self.onCharCandidateSelect(candidateName, charNum))
        self.char2Dropbox.activated[str].connect(lambda candidateName, charNum=2: self.onCharCandidateSelect(candidateName, charNum))
        self.char3Dropbox.activated[str].connect(lambda candidateName, charNum=3: self.onCharCandidateSelect(candidateName, charNum))
        self.char4Dropbox.activated[str].connect(lambda candidateName, charNum=4: self.onCharCandidateSelect(candidateName, charNum))
        self.char5Dropbox.activated[str].connect(lambda candidateName, charNum=5: self.onCharCandidateSelect(candidateName, charNum))
        self.handle = 0
        self.queryStatusTag.setText("请选择句柄")
        self.queryStatusTag.setStyleSheet("color:red")
    def resetAll(self):
        self.activeTeamNum = 1
        self.team1RadioButton.setChecked(True)
        self.queryResultStorageTeam1 = {'def': [], 'rjson': {}, 'itemCharImageList':[]}
        self.queryResultStorageTeam2 = {'def': [], 'rjson': {}, 'itemCharImageList':[]}
        self.queryResultStorageTeam3 = {'def': [], 'rjson': {}, 'itemCharImageList':[]}
        self.exclusionList  = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
        self.excludingSolutionIDList = ['','','']
        self.char1Dropbox.clear()
        self.char2Dropbox.clear()
        self.char3Dropbox.clear()
        self.char4Dropbox.clear()
        self.char5Dropbox.clear()
        self.switchActiveTeam(targetTeamNum=self.activeTeamNum, forced=True)
    def resetExclusionList(self, teamNumToReset:[-1, 0, 1, 2, 3]):
        if teamNumToReset == -1:
            self.exclusionList  = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
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
                for j in range(6):
                    char1DropboxItemList.append(self.queryResultStorageTeam3['char1CandidateList'][j]['name'])
                    char2DropboxItemList.append(self.queryResultStorageTeam3['char2CandidateList'][j]['name'])
                    char3DropboxItemList.append(self.queryResultStorageTeam3['char3CandidateList'][j]['name'])
                    char4DropboxItemList.append(self.queryResultStorageTeam3['char4CandidateList'][j]['name'])
                    char5DropboxItemList.append(self.queryResultStorageTeam3['char5CandidateList'][j]['name'])
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
            print(e)
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
                QMetaObject.invokeMethod(self, "addSolution",
                                        Qt.QueuedConnection,
                                        Q_ARG(dict, solution))
                self.queryStatusTag.setText('等待查询')
                self.queryStatusTag.setStyleSheet("color:green")
        except Exception as e:
            print(e)
        

    def setApiKey(self, apiKey):
        self.apiKey = apiKey
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
        id_list = [ x * 100 + 1 for x in raw_id_list ]
        payload = {
            "_sign": "a", 
            "def": id_list, 
            "nonce": "a", 
            "page": 1, 
            "sort": 1, 
            "ts": int(time.time()), 
            "region": self.region
        }        
        queryRunnable = RequestRunnable("https://api.pcrdfans.com/x/v1/search", payload, self, self.apiKey)
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
                self.algorithm = "cv2.TM_CCOEFF"
            if clickedRadioButton.objectName() == "TM_CCOEFF_NORMED":
                self.algorithm = "cv2.TM_CCOEFF_NORMED"
            if clickedRadioButton.objectName() == "TM_CCORR":
                self.algorithm = "cv2.TM_CCORR"
            if clickedRadioButton.objectName() == "TM_CCORR_NORMED":
                self.algorithm = "cv2.TM_CCORR_NORMED"
            if clickedRadioButton.objectName() == "TM_SQDIFF":
                self.algorithm = "cv2.TM_SQDIFF"
            if clickedRadioButton.objectName() == "TM_SQDIFF_NORMED":
                self.algorithm = "cv2.TM_SQDIFF_NORMED"

    def setRegionOnClicked(self):
        clickedRadioButton = self.sender()
        if clickedRadioButton.isChecked():
            if clickedRadioButton.objectName() == "setRegion1":
                self.region = 1
            if clickedRadioButton.objectName() == "setRegion2":
                self.region = 2
            if clickedRadioButton.objectName() == "setRegion3":
                self.region = 3
    def recognizeAndSolve(self, teamNum:[0, 1, 2, 3, 4]):
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
        screenshot = screen.grabWindow(self.handle).toImage()
        copyX = config.simulator['marginOffset'][0]
        copyY = config.simulator['marginOffset'][1]
        copyWidth = screenshot.width() - config.simulator['marginOffset'][0] - config.simulator['marginOffset'][2]
        copyHeight = screenshot.height() - config.simulator['marginOffset'][1] - config.simulator['marginOffset'][3]
        gameImage = screenshot.copy(copyX, copyY, copyWidth, copyHeight) # 根据边框裁剪出游戏图像
        if teamNum==0:
            # 当前目标队，右上
            translatedCharY = gameImage.height()*config.charLocationRatioConfig_CurrentEnemyTeam['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            translatedCharH = gameImage.height()*config.charLocationRatioConfig_CurrentEnemyTeam['h']
            translatedCharW = gameImage.width()*config.charLocationRatioConfig_CurrentEnemyTeam['w']
            if self.activeTeamNum == 1:
                self.queryResultStorageTeam1['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_CurrentEnemyTeam['x'] ]
            if self.activeTeamNum == 2:
                self.queryResultStorageTeam2['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_CurrentEnemyTeam['x'] ]
            if self.activeTeamNum == 3:
                self.queryResultStorageTeam3['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_CurrentEnemyTeam['x'] ]
            self.charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_CurrentEnemyTeam['x']] 
        if teamNum==1:
            # 履历一队
            translatedCharY = gameImage.height()*config.charLocationRatioConfig_HistoryTeamOne['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            translatedCharH = gameImage.height()*config.charLocationRatioConfig_HistoryTeamOne['h']
            translatedCharW = gameImage.width()*config.charLocationRatioConfig_HistoryTeamOne['w']
            if self.activeTeamNum == 1:
                self.queryResultStorageTeam1['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamOne['x']]
            if self.activeTeamNum == 2:
                self.queryResultStorageTeam2['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamOne['x']]
            if self.activeTeamNum == 3:
                self.queryResultStorageTeam3['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamOne['x']]
            self.charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamOne['x']]
        if teamNum==2:
            #履历二队
            translatedCharY = gameImage.height()*config.charLocationRatioConfig_HistoryTeamTwo['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            translatedCharH = gameImage.height()*config.charLocationRatioConfig_HistoryTeamTwo['h']
            translatedCharW = gameImage.width()*config.charLocationRatioConfig_HistoryTeamTwo['w']
            if self.activeTeamNum == 1:
                self.queryResultStorageTeam1['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamTwo['x']]
            if self.activeTeamNum == 2:
                self.queryResultStorageTeam2['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamTwo['x']]
            if self.activeTeamNum == 3:
                self.queryResultStorageTeam3['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamTwo['x']]
            self.charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamTwo['x']]
        if teamNum==3:
            #履历三队
            translatedCharY = gameImage.height()*config.charLocationRatioConfig_HistoryTeamThree['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            translatedCharH = gameImage.height()*config.charLocationRatioConfig_HistoryTeamThree['h']
            translatedCharW = gameImage.width()*config.charLocationRatioConfig_HistoryTeamThree['w']
            if self.activeTeamNum == 1:
                self.queryResultStorageTeam1['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamThree['x']]
            if self.activeTeamNum == 2:
                self.queryResultStorageTeam2['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamThree['x']]
            if self.activeTeamNum == 3:
                self.queryResultStorageTeam3['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamThree['x']]
            self.charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_HistoryTeamThree['x']]
        if teamNum==-1:
            # 当前防守队
            translatedCharY = gameImage.height()*config.charLocationRatioConfig_OwnTeam['y'] # 根据比例计算出对方阵容图标的y值、h值、w值
            translatedCharH = gameImage.height()*config.charLocationRatioConfig_OwnTeam['h']
            translatedCharW = gameImage.width()*config.charLocationRatioConfig_OwnTeam['w']
            if self.activeTeamNum == 1:
                self.queryResultStorageTeam1['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_OwnTeam['x']]
            if self.activeTeamNum == 2:
                self.queryResultStorageTeam2['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_OwnTeam['x']]
            if self.activeTeamNum == 3:
                self.queryResultStorageTeam3['charImageList'] = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_OwnTeam['x']]
            self.charImageList = [gameImage.copy(gameImage.width() * x, translatedCharY, translatedCharW, translatedCharH).scaledToWidth(60) for x in config.charLocationRatioConfig_OwnTeam['x']]
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
        raw_id_list = [charData['id'] for charData in self.charDataList]
        id_list = [ x * 100 + 1 for x in raw_id_list ]
        payload = {
            "_sign": "a", 
            "def": id_list, 
            "nonce": "a", 
            "page": 1, 
            "sort": 1, 
            "ts": int(time.time()), 
            "region": self.region
        }        
        queryRunnable = RequestRunnable("https://api.pcrdfans.com/x/v1/search", payload, self, self.apiKey)
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
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        refImagePath = os.path.join(base_path, 'resource/refImage.png')
        refImage = cv2.imread(refImagePath) # 读取参考图
        for i in range(len(self.charImageList)):
            charNum = i+1
            charIndex = (util.cv_getIndex(util.cv_getMidPoint(self.charImageList[i], refImage, eval("cv2.%s" % self.algorithm )))) # 计算出目标角色在参考图中的坐标位置（行与列）
            self.charDataList[i] = data.refGrid[(charIndex[1]-1)][(charIndex[0]-1)]
            charName = self.charDataList[i]['name']
            print(charNum, charName, charIndex)
        self.char1Dropbox.addItem(self.charDataList[0]['name'])
        self.char2Dropbox.addItem(self.charDataList[1]['name'])
        self.char3Dropbox.addItem(self.charDataList[2]['name'])
        self.char4Dropbox.addItem(self.charDataList[3]['name'])
        self.char5Dropbox.addItem(self.charDataList[4]['name'])
   
        
    

if __name__ == '__main__':
    # ### CLI测试部分
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    loop = quamash.QEventLoop(app)
    asyncio.set_event_loop(loop)  # NEW must set the event loop

    with loop:
        mainWin = GUIMainWin()
        mainWin.show()
        loop.run_forever()
    