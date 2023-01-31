# coding:utf-8
import os
import shutil
import fitz
import difflib
from datetime import datetime
import base64
from PIL import Image
from PIL import ImageDraw
import requests
from concurrent.futures import ThreadPoolExecutor
def initRoot(rootPath):
    """
    初始化目录
    :param rootPath:
    :return:rootPath
    """
    rootPath = os.path.abspath(rootPath)
    if os.path.exists(rootPath):
        # 检查用于放图片的目录是否存在，是的话删除
        shutil.rmtree(rootPath)  # 清空图片目录
    os.makedirs(rootPath)  # 创建图片目录
    return rootPath
def conver_img(pdfFilepath, outputPath):
    """
    pdf转换PNG图片
    :param outputPath: PNG图片输出路径
    :param pdfFilepath: pdf文档路径
    :return: doc.pageCount, ImagePath 文档图像张数，保存地址
    """

    pdfFilepath = os.path.abspath(pdfFilepath)  # 绝对路径
    if not os.path.exists(pdfFilepath):
        # 检查文件是否存在
        print('文件不存在：', pdfFilepath)
        exit(0)

    # 获取文件同名目录和类型
    pdfName = os.path.basename(pdfFilepath)  # 返回文件名
    pdfNamePath, extension = os.path.splitext(pdfName)
    ImagePath = os.path.join(outputPath, pdfNamePath)  # pdf文档图像保存地址
    if os.path.exists(ImagePath):
        # 检查用于放图片的目录是否存在，是的话删除
        shutil.rmtree(ImagePath)  # 清空图片目录
    os.makedirs(ImagePath)  # 创建图片目录

    # 读取文件
    doc = fitz.open(pdfFilepath)
    for page_index in range(doc.page_count):
        page = doc[page_index]  # 逐页读取pdf
        # 每个尺寸的缩放系数为2，这将为我们生成分辨率提高四倍的图像。
        zoom_x = 2.0
        zoom_y = 2.0
        trans = fitz.Matrix(zoom_x, zoom_y)  # .preRotate(0)  # .preRotate(rotate)是执行一个旋转
        pm = page.get_pixmap(matrix=trans, alpha=False)
        pm.save(os.path.join(ImagePath, str(page_index) + '.png'))  # 保存图片
    return doc.page_count, ImagePath


def imageDiff(resultRoot, originFile, contrastFile, page=1):
    """
    对比两张照片的区别
    :param resultRoot: 输出目录
    :param originFile: 源文件
    :param contrastFile: 扫描件
    :param page: 页数
    :return:
    """
    '''
    # 调用接口返回后的结果
    originResult = getImageInfo(filename=originFile)  # 识别原件内容
    contrastResult = getImageInfo(filename=contrastFile)  # 识别扫描件内容
    '''

    for origin_words in originResult['data']['prism_wordsInfo'][:]:
        # 获取词块的相关位置信息
        left, top = origin_words['pos'][0]['x'], origin_words['pos'][0]['y']
        # right, bottom = left + origin_words['location']['width'], top + origin_words['location']['height']
        for contrast_words in contrastResult['data']['prism_wordsInfo'][:]:
            # 获取词块的相关位置信息
            contrast_words_ll = []
            result_left, result_top = contrast_words['pos'][0]['x'], contrast_words['pos'][0]['y']
            contrast_words_ll.append(contrast_words['word'].replace('口', ''))
            # result_right, result_bottom = result_left + contrast_words['location']['width'], result_top + \
            #                               contrast_words['location']['height']

            # 判断词块距离顶部的位置是否在偏差范围内，可理解为两个词块位置是否一致
            if origin_words['word'].replace('口', '') in contrast_words_ll:
                contrastResult['data']['prism_wordsInfo'].remove(contrast_words)  # 删除原件词块
                originResult['data']['prism_wordsInfo'].remove(origin_words)  # 删除原件词块
                break  # 已找到词块退出循环

            elif origin_words['word'] in contrast_words['word']:
                # 说明扫描件内容和原件不一样
                originResult['data']['prism_wordsInfo'].remove(origin_words)  # 删除原件词块
                contrast_words['word'] = contrast_words['word'].replace(origin_words['word'], '', 1)
                break  # 已找到词块退出循环
    # 文档图像标注，画框标注出不一样的内容
    originImage = Image.open(originFile)
    originDraw = ImageDraw.ImageDraw(originImage)
    originText = ''  # 保存对比不一致的文本
    for origin_words in originResult['data']['prism_wordsInfo'][:]:
        # originText += words['words'] + '\n'
        left, top = origin_words['pos'][0]['x'], origin_words['pos'][0]['y']
        right, bottom = origin_words['pos'][2]['x'], origin_words['pos'][2]['y']
        originDraw.rectangle(((left, top), (right, bottom)), outline='red', width=2)
    # originDic[page] = originText  # 空字典，用于保存原件中每一页对比不一致的文本
    contrastImage = Image.open(contrastFile)
    contrastDraw = ImageDraw.ImageDraw(contrastImage)
    contrastText = ''
    for contrast_words in contrastResult['data']['prism_wordsInfo'][:]:
        # 获取扫描版的每个词块
        # contrastText += words['words'] + '\n'
        left, top = contrast_words['pos'][0]['x'], contrast_words['pos'][0]['y']
        right, bottom = contrast_words['pos'][2]['x'], contrast_words['pos'][2]['y']
        contrastDraw.rectangle(((left, top), (right, bottom)), outline='red', width=2)
    # contrastDic[page] = contrastText  # 文档扫描件
    # 图像合并，生成对比图
    originSize = originImage.size  # 获取原始照片大小
    contrastSize = contrastImage.size  # 获取扫描件大小
    newImage_width = originSize[0] + contrastSize[0]
    newImage_hight = originSize[1] if originSize[1] > contrastSize[1] else contrastSize[1]
    new_Image = Image.new('RGB', (newImage_width, newImage_hight), "#000000")
    new_Image.paste(originImage, (0, 0))
    new_Image.paste(contrastImage, (originSize[0], 0))
    # 展示合成图片
    # new_Image.show()
    # 展示扫描图片
    #contrastImage.show()
    #将结果图片保存到输出目录
    contrastImage.save(os.path.join(resultRoot, "第" + str(page) + '页文档.png'))
originResult={
    "code": 200,
    "data": {
        "figure": [],
        "prism_rowsInfo": [
            {
                "word": "REFERENCE：x xxxx",
                "rowId": 0
            },
            {
                "word": "In the event of any inconsistency between the English and Chinese versions， the Chinese version shall prevail.",
                "rowId": 1
            },
            {
                "word": "本确认书的中英文文本如有任何不一致，应以中文文本为准。",
                "rowId": 2
            },
            {
                "word": "The terms of the Transaction to which this Confirmation relates areas follows：",
                "rowId": 3
            },
            {
                "word": "本确认书所相关的交易的条款如下：",
                "rowId": 4
            },
            {
                "word": "Transaction Type：[Swap]",
                "rowId": 5
            },
            {
                "word": "交易种类：[掉期]",
                "rowId": 6
            },
            {
                "word": "Notional Quantity：",
                "rowId": 7
            },
            {
                "word": "xx metric tonnes",
                "rowId": 8
            },
            {
                "word": "名义数量：",
                "rowId": 9
            },
            {
                "word": "xx公吨",
                "rowId": 10
            },
            {
                "word": "Commodity：",
                "rowId": 11
            },
            {
                "word": "COBALT",
                "rowId": 12
            },
            {
                "word": "商品：",
                "rowId": 13
            },
            {
                "word": "钴",
                "rowId": 14
            },
            {
                "word": "Trade Date：",
                "rowId": 15
            },
            {
                "word": "XXXX，XXXX",
                "rowId": 16
            },
            {
                "word": "交易日：",
                "rowId": 17
            },
            {
                "word": "xxxx年xx月xx日",
                "rowId": 18
            },
            {
                "word": "Effective Date：",
                "rowId": 19
            },
            {
                "word": "XXXXXX，XXXX",
                "rowId": 20
            },
            {
                "word": "起始日：",
                "rowId": 21
            },
            {
                "word": "xxxx年xx月xx日",
                "rowId": 22
            },
            {
                "word": "Termination Date：",
                "rowId": 23
            },
            {
                "word": "XXXXXX，XXXX",
                "rowId": 24
            },
            {
                "word": "到期日",
                "rowId": 25
            },
            {
                "word": "xxxx年xx月xx日",
                "rowId": 26
            },
            {
                "word": "Calculation Period：",
                "rowId": 27
            },
            {
                "word": "Commencing on and including the Effective Date and ending on",
                "rowId": 28
            },
            {
                "word": "and including the Termination Date.",
                "rowId": 29
            },
            {
                "word": "计算期间：",
                "rowId": 30
            },
            {
                "word": "自起始日开始(含起始日)，到到期日结束(含到期日)。",
                "rowId": 31
            },
            {
                "word": "Payment Date：",
                "rowId": 32
            },
            {
                "word": "xxxx， xxxx， subject to adjustment in accordance with the Modified",
                "rowId": 33
            },
            {
                "word": "Following Business Day Convention.",
                "rowId": 34
            },
            {
                "word": "支付日：",
                "rowId": 35
            },
            {
                "word": "xxxx年xx月xx日，按经修正的下一个营业日准则调整。",
                "rowId": 36
            },
            {
                "word": "Fixed Amount",
                "rowId": 37
            },
            {
                "word": "固定金额",
                "rowId": 38
            },
            {
                "word": "Fixed Amount：",
                "rowId": 39
            },
            {
                "word": "Party x shall pay to Party x on the relevant Payment Date an",
                "rowId": 40
            },
            {
                "word": "amount in USD determined as follows：",
                "rowId": 41
            },
            {
                "word": "Notional Quantity*Fixed Price；",
                "rowId": 42
            },
            {
                "word": "x方须在相关支付日向x方支付按下列方式决定的美元金额：",
                "rowId": 43
            },
            {
                "word": "固定金额：",
                "rowId": 44
            },
            {
                "word": "名义数量*固定价格；",
                "rowId": 45
            },
            {
                "word": "Fixed Price：",
                "rowId": 46
            },
            {
                "word": "USD x， xxx.xxx per metric tonne",
                "rowId": 47
            },
            {
                "word": "固定价格：",
                "rowId": 48
            },
            {
                "word": "x，xxx.xxx美元/公吨",
                "rowId": 49
            },
            {
                "word": "Page 2 of 7",
                "rowId": 50
            }
        ],
        "algo_version": "",
        "orgWidth": 1191,
        "content": "REFERENCE：x xxxx In the event of any inconsistency between the English and Chinese versions， the Chinese version shall prevail. 本确认书的中英文文本如有任何不一致，应以中文文本为准。 The terms of the Transaction to which this Confirmation relates areas follows： 本确认书所相关的交易的条款如下： Transaction Type：[Swap] 交易种类：[掉期] Notional Quantity： xx metric tonnes 名义数量： xx公吨 Commodity： COBALT 商品： 钴 Trade Date： XXXX，XXXX 交易日： xxxx年xx月xx日 Effective Date： XXXXXX，XXXX 起始日： xxxx年xx月xx日 Termination Date： XXXXXX，XXXX 到期日 xxxx年xx月xx日 Calculation Period： Commencing on and including the Effective Date and ending on and including the Termination Date. 计算期间： 自起始日开始(含起始日)，到到期日结束(含到期日)。 Payment Date： xxxx， xxxx， subject to adjustment in accordance with the Modified Following Business Day Convention. 支付日： xxxx年xx月xx日，按经修正的下一个营业日准则调整。 Fixed Amount 固定金额 Fixed Amount： Party x shall pay to Party x on the relevant Payment Date an amount in USD determined as follows： Notional Quantity*Fixed Price； x方须在相关支付日向x方支付按下列方式决定的美元金额： 固定金额： 名义数量*固定价格； Fixed Price： USD x， xxx.xxx per metric tonne 固定价格： x，xxx.xxx美元/公吨 Page 2 of 7 ",
        "requestId": "FEDBFCAC-5E47-596A-B6AC-38D1B3C58B70",
        "prism_wnum": 51,
        "width": 1191,
        "angle": 0,
        "orgHeight": 1684,
        "prism_version": "1.0.9",
        "prism_wordsInfo": [
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 920,
                        "y": 229
                    },
                    {
                        "x": 1091,
                        "y": 229
                    },
                    {
                        "x": 1091,
                        "y": 246
                    },
                    {
                        "x": 920,
                        "y": 246
                    }
                ],
                "width": 17,
                "x": 997,
                "angle": -90,
                "y": 153,
                "word": "REFERENCE：x xxxx",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 14,
                        "x": 922,
                        "y": 230,
                        "word": "R"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 936,
                        "y": 230,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 946,
                        "y": 230,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 958,
                        "y": 230,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 971,
                        "y": 230,
                        "word": "R"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 983,
                        "y": 230,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 995,
                        "y": 230,
                        "word": "N"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 14,
                        "x": 1007,
                        "y": 230,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 1021,
                        "y": 230,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 1033,
                        "y": 230,
                        "word": "："
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 1042,
                        "y": 230,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 1052,
                        "y": 230,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 1061,
                        "y": 230,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 1070,
                        "y": 230,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 1078,
                        "y": 230,
                        "word": "x"
                    }
                ],
                "direction": 0,
                "height": 170,
                "rowId": 0
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 65,
                        "y": 285
                    },
                    {
                        "x": 948,
                        "y": 285
                    },
                    {
                        "x": 948,
                        "y": 304
                    },
                    {
                        "x": 65,
                        "y": 304
                    }
                ],
                "width": 17,
                "x": 497,
                "angle": -89,
                "y": -147,
                "word": "In the event of any inconsistency between the English and Chinese versions， the Chinese version shall prevail.",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 71,
                        "y": 285,
                        "word": "I"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 73,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 90,
                        "y": 285,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 94,
                        "y": 285,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 104,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 116,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 128,
                        "y": 285,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 137,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 147,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 156,
                        "y": 285,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 166,
                        "y": 285,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 178,
                        "y": 285,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 185,
                        "y": 285,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 197,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 206,
                        "y": 285,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 223,
                        "y": 285,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 225,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 235,
                        "y": 285,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 244,
                        "y": 285,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 254,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 263,
                        "y": 285,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 277,
                        "y": 285,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 280,
                        "y": 285,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 289,
                        "y": 285,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 292,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 301,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 313,
                        "y": 285,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 320,
                        "y": 285,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 332,
                        "y": 285,
                        "word": "b"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 344,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 353,
                        "y": 285,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 360,
                        "y": 285,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 372,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 382,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 391,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 406,
                        "y": 285,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 413,
                        "y": 285,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 422,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 436,
                        "y": 285,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 448,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 460,
                        "y": 285,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 470,
                        "y": 285,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 474,
                        "y": 285,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 477,
                        "y": 285,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 486,
                        "y": 285,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 498,
                        "y": 285,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 512,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 522,
                        "y": 285,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 534,
                        "y": 285,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 548,
                        "y": 285,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 560,
                        "y": 285,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 562,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 572,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 584,
                        "y": 285,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 591,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 605,
                        "y": 285,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 617,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 626,
                        "y": 285,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 634,
                        "y": 285,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 645,
                        "y": 285,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 650,
                        "y": 285,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 655,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 664,
                        "y": 285,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 674,
                        "y": 285,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 686,
                        "y": 285,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 688,
                        "y": 285,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 698,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 712,
                        "y": 285,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 726,
                        "y": 285,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 738,
                        "y": 285,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 740,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 750,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 762,
                        "y": 285,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 769,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 783,
                        "y": 285,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 794,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 801,
                        "y": 285,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 808,
                        "y": 285,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 823,
                        "y": 285,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 827,
                        "y": 285,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 832,
                        "y": 285,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 844,
                        "y": 285,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 856,
                        "y": 285,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 865,
                        "y": 285,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 880,
                        "y": 285,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 882,
                        "y": 285,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 887,
                        "y": 285,
                        "word": "p"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 899,
                        "y": 285,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 906,
                        "y": 285,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 915,
                        "y": 285,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 925,
                        "y": 285,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 934,
                        "y": 285,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 941,
                        "y": 285,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 944,
                        "y": 285,
                        "word": "."
                    }
                ],
                "direction": 0,
                "height": 883,
                "rowId": 1
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 66,
                        "y": 307
                    },
                    {
                        "x": 597,
                        "y": 307
                    },
                    {
                        "x": 597,
                        "y": 327
                    },
                    {
                        "x": 66,
                        "y": 327
                    }
                ],
                "width": 19,
                "x": 322,
                "angle": -89,
                "y": 50,
                "word": "本确认书的中英文文本如有任何不一致，应以中文文本为准。",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 67,
                        "y": 308,
                        "word": "本"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 87,
                        "y": 308,
                        "word": "确"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 107,
                        "y": 308,
                        "word": "认"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 127,
                        "y": 308,
                        "word": "书"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 147,
                        "y": 308,
                        "word": "的"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 167,
                        "y": 308,
                        "word": "中"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 187,
                        "y": 308,
                        "word": "英"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 207,
                        "y": 308,
                        "word": "文"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 227,
                        "y": 308,
                        "word": "文"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 247,
                        "y": 308,
                        "word": "本"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 267,
                        "y": 308,
                        "word": "如"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 287,
                        "y": 308,
                        "word": "有"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 307,
                        "y": 308,
                        "word": "任"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 327,
                        "y": 308,
                        "word": "何"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 346,
                        "y": 308,
                        "word": "不"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 366,
                        "y": 308,
                        "word": "一"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 18,
                        "x": 386,
                        "y": 308,
                        "word": "致"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 18,
                        "x": 409,
                        "y": 308,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 18,
                        "x": 426,
                        "y": 308,
                        "word": "应"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 449,
                        "y": 308,
                        "word": "以"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 469,
                        "y": 308,
                        "word": "中"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 486,
                        "y": 308,
                        "word": "文"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 505,
                        "y": 308,
                        "word": "文"
                    },
                    {
                        "prob": 100,
                        "w": 18,
                        "h": 18,
                        "x": 525,
                        "y": 308,
                        "word": "本"
                    },
                    {
                        "prob": 100,
                        "w": 18,
                        "h": 18,
                        "x": 545,
                        "y": 308,
                        "word": "为"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 568,
                        "y": 308,
                        "word": "准"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 588,
                        "y": 308,
                        "word": "。"
                    }
                ],
                "direction": 0,
                "height": 531,
                "rowId": 2
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 65,
                        "y": 344
                    },
                    {
                        "x": 689,
                        "y": 344
                    },
                    {
                        "x": 689,
                        "y": 361
                    },
                    {
                        "x": 65,
                        "y": 361
                    }
                ],
                "width": 16,
                "x": 369,
                "angle": -89,
                "y": 40,
                "word": "The terms of the Transaction to which this Confirmation relates areas follows：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 65,
                        "y": 345,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 78,
                        "y": 345,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 88,
                        "y": 345,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 107,
                        "y": 345,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 108,
                        "y": 345,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 120,
                        "y": 345,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 14,
                        "x": 125,
                        "y": 345,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 140,
                        "y": 345,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 153,
                        "y": 345,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 165,
                        "y": 345,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 172,
                        "y": 345,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 180,
                        "y": 345,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 189,
                        "y": 345,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 202,
                        "y": 345,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 215,
                        "y": 345,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 223,
                        "y": 345,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 230,
                        "y": 345,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 241,
                        "y": 345,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 251,
                        "y": 345,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 260,
                        "y": 345,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 271,
                        "y": 345,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 275,
                        "y": 345,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 277,
                        "y": 345,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 288,
                        "y": 345,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 301,
                        "y": 345,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 309,
                        "y": 345,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 322,
                        "y": 345,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 335,
                        "y": 345,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 344,
                        "y": 345,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 352,
                        "y": 345,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 359,
                        "y": 345,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 376,
                        "y": 345,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 378,
                        "y": 345,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 387,
                        "y": 345,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 393,
                        "y": 345,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 406,
                        "y": 345,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 419,
                        "y": 345,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 430,
                        "y": 345,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 442,
                        "y": 345,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 447,
                        "y": 345,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 451,
                        "y": 345,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 14,
                        "x": 455,
                        "y": 345,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 470,
                        "y": 345,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 479,
                        "y": 345,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 487,
                        "y": 345,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 493,
                        "y": 345,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 497,
                        "y": 345,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 512,
                        "y": 345,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 519,
                        "y": 345,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 530,
                        "y": 345,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 532,
                        "y": 345,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 545,
                        "y": 345,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 547,
                        "y": 345,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 557,
                        "y": 345,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 570,
                        "y": 345,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 581,
                        "y": 345,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 588,
                        "y": 345,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 602,
                        "y": 345,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 613,
                        "y": 345,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 626,
                        "y": 345,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 631,
                        "y": 345,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 645,
                        "y": 345,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 646,
                        "y": 345,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 652,
                        "y": 345,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 660,
                        "y": 345,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 673,
                        "y": 345,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 682,
                        "y": 345,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 625,
                "rowId": 3
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 66,
                        "y": 377
                    },
                    {
                        "x": 373,
                        "y": 377
                    },
                    {
                        "x": 373,
                        "y": 397
                    },
                    {
                        "x": 66,
                        "y": 397
                    }
                ],
                "width": 19,
                "x": 210,
                "angle": -90,
                "y": 233,
                "word": "本确认书所相关的交易的条款如下：",
                "charInfo": [
                    {
                        "prob": 100,
                        "w": 17,
                        "h": 17,
                        "x": 67,
                        "y": 378,
                        "word": "本"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 88,
                        "y": 378,
                        "word": "确"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 17,
                        "x": 107,
                        "y": 378,
                        "word": "认"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 17,
                        "x": 128,
                        "y": 378,
                        "word": "书"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 17,
                        "x": 147,
                        "y": 378,
                        "word": "所"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 17,
                        "x": 166,
                        "y": 378,
                        "word": "相"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 188,
                        "y": 378,
                        "word": "关"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 209,
                        "y": 378,
                        "word": "的"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 17,
                        "x": 228,
                        "y": 378,
                        "word": "交"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 249,
                        "y": 378,
                        "word": "易"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 268,
                        "y": 378,
                        "word": "的"
                    },
                    {
                        "prob": 100,
                        "w": 17,
                        "h": 17,
                        "x": 287,
                        "y": 378,
                        "word": "条"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 308,
                        "y": 378,
                        "word": "款"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 17,
                        "x": 327,
                        "y": 378,
                        "word": "如"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 348,
                        "y": 378,
                        "word": "下"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 367,
                        "y": 378,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 306,
                "rowId": 4
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 425
                    },
                    {
                        "x": 295,
                        "y": 427
                    },
                    {
                        "x": 294,
                        "y": 447
                    },
                    {
                        "x": 76,
                        "y": 445
                    }
                ],
                "width": 18,
                "x": 176,
                "angle": -89,
                "y": 326,
                "word": "Transaction Type：[Swap]",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 76,
                        "y": 426,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 89,
                        "y": 427,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 96,
                        "y": 427,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 103,
                        "y": 427,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 115,
                        "y": 427,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 124,
                        "y": 427,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 134,
                        "y": 427,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 143,
                        "y": 427,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 148,
                        "y": 427,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 151,
                        "y": 427,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 160,
                        "y": 427,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 174,
                        "y": 427,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 186,
                        "y": 427,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 196,
                        "y": 428,
                        "word": "p"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 205,
                        "y": 428,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 217,
                        "y": 428,
                        "word": "："
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 241,
                        "y": 428,
                        "word": "["
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 248,
                        "y": 428,
                        "word": "S"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 17,
                        "x": 253,
                        "y": 428,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 269,
                        "y": 428,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 276,
                        "y": 428,
                        "word": "p"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 286,
                        "y": 428,
                        "word": "]"
                    }
                ],
                "direction": 0,
                "height": 218,
                "rowId": 5
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 460
                    },
                    {
                        "x": 220,
                        "y": 460
                    },
                    {
                        "x": 220,
                        "y": 478
                    },
                    {
                        "x": 76,
                        "y": 478
                    }
                ],
                "width": 18,
                "x": 140,
                "angle": -90,
                "y": 396,
                "word": "交易种类：[掉期]",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 77,
                        "y": 460,
                        "word": "交"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 96,
                        "y": 460,
                        "word": "易"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 112,
                        "y": 460,
                        "word": "种"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 131,
                        "y": 460,
                        "word": "类"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 150,
                        "y": 460,
                        "word": "："
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 167,
                        "y": 460,
                        "word": "["
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 174,
                        "y": 460,
                        "word": "掉"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 195,
                        "y": 460,
                        "word": "期"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 212,
                        "y": 460,
                        "word": "]"
                    }
                ],
                "direction": 0,
                "height": 144,
                "rowId": 6
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 519
                    },
                    {
                        "x": 234,
                        "y": 519
                    },
                    {
                        "x": 234,
                        "y": 537
                    },
                    {
                        "x": 76,
                        "y": 537
                    }
                ],
                "width": 18,
                "x": 146,
                "angle": -89,
                "y": 449,
                "word": "Notional Quantity：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 16,
                        "x": 77,
                        "y": 519,
                        "word": "N"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 92,
                        "y": 519,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 105,
                        "y": 519,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 112,
                        "y": 519,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 115,
                        "y": 519,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 125,
                        "y": 519,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 135,
                        "y": 519,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 145,
                        "y": 519,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 16,
                        "x": 152,
                        "y": 519,
                        "word": "Q"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 170,
                        "y": 519,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 182,
                        "y": 519,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 192,
                        "y": 519,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 205,
                        "y": 519,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 210,
                        "y": 519,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 215,
                        "y": 519,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 217,
                        "y": 519,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 227,
                        "y": 519,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 157,
                "rowId": 7
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 520
                    },
                    {
                        "x": 622,
                        "y": 520
                    },
                    {
                        "x": 622,
                        "y": 537
                    },
                    {
                        "x": 471,
                        "y": 537
                    }
                ],
                "width": 17,
                "x": 538,
                "angle": -90,
                "y": 454,
                "word": "xx metric tonnes",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 473,
                        "y": 521,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 483,
                        "y": 521,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 14,
                        "x": 503,
                        "y": 521,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 520,
                        "y": 521,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 531,
                        "y": 521,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 537,
                        "y": 521,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 14,
                        "x": 544,
                        "y": 521,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 546,
                        "y": 521,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 561,
                        "y": 521,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 568,
                        "y": 521,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 578,
                        "y": 521,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 589,
                        "y": 521,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 597,
                        "y": 521,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 610,
                        "y": 521,
                        "word": "s"
                    }
                ],
                "direction": 0,
                "height": 150,
                "rowId": 8
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 78,
                        "y": 553
                    },
                    {
                        "x": 163,
                        "y": 553
                    },
                    {
                        "x": 163,
                        "y": 573
                    },
                    {
                        "x": 78,
                        "y": 573
                    }
                ],
                "width": 20,
                "x": 110,
                "angle": -90,
                "y": 520,
                "word": "名义数量：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 79,
                        "y": 554,
                        "word": "名"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 98,
                        "y": 554,
                        "word": "义"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 117,
                        "y": 554,
                        "word": "数"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 138,
                        "y": 554,
                        "word": "量"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 157,
                        "y": 554,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 85,
                "rowId": 9
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 553
                    },
                    {
                        "x": 545,
                        "y": 553
                    },
                    {
                        "x": 545,
                        "y": 573
                    },
                    {
                        "x": 471,
                        "y": 573
                    }
                ],
                "width": 20,
                "x": 498,
                "angle": -90,
                "y": 527,
                "word": "xx公吨",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 472,
                        "y": 554,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 484,
                        "y": 554,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 503,
                        "y": 554,
                        "word": "公"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 524,
                        "y": 554,
                        "word": "吨"
                    }
                ],
                "direction": 0,
                "height": 73,
                "rowId": 10
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 593
                    },
                    {
                        "x": 183,
                        "y": 593
                    },
                    {
                        "x": 183,
                        "y": 611
                    },
                    {
                        "x": 76,
                        "y": 611
                    }
                ],
                "width": 19,
                "x": 120,
                "angle": -90,
                "y": 548,
                "word": "Commodity：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 77,
                        "y": 593,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 93,
                        "y": 593,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 105,
                        "y": 593,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 120,
                        "y": 593,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 136,
                        "y": 593,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 148,
                        "y": 593,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 160,
                        "y": 593,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 165,
                        "y": 593,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 169,
                        "y": 593,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 176,
                        "y": 593,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 106,
                "rowId": 11
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 591
                    },
                    {
                        "x": 553,
                        "y": 591
                    },
                    {
                        "x": 553,
                        "y": 609
                    },
                    {
                        "x": 471,
                        "y": 609
                    }
                ],
                "width": 18,
                "x": 503,
                "angle": -90,
                "y": 560,
                "word": "COBALT",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 16,
                        "x": 474,
                        "y": 592,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 16,
                        "x": 489,
                        "y": 592,
                        "word": "O"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 504,
                        "y": 592,
                        "word": "B"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 516,
                        "y": 592,
                        "word": "A"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 529,
                        "y": 592,
                        "word": "L"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 16,
                        "x": 541,
                        "y": 592,
                        "word": "T"
                    }
                ],
                "direction": 0,
                "height": 81,
                "rowId": 12
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 627
                    },
                    {
                        "x": 123,
                        "y": 627
                    },
                    {
                        "x": 123,
                        "y": 646
                    },
                    {
                        "x": 76,
                        "y": 646
                    }
                ],
                "width": 17,
                "x": 91,
                "angle": -90,
                "y": 612,
                "word": "商品：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 79,
                        "y": 627,
                        "word": "商"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 98,
                        "y": 627,
                        "word": "品"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 117,
                        "y": 627,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 46,
                "rowId": 13
            },
            {
                "prob": 100,
                "pos": [
                    {
                        "x": 470,
                        "y": 626
                    },
                    {
                        "x": 496,
                        "y": 626
                    },
                    {
                        "x": 496,
                        "y": 647
                    },
                    {
                        "x": 470,
                        "y": 647
                    }
                ],
                "width": 20,
                "x": 473,
                "angle": -90,
                "y": 623,
                "word": "钴",
                "charInfo": [
                    {
                        "prob": 100,
                        "w": 19,
                        "h": 18,
                        "x": 473,
                        "y": 627,
                        "word": "钴"
                    }
                ],
                "direction": 0,
                "height": 27,
                "rowId": 14
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 663
                    },
                    {
                        "x": 183,
                        "y": 663
                    },
                    {
                        "x": 183,
                        "y": 682
                    },
                    {
                        "x": 76,
                        "y": 682
                    }
                ],
                "width": 18,
                "x": 121,
                "angle": -90,
                "y": 619,
                "word": "Trade Date：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 76,
                        "y": 664,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 90,
                        "y": 664,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 98,
                        "y": 664,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 108,
                        "y": 664,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 118,
                        "y": 664,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 134,
                        "y": 664,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 148,
                        "y": 664,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 16,
                        "x": 160,
                        "y": 664,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 166,
                        "y": 664,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 176,
                        "y": 664,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 106,
                "rowId": 15
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 667
                    },
                    {
                        "x": 572,
                        "y": 665
                    },
                    {
                        "x": 573,
                        "y": 682
                    },
                    {
                        "x": 471,
                        "y": 684
                    }
                ],
                "width": 102,
                "x": 471,
                "angle": -1,
                "y": 665,
                "word": "XXXX，XXXX",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 474,
                        "y": 667,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 484,
                        "y": 667,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 500,
                        "y": 667,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 510,
                        "y": 667,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 14,
                        "x": 521,
                        "y": 666,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 530,
                        "y": 666,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 541,
                        "y": 666,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 550,
                        "y": 666,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 560,
                        "y": 666,
                        "word": "X"
                    }
                ],
                "direction": 0,
                "height": 17,
                "rowId": 16
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 699
                    },
                    {
                        "x": 143,
                        "y": 699
                    },
                    {
                        "x": 143,
                        "y": 718
                    },
                    {
                        "x": 76,
                        "y": 718
                    }
                ],
                "width": 18,
                "x": 101,
                "angle": -90,
                "y": 674,
                "word": "交易日：",
                "charInfo": [
                    {
                        "prob": 100,
                        "w": 20,
                        "h": 16,
                        "x": 77,
                        "y": 699,
                        "word": "交"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 100,
                        "y": 699,
                        "word": "易"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 119,
                        "y": 699,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 137,
                        "y": 699,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 67,
                "rowId": 17
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 702
                    },
                    {
                        "x": 635,
                        "y": 699
                    },
                    {
                        "x": 635,
                        "y": 718
                    },
                    {
                        "x": 471,
                        "y": 721
                    }
                ],
                "width": 164,
                "x": 471,
                "angle": 0,
                "y": 700,
                "word": "xxxx年xx月xx日",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 472,
                        "y": 702,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 484,
                        "y": 702,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 494,
                        "y": 702,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 504,
                        "y": 702,
                        "word": "x"
                    },
                    {
                        "prob": 100,
                        "w": 18,
                        "h": 17,
                        "x": 519,
                        "y": 701,
                        "word": "年"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 542,
                        "y": 701,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 554,
                        "y": 701,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 17,
                        "x": 569,
                        "y": 701,
                        "word": "月"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 592,
                        "y": 700,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 604,
                        "y": 700,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 17,
                        "x": 619,
                        "y": 700,
                        "word": "日"
                    }
                ],
                "direction": 0,
                "height": 19,
                "rowId": 18
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 737
                    },
                    {
                        "x": 206,
                        "y": 737
                    },
                    {
                        "x": 206,
                        "y": 756
                    },
                    {
                        "x": 76,
                        "y": 756
                    }
                ],
                "width": 18,
                "x": 132,
                "angle": -90,
                "y": 681,
                "word": "Effective Date：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 78,
                        "y": 738,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 91,
                        "y": 738,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 97,
                        "y": 738,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 102,
                        "y": 738,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 113,
                        "y": 738,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 122,
                        "y": 738,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 130,
                        "y": 738,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 132,
                        "y": 738,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 143,
                        "y": 738,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 15,
                        "x": 158,
                        "y": 738,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 172,
                        "y": 738,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 183,
                        "y": 738,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 189,
                        "y": 738,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 200,
                        "y": 738,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 129,
                "rowId": 19
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 739
                    },
                    {
                        "x": 594,
                        "y": 739
                    },
                    {
                        "x": 594,
                        "y": 756
                    },
                    {
                        "x": 471,
                        "y": 756
                    }
                ],
                "width": 16,
                "x": 524,
                "angle": -90,
                "y": 686,
                "word": "XXXXXX，XXXX",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 473,
                        "y": 740,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 483,
                        "y": 740,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 494,
                        "y": 740,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 502,
                        "y": 740,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 516,
                        "y": 740,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 527,
                        "y": 740,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 14,
                        "x": 537,
                        "y": 740,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 553,
                        "y": 740,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 563,
                        "y": 740,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 571,
                        "y": 740,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 581,
                        "y": 740,
                        "word": "X"
                    }
                ],
                "direction": 0,
                "height": 121,
                "rowId": 20
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 78,
                        "y": 773
                    },
                    {
                        "x": 143,
                        "y": 773
                    },
                    {
                        "x": 143,
                        "y": 792
                    },
                    {
                        "x": 78,
                        "y": 792
                    }
                ],
                "width": 18,
                "x": 102,
                "angle": -90,
                "y": 749,
                "word": "起始日：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 79,
                        "y": 773,
                        "word": "起"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 98,
                        "y": 773,
                        "word": "始"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 119,
                        "y": 773,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 137,
                        "y": 773,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 66,
                "rowId": 21
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 773
                    },
                    {
                        "x": 633,
                        "y": 773
                    },
                    {
                        "x": 633,
                        "y": 792
                    },
                    {
                        "x": 471,
                        "y": 792
                    }
                ],
                "width": 18,
                "x": 544,
                "angle": -90,
                "y": 702,
                "word": "xxxx年xx月xx日",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 472,
                        "y": 773,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 486,
                        "y": 773,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 495,
                        "y": 773,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 505,
                        "y": 773,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 20,
                        "h": 16,
                        "x": 517,
                        "y": 773,
                        "word": "年"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 540,
                        "y": 773,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 552,
                        "y": 773,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 566,
                        "y": 773,
                        "word": "月"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 590,
                        "y": 773,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 602,
                        "y": 773,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 616,
                        "y": 773,
                        "word": "日"
                    }
                ],
                "direction": 0,
                "height": 162,
                "rowId": 22
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 811
                    },
                    {
                        "x": 234,
                        "y": 811
                    },
                    {
                        "x": 234,
                        "y": 828
                    },
                    {
                        "x": 76,
                        "y": 828
                    }
                ],
                "width": 16,
                "x": 147,
                "angle": -89,
                "y": 741,
                "word": "Termination Date：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 14,
                        "x": 77,
                        "y": 812,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 91,
                        "y": 812,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 101,
                        "y": 812,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 14,
                        "x": 109,
                        "y": 812,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 125,
                        "y": 812,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 127,
                        "y": 812,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 139,
                        "y": 812,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 14,
                        "x": 149,
                        "y": 812,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 159,
                        "y": 812,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 165,
                        "y": 812,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 14,
                        "x": 169,
                        "y": 812,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 14,
                        "x": 185,
                        "y": 812,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 14,
                        "x": 205,
                        "y": 812,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 14,
                        "x": 211,
                        "y": 812,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 217,
                        "y": 812,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 227,
                        "y": 812,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 157,
                "rowId": 23
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 813
                    },
                    {
                        "x": 594,
                        "y": 811
                    },
                    {
                        "x": 594,
                        "y": 829
                    },
                    {
                        "x": 471,
                        "y": 831
                    }
                ],
                "width": 123,
                "x": 471,
                "angle": 0,
                "y": 812,
                "word": "XXXXXX，XXXX",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 15,
                        "x": 474,
                        "y": 814,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 15,
                        "x": 486,
                        "y": 814,
                        "word": "X"
                    },
                    {
                        "prob": 98,
                        "w": 5,
                        "h": 15,
                        "x": 496,
                        "y": 814,
                        "word": "X"
                    },
                    {
                        "prob": 96,
                        "w": 9,
                        "h": 15,
                        "x": 504,
                        "y": 814,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 15,
                        "x": 518,
                        "y": 814,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 15,
                        "x": 530,
                        "y": 813,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 15,
                        "x": 542,
                        "y": 813,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 15,
                        "x": 554,
                        "y": 813,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 15,
                        "x": 564,
                        "y": 813,
                        "word": "X"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 15,
                        "x": 574,
                        "y": 813,
                        "word": "X"
                    },
                    {
                        "prob": 98,
                        "w": 9,
                        "h": 15,
                        "x": 583,
                        "y": 813,
                        "word": "X"
                    }
                ],
                "direction": 0,
                "height": 18,
                "rowId": 24
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 846
                    },
                    {
                        "x": 135,
                        "y": 846
                    },
                    {
                        "x": 135,
                        "y": 864
                    },
                    {
                        "x": 76,
                        "y": 864
                    }
                ],
                "width": 19,
                "x": 96,
                "angle": -90,
                "y": 825,
                "word": "到期日",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 79,
                        "y": 847,
                        "word": "到"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 99,
                        "y": 847,
                        "word": "期"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 16,
                        "x": 118,
                        "y": 847,
                        "word": "日"
                    }
                ],
                "direction": 0,
                "height": 58,
                "rowId": 25
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 848
                    },
                    {
                        "x": 633,
                        "y": 846
                    },
                    {
                        "x": 633,
                        "y": 865
                    },
                    {
                        "x": 471,
                        "y": 868
                    }
                ],
                "width": 163,
                "x": 471,
                "angle": 0,
                "y": 846,
                "word": "xxxx年xx月xx日",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 474,
                        "y": 849,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 484,
                        "y": 849,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 495,
                        "y": 849,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 505,
                        "y": 848,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 20,
                        "h": 17,
                        "x": 517,
                        "y": 848,
                        "word": "年"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 540,
                        "y": 848,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 552,
                        "y": 848,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 566,
                        "y": 847,
                        "word": "月"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 590,
                        "y": 847,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 602,
                        "y": 847,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 616,
                        "y": 847,
                        "word": "日"
                    }
                ],
                "direction": 0,
                "height": 20,
                "rowId": 26
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 884
                    },
                    {
                        "x": 242,
                        "y": 884
                    },
                    {
                        "x": 242,
                        "y": 902
                    },
                    {
                        "x": 76,
                        "y": 902
                    }
                ],
                "width": 18,
                "x": 149,
                "angle": -89,
                "y": 809,
                "word": "Calculation Period：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 16,
                        "x": 76,
                        "y": 885,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 92,
                        "y": 885,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 106,
                        "y": 885,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 108,
                        "y": 885,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 118,
                        "y": 885,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 130,
                        "y": 885,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 132,
                        "y": 885,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 146,
                        "y": 885,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 150,
                        "y": 885,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 152,
                        "y": 885,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 164,
                        "y": 885,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 180,
                        "y": 885,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 191,
                        "y": 885,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 16,
                        "x": 203,
                        "y": 885,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 211,
                        "y": 885,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 213,
                        "y": 885,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 223,
                        "y": 885,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 235,
                        "y": 885,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 165,
                "rowId": 27
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 884
                    },
                    {
                        "x": 1038,
                        "y": 884
                    },
                    {
                        "x": 1038,
                        "y": 904
                    },
                    {
                        "x": 471,
                        "y": 904
                    }
                ],
                "width": 19,
                "x": 745,
                "angle": -90,
                "y": 610,
                "word": "Commencing on and including the Effective Date and ending on",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 18,
                        "x": 472,
                        "y": 884,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 489,
                        "y": 884,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 18,
                        "x": 500,
                        "y": 884,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 18,
                        "x": 516,
                        "y": 884,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 533,
                        "y": 884,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 543,
                        "y": 884,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 554,
                        "y": 884,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 565,
                        "y": 884,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 568,
                        "y": 884,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 579,
                        "y": 884,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 596,
                        "y": 884,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 607,
                        "y": 884,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 623,
                        "y": 884,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 637,
                        "y": 884,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 648,
                        "y": 884,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 667,
                        "y": 884,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 670,
                        "y": 884,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 681,
                        "y": 884,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 691,
                        "y": 884,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 694,
                        "y": 884,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 705,
                        "y": 884,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 716,
                        "y": 884,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 719,
                        "y": 884,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 733,
                        "y": 884,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 746,
                        "y": 884,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 755,
                        "y": 884,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 765,
                        "y": 884,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 782,
                        "y": 884,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 796,
                        "y": 884,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 804,
                        "y": 884,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 807,
                        "y": 884,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 818,
                        "y": 884,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 828,
                        "y": 884,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 834,
                        "y": 884,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 837,
                        "y": 884,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 845,
                        "y": 884,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 18,
                        "x": 861,
                        "y": 884,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 878,
                        "y": 884,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 892,
                        "y": 884,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 894,
                        "y": 884,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 911,
                        "y": 884,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 922,
                        "y": 884,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 933,
                        "y": 884,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 949,
                        "y": 884,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 963,
                        "y": 884,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 974,
                        "y": 884,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 985,
                        "y": 884,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 987,
                        "y": 884,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 998,
                        "y": 884,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 1014,
                        "y": 884,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 1028,
                        "y": 884,
                        "word": "n"
                    }
                ],
                "direction": 0,
                "height": 566,
                "rowId": 28
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 907
                    },
                    {
                        "x": 780,
                        "y": 907
                    },
                    {
                        "x": 780,
                        "y": 925
                    },
                    {
                        "x": 471,
                        "y": 925
                    }
                ],
                "width": 18,
                "x": 617,
                "angle": -90,
                "y": 762,
                "word": "and including the Termination Date.",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 474,
                        "y": 907,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 486,
                        "y": 907,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 496,
                        "y": 907,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 514,
                        "y": 907,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 517,
                        "y": 907,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 526,
                        "y": 907,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 538,
                        "y": 907,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 540,
                        "y": 907,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 552,
                        "y": 907,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 564,
                        "y": 907,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 566,
                        "y": 907,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 578,
                        "y": 907,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 592,
                        "y": 907,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 600,
                        "y": 907,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 609,
                        "y": 907,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 623,
                        "y": 907,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 640,
                        "y": 907,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 649,
                        "y": 907,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 656,
                        "y": 907,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 673,
                        "y": 907,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 675,
                        "y": 907,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 687,
                        "y": 907,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 696,
                        "y": 907,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 705,
                        "y": 907,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 712,
                        "y": 907,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 717,
                        "y": 907,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 731,
                        "y": 907,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 747,
                        "y": 907,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 762,
                        "y": 907,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 764,
                        "y": 907,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 773,
                        "y": 907,
                        "word": "."
                    }
                ],
                "direction": 0,
                "height": 308,
                "rowId": 29
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 941
                    },
                    {
                        "x": 163,
                        "y": 941
                    },
                    {
                        "x": 163,
                        "y": 961
                    },
                    {
                        "x": 76,
                        "y": 961
                    }
                ],
                "width": 20,
                "x": 109,
                "angle": -90,
                "y": 908,
                "word": "计算期间：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 17,
                        "x": 77,
                        "y": 942,
                        "word": "计"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 17,
                        "x": 101,
                        "y": 942,
                        "word": "算"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 17,
                        "x": 117,
                        "y": 942,
                        "word": "期"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 137,
                        "y": 942,
                        "word": "间"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 156,
                        "y": 942,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 86,
                "rowId": 30
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 474,
                        "y": 941
                    },
                    {
                        "x": 977,
                        "y": 941
                    },
                    {
                        "x": 977,
                        "y": 961
                    },
                    {
                        "x": 474,
                        "y": 961
                    }
                ],
                "width": 19,
                "x": 716,
                "angle": -90,
                "y": 700,
                "word": "自起始日开始(含起始日)，到到期日结束(含到期日)。",
                "charInfo": [
                    {
                        "prob": 100,
                        "w": 13,
                        "h": 17,
                        "x": 477,
                        "y": 942,
                        "word": "自"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 494,
                        "y": 942,
                        "word": "起"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 515,
                        "y": 942,
                        "word": "始"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 534,
                        "y": 942,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 553,
                        "y": 942,
                        "word": "开"
                    },
                    {
                        "prob": 100,
                        "w": 20,
                        "h": 17,
                        "x": 572,
                        "y": 942,
                        "word": "始"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 601,
                        "y": 942,
                        "word": "("
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 17,
                        "x": 613,
                        "y": 942,
                        "word": "含"
                    },
                    {
                        "prob": 100,
                        "w": 18,
                        "h": 17,
                        "x": 632,
                        "y": 942,
                        "word": "起"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 653,
                        "y": 942,
                        "word": "始"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 17,
                        "x": 674,
                        "y": 942,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 691,
                        "y": 942,
                        "word": ")"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 710,
                        "y": 942,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 729,
                        "y": 942,
                        "word": "到"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 750,
                        "y": 942,
                        "word": "到"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 769,
                        "y": 942,
                        "word": "期"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 17,
                        "x": 791,
                        "y": 942,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 807,
                        "y": 942,
                        "word": "结"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 829,
                        "y": 942,
                        "word": "束"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 857,
                        "y": 942,
                        "word": "("
                    },
                    {
                        "prob": 100,
                        "w": 18,
                        "h": 17,
                        "x": 867,
                        "y": 942,
                        "word": "含"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 887,
                        "y": 942,
                        "word": "到"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 906,
                        "y": 942,
                        "word": "期"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 928,
                        "y": 942,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 947,
                        "y": 942,
                        "word": ")"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 966,
                        "y": 942,
                        "word": "。"
                    }
                ],
                "direction": 0,
                "height": 502,
                "rowId": 31
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 979
                    },
                    {
                        "x": 207,
                        "y": 981
                    },
                    {
                        "x": 207,
                        "y": 1001
                    },
                    {
                        "x": 76,
                        "y": 999
                    }
                ],
                "width": 19,
                "x": 131,
                "angle": -89,
                "y": 923,
                "word": "Payment Date：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 78,
                        "y": 980,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 92,
                        "y": 980,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 104,
                        "y": 980,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 113,
                        "y": 980,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 127,
                        "y": 980,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 139,
                        "y": 980,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 151,
                        "y": 981,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 160,
                        "y": 981,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 174,
                        "y": 981,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 186,
                        "y": 981,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 193,
                        "y": 981,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 202,
                        "y": 981,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 131,
                "rowId": 32
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 981
                    },
                    {
                        "x": 1038,
                        "y": 978
                    },
                    {
                        "x": 1038,
                        "y": 998
                    },
                    {
                        "x": 471,
                        "y": 1001
                    }
                ],
                "width": 567,
                "x": 471,
                "angle": 0,
                "y": 980,
                "word": "xxxx， xxxx， subject to adjustment in accordance with the Modified",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 472,
                        "y": 982,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 485,
                        "y": 982,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 497,
                        "y": 982,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 510,
                        "y": 982,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 520,
                        "y": 982,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 527,
                        "y": 982,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 540,
                        "y": 982,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 550,
                        "y": 982,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 560,
                        "y": 982,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 570,
                        "y": 982,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 577,
                        "y": 982,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 590,
                        "y": 982,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 600,
                        "y": 982,
                        "word": "b"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 612,
                        "y": 982,
                        "word": "j"
                    },
                    {
                        "prob": 100,
                        "w": 9,
                        "h": 17,
                        "x": 615,
                        "y": 982,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 627,
                        "y": 981,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 635,
                        "y": 981,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 645,
                        "y": 981,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 652,
                        "y": 981,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 665,
                        "y": 981,
                        "word": "a"
                    },
                    {
                        "prob": 100,
                        "w": 4,
                        "h": 17,
                        "x": 680,
                        "y": 981,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 690,
                        "y": 981,
                        "word": "j"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 692,
                        "y": 981,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 705,
                        "y": 981,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 712,
                        "y": 981,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 720,
                        "y": 981,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 735,
                        "y": 981,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 747,
                        "y": 981,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 757,
                        "y": 981,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 765,
                        "y": 981,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 772,
                        "y": 981,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 785,
                        "y": 981,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 800,
                        "y": 981,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 810,
                        "y": 981,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 820,
                        "y": 981,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 830,
                        "y": 981,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 837,
                        "y": 980,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 847,
                        "y": 980,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 857,
                        "y": 980,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 867,
                        "y": 980,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 877,
                        "y": 980,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 17,
                        "x": 890,
                        "y": 980,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 907,
                        "y": 980,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 912,
                        "y": 980,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 917,
                        "y": 980,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 930,
                        "y": 980,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 940,
                        "y": 980,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 950,
                        "y": 980,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 17,
                        "x": 965,
                        "y": 980,
                        "word": "M"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 982,
                        "y": 980,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 992,
                        "y": 980,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 1005,
                        "y": 980,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 1010,
                        "y": 980,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 1017,
                        "y": 980,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 1019,
                        "y": 980,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 1026,
                        "y": 980,
                        "word": "d"
                    }
                ],
                "direction": 0,
                "height": 18,
                "rowId": 33
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 1002
                    },
                    {
                        "x": 790,
                        "y": 1004
                    },
                    {
                        "x": 790,
                        "y": 1024
                    },
                    {
                        "x": 471,
                        "y": 1021
                    }
                ],
                "width": 19,
                "x": 621,
                "angle": -89,
                "y": 853,
                "word": "Following Business Day Convention.",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 472,
                        "y": 1003,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 492,
                        "y": 1003,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 497,
                        "y": 1003,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 504,
                        "y": 1003,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 509,
                        "y": 1003,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 514,
                        "y": 1003,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 532,
                        "y": 1003,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 534,
                        "y": 1003,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 544,
                        "y": 1003,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 559,
                        "y": 1003,
                        "word": "B"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 574,
                        "y": 1003,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 584,
                        "y": 1003,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 594,
                        "y": 1003,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 599,
                        "y": 1003,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 609,
                        "y": 1004,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 619,
                        "y": 1004,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 629,
                        "y": 1004,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 644,
                        "y": 1004,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 659,
                        "y": 1004,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 669,
                        "y": 1004,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 684,
                        "y": 1004,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 698,
                        "y": 1004,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 708,
                        "y": 1004,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 721,
                        "y": 1004,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 731,
                        "y": 1005,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 741,
                        "y": 1005,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 753,
                        "y": 1005,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 761,
                        "y": 1005,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 766,
                        "y": 1005,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 771,
                        "y": 1005,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 783,
                        "y": 1005,
                        "word": "."
                    }
                ],
                "direction": 0,
                "height": 318,
                "rowId": 34
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 78,
                        "y": 1038
                    },
                    {
                        "x": 143,
                        "y": 1038
                    },
                    {
                        "x": 143,
                        "y": 1056
                    },
                    {
                        "x": 78,
                        "y": 1056
                    }
                ],
                "width": 18,
                "x": 101,
                "angle": -90,
                "y": 1014,
                "word": "支付日：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 79,
                        "y": 1039,
                        "word": "支"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 16,
                        "x": 98,
                        "y": 1039,
                        "word": "付"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 16,
                        "x": 120,
                        "y": 1039,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 138,
                        "y": 1039,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 66,
                "rowId": 35
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 469,
                        "y": 1037
                    },
                    {
                        "x": 957,
                        "y": 1035
                    },
                    {
                        "x": 957,
                        "y": 1056
                    },
                    {
                        "x": 469,
                        "y": 1058
                    }
                ],
                "width": 489,
                "x": 468,
                "angle": 0,
                "y": 1036,
                "word": "xxxx年xx月xx日，按经修正的下一个营业日准则调整。",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 472,
                        "y": 1038,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 19,
                        "x": 485,
                        "y": 1038,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 19,
                        "x": 495,
                        "y": 1038,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 502,
                        "y": 1038,
                        "word": "x"
                    },
                    {
                        "prob": 100,
                        "w": 21,
                        "h": 19,
                        "x": 515,
                        "y": 1038,
                        "word": "年"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 540,
                        "y": 1038,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 552,
                        "y": 1038,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 19,
                        "x": 565,
                        "y": 1038,
                        "word": "月"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 587,
                        "y": 1038,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 600,
                        "y": 1038,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 19,
                        "x": 615,
                        "y": 1038,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 19,
                        "x": 634,
                        "y": 1038,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 19,
                        "x": 652,
                        "y": 1038,
                        "word": "按"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 19,
                        "x": 672,
                        "y": 1038,
                        "word": "经"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 19,
                        "x": 692,
                        "y": 1037,
                        "word": "修"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 19,
                        "x": 712,
                        "y": 1037,
                        "word": "正"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 19,
                        "x": 732,
                        "y": 1037,
                        "word": "的"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 19,
                        "x": 752,
                        "y": 1037,
                        "word": "下"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 19,
                        "x": 772,
                        "y": 1037,
                        "word": "一"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 19,
                        "x": 792,
                        "y": 1037,
                        "word": "个"
                    },
                    {
                        "prob": 100,
                        "w": 13,
                        "h": 19,
                        "x": 811,
                        "y": 1037,
                        "word": "营"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 19,
                        "x": 829,
                        "y": 1037,
                        "word": "业"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 19,
                        "x": 851,
                        "y": 1037,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 19,
                        "x": 869,
                        "y": 1037,
                        "word": "准"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 19,
                        "x": 889,
                        "y": 1037,
                        "word": "则"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 19,
                        "x": 909,
                        "y": 1037,
                        "word": "调"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 19,
                        "x": 929,
                        "y": 1037,
                        "word": "整"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 19,
                        "x": 949,
                        "y": 1037,
                        "word": "。"
                    }
                ],
                "direction": 0,
                "height": 21,
                "rowId": 36
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 1110
                    },
                    {
                        "x": 211,
                        "y": 1110
                    },
                    {
                        "x": 211,
                        "y": 1129
                    },
                    {
                        "x": 76,
                        "y": 1129
                    }
                ],
                "width": 18,
                "x": 134,
                "angle": -90,
                "y": 1052,
                "word": "Fixed Amount",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 78,
                        "y": 1111,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 93,
                        "y": 1111,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 95,
                        "y": 1111,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 106,
                        "y": 1111,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 117,
                        "y": 1111,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 15,
                        "x": 134,
                        "y": 1111,
                        "word": "A"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 15,
                        "x": 149,
                        "y": 1111,
                        "word": "m"
                    },
                    {
                        "prob": 100,
                        "w": 10,
                        "h": 15,
                        "x": 166,
                        "y": 1111,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 179,
                        "y": 1111,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 190,
                        "y": 1111,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 201,
                        "y": 1111,
                        "word": "t"
                    }
                ],
                "direction": 0,
                "height": 134,
                "rowId": 37
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 76,
                        "y": 1145
                    },
                    {
                        "x": 158,
                        "y": 1145
                    },
                    {
                        "x": 158,
                        "y": 1165
                    },
                    {
                        "x": 76,
                        "y": 1165
                    }
                ],
                "width": 20,
                "x": 106,
                "angle": -90,
                "y": 1113,
                "word": "固定金额",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 18,
                        "x": 80,
                        "y": 1146,
                        "word": "固"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 97,
                        "y": 1146,
                        "word": "定"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 117,
                        "y": 1146,
                        "word": "金"
                    },
                    {
                        "prob": 99,
                        "w": 19,
                        "h": 18,
                        "x": 136,
                        "y": 1146,
                        "word": "额"
                    }
                ],
                "direction": 0,
                "height": 81,
                "rowId": 38
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 111,
                        "y": 1181
                    },
                    {
                        "x": 247,
                        "y": 1184
                    },
                    {
                        "x": 247,
                        "y": 1204
                    },
                    {
                        "x": 111,
                        "y": 1201
                    }
                ],
                "width": 19,
                "x": 168,
                "angle": -88,
                "y": 1123,
                "word": "Fixed Amount：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 111,
                        "y": 1182,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 17,
                        "x": 127,
                        "y": 1183,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 129,
                        "y": 1183,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 139,
                        "y": 1183,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 149,
                        "y": 1183,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 165,
                        "y": 1184,
                        "word": "A"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 17,
                        "x": 179,
                        "y": 1184,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 195,
                        "y": 1184,
                        "word": "o"
                    },
                    {
                        "prob": 100,
                        "w": 6,
                        "h": 17,
                        "x": 207,
                        "y": 1184,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 217,
                        "y": 1185,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 227,
                        "y": 1185,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 17,
                        "x": 239,
                        "y": 1185,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 137,
                "rowId": 39
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 473,
                        "y": 1183
                    },
                    {
                        "x": 1040,
                        "y": 1184
                    },
                    {
                        "x": 1040,
                        "y": 1204
                    },
                    {
                        "x": 473,
                        "y": 1203
                    }
                ],
                "width": 19,
                "x": 746,
                "angle": -89,
                "y": 909,
                "word": "Party x shall pay to Party x on the relevant Payment Date an",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 474,
                        "y": 1184,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 487,
                        "y": 1184,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 498,
                        "y": 1184,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 508,
                        "y": 1184,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 511,
                        "y": 1184,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 18,
                        "x": 526,
                        "y": 1184,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 545,
                        "y": 1184,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 558,
                        "y": 1184,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 568,
                        "y": 1184,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 581,
                        "y": 1184,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 587,
                        "y": 1184,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 594,
                        "y": 1184,
                        "word": "p"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 607,
                        "y": 1184,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 618,
                        "y": 1184,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 634,
                        "y": 1184,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 644,
                        "y": 1184,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 18,
                        "x": 660,
                        "y": 1184,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 675,
                        "y": 1184,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 691,
                        "y": 1184,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 694,
                        "y": 1184,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 699,
                        "y": 1184,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 715,
                        "y": 1184,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 733,
                        "y": 1184,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 746,
                        "y": 1184,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 764,
                        "y": 1184,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 772,
                        "y": 1184,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 783,
                        "y": 1184,
                        "word": "e"
                    },
                    {
                        "prob": 100,
                        "w": 6,
                        "h": 18,
                        "x": 801,
                        "y": 1184,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 811,
                        "y": 1185,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 822,
                        "y": 1185,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 824,
                        "y": 1185,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 835,
                        "y": 1185,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 845,
                        "y": 1185,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 856,
                        "y": 1185,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 866,
                        "y": 1185,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 879,
                        "y": 1185,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 892,
                        "y": 1185,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 903,
                        "y": 1185,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 18,
                        "x": 913,
                        "y": 1185,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 929,
                        "y": 1185,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 942,
                        "y": 1185,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 950,
                        "y": 1185,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 18,
                        "x": 963,
                        "y": 1185,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 979,
                        "y": 1185,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 989,
                        "y": 1185,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 997,
                        "y": 1185,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 1015,
                        "y": 1185,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 1027,
                        "y": 1185,
                        "word": "n"
                    }
                ],
                "direction": 0,
                "height": 568,
                "rowId": 40
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 469,
                        "y": 1206
                    },
                    {
                        "x": 806,
                        "y": 1206
                    },
                    {
                        "x": 806,
                        "y": 1226
                    },
                    {
                        "x": 469,
                        "y": 1226
                    }
                ],
                "width": 20,
                "x": 627,
                "angle": -90,
                "y": 1047,
                "word": "amount in USD determined as follows：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 474,
                        "y": 1207,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 17,
                        "x": 486,
                        "y": 1207,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 502,
                        "y": 1207,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 514,
                        "y": 1207,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 524,
                        "y": 1207,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 534,
                        "y": 1207,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 544,
                        "y": 1207,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 550,
                        "y": 1207,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 17,
                        "x": 564,
                        "y": 1207,
                        "word": "U"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 580,
                        "y": 1207,
                        "word": "S"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 17,
                        "x": 592,
                        "y": 1207,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 610,
                        "y": 1207,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 624,
                        "y": 1207,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 634,
                        "y": 1207,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 640,
                        "y": 1207,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 650,
                        "y": 1207,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 656,
                        "y": 1207,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 674,
                        "y": 1207,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 676,
                        "y": 1207,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 688,
                        "y": 1207,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 698,
                        "y": 1207,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 713,
                        "y": 1207,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 725,
                        "y": 1207,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 737,
                        "y": 1207,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 747,
                        "y": 1207,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 757,
                        "y": 1207,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 761,
                        "y": 1207,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 763,
                        "y": 1207,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 17,
                        "x": 775,
                        "y": 1207,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 789,
                        "y": 1207,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 799,
                        "y": 1207,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 337,
                "rowId": 41
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 1242
                    },
                    {
                        "x": 755,
                        "y": 1242
                    },
                    {
                        "x": 755,
                        "y": 1260
                    },
                    {
                        "x": 471,
                        "y": 1260
                    }
                ],
                "width": 19,
                "x": 603,
                "angle": -90,
                "y": 1109,
                "word": "Notional Quantity*Fixed Price；",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 16,
                        "x": 474,
                        "y": 1242,
                        "word": "N"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 489,
                        "y": 1242,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 502,
                        "y": 1242,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 507,
                        "y": 1242,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 509,
                        "y": 1242,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 522,
                        "y": 1242,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 532,
                        "y": 1242,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 542,
                        "y": 1242,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 552,
                        "y": 1242,
                        "word": "Q"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 569,
                        "y": 1242,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 579,
                        "y": 1242,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 592,
                        "y": 1242,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 604,
                        "y": 1242,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 612,
                        "y": 1242,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 614,
                        "y": 1242,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 619,
                        "y": 1242,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 632,
                        "y": 1242,
                        "word": "*"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 647,
                        "y": 1242,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 659,
                        "y": 1242,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 664,
                        "y": 1242,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 674,
                        "y": 1242,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 16,
                        "x": 684,
                        "y": 1242,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 702,
                        "y": 1242,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 714,
                        "y": 1242,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 724,
                        "y": 1242,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 727,
                        "y": 1242,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 737,
                        "y": 1242,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 747,
                        "y": 1242,
                        "word": "；"
                    }
                ],
                "direction": 0,
                "height": 284,
                "rowId": 42
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 469,
                        "y": 1276
                    },
                    {
                        "x": 995,
                        "y": 1276
                    },
                    {
                        "x": 995,
                        "y": 1296
                    },
                    {
                        "x": 469,
                        "y": 1296
                    }
                ],
                "width": 20,
                "x": 722,
                "angle": -90,
                "y": 1024,
                "word": "x方须在相关支付日向x方支付按下列方式决定的美元金额：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 472,
                        "y": 1277,
                        "word": "x"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 487,
                        "y": 1277,
                        "word": "方"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 507,
                        "y": 1277,
                        "word": "须"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 527,
                        "y": 1277,
                        "word": "在"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 547,
                        "y": 1277,
                        "word": "相"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 567,
                        "y": 1277,
                        "word": "关"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 587,
                        "y": 1277,
                        "word": "支"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 18,
                        "x": 607,
                        "y": 1277,
                        "word": "付"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 630,
                        "y": 1277,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 650,
                        "y": 1277,
                        "word": "向"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 672,
                        "y": 1277,
                        "word": "x"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 687,
                        "y": 1277,
                        "word": "方"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 707,
                        "y": 1277,
                        "word": "支"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 727,
                        "y": 1277,
                        "word": "付"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 747,
                        "y": 1277,
                        "word": "按"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 769,
                        "y": 1277,
                        "word": "下"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 787,
                        "y": 1277,
                        "word": "列"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 807,
                        "y": 1277,
                        "word": "方"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 827,
                        "y": 1277,
                        "word": "式"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 847,
                        "y": 1277,
                        "word": "决"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 867,
                        "y": 1277,
                        "word": "定"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 887,
                        "y": 1277,
                        "word": "的"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 907,
                        "y": 1277,
                        "word": "美"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 926,
                        "y": 1277,
                        "word": "元"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 946,
                        "y": 1277,
                        "word": "金"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 966,
                        "y": 1277,
                        "word": "额"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 986,
                        "y": 1277,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 526,
                "rowId": 43
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 111,
                        "y": 1294
                    },
                    {
                        "x": 204,
                        "y": 1294
                    },
                    {
                        "x": 204,
                        "y": 1313
                    },
                    {
                        "x": 111,
                        "y": 1313
                    }
                ],
                "width": 17,
                "x": 148,
                "angle": -90,
                "y": 1255,
                "word": "固定金额：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 112,
                        "y": 1294,
                        "word": "固"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 132,
                        "y": 1294,
                        "word": "定"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 151,
                        "y": 1294,
                        "word": "金"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 16,
                        "x": 171,
                        "y": 1294,
                        "word": "额"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 196,
                        "y": 1294,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 93,
                "rowId": 44
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 474,
                        "y": 1314
                    },
                    {
                        "x": 660,
                        "y": 1314
                    },
                    {
                        "x": 660,
                        "y": 1333
                    },
                    {
                        "x": 474,
                        "y": 1333
                    }
                ],
                "width": 18,
                "x": 557,
                "angle": -90,
                "y": 1231,
                "word": "名义数量*固定价格；",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 474,
                        "y": 1314,
                        "word": "名"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 492,
                        "y": 1314,
                        "word": "义"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 515,
                        "y": 1314,
                        "word": "数"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 16,
                        "x": 534,
                        "y": 1314,
                        "word": "量"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 557,
                        "y": 1314,
                        "word": "*"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 16,
                        "x": 571,
                        "y": 1314,
                        "word": "固"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 591,
                        "y": 1314,
                        "word": "定"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 16,
                        "x": 611,
                        "y": 1314,
                        "word": "价"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 633,
                        "y": 1314,
                        "word": "格"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 656,
                        "y": 1314,
                        "word": "；"
                    }
                ],
                "direction": 0,
                "height": 185,
                "rowId": 45
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 111,
                        "y": 1367
                    },
                    {
                        "x": 216,
                        "y": 1367
                    },
                    {
                        "x": 216,
                        "y": 1385
                    },
                    {
                        "x": 111,
                        "y": 1385
                    }
                ],
                "width": 19,
                "x": 153,
                "angle": -90,
                "y": 1323,
                "word": "Fixed Price：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 113,
                        "y": 1368,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 126,
                        "y": 1368,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 128,
                        "y": 1368,
                        "word": "x"
                    },
                    {
                        "prob": 100,
                        "w": 8,
                        "h": 15,
                        "x": 139,
                        "y": 1368,
                        "word": "e"
                    },
                    {
                        "prob": 100,
                        "w": 10,
                        "h": 15,
                        "x": 150,
                        "y": 1368,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 165,
                        "y": 1368,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 178,
                        "y": 1368,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 187,
                        "y": 1368,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 189,
                        "y": 1368,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 199,
                        "y": 1368,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 208,
                        "y": 1368,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 105,
                "rowId": 46
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 1366
                    },
                    {
                        "x": 747,
                        "y": 1368
                    },
                    {
                        "x": 747,
                        "y": 1388
                    },
                    {
                        "x": 471,
                        "y": 1386
                    }
                ],
                "width": 20,
                "x": 598,
                "angle": -89,
                "y": 1239,
                "word": "USD x， xxx.xxx per metric tonne",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 17,
                        "x": 472,
                        "y": 1367,
                        "word": "U"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 488,
                        "y": 1367,
                        "word": "S"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 17,
                        "x": 501,
                        "y": 1367,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 519,
                        "y": 1367,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 535,
                        "y": 1367,
                        "word": "，"
                    },
                    {
                        "prob": 96,
                        "w": 1,
                        "h": 17,
                        "x": 540,
                        "y": 1367,
                        "word": "x"
                    },
                    {
                        "prob": 98,
                        "w": 6,
                        "h": 17,
                        "x": 545,
                        "y": 1367,
                        "word": "x"
                    },
                    {
                        "prob": 98,
                        "w": 6,
                        "h": 17,
                        "x": 556,
                        "y": 1367,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 566,
                        "y": 1367,
                        "word": "."
                    },
                    {
                        "prob": 95,
                        "w": 6,
                        "h": 17,
                        "x": 571,
                        "y": 1367,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 579,
                        "y": 1367,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 589,
                        "y": 1367,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 602,
                        "y": 1367,
                        "word": "p"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 616,
                        "y": 1368,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 626,
                        "y": 1368,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 17,
                        "x": 636,
                        "y": 1368,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 655,
                        "y": 1368,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 668,
                        "y": 1368,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 673,
                        "y": 1368,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 678,
                        "y": 1368,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 681,
                        "y": 1368,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 702,
                        "y": 1368,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 706,
                        "y": 1368,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 711,
                        "y": 1368,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 721,
                        "y": 1368,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 17,
                        "x": 732,
                        "y": 1368,
                        "word": "e"
                    }
                ],
                "direction": 0,
                "height": 276,
                "rowId": 47
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 112,
                        "y": 1403
                    },
                    {
                        "x": 202,
                        "y": 1403
                    },
                    {
                        "x": 202,
                        "y": 1421
                    },
                    {
                        "x": 112,
                        "y": 1421
                    }
                ],
                "width": 19,
                "x": 147,
                "angle": -90,
                "y": 1366,
                "word": "固定价格：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 115,
                        "y": 1403,
                        "word": "固"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 134,
                        "y": 1403,
                        "word": "定"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 152,
                        "y": 1403,
                        "word": "价"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 173,
                        "y": 1403,
                        "word": "格"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 193,
                        "y": 1403,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 90,
                "rowId": 48
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 471,
                        "y": 1404
                    },
                    {
                        "x": 646,
                        "y": 1402
                    },
                    {
                        "x": 647,
                        "y": 1421
                    },
                    {
                        "x": 471,
                        "y": 1423
                    }
                ],
                "width": 176,
                "x": 470,
                "angle": 0,
                "y": 1402,
                "word": "x，xxx.xxx美元/公吨",
                "charInfo": [
                    {
                        "prob": 94,
                        "w": 8,
                        "h": 17,
                        "x": 472,
                        "y": 1403,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 489,
                        "y": 1403,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 494,
                        "y": 1403,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 499,
                        "y": 1403,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 509,
                        "y": 1403,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 522,
                        "y": 1403,
                        "word": "."
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 524,
                        "y": 1403,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 534,
                        "y": 1403,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 544,
                        "y": 1403,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 17,
                        "x": 557,
                        "y": 1402,
                        "word": "美"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 17,
                        "x": 576,
                        "y": 1402,
                        "word": "元"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 595,
                        "y": 1402,
                        "word": "/"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 17,
                        "x": 605,
                        "y": 1402,
                        "word": "公"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 17,
                        "x": 625,
                        "y": 1402,
                        "word": "吨"
                    }
                ],
                "direction": 0,
                "height": 20,
                "rowId": 49
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 548,
                        "y": 1592
                    },
                    {
                        "x": 641,
                        "y": 1589
                    },
                    {
                        "x": 642,
                        "y": 1609
                    },
                    {
                        "x": 549,
                        "y": 1611
                    }
                ],
                "width": 93,
                "x": 547,
                "angle": -1,
                "y": 1591,
                "word": "Page 2 of 7",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 549,
                        "y": 1593,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 561,
                        "y": 1593,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 570,
                        "y": 1593,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 579,
                        "y": 1592,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 592,
                        "y": 1592,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 608,
                        "y": 1591,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 619,
                        "y": 1591,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 628,
                        "y": 1591,
                        "word": "7"
                    }
                ],
                "direction": 0,
                "height": 18,
                "rowId": 50
            }
        ],
        "height": 1684
    },
    "requestId": "576b7eb5-c0ea-4445-8205-06c66a14e1bc"
}
contrastResult={
    "code": 200,
    "data": {
        "figure": [
            {
                "w": 39,
                "x": 1152,
                "h": 176,
                "y": 924,
                "box": {
                    "w": 174,
                    "x": 1171,
                    "h": 32,
                    "y": 1011,
                    "angle": -87
                },
                "type": "oval_stamp",
                "points": [
                    {
                        "x": 1160,
                        "y": 924
                    },
                    {
                        "x": 1152,
                        "y": 1084
                    },
                    {
                        "x": 1184,
                        "y": 1100
                    },
                    {
                        "x": 1191,
                        "y": 938
                    }
                ]
            }
        ],
        "prism_rowsInfo": [
            {
                "word": "cit",
                "rowId": 0
            },
            {
                "word": "REFERENCE ： 40049030",
                "rowId": 1
            },
            {
                "word": "In the event of any inconsistency between the English and Chinese versions， the Chinese version shall prevail.",
                "rowId": 2
            },
            {
                "word": "本确认书的中英文文本如有任何不一致，应以中文文本为准。",
                "rowId": 3
            },
            {
                "word": "The terms of the Transaction to which this Confirmation relates areas follows：",
                "rowId": 4
            },
            {
                "word": "本确认书所相关的交易的条款如下：",
                "rowId": 5
            },
            {
                "word": "Transaction Type：[Swap]",
                "rowId": 6
            },
            {
                "word": "交易种类：[掉期]",
                "rowId": 7
            },
            {
                "word": "Notional Quantity：",
                "rowId": 8
            },
            {
                "word": "42 metric tonnes",
                "rowId": 9
            },
            {
                "word": "名义数量：",
                "rowId": 10
            },
            {
                "word": "42公吨√",
                "rowId": 11
            },
            {
                "word": "Commodity：",
                "rowId": 12
            },
            {
                "word": "COBALT/",
                "rowId": 13
            },
            {
                "word": "商品：",
                "rowId": 14
            },
            {
                "word": "钴",
                "rowId": 15
            },
            {
                "word": "Trade Date：",
                "rowId": 16
            },
            {
                "word": "Oct 14， 2022",
                "rowId": 17
            },
            {
                "word": "交易日：",
                "rowId": 18
            },
            {
                "word": "2022年10月14日",
                "rowId": 19
            },
            {
                "word": "Effective Date：",
                "rowId": 20
            },
            {
                "word": "Jun 01， 2023",
                "rowId": 21
            },
            {
                "word": "起始日：",
                "rowId": 22
            },
            {
                "word": "2023年06月01日",
                "rowId": 23
            },
            {
                "word": "Termination Date：",
                "rowId": 24
            },
            {
                "word": "Aug 31， 2023",
                "rowId": 25
            },
            {
                "word": "到期日",
                "rowId": 26
            },
            {
                "word": "2023年08月31日",
                "rowId": 27
            },
            {
                "word": "Calculation Period：",
                "rowId": 28
            },
            {
                "word": "Commencing on and including the Effective Date and ending on",
                "rowId": 29
            },
            {
                "word": "and including the Termination Date.",
                "rowId": 30
            },
            {
                "word": "计算期间",
                "rowId": 31
            },
            {
                "word": "自起始日开始(含起始日)，到到期日结束(含到期日)。",
                "rowId": 32
            },
            {
                "word": "Payment Date：",
                "rowId": 33
            },
            {
                "word": "10Oct 2023， subject to adjustment in accordance with the",
                "rowId": 34
            },
            {
                "word": "Mod iied Following Business Day Convention.",
                "rowId": 35
            },
            {
                "word": "支付日：",
                "rowId": 36
            },
            {
                "word": "2023年10月10日，按经修正的下一个营业日准则调整。",
                "rowId": 37
            },
            {
                "word": "Fixed Amount",
                "rowId": 38
            },
            {
                "word": "固定金额",
                "rowId": 39
            },
            {
                "word": "Fixed Amount：",
                "rowId": 40
            },
            {
                "word": "Party B shall pay to Party A on the relevant Payment Date an",
                "rowId": 41
            },
            {
                "word": "amount in USD determined as follows：",
                "rowId": 42
            },
            {
                "word": "Notional Quantity*Fixed Price；",
                "rowId": 43
            },
            {
                "word": "乙方须在相关支付日向甲方支付按下列方式决定的美元金额：",
                "rowId": 44
            },
            {
                "word": "固定金额：",
                "rowId": 45
            },
            {
                "word": "名义数量*固定价格；",
                "rowId": 46
            },
            {
                "word": "Fixed Price：",
                "rowId": 47
            },
            {
                "word": "USD 57， 871.34permetrictonne",
                "rowId": 48
            },
            {
                "word": "固定价格：",
                "rowId": 49
            },
            {
                "word": "57，871.34美元/公吨",
                "rowId": 50
            },
            {
                "word": "Page 2 of 7",
                "rowId": 51
            },
            {
                "word": "么",
                "rowId": 52
            },
            {
                "word": "32",
                "rowId": 54
            }
        ],
        "algo_version": "",
        "orgWidth": 1191,
        "content": "cit REFERENCE ： 40049030 In the event of any inconsistency between the English and Chinese versions， the Chinese version shall prevail. 本确认书的中英文文本如有任何不一致，应以中文文本为准。 The terms of the Transaction to which this Confirmation relates areas follows： 本确认书所相关的交易的条款如下： Transaction Type：[Swap] 交易种类：[掉期] Notional Quantity： 42 metric tonnes 名义数量： 42公吨√ Commodity： COBALT/ 商品： 钴 Trade Date： Oct 14， 2022 交易日： 2022年10月14日 Effective Date： Jun 01， 2023 起始日： 2023年06月01日 Termination Date： Aug 31， 2023 到期日 2023年08月31日 Calculation Period： Commencing on and including the Effective Date and ending on and including the Termination Date. 么 计算期间 自起始日开始(含起始日)，到到期日结束(含到期日)。 Payment Date： 10Oct 2023， subject to adjustment in accordance with the Mod iied Following Business Day Convention. 32 支付日： 2023年10月10日，按经修正的下一个营业日准则调整。 Fixed Amount 固定金额 Fixed Amount： Party B shall pay to Party A on the relevant Payment Date an amount in USD determined as follows： Notional Quantity*Fixed Price； 乙方须在相关支付日向甲方支付按下列方式决定的美元金额： 固定金额： 名义数量*固定价格； Fixed Price： USD 57， 871.34permetrictonne 固定价格： 57，871.34美元/公吨 Page 2 of 7 ",
        "requestId": "7B3C0F8D-77A8-57EE-B030-9CFB80D96134",
        "prism_wnum": 54,
        "width": 1191,
        "angle": 0,
        "orgHeight": 1684,
        "prism_version": "1.0.9",
        "prism_wordsInfo": [
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 981,
                        "y": 165
                    },
                    {
                        "x": 1075,
                        "y": 165
                    },
                    {
                        "x": 1075,
                        "y": 214
                    },
                    {
                        "x": 981,
                        "y": 214
                    }
                ],
                "width": 48,
                "x": 1004,
                "angle": -90,
                "y": 142,
                "word": "cit",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 22,
                        "h": 46,
                        "x": 988,
                        "y": 165,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 46,
                        "x": 1026,
                        "y": 165,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 30,
                        "h": 46,
                        "x": 1035,
                        "y": 165,
                        "word": "t"
                    }
                ],
                "direction": 0,
                "height": 93,
                "rowId": 0
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 841,
                        "y": 259
                    },
                    {
                        "x": 1038,
                        "y": 259
                    },
                    {
                        "x": 1038,
                        "y": 276
                    },
                    {
                        "x": 841,
                        "y": 276
                    }
                ],
                "width": 16,
                "x": 932,
                "angle": -90,
                "y": 169,
                "word": "REFERENCE ： 40049030",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 843,
                        "y": 260,
                        "word": "R"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 856,
                        "y": 260,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 867,
                        "y": 260,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 878,
                        "y": 260,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 890,
                        "y": 260,
                        "word": "R"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 901,
                        "y": 260,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 912,
                        "y": 260,
                        "word": "N"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 925,
                        "y": 260,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 937,
                        "y": 260,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 950,
                        "y": 260,
                        "word": "："
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 956,
                        "y": 260,
                        "word": "4"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 967,
                        "y": 260,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 977,
                        "y": 260,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 988,
                        "y": 260,
                        "word": "4"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 998,
                        "y": 260,
                        "word": "9"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 1005,
                        "y": 260,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 1015,
                        "y": 260,
                        "word": "3"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 1025,
                        "y": 260,
                        "word": "0"
                    }
                ],
                "direction": 0,
                "height": 197,
                "rowId": 1
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 89,
                        "y": 335
                    },
                    {
                        "x": 938,
                        "y": 335
                    },
                    {
                        "x": 938,
                        "y": 353
                    },
                    {
                        "x": 89,
                        "y": 353
                    }
                ],
                "width": 18,
                "x": 504,
                "angle": -89,
                "y": -80,
                "word": "In the event of any inconsistency between the English and Chinese versions， the Chinese version shall prevail.",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 94,
                        "y": 336,
                        "word": "I"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 96,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 109,
                        "y": 336,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 117,
                        "y": 336,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 128,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 138,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 149,
                        "y": 336,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 160,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 168,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 177,
                        "y": 336,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 187,
                        "y": 336,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 198,
                        "y": 336,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 206,
                        "y": 336,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 217,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 225,
                        "y": 336,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 238,
                        "y": 336,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 245,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 253,
                        "y": 336,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 264,
                        "y": 336,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 272,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 283,
                        "y": 336,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 293,
                        "y": 336,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 298,
                        "y": 336,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 302,
                        "y": 336,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 308,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 317,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 327,
                        "y": 336,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 336,
                        "y": 336,
                        "word": "y"
                    },
                    {
                        "prob": 100,
                        "w": 9,
                        "h": 16,
                        "x": 346,
                        "y": 336,
                        "word": "b"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 359,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 368,
                        "y": 336,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 374,
                        "y": 336,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 387,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 395,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 406,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 416,
                        "y": 336,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 425,
                        "y": 336,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 433,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 446,
                        "y": 336,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 459,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 469,
                        "y": 336,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 480,
                        "y": 336,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 484,
                        "y": 336,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 486,
                        "y": 336,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 495,
                        "y": 336,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 508,
                        "y": 336,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 518,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 529,
                        "y": 336,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 542,
                        "y": 336,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 554,
                        "y": 336,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 565,
                        "y": 336,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 569,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 580,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 588,
                        "y": 336,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 597,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 610,
                        "y": 336,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 620,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 629,
                        "y": 336,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 635,
                        "y": 336,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 646,
                        "y": 336,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 648,
                        "y": 336,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 658,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 667,
                        "y": 336,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 675,
                        "y": 336,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 684,
                        "y": 336,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 690,
                        "y": 336,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 701,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 714,
                        "y": 336,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 726,
                        "y": 336,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 737,
                        "y": 336,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 739,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 750,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 758,
                        "y": 336,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 767,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 779,
                        "y": 336,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 792,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 801,
                        "y": 336,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 807,
                        "y": 336,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 818,
                        "y": 336,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 824,
                        "y": 336,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 828,
                        "y": 336,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 841,
                        "y": 336,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 849,
                        "y": 336,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 860,
                        "y": 336,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 873,
                        "y": 336,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 875,
                        "y": 336,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 881,
                        "y": 336,
                        "word": "p"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 892,
                        "y": 336,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 898,
                        "y": 336,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 907,
                        "y": 336,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 915,
                        "y": 336,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 928,
                        "y": 336,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 932,
                        "y": 336,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 934,
                        "y": 336,
                        "word": "."
                    }
                ],
                "direction": 0,
                "height": 848,
                "rowId": 2
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 91,
                        "y": 356
                    },
                    {
                        "x": 602,
                        "y": 356
                    },
                    {
                        "x": 602,
                        "y": 374
                    },
                    {
                        "x": 91,
                        "y": 374
                    }
                ],
                "width": 18,
                "x": 338,
                "angle": -89,
                "y": 109,
                "word": "本确认书的中英文文本如有任何不一致，应以中文文本为准。",
                "charInfo": [
                    {
                        "prob": 100,
                        "w": 17,
                        "h": 16,
                        "x": 92,
                        "y": 356,
                        "word": "本"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 113,
                        "y": 356,
                        "word": "确"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 132,
                        "y": 356,
                        "word": "认"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 151,
                        "y": 356,
                        "word": "书"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 170,
                        "y": 356,
                        "word": "的"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 189,
                        "y": 356,
                        "word": "中"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 208,
                        "y": 356,
                        "word": "英"
                    },
                    {
                        "prob": 100,
                        "w": 17,
                        "h": 16,
                        "x": 227,
                        "y": 356,
                        "word": "文"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 248,
                        "y": 356,
                        "word": "文"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 267,
                        "y": 356,
                        "word": "本"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 286,
                        "y": 356,
                        "word": "如"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 305,
                        "y": 356,
                        "word": "有"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 324,
                        "y": 356,
                        "word": "任"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 343,
                        "y": 356,
                        "word": "何"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 364,
                        "y": 356,
                        "word": "不"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 383,
                        "y": 356,
                        "word": "一"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 402,
                        "y": 356,
                        "word": "致"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 421,
                        "y": 356,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 438,
                        "y": 356,
                        "word": "应"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 459,
                        "y": 356,
                        "word": "以"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 478,
                        "y": 356,
                        "word": "中"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 497,
                        "y": 356,
                        "word": "文"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 516,
                        "y": 356,
                        "word": "文"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 535,
                        "y": 356,
                        "word": "本"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 554,
                        "y": 356,
                        "word": "为"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 575,
                        "y": 356,
                        "word": "准"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 594,
                        "y": 356,
                        "word": "。"
                    }
                ],
                "direction": 0,
                "height": 511,
                "rowId": 3
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 89,
                        "y": 390
                    },
                    {
                        "x": 691,
                        "y": 390
                    },
                    {
                        "x": 691,
                        "y": 409
                    },
                    {
                        "x": 89,
                        "y": 409
                    }
                ],
                "width": 17,
                "x": 381,
                "angle": -89,
                "y": 98,
                "word": "The terms of the Transaction to which this Confirmation relates areas follows：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 91,
                        "y": 391,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 102,
                        "y": 391,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 112,
                        "y": 391,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 125,
                        "y": 391,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 134,
                        "y": 391,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 142,
                        "y": 391,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 147,
                        "y": 391,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 161,
                        "y": 391,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 174,
                        "y": 391,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 185,
                        "y": 391,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 192,
                        "y": 391,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 200,
                        "y": 391,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 209,
                        "y": 391,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 222,
                        "y": 391,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 234,
                        "y": 391,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 241,
                        "y": 391,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 249,
                        "y": 391,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 258,
                        "y": 391,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 269,
                        "y": 391,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 277,
                        "y": 391,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 288,
                        "y": 391,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 292,
                        "y": 391,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 295,
                        "y": 391,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 305,
                        "y": 391,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 316,
                        "y": 391,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 325,
                        "y": 391,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 15,
                        "x": 337,
                        "y": 391,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 352,
                        "y": 391,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 359,
                        "y": 391,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 365,
                        "y": 391,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 372,
                        "y": 391,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 385,
                        "y": 391,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 393,
                        "y": 391,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 402,
                        "y": 391,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 404,
                        "y": 391,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 417,
                        "y": 391,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 430,
                        "y": 391,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 441,
                        "y": 391,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 451,
                        "y": 391,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 456,
                        "y": 391,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 460,
                        "y": 391,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 466,
                        "y": 391,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 479,
                        "y": 391,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 488,
                        "y": 391,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 496,
                        "y": 391,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 498,
                        "y": 391,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 507,
                        "y": 391,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 520,
                        "y": 391,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 528,
                        "y": 391,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 539,
                        "y": 391,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 541,
                        "y": 391,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 550,
                        "y": 391,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 556,
                        "y": 391,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 565,
                        "y": 391,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 576,
                        "y": 391,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 588,
                        "y": 391,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 593,
                        "y": 391,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 606,
                        "y": 391,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 617,
                        "y": 391,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 631,
                        "y": 391,
                        "word": "f"
                    },
                    {
                        "prob": 100,
                        "w": 4,
                        "h": 15,
                        "x": 638,
                        "y": 391,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 647,
                        "y": 391,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 653,
                        "y": 391,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 657,
                        "y": 391,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 662,
                        "y": 391,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 676,
                        "y": 391,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 683,
                        "y": 391,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 601,
                "rowId": 4
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 91,
                        "y": 422
                    },
                    {
                        "x": 390,
                        "y": 424
                    },
                    {
                        "x": 390,
                        "y": 444
                    },
                    {
                        "x": 91,
                        "y": 442
                    }
                ],
                "width": 18,
                "x": 231,
                "angle": -89,
                "y": 283,
                "word": "本确认书所相关的交易的条款如下：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 92,
                        "y": 424,
                        "word": "本"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 111,
                        "y": 424,
                        "word": "确"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 17,
                        "x": 130,
                        "y": 424,
                        "word": "认"
                    },
                    {
                        "prob": 100,
                        "w": 17,
                        "h": 17,
                        "x": 148,
                        "y": 424,
                        "word": "书"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 17,
                        "x": 170,
                        "y": 424,
                        "word": "所"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 189,
                        "y": 424,
                        "word": "相"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 207,
                        "y": 424,
                        "word": "关"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 226,
                        "y": 424,
                        "word": "的"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 17,
                        "x": 245,
                        "y": 425,
                        "word": "交"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 17,
                        "x": 266,
                        "y": 425,
                        "word": "易"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 285,
                        "y": 425,
                        "word": "的"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 304,
                        "y": 425,
                        "word": "条"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 323,
                        "y": 425,
                        "word": "款"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 341,
                        "y": 425,
                        "word": "如"
                    },
                    {
                        "prob": 100,
                        "w": 17,
                        "h": 17,
                        "x": 360,
                        "y": 425,
                        "word": "下"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 381,
                        "y": 426,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 298,
                "rowId": 5
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 99,
                        "y": 468
                    },
                    {
                        "x": 309,
                        "y": 470
                    },
                    {
                        "x": 309,
                        "y": 490
                    },
                    {
                        "x": 99,
                        "y": 488
                    }
                ],
                "width": 19,
                "x": 195,
                "angle": -89,
                "y": 372,
                "word": "Transaction Type：[Swap]",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 100,
                        "y": 470,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 113,
                        "y": 470,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 120,
                        "y": 470,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 127,
                        "y": 470,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 138,
                        "y": 470,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 147,
                        "y": 470,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 156,
                        "y": 470,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 167,
                        "y": 470,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 174,
                        "y": 470,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 178,
                        "y": 470,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 183,
                        "y": 470,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 196,
                        "y": 470,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 207,
                        "y": 470,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 216,
                        "y": 471,
                        "word": "p"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 225,
                        "y": 471,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 237,
                        "y": 471,
                        "word": "："
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 252,
                        "y": 471,
                        "word": "["
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 17,
                        "x": 261,
                        "y": 471,
                        "word": "S"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 272,
                        "y": 471,
                        "word": "w"
                    },
                    {
                        "prob": 100,
                        "w": 3,
                        "h": 17,
                        "x": 286,
                        "y": 471,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 293,
                        "y": 471,
                        "word": "p"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 302,
                        "y": 471,
                        "word": "]"
                    }
                ],
                "direction": 0,
                "height": 210,
                "rowId": 6
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 99,
                        "y": 502
                    },
                    {
                        "x": 240,
                        "y": 502
                    },
                    {
                        "x": 240,
                        "y": 521
                    },
                    {
                        "x": 99,
                        "y": 521
                    }
                ],
                "width": 18,
                "x": 160,
                "angle": -90,
                "y": 441,
                "word": "交易种类：[掉期]",
                "charInfo": [
                    {
                        "prob": 100,
                        "w": 17,
                        "h": 16,
                        "x": 100,
                        "y": 503,
                        "word": "交"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 16,
                        "x": 120,
                        "y": 503,
                        "word": "易"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 16,
                        "x": 136,
                        "y": 503,
                        "word": "种"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 16,
                        "x": 154,
                        "y": 503,
                        "word": "类"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 172,
                        "y": 503,
                        "word": "："
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 188,
                        "y": 503,
                        "word": "["
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 194,
                        "y": 503,
                        "word": "掉"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 16,
                        "x": 215,
                        "y": 503,
                        "word": "期"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 232,
                        "y": 503,
                        "word": "]"
                    }
                ],
                "direction": 0,
                "height": 140,
                "rowId": 7
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 101,
                        "y": 558
                    },
                    {
                        "x": 250,
                        "y": 560
                    },
                    {
                        "x": 250,
                        "y": 578
                    },
                    {
                        "x": 101,
                        "y": 576
                    }
                ],
                "width": 19,
                "x": 166,
                "angle": -88,
                "y": 493,
                "word": "Notional Quantity：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 102,
                        "y": 558,
                        "word": "N"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 116,
                        "y": 558,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 126,
                        "y": 558,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 138,
                        "y": 558,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 142,
                        "y": 558,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 147,
                        "y": 558,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 157,
                        "y": 558,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 166,
                        "y": 558,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 176,
                        "y": 559,
                        "word": "Q"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 192,
                        "y": 559,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 202,
                        "y": 559,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 214,
                        "y": 559,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 223,
                        "y": 559,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 228,
                        "y": 559,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 237,
                        "y": 560,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 240,
                        "y": 560,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 247,
                        "y": 560,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 149,
                "rowId": 8
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 481,
                        "y": 560
                    },
                    {
                        "x": 622,
                        "y": 560
                    },
                    {
                        "x": 622,
                        "y": 577
                    },
                    {
                        "x": 481,
                        "y": 577
                    }
                ],
                "width": 16,
                "x": 543,
                "angle": -90,
                "y": 497,
                "word": "42 metric tonnes",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 14,
                        "x": 482,
                        "y": 561,
                        "word": "4"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 496,
                        "y": 561,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 14,
                        "x": 510,
                        "y": 561,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 528,
                        "y": 561,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 14,
                        "x": 536,
                        "y": 561,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 544,
                        "y": 561,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 548,
                        "y": 561,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 552,
                        "y": 561,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 564,
                        "y": 561,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 572,
                        "y": 561,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 582,
                        "y": 561,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 592,
                        "y": 561,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 602,
                        "y": 561,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 611,
                        "y": 561,
                        "word": "s"
                    }
                ],
                "direction": 0,
                "height": 140,
                "rowId": 9
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 103,
                        "y": 593
                    },
                    {
                        "x": 184,
                        "y": 593
                    },
                    {
                        "x": 184,
                        "y": 611
                    },
                    {
                        "x": 103,
                        "y": 611
                    }
                ],
                "width": 18,
                "x": 134,
                "angle": -90,
                "y": 560,
                "word": "名义数量：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 103,
                        "y": 594,
                        "word": "名"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 122,
                        "y": 594,
                        "word": "义"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 16,
                        "x": 142,
                        "y": 594,
                        "word": "数"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 160,
                        "y": 594,
                        "word": "量"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 179,
                        "y": 594,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 81,
                "rowId": 10
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 481,
                        "y": 593
                    },
                    {
                        "x": 582,
                        "y": 593
                    },
                    {
                        "x": 582,
                        "y": 611
                    },
                    {
                        "x": 481,
                        "y": 611
                    }
                ],
                "width": 19,
                "x": 522,
                "angle": -90,
                "y": 551,
                "word": "42公吨√",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 482,
                        "y": 593,
                        "word": "4"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 493,
                        "y": 593,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 16,
                        "x": 507,
                        "y": 593,
                        "word": "公"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 16,
                        "x": 526,
                        "y": 593,
                        "word": "吨"
                    },
                    {
                        "prob": 98,
                        "w": 31,
                        "h": 16,
                        "x": 551,
                        "y": 593,
                        "word": "√"
                    }
                ],
                "direction": 0,
                "height": 102,
                "rowId": 11
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 99,
                        "y": 629
                    },
                    {
                        "x": 202,
                        "y": 629
                    },
                    {
                        "x": 202,
                        "y": 647
                    },
                    {
                        "x": 99,
                        "y": 647
                    }
                ],
                "width": 19,
                "x": 142,
                "angle": -90,
                "y": 586,
                "word": "Commodity：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 100,
                        "y": 629,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 116,
                        "y": 629,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 126,
                        "y": 629,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 142,
                        "y": 629,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 159,
                        "y": 629,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 168,
                        "y": 629,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 182,
                        "y": 629,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 185,
                        "y": 629,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 189,
                        "y": 629,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 196,
                        "y": 629,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 103,
                "rowId": 12
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 481,
                        "y": 629
                    },
                    {
                        "x": 571,
                        "y": 629
                    },
                    {
                        "x": 571,
                        "y": 651
                    },
                    {
                        "x": 481,
                        "y": 651
                    }
                ],
                "width": 22,
                "x": 515,
                "angle": -90,
                "y": 595,
                "word": "COBALT/",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 19,
                        "x": 482,
                        "y": 630,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 19,
                        "x": 498,
                        "y": 630,
                        "word": "O"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 19,
                        "x": 511,
                        "y": 630,
                        "word": "B"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 19,
                        "x": 523,
                        "y": 630,
                        "word": "A"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 19,
                        "x": 536,
                        "y": 630,
                        "word": "L"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 19,
                        "x": 547,
                        "y": 630,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 19,
                        "x": 560,
                        "y": 630,
                        "word": "/"
                    }
                ],
                "direction": 0,
                "height": 90,
                "rowId": 13
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 99,
                        "y": 662
                    },
                    {
                        "x": 148,
                        "y": 662
                    },
                    {
                        "x": 148,
                        "y": 680
                    },
                    {
                        "x": 99,
                        "y": 680
                    }
                ],
                "width": 19,
                "x": 115,
                "angle": -90,
                "y": 646,
                "word": "商品：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 102,
                        "y": 662,
                        "word": "商"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 121,
                        "y": 662,
                        "word": "品"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 139,
                        "y": 662,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 49,
                "rowId": 14
            },
            {
                "prob": 90,
                "pos": [
                    {
                        "x": 478,
                        "y": 662
                    },
                    {
                        "x": 503,
                        "y": 662
                    },
                    {
                        "x": 503,
                        "y": 683
                    },
                    {
                        "x": 478,
                        "y": 683
                    }
                ],
                "width": 20,
                "x": 481,
                "angle": -90,
                "y": 661,
                "word": "钴",
                "charInfo": [
                    {
                        "prob": 90,
                        "w": 19,
                        "h": 18,
                        "x": 481,
                        "y": 663,
                        "word": "钴"
                    }
                ],
                "direction": 0,
                "height": 24,
                "rowId": 15
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 101,
                        "y": 699
                    },
                    {
                        "x": 201,
                        "y": 699
                    },
                    {
                        "x": 201,
                        "y": 716
                    },
                    {
                        "x": 101,
                        "y": 716
                    }
                ],
                "width": 17,
                "x": 142,
                "angle": -90,
                "y": 657,
                "word": "Trade Date：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 101,
                        "y": 700,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 115,
                        "y": 700,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 121,
                        "y": 700,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 131,
                        "y": 700,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 141,
                        "y": 700,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 14,
                        "x": 155,
                        "y": 700,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 171,
                        "y": 700,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 180,
                        "y": 700,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 186,
                        "y": 700,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 196,
                        "y": 700,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 100,
                "rowId": 16
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 698
                    },
                    {
                        "x": 604,
                        "y": 698
                    },
                    {
                        "x": 604,
                        "y": 716
                    },
                    {
                        "x": 479,
                        "y": 716
                    }
                ],
                "width": 19,
                "x": 532,
                "angle": -90,
                "y": 645,
                "word": "Oct 14， 2022",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 16,
                        "x": 482,
                        "y": 699,
                        "word": "O"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 497,
                        "y": 699,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 507,
                        "y": 699,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 522,
                        "y": 699,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 533,
                        "y": 699,
                        "word": "4"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 543,
                        "y": 699,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 558,
                        "y": 699,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 571,
                        "y": 699,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 581,
                        "y": 699,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 592,
                        "y": 699,
                        "word": "2"
                    }
                ],
                "direction": 0,
                "height": 124,
                "rowId": 17
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 101,
                        "y": 732
                    },
                    {
                        "x": 166,
                        "y": 732
                    },
                    {
                        "x": 166,
                        "y": 751
                    },
                    {
                        "x": 101,
                        "y": 751
                    }
                ],
                "width": 18,
                "x": 125,
                "angle": -90,
                "y": 708,
                "word": "交易日：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 102,
                        "y": 732,
                        "word": "交"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 123,
                        "y": 732,
                        "word": "易"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 142,
                        "y": 732,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 158,
                        "y": 732,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 66,
                "rowId": 18
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 734
                    },
                    {
                        "x": 646,
                        "y": 732
                    },
                    {
                        "x": 647,
                        "y": 754
                    },
                    {
                        "x": 479,
                        "y": 756
                    }
                ],
                "width": 167,
                "x": 479,
                "angle": 0,
                "y": 734,
                "word": "2022年10月14日",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 482,
                        "y": 735,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 19,
                        "x": 495,
                        "y": 734,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 19,
                        "x": 504,
                        "y": 734,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 514,
                        "y": 734,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 21,
                        "h": 19,
                        "x": 527,
                        "y": 734,
                        "word": "年"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 562,
                        "y": 734,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 19,
                        "x": 569,
                        "y": 733,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 21,
                        "h": 19,
                        "x": 575,
                        "y": 733,
                        "word": "月"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 601,
                        "y": 733,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 19,
                        "x": 614,
                        "y": 733,
                        "word": "4"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 19,
                        "x": 630,
                        "y": 733,
                        "word": "日"
                    }
                ],
                "direction": 0,
                "height": 20,
                "rowId": 19
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 99,
                        "y": 767
                    },
                    {
                        "x": 224,
                        "y": 769
                    },
                    {
                        "x": 224,
                        "y": 787
                    },
                    {
                        "x": 99,
                        "y": 785
                    }
                ],
                "width": 17,
                "x": 153,
                "angle": -89,
                "y": 714,
                "word": "Effective Date：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 15,
                        "x": 102,
                        "y": 769,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 119,
                        "y": 769,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 121,
                        "y": 769,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 128,
                        "y": 769,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 138,
                        "y": 769,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 147,
                        "y": 769,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 153,
                        "y": 769,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 155,
                        "y": 769,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 166,
                        "y": 770,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 15,
                        "x": 179,
                        "y": 770,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 193,
                        "y": 770,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 202,
                        "y": 770,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 208,
                        "y": 770,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 219,
                        "y": 770,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 124,
                "rowId": 20
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 769
                    },
                    {
                        "x": 602,
                        "y": 769
                    },
                    {
                        "x": 602,
                        "y": 787
                    },
                    {
                        "x": 479,
                        "y": 787
                    }
                ],
                "width": 17,
                "x": 532,
                "angle": -90,
                "y": 716,
                "word": "Jun 01， 2023",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 482,
                        "y": 770,
                        "word": "J"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 492,
                        "y": 770,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 16,
                        "x": 501,
                        "y": 770,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 522,
                        "y": 770,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 534,
                        "y": 770,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 543,
                        "y": 770,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 557,
                        "y": 770,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 568,
                        "y": 770,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 579,
                        "y": 770,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 16,
                        "x": 590,
                        "y": 770,
                        "word": "3"
                    }
                ],
                "direction": 0,
                "height": 122,
                "rowId": 21
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 101,
                        "y": 801
                    },
                    {
                        "x": 166,
                        "y": 801
                    },
                    {
                        "x": 166,
                        "y": 820
                    },
                    {
                        "x": 101,
                        "y": 820
                    }
                ],
                "width": 18,
                "x": 125,
                "angle": -90,
                "y": 777,
                "word": "起始日：",
                "charInfo": [
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 102,
                        "y": 801,
                        "word": "起"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 121,
                        "y": 801,
                        "word": "始"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 142,
                        "y": 801,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 158,
                        "y": 801,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 66,
                "rowId": 22
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 803
                    },
                    {
                        "x": 647,
                        "y": 803
                    },
                    {
                        "x": 647,
                        "y": 823
                    },
                    {
                        "x": 479,
                        "y": 823
                    }
                ],
                "width": 20,
                "x": 553,
                "angle": -90,
                "y": 730,
                "word": "2023年06月01日",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 480,
                        "y": 804,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 495,
                        "y": 804,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 505,
                        "y": 804,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 515,
                        "y": 804,
                        "word": "3"
                    },
                    {
                        "prob": 99,
                        "w": 19,
                        "h": 18,
                        "x": 528,
                        "y": 804,
                        "word": "年"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 553,
                        "y": 804,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 565,
                        "y": 804,
                        "word": "6"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 578,
                        "y": 804,
                        "word": "月"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 603,
                        "y": 804,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 615,
                        "y": 804,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 18,
                        "x": 630,
                        "y": 804,
                        "word": "日"
                    }
                ],
                "direction": 0,
                "height": 167,
                "rowId": 23
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 99,
                        "y": 839
                    },
                    {
                        "x": 250,
                        "y": 839
                    },
                    {
                        "x": 250,
                        "y": 856
                    },
                    {
                        "x": 99,
                        "y": 856
                    }
                ],
                "width": 15,
                "x": 167,
                "angle": -89,
                "y": 771,
                "word": "Termination Date：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 14,
                        "x": 100,
                        "y": 840,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 114,
                        "y": 840,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 14,
                        "x": 124,
                        "y": 840,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 14,
                        "x": 130,
                        "y": 840,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 14,
                        "x": 146,
                        "y": 840,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 150,
                        "y": 840,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 160,
                        "y": 840,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 14,
                        "x": 170,
                        "y": 840,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 178,
                        "y": 840,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 180,
                        "y": 840,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 14,
                        "x": 190,
                        "y": 840,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 14,
                        "x": 204,
                        "y": 840,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 219,
                        "y": 840,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 231,
                        "y": 840,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 14,
                        "x": 233,
                        "y": 840,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 14,
                        "x": 243,
                        "y": 840,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 151,
                "rowId": 24
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 839
                    },
                    {
                        "x": 605,
                        "y": 839
                    },
                    {
                        "x": 605,
                        "y": 858
                    },
                    {
                        "x": 479,
                        "y": 858
                    }
                ],
                "width": 18,
                "x": 534,
                "angle": -90,
                "y": 786,
                "word": "Aug 31， 2023",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 480,
                        "y": 840,
                        "word": "A"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 493,
                        "y": 840,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 504,
                        "y": 840,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 524,
                        "y": 840,
                        "word": "3"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 535,
                        "y": 840,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 544,
                        "y": 840,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 560,
                        "y": 840,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 571,
                        "y": 840,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 16,
                        "x": 582,
                        "y": 840,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 593,
                        "y": 840,
                        "word": "3"
                    }
                ],
                "direction": 0,
                "height": 126,
                "rowId": 25
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 101,
                        "y": 872
                    },
                    {
                        "x": 156,
                        "y": 872
                    },
                    {
                        "x": 156,
                        "y": 890
                    },
                    {
                        "x": 101,
                        "y": 890
                    }
                ],
                "width": 17,
                "x": 119,
                "angle": -90,
                "y": 853,
                "word": "到期日",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 102,
                        "y": 872,
                        "word": "到"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 120,
                        "y": 872,
                        "word": "期"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 141,
                        "y": 872,
                        "word": "日"
                    }
                ],
                "direction": 0,
                "height": 54,
                "rowId": 26
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 874
                    },
                    {
                        "x": 643,
                        "y": 874
                    },
                    {
                        "x": 643,
                        "y": 894
                    },
                    {
                        "x": 479,
                        "y": 894
                    }
                ],
                "width": 19,
                "x": 552,
                "angle": -90,
                "y": 802,
                "word": "2023年08月31日",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 480,
                        "y": 875,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 495,
                        "y": 875,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 505,
                        "y": 875,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 515,
                        "y": 875,
                        "word": "3"
                    },
                    {
                        "prob": 100,
                        "w": 18,
                        "h": 18,
                        "x": 527,
                        "y": 875,
                        "word": "年"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 550,
                        "y": 875,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 562,
                        "y": 875,
                        "word": "8"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 577,
                        "y": 875,
                        "word": "月"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 600,
                        "y": 875,
                        "word": "3"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 612,
                        "y": 875,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 625,
                        "y": 875,
                        "word": "日"
                    }
                ],
                "direction": 0,
                "height": 163,
                "rowId": 27
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 99,
                        "y": 908
                    },
                    {
                        "x": 258,
                        "y": 908
                    },
                    {
                        "x": 258,
                        "y": 927
                    },
                    {
                        "x": 99,
                        "y": 927
                    }
                ],
                "width": 17,
                "x": 170,
                "angle": -89,
                "y": 837,
                "word": "Calculation Period：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 101,
                        "y": 909,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 114,
                        "y": 909,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 127,
                        "y": 909,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 129,
                        "y": 909,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 140,
                        "y": 909,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 15,
                        "x": 153,
                        "y": 909,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 157,
                        "y": 909,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 168,
                        "y": 909,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 170,
                        "y": 909,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 173,
                        "y": 909,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 183,
                        "y": 909,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 197,
                        "y": 909,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 15,
                        "x": 210,
                        "y": 909,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 221,
                        "y": 909,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 15,
                        "x": 229,
                        "y": 909,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 15,
                        "x": 231,
                        "y": 909,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 15,
                        "x": 244,
                        "y": 909,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 15,
                        "x": 252,
                        "y": 909,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 160,
                "rowId": 28
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 910
                    },
                    {
                        "x": 1023,
                        "y": 910
                    },
                    {
                        "x": 1023,
                        "y": 928
                    },
                    {
                        "x": 479,
                        "y": 928
                    }
                ],
                "width": 19,
                "x": 742,
                "angle": -90,
                "y": 647,
                "word": "Commencing on and including the Effective Date and ending on",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 480,
                        "y": 910,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 496,
                        "y": 910,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 506,
                        "y": 910,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 522,
                        "y": 910,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 537,
                        "y": 910,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 549,
                        "y": 910,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 565,
                        "y": 910,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 567,
                        "y": 910,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 572,
                        "y": 910,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 582,
                        "y": 910,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 596,
                        "y": 910,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 610,
                        "y": 910,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 624,
                        "y": 910,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 636,
                        "y": 910,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 648,
                        "y": 910,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 662,
                        "y": 910,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 669,
                        "y": 910,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 679,
                        "y": 910,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 691,
                        "y": 910,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 693,
                        "y": 910,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 702,
                        "y": 910,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 714,
                        "y": 910,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 717,
                        "y": 910,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 729,
                        "y": 910,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 747,
                        "y": 910,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 750,
                        "y": 910,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 759,
                        "y": 910,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 776,
                        "y": 910,
                        "word": "E"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 795,
                        "y": 910,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 797,
                        "y": 910,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 802,
                        "y": 910,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 811,
                        "y": 910,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 818,
                        "y": 910,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 826,
                        "y": 910,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 830,
                        "y": 910,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 837,
                        "y": 910,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 854,
                        "y": 910,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 868,
                        "y": 910,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 878,
                        "y": 910,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 885,
                        "y": 910,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 899,
                        "y": 910,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 911,
                        "y": 910,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 920,
                        "y": 910,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 937,
                        "y": 910,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 949,
                        "y": 910,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 958,
                        "y": 910,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 970,
                        "y": 910,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 972,
                        "y": 910,
                        "word": "n"
                    },
                    {
                        "prob": 100,
                        "w": 10,
                        "h": 16,
                        "x": 981,
                        "y": 910,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 997,
                        "y": 910,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 1009,
                        "y": 910,
                        "word": "n"
                    }
                ],
                "direction": 0,
                "height": 544,
                "rowId": 29
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 933
                    },
                    {
                        "x": 775,
                        "y": 933
                    },
                    {
                        "x": 775,
                        "y": 950
                    },
                    {
                        "x": 479,
                        "y": 950
                    }
                ],
                "width": 17,
                "x": 619,
                "angle": -90,
                "y": 794,
                "word": "and including the Termination Date.",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 480,
                        "y": 933,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 492,
                        "y": 933,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 504,
                        "y": 933,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 14,
                        "x": 515,
                        "y": 933,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 522,
                        "y": 933,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 532,
                        "y": 933,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 544,
                        "y": 933,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 546,
                        "y": 933,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 556,
                        "y": 933,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 567,
                        "y": 933,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 570,
                        "y": 933,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 582,
                        "y": 933,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 598,
                        "y": 933,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 600,
                        "y": 933,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 612,
                        "y": 933,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 14,
                        "x": 624,
                        "y": 933,
                        "word": "T"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 641,
                        "y": 933,
                        "word": "e"
                    },
                    {
                        "prob": 97,
                        "w": 1,
                        "h": 14,
                        "x": 653,
                        "y": 933,
                        "word": "r"
                    },
                    {
                        "prob": 98,
                        "w": 17,
                        "h": 14,
                        "x": 650,
                        "y": 933,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 671,
                        "y": 933,
                        "word": "i"
                    },
                    {
                        "prob": 100,
                        "w": 6,
                        "h": 14,
                        "x": 676,
                        "y": 933,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 686,
                        "y": 933,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 697,
                        "y": 933,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 702,
                        "y": 933,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 705,
                        "y": 933,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 716,
                        "y": 933,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 731,
                        "y": 933,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 745,
                        "y": 933,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 14,
                        "x": 754,
                        "y": 933,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 761,
                        "y": 933,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 14,
                        "x": 771,
                        "y": 933,
                        "word": "."
                    }
                ],
                "direction": 0,
                "height": 295,
                "rowId": 30
            },
            {
                "prob": 85,
                "pos": [
                    {
                        "x": 1165,
                        "y": 941
                    },
                    {
                        "x": 1178,
                        "y": 941
                    },
                    {
                        "x": 1178,
                        "y": 956
                    },
                    {
                        "x": 1165,
                        "y": 956
                    }
                ],
                "width": 15,
                "x": 1164,
                "angle": -90,
                "y": 943,
                "word": "么",
                "charInfo": [
                    {
                        "prob": 85,
                        "w": 15,
                        "h": 13,
                        "x": 1165,
                        "y": 941,
                        "word": "么"
                    }
                ],
                "direction": 0,
                "height": 12,
                "rowId": 52
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 99,
                        "y": 964
                    },
                    {
                        "x": 181,
                        "y": 966
                    },
                    {
                        "x": 181,
                        "y": 985
                    },
                    {
                        "x": 99,
                        "y": 982
                    }
                ],
                "width": 19,
                "x": 129,
                "angle": -88,
                "y": 932,
                "word": "计算期间",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 100,
                        "y": 964,
                        "word": "计"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 120,
                        "y": 964,
                        "word": "算"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 16,
                        "x": 140,
                        "y": 965,
                        "word": "期"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 158,
                        "y": 965,
                        "word": "间"
                    }
                ],
                "direction": 0,
                "height": 82,
                "rowId": 31
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 483,
                        "y": 966
                    },
                    {
                        "x": 962,
                        "y": 966
                    },
                    {
                        "x": 962,
                        "y": 984
                    },
                    {
                        "x": 483,
                        "y": 984
                    }
                ],
                "width": 19,
                "x": 713,
                "angle": -90,
                "y": 735,
                "word": "自起始日开始(含起始日)，到到期日结束(含到期日)。",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 484,
                        "y": 966,
                        "word": "自"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 500,
                        "y": 966,
                        "word": "起"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 519,
                        "y": 966,
                        "word": "始"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 541,
                        "y": 966,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 557,
                        "y": 966,
                        "word": "开"
                    },
                    {
                        "prob": 100,
                        "w": 17,
                        "h": 16,
                        "x": 576,
                        "y": 966,
                        "word": "始"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 605,
                        "y": 966,
                        "word": "("
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 614,
                        "y": 966,
                        "word": "含"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 633,
                        "y": 966,
                        "word": "起"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 654,
                        "y": 966,
                        "word": "始"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 673,
                        "y": 966,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 692,
                        "y": 966,
                        "word": ")"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 709,
                        "y": 966,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 728,
                        "y": 966,
                        "word": "到"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 747,
                        "y": 966,
                        "word": "到"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 766,
                        "y": 966,
                        "word": "期"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 787,
                        "y": 966,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 804,
                        "y": 966,
                        "word": "结"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 822,
                        "y": 966,
                        "word": "束"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 851,
                        "y": 966,
                        "word": "("
                    },
                    {
                        "prob": 100,
                        "w": 13,
                        "h": 16,
                        "x": 863,
                        "y": 966,
                        "word": "含"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 878,
                        "y": 966,
                        "word": "到"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 897,
                        "y": 966,
                        "word": "期"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 916,
                        "y": 966,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 935,
                        "y": 966,
                        "word": ")"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 952,
                        "y": 966,
                        "word": "。"
                    }
                ],
                "direction": 0,
                "height": 480,
                "rowId": 32
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 99,
                        "y": 1000
                    },
                    {
                        "x": 227,
                        "y": 1000
                    },
                    {
                        "x": 227,
                        "y": 1019
                    },
                    {
                        "x": 99,
                        "y": 1019
                    }
                ],
                "width": 18,
                "x": 154,
                "angle": -90,
                "y": 945,
                "word": "Payment Date：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 100,
                        "y": 1000,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 116,
                        "y": 1000,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 123,
                        "y": 1000,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 135,
                        "y": 1000,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 149,
                        "y": 1000,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 161,
                        "y": 1000,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 170,
                        "y": 1000,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 179,
                        "y": 1000,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 193,
                        "y": 1000,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 209,
                        "y": 1000,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 213,
                        "y": 1000,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 218,
                        "y": 1000,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 128,
                "rowId": 33
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 1002
                    },
                    {
                        "x": 1023,
                        "y": 1002
                    },
                    {
                        "x": 1023,
                        "y": 1020
                    },
                    {
                        "x": 479,
                        "y": 1020
                    }
                ],
                "width": 19,
                "x": 742,
                "angle": -90,
                "y": 739,
                "word": "10Oct 2023， subject to adjustment in accordance with the",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 487,
                        "y": 1002,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 489,
                        "y": 1002,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 511,
                        "y": 1002,
                        "word": "O"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 530,
                        "y": 1002,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 537,
                        "y": 1002,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 551,
                        "y": 1002,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 563,
                        "y": 1002,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 572,
                        "y": 1002,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 584,
                        "y": 1002,
                        "word": "3"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 594,
                        "y": 1002,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 610,
                        "y": 1002,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 620,
                        "y": 1002,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 631,
                        "y": 1002,
                        "word": "b"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 641,
                        "y": 1002,
                        "word": "j"
                    },
                    {
                        "prob": 100,
                        "w": 8,
                        "h": 16,
                        "x": 646,
                        "y": 1002,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 657,
                        "y": 1002,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 665,
                        "y": 1002,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 681,
                        "y": 1002,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 691,
                        "y": 1002,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 710,
                        "y": 1002,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 721,
                        "y": 1002,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 736,
                        "y": 1002,
                        "word": "j"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 740,
                        "y": 1002,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 745,
                        "y": 1002,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 755,
                        "y": 1002,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 762,
                        "y": 1002,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 776,
                        "y": 1002,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 788,
                        "y": 1002,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 797,
                        "y": 1002,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 816,
                        "y": 1002,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 818,
                        "y": 1002,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 840,
                        "y": 1002,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 852,
                        "y": 1002,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 861,
                        "y": 1002,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 871,
                        "y": 1002,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 880,
                        "y": 1002,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 887,
                        "y": 1002,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 897,
                        "y": 1002,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 906,
                        "y": 1002,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 918,
                        "y": 1002,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 927,
                        "y": 1002,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 946,
                        "y": 1002,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 963,
                        "y": 1002,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 968,
                        "y": 1002,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 972,
                        "y": 1002,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 990,
                        "y": 1002,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 1000,
                        "y": 1002,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 1009,
                        "y": 1002,
                        "word": "e"
                    }
                ],
                "direction": 0,
                "height": 544,
                "rowId": 34
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 1023
                    },
                    {
                        "x": 857,
                        "y": 1025
                    },
                    {
                        "x": 857,
                        "y": 1045
                    },
                    {
                        "x": 479,
                        "y": 1042
                    }
                ],
                "width": 19,
                "x": 659,
                "angle": -89,
                "y": 845,
                "word": "Mod iied Following Business Day Convention.",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 17,
                        "x": 480,
                        "y": 1024,
                        "word": "M"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 497,
                        "y": 1024,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 510,
                        "y": 1024,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 520,
                        "y": 1024,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 530,
                        "y": 1024,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 532,
                        "y": 1024,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 542,
                        "y": 1024,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 555,
                        "y": 1024,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 567,
                        "y": 1024,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 580,
                        "y": 1024,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 587,
                        "y": 1024,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 592,
                        "y": 1024,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 597,
                        "y": 1024,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 612,
                        "y": 1024,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 614,
                        "y": 1025,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 624,
                        "y": 1025,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 639,
                        "y": 1025,
                        "word": "B"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 652,
                        "y": 1025,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 664,
                        "y": 1025,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 674,
                        "y": 1025,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 677,
                        "y": 1025,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 689,
                        "y": 1025,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 699,
                        "y": 1025,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 707,
                        "y": 1025,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 17,
                        "x": 719,
                        "y": 1025,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 736,
                        "y": 1025,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 744,
                        "y": 1025,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 17,
                        "x": 756,
                        "y": 1026,
                        "word": "C"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 774,
                        "y": 1026,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 784,
                        "y": 1026,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 794,
                        "y": 1026,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 803,
                        "y": 1026,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 813,
                        "y": 1026,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 825,
                        "y": 1026,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 17,
                        "x": 830,
                        "y": 1026,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 833,
                        "y": 1026,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 843,
                        "y": 1026,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 853,
                        "y": 1026,
                        "word": "."
                    }
                ],
                "direction": 0,
                "height": 378,
                "rowId": 35
            },
            {
                "prob": 96,
                "pos": [
                    {
                        "x": 1159,
                        "y": 974
                    },
                    {
                        "x": 1176,
                        "y": 974
                    },
                    {
                        "x": 1176,
                        "y": 1062
                    },
                    {
                        "x": 1159,
                        "y": 1062
                    }
                ],
                "width": 88,
                "x": 1124,
                "angle": -90,
                "y": 1010,
                "word": "32",
                "charInfo": [
                    {
                        "prob": 94,
                        "w": 11,
                        "h": 13,
                        "x": 1161,
                        "y": 1010,
                        "word": "3"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 11,
                        "x": 1161,
                        "y": 1029,
                        "word": "2"
                    }
                ],
                "direction": 1,
                "height": 16,
                "rowId": 54
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 101,
                        "y": 1056
                    },
                    {
                        "x": 165,
                        "y": 1056
                    },
                    {
                        "x": 165,
                        "y": 1076
                    },
                    {
                        "x": 101,
                        "y": 1076
                    }
                ],
                "width": 20,
                "x": 122,
                "angle": -90,
                "y": 1034,
                "word": "支付日：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 17,
                        "x": 102,
                        "y": 1057,
                        "word": "支"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 17,
                        "x": 120,
                        "y": 1057,
                        "word": "付"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 17,
                        "x": 141,
                        "y": 1057,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 17,
                        "x": 156,
                        "y": 1057,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 64,
                "rowId": 36
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 478,
                        "y": 1058
                    },
                    {
                        "x": 954,
                        "y": 1058
                    },
                    {
                        "x": 954,
                        "y": 1078
                    },
                    {
                        "x": 478,
                        "y": 1078
                    }
                ],
                "width": 20,
                "x": 706,
                "angle": -90,
                "y": 829,
                "word": "2023年10月10日，按经修正的下一个营业日准则调整。",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 479,
                        "y": 1059,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 491,
                        "y": 1059,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 504,
                        "y": 1059,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 514,
                        "y": 1059,
                        "word": "3"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 18,
                        "x": 526,
                        "y": 1059,
                        "word": "年"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 18,
                        "x": 554,
                        "y": 1059,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 559,
                        "y": 1059,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 574,
                        "y": 1059,
                        "word": "月"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 599,
                        "y": 1059,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 609,
                        "y": 1059,
                        "word": "0"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 626,
                        "y": 1059,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 644,
                        "y": 1059,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 661,
                        "y": 1059,
                        "word": "按"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 681,
                        "y": 1059,
                        "word": "经"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 701,
                        "y": 1059,
                        "word": "修"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 718,
                        "y": 1059,
                        "word": "正"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 738,
                        "y": 1059,
                        "word": "的"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 756,
                        "y": 1059,
                        "word": "下"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 776,
                        "y": 1059,
                        "word": "一"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 796,
                        "y": 1059,
                        "word": "个"
                    },
                    {
                        "prob": 100,
                        "w": 13,
                        "h": 18,
                        "x": 813,
                        "y": 1059,
                        "word": "营"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 831,
                        "y": 1059,
                        "word": "业"
                    },
                    {
                        "prob": 100,
                        "w": 11,
                        "h": 18,
                        "x": 853,
                        "y": 1059,
                        "word": "日"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 868,
                        "y": 1059,
                        "word": "准"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 888,
                        "y": 1059,
                        "word": "则"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 906,
                        "y": 1059,
                        "word": "调"
                    },
                    {
                        "prob": 100,
                        "w": 13,
                        "h": 18,
                        "x": 926,
                        "y": 1059,
                        "word": "整"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 943,
                        "y": 1059,
                        "word": "。"
                    }
                ],
                "direction": 0,
                "height": 478,
                "rowId": 37
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 99,
                        "y": 1127
                    },
                    {
                        "x": 229,
                        "y": 1127
                    },
                    {
                        "x": 229,
                        "y": 1144
                    },
                    {
                        "x": 99,
                        "y": 1144
                    }
                ],
                "width": 17,
                "x": 155,
                "angle": -90,
                "y": 1070,
                "word": "Fixed Amount",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 99,
                        "y": 1128,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 14,
                        "x": 112,
                        "y": 1128,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 118,
                        "y": 1128,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 127,
                        "y": 1128,
                        "word": "e"
                    },
                    {
                        "prob": 100,
                        "w": 8,
                        "h": 14,
                        "x": 140,
                        "y": 1128,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 14,
                        "x": 153,
                        "y": 1128,
                        "word": "A"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 14,
                        "x": 168,
                        "y": 1128,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 14,
                        "x": 184,
                        "y": 1128,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 197,
                        "y": 1128,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 14,
                        "x": 208,
                        "y": 1128,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 14,
                        "x": 219,
                        "y": 1128,
                        "word": "t"
                    }
                ],
                "direction": 0,
                "height": 129,
                "rowId": 38
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 98,
                        "y": 1159
                    },
                    {
                        "x": 180,
                        "y": 1162
                    },
                    {
                        "x": 179,
                        "y": 1181
                    },
                    {
                        "x": 97,
                        "y": 1179
                    }
                ],
                "width": 19,
                "x": 128,
                "angle": -88,
                "y": 1128,
                "word": "固定金额",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 17,
                        "x": 102,
                        "y": 1160,
                        "word": "固"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 17,
                        "x": 120,
                        "y": 1160,
                        "word": "定"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 17,
                        "x": 140,
                        "y": 1161,
                        "word": "金"
                    },
                    {
                        "prob": 99,
                        "w": 19,
                        "h": 17,
                        "x": 158,
                        "y": 1161,
                        "word": "额"
                    }
                ],
                "direction": 0,
                "height": 82,
                "rowId": 39
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 132,
                        "y": 1197
                    },
                    {
                        "x": 260,
                        "y": 1197
                    },
                    {
                        "x": 260,
                        "y": 1216
                    },
                    {
                        "x": 132,
                        "y": 1216
                    }
                ],
                "width": 18,
                "x": 186,
                "angle": -90,
                "y": 1142,
                "word": "Fixed Amount：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 134,
                        "y": 1198,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 146,
                        "y": 1198,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 150,
                        "y": 1198,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 160,
                        "y": 1198,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 170,
                        "y": 1198,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 16,
                        "x": 182,
                        "y": 1198,
                        "word": "A"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 16,
                        "x": 198,
                        "y": 1198,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 214,
                        "y": 1198,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 224,
                        "y": 1198,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 233,
                        "y": 1198,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 243,
                        "y": 1198,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 253,
                        "y": 1198,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 127,
                "rowId": 40
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 1197
                    },
                    {
                        "x": 1023,
                        "y": 1197
                    },
                    {
                        "x": 1023,
                        "y": 1218
                    },
                    {
                        "x": 479,
                        "y": 1218
                    }
                ],
                "width": 20,
                "x": 741,
                "angle": -90,
                "y": 936,
                "word": "Party B shall pay to Party A on the relevant Payment Date an",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 480,
                        "y": 1198,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 495,
                        "y": 1198,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 18,
                        "x": 510,
                        "y": 1198,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 512,
                        "y": 1198,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 517,
                        "y": 1198,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 535,
                        "y": 1198,
                        "word": "B"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 552,
                        "y": 1198,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 565,
                        "y": 1198,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 575,
                        "y": 1198,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 18,
                        "x": 587,
                        "y": 1198,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 592,
                        "y": 1198,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 597,
                        "y": 1198,
                        "word": "p"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 18,
                        "x": 612,
                        "y": 1198,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 620,
                        "y": 1198,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 635,
                        "y": 1198,
                        "word": "t"
                    },
                    {
                        "prob": 100,
                        "w": 8,
                        "h": 18,
                        "x": 645,
                        "y": 1198,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 657,
                        "y": 1198,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 672,
                        "y": 1198,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 18,
                        "x": 682,
                        "y": 1198,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 692,
                        "y": 1198,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 695,
                        "y": 1198,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 710,
                        "y": 1198,
                        "word": "A"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 735,
                        "y": 1198,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 747,
                        "y": 1198,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 767,
                        "y": 1198,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 770,
                        "y": 1198,
                        "word": "h"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 780,
                        "y": 1198,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 18,
                        "x": 797,
                        "y": 1198,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 18,
                        "x": 805,
                        "y": 1198,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 817,
                        "y": 1198,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 822,
                        "y": 1198,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 827,
                        "y": 1198,
                        "word": "v"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 842,
                        "y": 1198,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 847,
                        "y": 1198,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 857,
                        "y": 1198,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 870,
                        "y": 1198,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 882,
                        "y": 1198,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 892,
                        "y": 1198,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 902,
                        "y": 1198,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 18,
                        "x": 920,
                        "y": 1198,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 927,
                        "y": 1198,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 937,
                        "y": 1198,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 11,
                        "h": 18,
                        "x": 947,
                        "y": 1198,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 18,
                        "x": 962,
                        "y": 1198,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 976,
                        "y": 1198,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 979,
                        "y": 1198,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 999,
                        "y": 1198,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 18,
                        "x": 1011,
                        "y": 1198,
                        "word": "n"
                    }
                ],
                "direction": 0,
                "height": 544,
                "rowId": 41
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 478,
                        "y": 1219
                    },
                    {
                        "x": 799,
                        "y": 1218
                    },
                    {
                        "x": 800,
                        "y": 1237
                    },
                    {
                        "x": 478,
                        "y": 1239
                    }
                ],
                "width": 322,
                "x": 476,
                "angle": 0,
                "y": 1218,
                "word": "amount in USD determined as follows：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 480,
                        "y": 1221,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 491,
                        "y": 1221,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 508,
                        "y": 1221,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 519,
                        "y": 1221,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 529,
                        "y": 1221,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 538,
                        "y": 1221,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 551,
                        "y": 1221,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 553,
                        "y": 1221,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 16,
                        "x": 568,
                        "y": 1221,
                        "word": "U"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 583,
                        "y": 1221,
                        "word": "S"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 594,
                        "y": 1221,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 612,
                        "y": 1221,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 625,
                        "y": 1220,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 633,
                        "y": 1220,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 640,
                        "y": 1220,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 650,
                        "y": 1220,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 16,
                        "x": 657,
                        "y": 1220,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 674,
                        "y": 1220,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 676,
                        "y": 1220,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 685,
                        "y": 1220,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 696,
                        "y": 1220,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 711,
                        "y": 1220,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 722,
                        "y": 1220,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 16,
                        "x": 735,
                        "y": 1220,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 743,
                        "y": 1220,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 754,
                        "y": 1220,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 757,
                        "y": 1220,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 759,
                        "y": 1220,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 770,
                        "y": 1220,
                        "word": "w"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 783,
                        "y": 1220,
                        "word": "s"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 16,
                        "x": 792,
                        "y": 1220,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 19,
                "rowId": 42
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 1253
                    },
                    {
                        "x": 749,
                        "y": 1253
                    },
                    {
                        "x": 749,
                        "y": 1272
                    },
                    {
                        "x": 479,
                        "y": 1272
                    }
                ],
                "width": 18,
                "x": 604,
                "angle": -90,
                "y": 1128,
                "word": "Notional Quantity*Fixed Price；",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 480,
                        "y": 1253,
                        "word": "N"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 496,
                        "y": 1253,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 508,
                        "y": 1253,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 515,
                        "y": 1253,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 520,
                        "y": 1253,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 525,
                        "y": 1253,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 537,
                        "y": 1253,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 546,
                        "y": 1253,
                        "word": "l"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 16,
                        "x": 556,
                        "y": 1253,
                        "word": "Q"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 572,
                        "y": 1253,
                        "word": "u"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 582,
                        "y": 1253,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 593,
                        "y": 1253,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 605,
                        "y": 1253,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 612,
                        "y": 1253,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 615,
                        "y": 1253,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 619,
                        "y": 1253,
                        "word": "y"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 631,
                        "y": 1253,
                        "word": "*"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 645,
                        "y": 1253,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 657,
                        "y": 1253,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 664,
                        "y": 1253,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 671,
                        "y": 1253,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 683,
                        "y": 1253,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 697,
                        "y": 1253,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 712,
                        "y": 1253,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 719,
                        "y": 1253,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 721,
                        "y": 1253,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 733,
                        "y": 1253,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 742,
                        "y": 1253,
                        "word": "；"
                    }
                ],
                "direction": 0,
                "height": 269,
                "rowId": 43
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 481,
                        "y": 1286
                    },
                    {
                        "x": 985,
                        "y": 1286
                    },
                    {
                        "x": 985,
                        "y": 1306
                    },
                    {
                        "x": 481,
                        "y": 1306
                    }
                ],
                "width": 20,
                "x": 722,
                "angle": -90,
                "y": 1044,
                "word": "乙方须在相关支付日向甲方支付按下列方式决定的美元金额：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 482,
                        "y": 1287,
                        "word": "乙"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 499,
                        "y": 1287,
                        "word": "方"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 519,
                        "y": 1287,
                        "word": "须"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 537,
                        "y": 1287,
                        "word": "在"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 557,
                        "y": 1287,
                        "word": "相"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 577,
                        "y": 1287,
                        "word": "关"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 597,
                        "y": 1287,
                        "word": "支"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 18,
                        "x": 614,
                        "y": 1287,
                        "word": "付"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 634,
                        "y": 1287,
                        "word": "日"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 654,
                        "y": 1287,
                        "word": "向"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 674,
                        "y": 1287,
                        "word": "甲"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 692,
                        "y": 1287,
                        "word": "方"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 712,
                        "y": 1287,
                        "word": "支"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 732,
                        "y": 1287,
                        "word": "付"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 749,
                        "y": 1287,
                        "word": "按"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 769,
                        "y": 1287,
                        "word": "下"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 789,
                        "y": 1287,
                        "word": "列"
                    },
                    {
                        "prob": 100,
                        "w": 16,
                        "h": 18,
                        "x": 807,
                        "y": 1287,
                        "word": "方"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 827,
                        "y": 1287,
                        "word": "式"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 844,
                        "y": 1287,
                        "word": "决"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 864,
                        "y": 1287,
                        "word": "定"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 884,
                        "y": 1287,
                        "word": "的"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 902,
                        "y": 1287,
                        "word": "美"
                    },
                    {
                        "prob": 99,
                        "w": 13,
                        "h": 18,
                        "x": 922,
                        "y": 1287,
                        "word": "元"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 939,
                        "y": 1287,
                        "word": "金"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 18,
                        "x": 959,
                        "y": 1287,
                        "word": "额"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 18,
                        "x": 979,
                        "y": 1287,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 505,
                "rowId": 44
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 132,
                        "y": 1304
                    },
                    {
                        "x": 222,
                        "y": 1304
                    },
                    {
                        "x": 222,
                        "y": 1323
                    },
                    {
                        "x": 132,
                        "y": 1323
                    }
                ],
                "width": 18,
                "x": 168,
                "angle": -90,
                "y": 1268,
                "word": "固定金额：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 16,
                        "x": 135,
                        "y": 1304,
                        "word": "固"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 151,
                        "y": 1304,
                        "word": "定"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 172,
                        "y": 1304,
                        "word": "金"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 191,
                        "y": 1304,
                        "word": "额"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 213,
                        "y": 1304,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 90,
                "rowId": 45
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 1324
                    },
                    {
                        "x": 660,
                        "y": 1324
                    },
                    {
                        "x": 660,
                        "y": 1342
                    },
                    {
                        "x": 479,
                        "y": 1342
                    }
                ],
                "width": 18,
                "x": 560,
                "angle": -90,
                "y": 1244,
                "word": "名义数量*固定价格；",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 480,
                        "y": 1324,
                        "word": "名"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 499,
                        "y": 1324,
                        "word": "义"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 16,
                        "x": 518,
                        "y": 1324,
                        "word": "数"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 16,
                        "x": 539,
                        "y": 1324,
                        "word": "量"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 561,
                        "y": 1324,
                        "word": "*"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 575,
                        "y": 1324,
                        "word": "固"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 16,
                        "x": 594,
                        "y": 1324,
                        "word": "定"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 16,
                        "x": 613,
                        "y": 1324,
                        "word": "价"
                    },
                    {
                        "prob": 100,
                        "w": 15,
                        "h": 16,
                        "x": 634,
                        "y": 1324,
                        "word": "格"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 653,
                        "y": 1324,
                        "word": "；"
                    }
                ],
                "direction": 0,
                "height": 180,
                "rowId": 46
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 132,
                        "y": 1372
                    },
                    {
                        "x": 232,
                        "y": 1374
                    },
                    {
                        "x": 232,
                        "y": 1392
                    },
                    {
                        "x": 132,
                        "y": 1390
                    }
                ],
                "width": 19,
                "x": 171,
                "angle": -88,
                "y": 1330,
                "word": "Fixed Price：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 132,
                        "y": 1372,
                        "word": "F"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 146,
                        "y": 1373,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 148,
                        "y": 1373,
                        "word": "x"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 158,
                        "y": 1373,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 168,
                        "y": 1373,
                        "word": "d"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 184,
                        "y": 1374,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 16,
                        "x": 196,
                        "y": 1374,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 0,
                        "h": 16,
                        "x": 204,
                        "y": 1374,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 206,
                        "y": 1374,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 218,
                        "y": 1374,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 2,
                        "h": 16,
                        "x": 227,
                        "y": 1375,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 100,
                "rowId": 47
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 479,
                        "y": 1373
                    },
                    {
                        "x": 755,
                        "y": 1373
                    },
                    {
                        "x": 755,
                        "y": 1392
                    },
                    {
                        "x": 479,
                        "y": 1392
                    }
                ],
                "width": 18,
                "x": 608,
                "angle": -90,
                "y": 1245,
                "word": "USD 57， 871.34permetrictonne",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 480,
                        "y": 1374,
                        "word": "U"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 493,
                        "y": 1374,
                        "word": "S"
                    },
                    {
                        "prob": 99,
                        "w": 12,
                        "h": 16,
                        "x": 507,
                        "y": 1374,
                        "word": "D"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 525,
                        "y": 1374,
                        "word": "5"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 538,
                        "y": 1374,
                        "word": "7"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 550,
                        "y": 1374,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 552,
                        "y": 1374,
                        "word": "8"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 563,
                        "y": 1374,
                        "word": "7"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 574,
                        "y": 1374,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 16,
                        "x": 583,
                        "y": 1374,
                        "word": "."
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 590,
                        "y": 1374,
                        "word": "3"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 601,
                        "y": 1374,
                        "word": "4"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 617,
                        "y": 1374,
                        "word": "p"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 628,
                        "y": 1374,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 640,
                        "y": 1374,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 17,
                        "h": 16,
                        "x": 649,
                        "y": 1374,
                        "word": "m"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 667,
                        "y": 1374,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 680,
                        "y": 1374,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 685,
                        "y": 1374,
                        "word": "r"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 16,
                        "x": 689,
                        "y": 1374,
                        "word": "i"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 691,
                        "y": 1374,
                        "word": "c"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 704,
                        "y": 1374,
                        "word": "t"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 713,
                        "y": 1374,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 5,
                        "h": 16,
                        "x": 722,
                        "y": 1374,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 16,
                        "x": 731,
                        "y": 1374,
                        "word": "n"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 16,
                        "x": 742,
                        "y": 1374,
                        "word": "e"
                    }
                ],
                "direction": 0,
                "height": 276,
                "rowId": 48
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 134,
                        "y": 1408
                    },
                    {
                        "x": 220,
                        "y": 1408
                    },
                    {
                        "x": 220,
                        "y": 1426
                    },
                    {
                        "x": 134,
                        "y": 1426
                    }
                ],
                "width": 19,
                "x": 167,
                "angle": -90,
                "y": 1373,
                "word": "固定价格：",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 16,
                        "x": 138,
                        "y": 1408,
                        "word": "固"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 155,
                        "y": 1408,
                        "word": "定"
                    },
                    {
                        "prob": 99,
                        "w": 16,
                        "h": 16,
                        "x": 175,
                        "y": 1408,
                        "word": "价"
                    },
                    {
                        "prob": 99,
                        "w": 14,
                        "h": 16,
                        "x": 194,
                        "y": 1408,
                        "word": "格"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 16,
                        "x": 212,
                        "y": 1408,
                        "word": "："
                    }
                ],
                "direction": 0,
                "height": 87,
                "rowId": 49
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 478,
                        "y": 1408
                    },
                    {
                        "x": 658,
                        "y": 1408
                    },
                    {
                        "x": 658,
                        "y": 1428
                    },
                    {
                        "x": 478,
                        "y": 1428
                    }
                ],
                "width": 20,
                "x": 557,
                "angle": -90,
                "y": 1327,
                "word": "57，871.34美元/公吨",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 479,
                        "y": 1408,
                        "word": "5"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 493,
                        "y": 1408,
                        "word": "7"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 507,
                        "y": 1408,
                        "word": "，"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 512,
                        "y": 1408,
                        "word": "8"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 517,
                        "y": 1408,
                        "word": "7"
                    },
                    {
                        "prob": 99,
                        "w": 4,
                        "h": 18,
                        "x": 537,
                        "y": 1408,
                        "word": "1"
                    },
                    {
                        "prob": 99,
                        "w": 1,
                        "h": 18,
                        "x": 539,
                        "y": 1408,
                        "word": "."
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 545,
                        "y": 1408,
                        "word": "3"
                    },
                    {
                        "prob": 99,
                        "w": 9,
                        "h": 18,
                        "x": 556,
                        "y": 1408,
                        "word": "4"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 18,
                        "x": 569,
                        "y": 1408,
                        "word": "美"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 18,
                        "x": 588,
                        "y": 1408,
                        "word": "元"
                    },
                    {
                        "prob": 99,
                        "w": 7,
                        "h": 18,
                        "x": 608,
                        "y": 1408,
                        "word": "/"
                    },
                    {
                        "prob": 99,
                        "w": 15,
                        "h": 18,
                        "x": 619,
                        "y": 1408,
                        "word": "公"
                    },
                    {
                        "prob": 99,
                        "w": 18,
                        "h": 18,
                        "x": 638,
                        "y": 1408,
                        "word": "吨"
                    }
                ],
                "direction": 0,
                "height": 181,
                "rowId": 50
            },
            {
                "prob": 99,
                "pos": [
                    {
                        "x": 550,
                        "y": 1567
                    },
                    {
                        "x": 641,
                        "y": 1565
                    },
                    {
                        "x": 642,
                        "y": 1584
                    },
                    {
                        "x": 550,
                        "y": 1587
                    }
                ],
                "width": 92,
                "x": 549,
                "angle": -1,
                "y": 1566,
                "word": "Page 2 of 7",
                "charInfo": [
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 551,
                        "y": 1569,
                        "word": "P"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 568,
                        "y": 1568,
                        "word": "a"
                    },
                    {
                        "prob": 99,
                        "w": 3,
                        "h": 17,
                        "x": 575,
                        "y": 1568,
                        "word": "g"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 582,
                        "y": 1568,
                        "word": "e"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 594,
                        "y": 1568,
                        "word": "2"
                    },
                    {
                        "prob": 99,
                        "w": 10,
                        "h": 17,
                        "x": 608,
                        "y": 1567,
                        "word": "o"
                    },
                    {
                        "prob": 99,
                        "w": 6,
                        "h": 17,
                        "x": 621,
                        "y": 1567,
                        "word": "f"
                    },
                    {
                        "prob": 99,
                        "w": 8,
                        "h": 17,
                        "x": 628,
                        "y": 1567,
                        "word": "7"
                    }
                ],
                "direction": 0,
                "height": 19,
                "rowId": 51
            }
        ],
        "height": 1684
    },
    "requestId": "b72bf3f2-9086-43f6-a9f3-bb3128f41a0b"
}
# 调用函数进行图片识别对比
if __name__ == '__main__':
    # 读取要对比的文件
    #originPDF =r'F:\kq\OCR 测试\3.CITI_Cobalt.pdf'  # 文档原件
    #contrastPDF = r'F:\kq\OCR 测试\3.CITI_zss模板.pdf'  # 文档扫描件
    #resultRoot =r'F:\kq\OCR 测试\20221214'  # 输出目录
    originPDF = r'F:\kq\文本比对\6.CCB汇率交易申请书template.pdf'  # 文档原件
    contrastPDF = r'F:\kq\文本比对\6.建行：汇率交易申请书.pdf'  # 文档扫描件
    resultRoot = r'F:\kq\20230116'  # 输出目录



    resultRoot = initRoot(resultRoot)  # 清空输出目录
    originImageNum, originImagePath = conver_img(originPDF, resultRoot)  # 将原件pdf文档转换为图像
    contrastImageNum, contrastImagePath = conver_img(contrastPDF, resultRoot)  # 将扫描件pdf文档转换为图像
    if originImageNum != contrastImageNum:
        print('文档页数不一致！请查看', resultRoot)
    else :
        resultRoot = os.path.join(resultRoot, '对比结果')  # 创建输出结果目录
        os.makedirs(resultRoot)  # 创建输出目录
        for i in range(originImageNum):
            originFile = os.path.join(originImagePath, str(i) + '.png')
            contrastFile = os.path.join(contrastImagePath, str(i) + '.png')
            imageDiff(resultRoot, originFile, contrastFile, i + 1)  # 图像对比
        print('执行成功，请查看输出目录：', resultRoot)
