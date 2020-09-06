#-*- coding: UTF-8 -*-
#-------------------------------------------------------------------------------
# Name:        模块except hook handler 
# Purpose:     全局捕获异常
#
# Author:      ankier
#
# Created:     17-08-2013
# Copyright:   (c) ankier 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import logging
import sys
import traceback 
import datetime
from PyQt5.QtWidgets import QMessageBox

## @detail 创建记录异常的信息
class ExceptHookHandler(object):
    ## @detail 构造函数
    #  @param logFile: log的输入地址
    #  @param mainFrame: 是否需要在主窗口中弹出提醒
    def __init__(self, mainGUI, logFile, mainFrame = None):
        self.__mainGUI = mainGUI
        self.__LogFile = logFile
        self.__MainFrame = mainFrame
        
        self.__Logger = self.__BuildLogger()
        #重定向异常捕获
        sys.excepthook = self.__HandleException
    
    ## @detail 创建logger类
    def __BuildLogger(self):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.FileHandler(self.__LogFile))
        return logger
    
    ## @detail 捕获及输出异常类
    #  @param excType: 异常类型
    #  @param excValue: 异常对象
    #  @param tb: 异常的trace back
    def __HandleException(self, excType, excValue, tb):
        # first logger 
        try:
            currentTime = datetime.datetime.now()
            self.__Logger.info('Timestamp: %s'%(currentTime.strftime("%Y-%m-%d %H:%M:%S")))
            self.__Logger.error("Uncaught exception：", exc_info=(excType, excValue, tb))
            self.__Logger.info('\n\n\n')
        except:
            pass
        
        # then call the default handler
        sys.__excepthook__(excType, excValue, tb)     
        
        err_msg = ''.join(traceback.format_exception(excType, excValue, tb))
        err_msg += '\nPCRJJCAnalyzer遇到了意料之外的错误。请在反馈时附上本对话框截图。'
        # Here collecting traceback and some log files to be sent for debugging.
        # But also possible to handle the error and continue working.
        QMessageBox.information(self.__mainGUI, "Error", err_msg)
        # dlg = wx.MessageDialog(None, err_msg, 'Administration', wx.OK | wx.ICON_ERROR)