import base64
import hashlib
import json
import logging
import os.path
import pickle
import shutil
import threading
import time
from urllib.parse import quote

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal

from bs4 import BeautifulSoup

import mainWindow
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
import requests
from moviepy.editor import *

from conf import backgroundMusic, BaiduButton, DoutulaButton


# 利用百度语音合成进行配音
from utils import getUuid


def getBaiDuAudio(text, filePath):
    # 生成文件名
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    fileName = md5.hexdigest() + '.mp3'
    fileName = os.path.join(filePath, fileName)
    # 文件已经存在的话直接返回
    if os.path.exists(fileName):
        return fileName

    url = 'https://cloud.baidu.com/aidemo'
    data = 'type=tns&per=4105&spd=8&pit=7&vol=5&aue=6&tex=' + quote(text)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    res = requests.post(url, data=data, headers=headers, verify=False)
    if res.status_code != 200:
        return None
    res = json.loads(res.text)
    if res['msg'] != 'success':
        return None
    data = res['data'].replace('data:audio/x-mpeg;base64,', '')
    if ',' in data:
        data = data[:data.find(',')]
    data = base64.b64decode(data)
    with open(fileName, 'wb') as f:
        f.write(data)
    return fileName


# 生成视频线程
class genVideoThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, sections, path, fileName):
        super().__init__()
        self.sections = sections
        self.path = path
        self.fileName = fileName

    def __del__(self):
        self.wait()

    def run(self):
        screensize = (800, 600)
        videoClips = []
        for imgPath, text in self.sections:
            texts = text.strip().split('\n')
            if imgPath is None:
                imgPath = 'background.png'
            # TODO
            # 优化gif显示问题
            duration_time = 2
            if imgPath.endswith('.gif'):
                clip = VideoFileClip(imgPath)
                duration_time = clip.duration / len(texts)
            else:
                clip = ImageClip(imgPath)

            # 考虑到每张表情包可能对应多句字幕
            for txt in texts:
                txtClip = TextClip(txt, color='white', font='STKaiti', kerning=5, fontsize=50, align='South')
                # 合成语音
                txtAudio = getBaiDuAudio(txt, os.path.join(self.path, 'audio'))
                if txtAudio is None:
                    logging.error('get the audio of {} failed!'.format(txt))
                    continue
                txtAudio = AudioFileClip(txtAudio)
                # 表情包视频与字幕融合
                cvc = CompositeVideoClip([clip.set_position(('center', 'center')),
                                          txtClip.set_position(('center', 0.85), relative=True)],
                                         size=screensize).subclip(0, txtAudio.duration)
                # 添加配音
                cvc = cvc.set_audio(txtAudio)
                videoClips.append(cvc)
        finalClip = concatenate_videoclips(videoClips)
        # 获取原视频声音
        audio = finalClip.audio

        # 整体背景音乐
        audioClip = AudioFileClip(backgroundMusic)
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


# 获取网络表情包线程
class addImgThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, mText, mButton):
        super().__init__()
        self.text = mText
        self.button = mButton

    def __del__(self):
        self.wait()

    def run(self):
        if self.button == BaiduButton:
            # 百度图片地址解码函数
            def decodeBaiduImg(objUrl):
                res = ''
                c = ['_z2C$q', '_z&e3B', 'AzdH3F']
                d = {'w': 'a',
                     'k': 'b',
                     'v': 'c',
                     '1': 'd',
                     'j': 'e',
                     'u': 'f',
                     '2': 'g',
                     'i': 'h',
                     't': 'i',
                     '3': 'j',
                     'h': 'k',
                     's': 'l',
                     '4': 'm',
                     'g': 'n',
                     '5': 'o',
                     'r': 'p',
                     'q': 'q',
                     '6': 'r',
                     'f': 's',
                     'p': 't',
                     '7': 'u',
                     'e': 'v',
                     'o': 'w',
                     '8': '1',
                     'd': '2',
                     'n': '3',
                     '9': '4',
                     'c': '5',
                     'm': '6',
                     '0': '7',
                     'b': '8',
                     'l': '9',
                     'a': '0',
                     '_z2C$q': ':',
                     '_z&e3B': '.',
                     'AzdH3F': '/'}
                for m in c:
                    objUrl = objUrl.replace(m, d[m])
                for char in objUrl:
                    char = d[char] if char in d else char
                    res = res + char
                return res

            url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&logid=8763701186511659178&ipn=rj&ct=201326592&is=' \
                  '&fp=result&queryWord={0}&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=0&hd=&latest=&copyright=&word={0}' \
                  '&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&nojc=&acjsonfr=click&pn=0&rn=30&itg=1' \
                  '&gsm=3c&1634043752626='
            url = url.format(self.text)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'}
            res = requests.get(url, headers=headers, verify=False)
            if res.status_code != 200:
                return
            jsonData = json.loads(res.text)
            if 'data' not in jsonData:
                return
            data = jsonData['data']
            for img in data:
                imgUrl = ''
                if 'objURL' in img:
                    imgUrl = decodeBaiduImg(img['objURL'])
                elif 'middleURL' in img:
                    imgUrl = img['middleURL']
                elif 'thumbURL' in img:
                    imgUrl = img['thumbURL']
                elif imgUrl == '':
                    return
                if 'is_gif' in img and img['is_gif'] == 1:
                    is_gif = 1
                else:
                    is_gif = 0
                res = requests.get(imgUrl)
                if res.status_code != 200:
                    continue
                md5 = hashlib.md5()
                md5.update(res.content)
                fileName = md5.hexdigest() + '.gif' if is_gif else md5.hexdigest() + '.png'
                path = os.path.join('tmp', fileName)
                with open(path, 'wb') as f:
                    f.write(res.content)
                self.signal.emit(path)

        if self.button == DoutulaButton:
            url = 'https://www.doutula.com/search?keyword=' + self.text
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'}
            res = requests.get(url, headers=headers)
            if res.status_code != 200:
                return
            soup = BeautifulSoup(res.text, 'html.parser')
            randomPics = soup.find_all('a', attrs={'class': 'col-xs-6 col-md-2'})
            for pic in randomPics:
                x = pic.find('img', attrs={'referrerpolicy': 'no-referrer'})
                imgUrl = x['data-original']
                res = requests.get(imgUrl)
                if res.status_code != 200:
                    continue
                path = os.path.join('tmp', imgUrl[imgUrl.rfind('/') + 1:])
                with open(path, 'wb') as f:
                    f.write(res.content)
                self.signal.emit(path)


class MainDialog(QDialog):
    def __init__(self, parent=None):
        super(QDialog, self).__init__(parent)
        self.ui = mainWindow.Ui_MainWindow()
        self.ui.setupUi(self)
        # 当前指向的句子
        self.nowPos = None
        # 所有的句子
        self.allSentence = []
        # 获取表情包线程句柄
        self.subThread = None
        # 已经设定好的句子以及表情包,三元组(图片路径, 文案, 时间戳),时间戳一旦生成不再修改,主要用于区分文案并生成对应的图片路径
        self.sections = None
        # 接收拖放对象
        self.setAcceptDrops(True)

        self.fileName = None
        self.materialName = None
        self.oldMaterialName = None

        # lock of save and read the bfs file
        self.lock = threading.Lock()

        # start save thread
        self.saveThread = threading.Thread(target=self.save)
        self.saveThread.start()

    # 每隔5秒保存一次工程信息
    def save(self):
        # 窗口存在则一直保存
        while self.ui.centralwidget.isVisible():
            self.lock.acquire()
            if len(self.allSentence) <= 0:
                self.lock.release()
                time.sleep(5)
                continue
            data = dict()
            data['nowPos'] = self.nowPos
            data['sections'] = self.sections
            data['fileName'] = self.fileName
            data['allSentence'] = self.allSentence
            data['materialName'] = self.materialName
            data['oldMaterialName'] = self.oldMaterialName
            data['allText'] = self.ui.allText.toPlainText()
            fileName = os.path.join(self.materialName, self.fileName[:self.fileName.rfind('.')] + '.bfs')
            with open(fileName, 'wb') as f:
                pickle.dump(data, f)
            self.lock.release()
            time.sleep(5)

    # 拖放事件
    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.accept()
        else:
            e.ignore()

    # 拖放事件
    def dropEvent(self, e):
        filePathList = e.mimeData().text()
        filePath = filePathList.split('\n')[0]
        filePath = filePath.replace('file:///', '', 1)
        # 说明是加载的工程文件
        if filePath.endswith('.bfs'):


        # 说明加载的是文案文件
        if filePath.endswith('.txt'):
            if self.fileName is None:
                self.ui.msgBox('请先设置工程目录!')
                return
            self.loadText(True, filePath)
            return

        # 其他情况是加载的图片文件
        imgPath = filePath
        if not imgPath.endswith('.gif'):
            # 通过加载文件来判断是否为图片,不是则返回
            try:
                ImageClip(imgPath)
            except:
                return
        if self.nowPos is None:
            # 没有工程内容则忽略该次拖入文件
            QtWidgets.QMessageBox.information(self, '提示', '请先新建工程', QMessageBox.Ok)
            return
        self.ui.changeVideoImg(path=imgPath)
        self.sections[self.nowPos] = (imgPath, self.ui.singleText.text())

        # 将表情包复制到到material目录
        imgBaseName = os.path.basename(imgPath)
        newPath = '{}.{}'.format(self.nowPos, imgBaseName[imgBaseName.rfind('.') + 1:])
        newPath = os.path.join(os.path.join(self.materialName, 'img'), newPath)
        shutil.copyfile(imgPath, newPath)
        # 保存图片与字幕信息
        self.sections[self.nowPos] = (newPath, self.ui.singleText.text())


    def loadBfs(self, filePath: str) -> None:
        """
        加载工程文件
        :param filePath: 工程文件路径
        :return: None
        """
        if self.sections is not None and len(self.sections) > 0:
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
            for data in self.sections:
                if data[0] is not None and not os.path.exists(data[0]):
                    self.nowPos = None
                    self.sections = None
                    self.ui.msgBox('对应的素材缺失!')
                    self.lock.release()
                    return

            self.fileName = data['fileName']
            self.ui.setFileName(self.fileName)
            self.materialName = data['materialName']

            # 将sections的内容填充到表格
            self.ui.delAllRow()
            for data in self.sections:
                self.ui.addRow(data[1])

            self.ui.singleText.setText(self.sections[self.nowPos][1])
            self.ui.searchText.setText(self.sections[self.nowPos][1])
            imgPath = self.sections[self.nowPos][0]
            if imgPath is not None:
                self.ui.changeVideoImg(path=imgPath)
            else:
                self.ui.delVideoImg()
            self.lock.release()
        return


    def setFilename(self) -> None:
        """
        设置文件名
        :return: None
        """
        # 加锁,禁止保存或者载入工程文件
        self.lock.acquire()
        fileName = self.ui.filenName.text()
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
            os.makedirs(os.path.join(self.materialName, 'audio'))
            os.makedirs(os.path.join(self.materialName, 'img'))
            self.ui.msgBox('新建工程文件夹成功!')
        else:
            # 当前工作区有内容,说明工程已经存在,需要对所有数据进行重命名
            self.changeFileName(self.materialName, materialName)
            self.materialName = materialName
            self.ui.msgBox('重命名工程文件夹成功!')
        self.lock.release()

    def changeFileName(self, oldMaterialName: str, materialName: str) -> None:
        """
        修改了文件名需要对文件夹等全部进行修改
        :param oldMaterialName: 旧的素材文件夹名
        :param materialName: 新的素材文件夹名
        :return:
        """
        # 对sections里面包含的图片信息的地址进行修改
        for data in self.sections:
            if data[0] is None:
                continue
            imgBaseName = os.path.basename(data[0])
            newPath = os.path.join(os.path.join(materialName, 'img'), imgBaseName)
            data[0] = newPath

        # 更改文件夹名字
        os.rename(oldMaterialName, materialName)

    def setSubtitleInfo(self) -> None:
        """
        设置上一句/下一句对应的字幕以及图片信息
        :return: None
        """
        self.ui.singleText.setText(self.sections[self.nowPos][1])
        self.ui.singleText.home(False)
        self.ui.searchText.setText(self.sections[self.nowPos][1])
        self.ui.searchText.home(False)
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

        self.nowPos = self.nowPos - 1 if self.nowPos > -1 else len(self.sections) - 1
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

        self.nowPos = self.nowPos + 1 if self.nowPos < len(self.sections) else 0
        self.setSubtitleInfo()

    def changeThePicText(self, text: str) -> None:
        """
        视频字幕实时更改
        :param text: 字幕信息
        :return: None
        """
        self.ui.setVideoText(text)

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
        if self.sections is not None and not self.ui.msgBox('当前导入会覆盖工作区内容,不可撤销!是否继续?', True):
            return
        self.ui.delAllRow()
        if not drag:
            fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, '选择文案', os.getcwd(), 'Text Files (*.txt)')
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
        if self.sections is None:
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
        self.ui.insertRow(index)
        self.sections.insert(index + 1, [None, "", getUuid()])

    def addBehindText(self) -> None:
        """
        在当前选中的表格单元后面增加一行空白行
        :return: None
        """
        if self.sections is None:
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
        self.ui.insertRow(index + 1)
        self.sections.insert(index + 1, [None, "", getUuid()])

    def delText(self) -> None:
        """
        删除该行
        :return: None
        """
        if self.sections is None:
            self.ui.msgBox('请先创建工程或输入文案!')
        index = self.ui.getCurrentSelected()
        if index == -1:
            self.ui.msgBox('未选中表格!')
            return
        self.ui.delRow(index)
        self.sections.pop(index)



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
