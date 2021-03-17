import requests
import brotli
import logging
import sqlite3
import time
import json
import os
import PIL.Image as Image

# https://redive.estertion.win/last_version_jp.json
# https://redive.estertion.win/last_version_cn.json
# https://redive.estertion.win/db/redive_jp.db.br
# https://redive.estertion.win/db/redive_cn.db.br
global_logger = logging.getLogger()

def updateCharacterIndexListByURL(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
        'Referer': 'https://redive.estertion.win/api.htm',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.9',
        'Accept-Encoding': 'br',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh-TW;q=0.7,zh;q=0.6,ja;q=0.5',
        'Accept-Charset': "UTF-8"
    }
    try:
        # 获取网页内容，返回html数据
        response = requests.get(url, headers=headers)
        # 通过状态码判断是否获取成功
        if response.status_code == 200:
            # response.encoding = 'utf-8'
            key = 'Content-Encoding'
            # print(response.headers[key])
            print("-----------")
            data = brotli.decompress(response.content)
            savedBinFile = open("./Database.db", "wb")
            savedBinFile.write(data)
            savedBinFile.close()
            connection = sqlite3.connect("./Database.db")
            unitDataCursor = connection.cursor().execute("select * from unit_data")
            characterIndexList = []
            for row in unitDataCursor:
                characterIndexList.append({"unit_id": row[0], "unit_name": row[1]})
            characterIndexListJsonFile = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "characterIndexList.json"),'w',encoding='utf-8')
            json.dump(characterIndexList, characterIndexListJsonFile, ensure_ascii=False)
            characterIndexListJsonFile.close()
        return None
    except Exception as e:
        print(e)
        global_logger.exception("updateCharacterIndexListByURL失败")
        global_logger.exception("Exception %s" % e)
        return None
    
def updateAssetsByCharacterIndexList(characterIndexList):
    for entry in characterIndexList:
        charId = str(entry["unit_id"])[:4]
        if not os.path.exists(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "%s11.webp" % charId)):
            global_logger.warning("没有找到%s(id:%s)的头像文件，尝试获取" % (entry["unit_name"], entry["unit_id"]) )
            webpURLOne = "https://redive.estertion.win/icon/unit/%s11.webp" % charId
            webpURLThree = "https://redive.estertion.win/icon/unit/%s31.webp" % charId
            webpURLSix = "https://redive.estertion.win/icon/unit/%s61.webp" % charId
            try:
                webpContentOne = requests.get(webpURLOne)
                if webpContentOne.status_code == 200:
                    with open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "%s11%s" % (charId, ".webp")), 'wb') as file:
                        file.write(webpContentOne.content)
                        global_logger.warning("成功下载角色头像（角色名：%s, 角色id：%s， 角色头像星级：1" % (entry["unit_name"], entry["unit_id"]))
                webpContentThree = requests.get(webpURLThree)
                if webpContentThree.status_code == 200:
                    with open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "%s31%s" % (charId, ".webp")), 'wb') as file:
                        file.write(webpContentThree.content)
                        global_logger.warning("成功下载角色头像（角色名：%s, 角色id：%s， 角色头像星级：3" % (entry["unit_name"], entry["unit_id"]))
                webpContentSix = requests.get(webpURLSix)
                if webpContentSix.status_code == 200:
                    with open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "%s61%s" % (charId, ".webp")), 'wb') as file:
                        file.write(webpContentSix.content)
                        global_logger.warning("成功下载角色头像（角色名：%s, 角色id：%s， 角色头像星级：6" % (entry["unit_name"], entry["unit_id"]))
            except Exception as e:
                print(e)

def generateRefImageByCharacterIndexList(characterIndexList):
    refImagePath = os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "refImage.png")
    refImage = Image.new('RGBA', (len(characterIndexList) * (60+2) * 3, 62)) #创建一个新图
    for index in range(len(characterIndexList)):
        charId = str(characterIndexList[index]['unit_id'])[:4]
        try:
            icon_imageOne = Image.open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "%s11.webp" % charId)).resize((60, 60),Image.ANTIALIAS)
            coordinateImageOne = ((2+3*62*index, 2))
            refImage.paste(icon_imageOne, coordinateImageOne)
            icon_imageThree = Image.open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "%s31.webp" % charId)).resize((60, 60),Image.ANTIALIAS)
            coordinateImageThree = ((64+3*62*index, 2))
            refImage.paste(icon_imageThree, coordinateImageThree)
            icon_imageSix = Image.open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "%s61.webp" % charId)).resize((60, 60),Image.ANTIALIAS)
            coordinateImageSix = ((126+3*62*index, 2))
            refImage.paste(icon_imageSix, coordinateImageSix)
        except Exception as e:
            global_logger.error("图片粘贴失败, Exception: %s" % e)
    refImage.save(refImagePath)
    global_logger.info("成功更新refImage")

def devMain():
    logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s',
        level=logging.WARNING)
    url = "https://redive.estertion.win/db/redive_cn.db.br"
    updateCharacterIndexListByURL(url)
    characterIndexListJsonFile = open(os.path.join(os.path.expanduser('~'), "PCRJJCAnalyzer", "CharData", "characterIndexList.json"),'r',encoding='utf-8')
    characterIndexList = json.load(characterIndexListJsonFile)
    updateAssetsByCharacterIndexList(characterIndexList)
    generateRefImageByCharacterIndexList(characterIndexList)


if __name__ == "__main__":
    # 直接执行则为开发模式入口
        devMain()
