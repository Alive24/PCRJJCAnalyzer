# PCRJJCAnalyzer
- 使用开发交流QQ群：931482960
- 仓库地址：https://github.com/xct24/PCRJJCAnalyzer
- NGA讨论地址：https://nga.178.com/read.php?tid=22983407
- BigFun讨论地址：https://www.bigfun.cn/post/526503
- Bot申请地址（暂未开放）：https://www.pcrdfans.com/bot

## 前言

由于JJC和PJJC的奖励太好，虽然不大喜欢玩PVP但不得不打，好在有[作业网](https://www.pcrdfans.com/battle)的存在减少了很多精力消耗。然而实际操作过程中，尤其是在PJJC中，需要来来回回点很多次才能确定是否可以使用该作业，因此希望通过图像识别的方式再加上已经实装在[HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot)中的API查询方法做到自动查询，并在简单分析后指导应当如何选择阵容或者是否需要刷新列表。

## 简介

使用OpenCV所提供的matchTemplate功能，识别当前模拟器处于对战阵容选择画面时显示的对方阵容具体构成，然后调用[公主连结Re: Dive Fan Club](https://www.pcrdfans.com/battle)所提供的接口进行阵容查询，并按照结果指导操作，以减少玩家精力消耗。



## 使用流程（当前初版图形界面测试阶段）
0. 程序可在Release中下载。另有onefile单文件版本，但启动速度会稍慢一些。
1. 启动后请在程序右下方填入你的apiKey（在作业网[公主连结Re: Dive Fan Club - Bot](https://www.pcrdfans.com/bot)处申请，请确认你当前ip与作业网中登记的是相同的，否则请重置ip）
2. 请根据标题在程序左下方选择你运行PCR的模拟器句柄。
3. 游戏中进入对战阵容选择画面后（目前需要人工确认），点击识别求解按钮。
4. 在对战履历界面，可以点击履历解第一队、履历解第二队和履历解第三队按钮查询相应的作业。
5. 在队伍编程页面，可以点击查防守阵容按钮查询相应的作业。


## 编译方法
1. 创建适合的python环境（开发环境下为conda建立的python3.7虚拟环境）
2. 使用`pip install -r requirements.txt`安装环境
3. 使用`pyinstaller .\main.spec`以文件夹形式编译（启动速度更快）或使用`pyinstaller .\main-onefile.spec`以单文件形式编译（启动速度稍慢）

## 工作原理
1. 程序对句柄对应窗口进行截图后，参照config中浏览器相关的边距参数进行裁剪，仅保留游戏画面
2. 根据比例获取对面阵容的每个角色的头像，作为matchTemplate中的template
3. 以每个角色的头像对照参考图片（refImage，来自于[公主连结Re: Dive Fan Club](https://www.pcrdfans.com/battle)）进行matchTemplate后，获得识别结果的坐标的中点
4. 根据中点和config中的refImage相关数据，判断其行列坐标并输出

## 示例
- [PCRJJCAnalyzer - 基本用法展示 1](https://www.bilibili.com/video/bv1kk4y1175r)
- [PCRJJCAnalyzer - 基本用法展示 2 (PJJC)](https://www.bilibili.com/video/bv1K5411h783)
- [PCRJJCAnalyzer - 基本用法展示 3 (防守阵容自查)](https://www.bilibili.com/video/bv1FK411M7Wn)

![sample3](https://github.com/xct24/PCRJJCAnalyzer/blob/master/doc/img/sample3.png?raw=true)

### 开发计划
1. 基于PyQt5的图形界面 
    - 已初步完成
2. 以行列坐标对照数据库，获得相应角色的名字和作业网对应id
    - 已完成
3. 为JJC和PJJC提供不同的操作流程
    - 已初步完成
4. 使用不同的算法并总结出最有把握的识别结果
    - 已初步完成，所有结果都可以待选
5. 根据结果自动进行查询，并对查询结果简单分析，作出推荐
    - 已实现查询，但尚未尝试做查询结果分析
6. 添加防守阵容自查功能
    - 已完成
7. 用户配置文件储存apiKey，以及收藏/黑名单作业功能


## 声明
1. 此工具遵循相关开源协议，不可作商业用途。
2. 此工具唯一访问游戏的方式是截图，绝不通过其他不正当方式获取游戏数据，绝不代替人对游戏进行任何操作，更不可能涉嫌篡改游戏程序代码等作弊行为。

## 更新日志
1. 2020-08-15 - 目前发现refImage均为三星后立绘，若有使用二星立绘的角色会识别失败，需要添加旧立绘头像数据。
    - 已解决
2. 2020-08-16 - 本来以为履历查一队用不上，但实际上还是挺好用的，下个版本会加上（希望能跟锁定阵容功能一起上）
    - 已先行完成，锁定阵容功能下个版本再上吧~
3. 2020-08-16 - 少部分的角色识别结果还是容易出错，计划下次做成多个算法同时进行后取众数，以及提供各算法结果选择功能。 目前查询失败时还是容易崩溃，正在排查原因。
    -  [3c802db](https://github.com/xct24/PCRJJCAnalyzer/commit/3c802db4921f25c4a7c109f288702744e5bbf218) 已解决。放弃使用众数的方法（意义不大）

