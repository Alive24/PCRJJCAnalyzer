# PCRJJCAnalyzer

## 前言

由于JJC和PJJC的奖励太好，虽然不大喜欢玩PVP但不得不打，好在有[作业网](https://www.pcrdfans.com/battle)的存在减少了很多精力消耗。然而实际操作过程中，尤其是在PJJC中，需要来来回回点很多次才能确定是否可以使用该作业，因此希望通过图像识别的方式再加上已经实装在[HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot)中的API查询方法做到自动查询，并在简单分析后指导应当如何选择阵容或者是否需要刷新列表。

## 简介

使用OpenCV所提供的matchTemplate功能，识别当前模拟器处于对战阵容选择画面时显示的对方阵容具体构成，然后调用[公主连结Re: Dive Fan Club](https://www.pcrdfans.com/battle)所提供的接口进行阵容查询，并按照结果指导操作，以减少玩家精力消耗。

## 使用流程及原理（当前CLI测试阶段）
1. 使用win32gui库获得所有窗口的句柄和标题后，提示用户手动输入句柄号
2. 对战阵容选择画面时（目前需要人工确认），对句柄对应窗口进行截图后，参照config中浏览器相关的边距参数进行裁剪，仅保留游戏画面
3. 根据比例获取对面阵容的每个角色的头像，作为matchTemplate中的template
4. 以每个角色的头像对照参考图片（refImage，来自于[公主连结Re: Dive Fan Club](https://www.pcrdfans.com/battle)）进行matchTemplate后，获得识别结果的坐标的中点
5. 根据中点和config中的refImage相关数据，判断其行列坐标并输出

## 示例（外链nga图片）

### 开发计划
1. 基于PyQt5的图形界面
2. 以行列坐标对照数据库，获得相应角色的名字和作业网对应id
3. 为JJC和PJJC提供不同的操作流程
4. 使用不同的算法并总结出最有把握的识别结果
5. 根据结果自动进行查询，并对查询结果简单分析，作出推荐
