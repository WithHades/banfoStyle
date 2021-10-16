import logging
import os.path
import pickle
import shutil
import threading
import time

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QDropEvent, QDragEnterEvent, QStandardItem

import mainWindow
from PyQt5.QtWidgets import QApplication, QDialog
from moviepy.editor import *

from conf import BackgroundMusic, BaiduButton, DoutulaButton

from utils import getUuid, getBaiDuAudio, getBaiduImgPath, getDoutulaImgPath, resizeImg


class genVideoThread(QThread):
    """
    生成视频线程类
    """
    signal = pyqtSignal(str)

    def __init__(self, sections: list, materialName: str, fileName: str) -> None:
        """
        初始化几个参数
        :param sections: 字幕以及图片信息
        :param materialName: 素材路径
        :param fileName: 保存视频名称
        """
        super().__init__()
        self.sections = sections
        self.materialName = materialName
        self.fileName = fileName

    def __del__(self):
        self.wait()

    def run(self):
        screensize = (800, 600)
        videoClips = []
        for section in self.sections:
            imgPath, text = section[0], section[1]
            text = text.strip(r'\\')
            text = "\\".join([x.replace(r'\n', '\n') for x in text])
            texts = text.strip().split('\n')
            if imgPath is None:
                imgPath = 'background.png'

            # gif用到,用于标记当前字幕对应的gif从哪儿开始
            index = 0
            if imgPath.endswith('.gif'):
                # 首先计算一下当前所有语音时间长度
                clip = VideoFileClip(imgPath)
                clip = clip.loop()
            else:
                clip = ImageClip(imgPath)

            # 设置一下图片/gif大小
            width, height = clip.size
            width, height = resizeImg(width, height)
            clip.resize((width, height))

            # 考虑到每张表情包可能对应多句字幕
            for txt in texts:
                txtClip = TextClip(txt, color='white', font='STKaiti', kerning=5, fontsize=50, align='South')
                # 合成语音
                txtAudio = getBaiDuAudio(txt, os.path.join(self.materialName, 'audio'))
                if txtAudio is None:
                    logging.error('get the audio of {} failed!'.format(txt))
                    continue
                txtAudio = AudioFileClip(txtAudio)
                # 表情包视频与字幕融合

                cvc = CompositeVideoClip([clip.set_position(('center', 'center')).subclip(index, txtAudio.duration),
                                          txtClip.set_position(('center', 0.85), relative=True)],
                                         size=screensize).subclip(0, txtAudio.duration)
                index += txtAudio.duration
                # 添加配音
                cvc = cvc.set_audio(txtAudio)
                videoClips.append(cvc)
        finalClip = concatenate_videoclips(videoClips)
        # 获取原视频声音
        audio = finalClip.audio

        # 整体背景音乐
        audioClip = AudioFileClip(BackgroundMusic)
        if audioClip.duration > finalClip.duration:
            audioClip = audioClip.subclip(0, audio.duration)
        elif audioClip.duration < finalClip.duration:
            audioClip = afx.audio_loop(audioClip, duration=audio.duration)

        # 声音结合起来
        audio = CompositeAudioClip([audio, audioClip])
        finalClip = finalClip.set_audio(audio)
        fileName = os.path.join('out', self.fileName)
        finalClip.write_videofile(fileName, fps=25, codec='mpeg4')
        self.signal.emit(fileName)


class addImgThread(QThread):
    """
    获取网络表情包线程类
    """
    signal = pyqtSignal(str)

    def __init__(self, mText: str, mButton: int) -> None:
        """
        初始化获取网络表情包线程类
        :param mText: 搜索关键词
        :param mButton: 采用哪个搜索引擎
        """
        super().__init__()
        self.text = mText
        self.button = mButton

    def __del__(self):
        self.wait()

    def run(self):
        if self.button == BaiduButton:
            for path in getBaiduImgPath(self.text):
                self.signal.emit(path)

        if self.button == DoutulaButton:
            for path in getDoutulaImgPath(self.text):
                self.signal.emit(path)


class MainDialog(QDialog):
    def __init__(self, parent=None):
        super(QDialog, self).__init__(parent)

        # 当前指向的句子
        self.nowPos = None
        # 获取表情包线程句柄
        self.subThread = None
        # 已经设定好的句子以及表情包,三元组(图片路径, 文案, 时间戳),时间戳一旦生成不再修改,主要用于区分文案并生成对应的图片路径
        self.sections = []
        # 接收拖放对象
        self.setAcceptDrops(True)
        self.fileName = None
        self.materialName = None

        # lock of save and read the bfs file
        self.lock = threading.Lock()

        self.ui = mainWindow.Ui_MainWindow()
        self.ui.setupUi(self)

        # start save thread
        self.saveThread = threading.Thread(target=self.save)
        self.saveThread.start()

    # 每隔5秒保存一次工程信息
    def save(self) -> None:
        time.sleep(5)
        # 窗口存在则一直保存
        while self.ui.windowIsVisible():
            self.lock.acquire()
            if len(self.sections) <= 0:
                self.lock.release()
                time.sleep(5)
                continue
            data = dict()
            data['nowPos'] = self.nowPos
            data['sections'] = self.sections
            data['fileName'] = self.fileName
            data['materialName'] = self.materialName
            fileName = os.path.join(self.materialName, self.fileName[:self.fileName.rfind('.')] + '.bfs')
            with open(fileName, 'wb') as f:
                pickle.dump(data, f)
            self.lock.release()
            time.sleep(5)


    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        拖放事件
        :param event: QDragEnterEvent
        :return: None
        """
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """
        拖放事件,主要处理.bfs工程文件, .txt文案文件, .gif/.png等图片文件
        :param event: 拖放对象事件
        :return: None
        """
        filePathList = event.mimeData().text()
        filePath = filePathList.split('\n')[0].replace('file:///', '', 1)
        # 说明是加载的工程文件
        if filePath.endswith('.bfs'):
            self.loadBfs(filePath)
            return

        # 说明加载的是文案文件
        if filePath.endswith('.txt'):
            if self.fileName is None:
                self.ui.msgBox('请先设置工程目录!')
                return
            self.loadText(True, filePath)
            return

        # 其他情况应该是加载的图片文件,先判断是不是gif/图片
        if not filePath.endswith('.gif'):
            # 通过加载文件来判断是否为图片,不是则返回
            try:
                ImageClip(filePath)
            except:
                return
        self.loadPic(filePath)


    def loadBfs(self, filePath: str) -> None:
        """
        加载工程文件
        :param filePath: 工程文件路径
        :return: None
        """
        if len(self.sections) > 0:
            if not self.ui.msgBox('导入工程文件将清空当前工作内容,可能导致部分内容丢失,是否继续?', True):
                return

        # 需要在material目录下有对应的文件夹,没有的禁止载入
        fileName = os.path.basename(filePath).replace('.bfs', '')
        if not os.path.exists(os.path.join('material', fileName)):
            self.ui.msgBox('未找到对应的素材文件夹!')
            return

        with open(filePath, 'rb') as f:
            data = pickle.load(f)

        self.lock.acquire()
        self.nowPos = data['nowPos']
        self.sections = data['sections']

        # 检查资源文件是否都存在
        for section in self.sections:
            if section[0] is not None and not os.path.exists(section[0]):
                self.nowPos = None
                self.sections = []
                self.ui.msgBox('对应的素材缺失!')
                self.lock.release()
                return

        self.fileName = data['fileName']
        self.ui.setFileName(self.fileName)
        self.materialName = data['materialName']

        # 将sections的内容填充到表格
        self.ui.delAllRow()
        for section in self.sections:
            self.ui.addRow(section[1])
        if self.nowPos is not None:
            self.ui.setSubTileText(self.sections[self.nowPos][1])
            self.ui.setSearchText(self.sections[self.nowPos][1])

            imgPath = self.sections[self.nowPos][0]
            if imgPath is None:
                self.ui.delVideoImg()
            else:
                self.ui.changeVideoImg(imgPath)
        else:
            self.ui.delVideoImg()
        self.lock.release()

    def loadPic(self, imgPath: str) -> None:
        """
        加载拖放进来的图片文件
        :param imgPath: 图片文件路径
        :return: None
        """
        if self.nowPos is None:
            # 没有工程内容则忽略该次拖入文件
            self.ui.msgBox('请先设置字幕内容!')
            return

        self.ui.changeVideoImg(imgPath)

        imgBaseName = os.path.basename(imgPath)
        suffix = imgBaseName[imgBaseName.rfind('.') + 1:]
        uuid = self.sections[self.nowPos][2]
        newPath = '{}.{}'.format(uuid, suffix)
        newPath = os.path.join(os.path.join(self.materialName, 'img'), newPath)
        shutil.copyfile(imgPath, newPath)
        # 保存图片与字幕信息
        self.sections[self.nowPos] = [newPath, self.ui.getSubtitle(), uuid]
        self.ui.setRowText(self.nowPos, self.ui.getSubtitle())

    def setFilename(self) -> None:
        """
        设置文件名
        :return: None
        """
        # 加锁,禁止保存或者载入工程文件
        self.lock.acquire()
        fileName = self.ui.getFileName()
        materialName = os.path.join('material', fileName[:fileName.rfind('.')])

        # 当前工作区没内容,说明是新建的工程,新建的工程的名字不能和之前重复
        if len(self.sections) <= 0 and os.path.exists(materialName):
            self.ui.msgBox('文件名已存在,请更换名字或加载之前缓存!')
            self.lock.release()
            return

        self.fileName = fileName

        # 文件名并未更改,可能是未修改或者只修改了后缀名,都可以忽略
        if self.materialName == materialName:
            self.ui.msgBox('设置工程文件夹成功!')
            self.lock.release()
            return
        # 当前工作区无内容,说明是新建的工程,需要新建文件夹
        if len(self.sections) <= 0:
            os.makedirs(os.path.join(materialName, 'audio'))
            os.makedirs(os.path.join(materialName, 'img'))
            self.ui.msgBox('新建工程文件夹成功!')
        else:
            # 当前工作区有内容,说明工程已经存在,需要对所有数据进行重命名
            self.changeFileName(self.materialName, materialName)
            self.ui.msgBox('重命名工程文件夹成功!')
        self.materialName = materialName
        self.lock.release()

    def changeFileName(self, oldMaterialName: str, materialName: str) -> None:
        """
        修改了文件名需要对文件夹等全部进行修改
        :param oldMaterialName: 旧的素材文件夹名
        :param materialName: 新的素材文件夹名
        :return:
        """
        # 对sections里面包含的图片信息的地址进行修改
        for section in self.sections:
            if section[0] is None:
                continue
            imgBaseName = os.path.basename(section[0])
            newPath = os.path.join(os.path.join(materialName, 'img'), imgBaseName)
            section[0] = newPath

        # 更改文件夹名字
        os.rename(oldMaterialName, materialName)

    def setSubtitleInfo(self) -> None:
        """
        设置上一句/下一句对应的字幕以及图片信息
        :return: None
        """
        self.ui.setSubTileText(self.sections[self.nowPos][1])
        self.ui.setSearchText(self.sections[self.nowPos][1])
        # 如果已经设置好了表情包,显示出来;否则就清空
        imgPath = self.sections[self.nowPos][0]
        if imgPath is None:
            self.ui.delVideoImg()
        else:
            self.ui.changeVideoImg(imgPath)

    def last(self) -> None:
        """
        上一句,加载上一句字幕与图片
        :return: None
        """
        if len(self.sections) <= 0:
            self.ui.msgBox('当前工作区暂无内容!')
            return

        # 计算当前应该到达的光标
        if self.nowPos is None:
            self.nowPos = 1
        else:
            # 保存下一句的字幕信息
            self.sections[self.nowPos][1] = self.ui.getSubtitle()
            self.ui.setRowText(self.nowPos, self.ui.getSubtitle())

        self.nowPos = self.nowPos - 1 if self.nowPos > 0 else len(self.sections) - 1
        self.setSubtitleInfo()

    def next(self) -> None:
        """
        下一句,加载下一句字幕与图片
        :return: None
        """
        if len(self.sections) <= 0:
            self.ui.msgBox('当前工作区暂无内容!')
            return

        if self.nowPos is None:
            self.nowPos = -1
        else:
            # 保存上一句的字幕信息
            self.sections[self.nowPos][1] = self.ui.getSubtitle()
            self.ui.setRowText(self.nowPos, self.ui.getSubtitle())

        self.nowPos = self.nowPos + 1 if self.nowPos < len(self.sections) - 1 else 0
        self.setSubtitleInfo()

    def changeThePicText(self, text: str) -> None:
        """
        视频字幕实时更改
        :param text: 字幕信息
        :return: None
        """
        if len(self.sections) <= 0:
            return
        self.ui.setVideoText(text)
        self.sections[self.nowPos][1] = text
        self.ui.setRowText(self.nowPos, text)

    def previewImg(self, path: str) -> None:
        """
        将网络表情包加载预览以供选择
        :param path: 网络表情包路径
        :return: None
        """
        self.ui.addImg(path)

    def search(self, button: int) -> None:
        """
        搜索表情包,button代表了不同的搜索引擎
        :param button: 来自哪个按钮,代表了不同的搜索引擎
        :return: None
        """
        if len(self.sections) <= 0 or self.ui.getSearchText() == '':
            self.ui.msgBox('工作区暂无内容或未输入搜索文字!')
            return
        if self.subThread is not None:
            self.subThread.terminate()
            while self.subThread.isRunning() and not self.subThread.isFinished():
                time.sleep(0.1)
        # 清空当前的所有表情包图片
        self.ui.delImg()
        self.subThread = addImgThread(self.ui.getSearchText(), button)
        self.subThread.signal.connect(self.previewImg)
        self.subThread.start()

    def imgClicked(self, index: int) -> None:
        """
        表情包点击回调函数,将选好的表情包加载到视频预览区
        :param index: 选好的表情包索引
        :return: None
        """
        if len(self.sections) <= 0:
            self.ui.msgBox('工作区无内容!')
            return
        if self.nowPos is None:
            self.ui.msgBox('暂未选择文案与字幕!')
            return
        imgPath = self.ui.getImgPathByIndex(index)
        self.ui.changeVideoImg(imgPath)
        # 将表情包复制到material目录
        imgBaseName = os.path.basename(imgPath)
        suffix = imgBaseName[imgBaseName.rfind('.') + 1:]
        uuid = self.sections[self.nowPos][2]
        newPath = '{}.{}'.format(uuid, suffix)
        newPath = os.path.join(os.path.join(self.materialName, 'img'), newPath)
        shutil.copyfile(imgPath, newPath)
        # 保存图片与字幕信息
        self.sections[self.nowPos] = [newPath, self.ui.getSubtitle(), uuid]
        self.ui.setRowText(self.nowPos, self.ui.getSubtitle())

    def genVideo(self) -> None:
        """
        开始生成视频
        :return: None
        """
        if len(self.sections) <= 0:
            self.ui.msgBox('工作区无内容!')
            return
        gvt = genVideoThread(self.sections, self.materialName, self.fileName)
        gvt.signal.connect(self.genVideoFinished)
        gvt.start()

    def genVideoFinished(self, fileName: str) -> None:
        """
        视频生成完成回调函数
        :param fileName: 生成的视频路径
        :return: None
        """
        self.ui.msgBox('生成完毕!位置:{}'.format(fileName))

    def loadText(self, drag=False, fileName: str=None) -> None:
        """
        文件浏览器回调函数/同时支持拖放导入文案解析
        :param drag: 是否是拖放导入的
        :param fileName: 拖放进来的文件名
        :return: None
        """
        if self.fileName is None:
            self.ui.msgBox('请先设置工程目录!')
            return
        if len(self.sections) > 0 and not self.ui.msgBox('当前导入会覆盖工作区内容,不可撤销!是否继续?', True):
            return
        self.ui.delAllRow()
        if not drag:
            fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, '选择文案', os.getcwd(), 'Text Files (*.txt)')
        if fileName is not None and not os.path.exists(fileName):
            self.ui.msgBox('未选择文件!')
            return
        with open(fileName) as f:
            data = f.read()
        self.sections = list()
        for text in data.split('\n'):
            if text == '':
                continue
            text = text.strip()
            self.ui.addRow(text)
            self.sections.append([None, text, getUuid()])
        self.ui.msgBox('导入完成!')

    def addFrontText(self) -> None:
        """
        在当前选中的表格单元前面增加一行空白行
        :return: None
        """
        if len(self.sections) <= 0:
            if self.fileName is not None:
                index = 0
            else:
                self.ui.msgBox('请设置文件名后再添加!')
                return
        else:
            index = self.ui.getCurrentSelected()
            if index == -1:
                self.ui.msgBox('未选中表格!')
                return

        if self.nowPos is not None and self.nowPos >= index:
            self.nowPos += 1

        self.ui.insertRow(index)
        self.sections.insert(index, [None, '', getUuid()])

    def addBehindText(self) -> None:
        """
        在当前选中的表格单元后面增加一行空白行
        :return: None
        """
        if len(self.sections) <= 0:
            if self.fileName is not None:
                index = -1
            else:
                self.ui.msgBox('请设置文件名后再添加!')
                return
        else:
            index = self.ui.getCurrentSelected()
            if index == -1:
                self.ui.msgBox('未选中表格!')
                return

        if self.nowPos is not None and self.nowPos > index:
            self.nowPos += 1

        self.ui.insertRow(index + 1)
        self.sections.insert(index + 1, [None, '', getUuid()])

    def delText(self) -> None:
        """
        删除该行
        :return: None
        """
        if len(self.sections) <= 0:
            self.ui.msgBox('请先创建工程或输入文案!')
            return
        index = self.ui.getCurrentSelected()
        if index == -1:
            self.ui.msgBox('未选中表格!')
            return

        # 如果删除了当前预览位置的文案
        if self.nowPos is not None and self.nowPos == index:
            # 加载下一句文案
            self.next()

        # 如果在当前位置之前删除了一个文案,那么当前位置-1
        if self.nowPos is not None and self.nowPos >= index:
            self.nowPos -= 1

        self.ui.delRow(index)
        del self.sections[index]

    def exportText(self) -> None:
        """
        导出文案内容
        :return: None
        """
        if len(self.sections) <= 0:
            self.ui.msgBox('当前工作区没有内容!')
            return
        texts = ''
        for section in self.sections:
            texts += section[1] + '\n'

        path = os.path.join(self.materialName, 'work.txt')
        with open(path, 'w+') as f:
            f.write(texts)
        self.ui.msgBox('导出文案成功!位置:{}'.format(path))

    def tableItemChange(self, item: QStandardItem) -> None:
        """
        文案内容被修改时,同步到sections
        :param item: 被修改的表格item
        :return:
        """
        if len(self.sections) >= item.row():
            self.sections[item.row()][1] = item.text()
            # 如果当前单句字幕正好是修改的单元格部分,则修改的内容同步修改到单句字幕编辑处. 需要排除由于单句字幕修改造成的表格修改的情况
            if self.nowPos is not None and self.nowPos == item.row() and self.ui.getSubtitle() != item.text():
                self.ui.setSubTileText(item.text())
                self.ui.setSearchText(item.text())

    def jumpToIndex(self) -> None:
        """
        跳转到指定的文案
        :return: None
        """
        if self.nowPos is not None and self.ui.getCurrentSelected() != -1:
            # 保存上一句的字幕信息
            self.sections[self.nowPos][1] = self.ui.getSubtitle()
            self.ui.setRowText(self.nowPos, self.ui.getSubtitle())
        self.nowPos = self.ui.getCurrentSelected()
        self.setSubtitleInfo()


if __name__ == '__main__':
    if os.path.exists('tmp'):
        shutil.rmtree('tmp')
        os.mkdir('tmp')
    if not os.path.exists('out'):
        os.mkdir('out')
    myapp = QApplication(sys.argv)
    myDlg = MainDialog()
    myDlg.show()
    sys.exit(myapp.exec_())
