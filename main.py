import util
import config
import cv2
global handle

if __name__ == '__main__':
    ### CLI测试部分
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
    refImage = cv2.imread('refImage.png') # 读取参考图
    for i in range(len(charImageList)):
        charNum = i+1
        charIndex = [(util.cv_getIndex(util.cv_getMidPoint(charImageList[i], refImage, eval('cv2.TM_SQDIFF' ))))] # 计算出目标角色在参考图中的坐标位置（行与列）
        charImageList[i].save("char%s.jpg" % i) # 为了检测是否成功裁剪保存图片
        print(charIndex, charNum) 
 

    # 还没完成的Qt部分
    # app = QApplication(sys.argv)
    # myWin = MyWindow()
    # myWin.show()
    # sys.exit(app.exec_())