import PIL.Image as Image
import os
 
IMAGES_PATH = './tool/pics/'  # 图片集地址
IMAGES_FORMAT = ['.jpg', '.JPG', 'png', '.webp@w200']  # 图片格式
IMAGE_WIDTH = 60  # 每张图片的宽度
IMAGE_HEIGHT = 60 # 每张图片的高度
IMAGE_ROW = 12  # 图片间隔，也就是合并成一张图后，一共有几行
IMAGE_COLUMN = 11  # 图片间隔，也就是合并成一张图后，一共有几列
IMAGE_SAVE_PATH = 'final.png'  # 图片转换后的地址
 
# 获取图片集地址下的所有图片名称
image_names = [name for name in os.listdir(IMAGES_PATH) for item in IMAGES_FORMAT if
               os.path.splitext(name)[1] == item]

print(len(image_names))
 
# 简单的对于参数的设定和实际图片集的大小进行数量判断
if len(image_names) != IMAGE_ROW * IMAGE_COLUMN:
    raise ValueError("合成图片的参数和要求的数量不能匹配！")
 
# 定义图像拼接函数
def image_compose():
    to_image = Image.new('RGBA', (IMAGE_COLUMN * (IMAGE_WIDTH+2), IMAGE_ROW * (IMAGE_HEIGHT+2))) #创建一个新图
    # 循环遍历，把每张图片按顺序粘贴到对应位置上
    for y in range(1, IMAGE_ROW + 1):
        for x in range(1, IMAGE_COLUMN + 1):
            from_image = Image.open(IMAGES_PATH + image_names[IMAGE_COLUMN * (y - 1) + x - 1]).resize(
                (IMAGE_WIDTH, IMAGE_HEIGHT),Image.ANTIALIAS)
            to_image.paste(from_image, ((x - 1) * (IMAGE_WIDTH+2), (y - 1) * (IMAGE_HEIGHT+2)))
    return to_image.save(IMAGE_SAVE_PATH) # 保存新图


def getDict():
    dictResult = []
    for y in range(1, IMAGE_ROW + 1):
        rowEntry = []
        for x in range(1, IMAGE_COLUMN + 1):
            newName = image_names[IMAGE_COLUMN * (y - 1) + x - 1]
            entry = {'name': '无角色', 'id': newName[:4]}
            rowEntry.append(entry)
        dictResult.append(rowEntry)
    return dictResult

print(getDict())
    
            
            
            


