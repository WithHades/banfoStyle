import base64
import hashlib
import json
import logging
import os.path
import shutil
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
def getBaiDuAudio(text, filePath):
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

    md5 = hashlib.md5()
    md5.update(data)
    fileName = md5.hexdigest() + '.mp3'
    fileName = os.path.join(filePath, fileName)
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
        # 已经设定好的句子以及表情包
        self.sections = []
        # 接收拖放对象
        self.setAcceptDrops(True)

        self.materialName = None
        self.oldMaterialName = None

    # 拖放事件
    def dragEnterEvent(self, e):
        if e.mimeData().hasText():
            e.accept()
        else:
            e.ignore()

    # 拖放事件
    def dropEvent(self, e):
        if self.nowPos is None:
            return
        filePathList = e.mimeData().text()
        filePath = filePathList.split('\n')[0]
        imgPath = filePath.replace('file:///', '', 1)

        self.ui.changeVideoImg(path=imgPath)
        self.sections[self.nowPos] = (imgPath, self.ui.singleText.text())

        # 将表情包复制到到material目录
        imgBaseName = os.path.basename(imgPath)
        newPath = '{}.{}'.format(self.nowPos, imgBaseName[imgBaseName.rfind('.') + 1:])
        newPath = os.path.join(os.path.join(self.materialName, 'img'), newPath)
        shutil.copyfile(imgPath, newPath)
        # 保存图片与字幕信息
        self.sections[self.nowPos] = (newPath, self.ui.singleText.text())

    # 设置文件名
    def setFilename(self):
        fileName = self.ui.filenName.text()
        materialName = os.path.join('material', fileName[:fileName.rfind('.')])

        # 当前工作区没内容，说明是新建的工程，新建的工程的名字不能和之前重复
        if len(self.allSentence) <= 0 and os.path.exists(materialName):
            QtWidgets.QMessageBox.information(self, '提示', '文件名已存在，请更换名字或加载之前缓存！', QMessageBox.Ok)
            return

        self.fileName = fileName
        self.oldMaterialName = self.materialName
        self.materialName = materialName

        # 文件名并未更改
        if self.oldMaterialName == self.materialName:
            return


        # 当前工作区无内容，说明是新建的工程，需要新建文件夹
        if len(self.allSentence) <= 0 and self.ui.allText.isReadOnly() is True:
            os.makedirs(os.path.join(self.materialName, 'audio'))
            os.makedirs(os.path.join(self.materialName, 'img'))
            # 工作区允许编辑
            self.ui.allText.setReadOnly(False)
        else:
            # 当前工作区有内容，说明工程已经存在，需要对所有数据进行重命名
            self.changeFileName()

    # 修改了文件名需要对文件夹等全部进行修改
    def changeFileName(self):
        # 对sections的内容进行修改
        for index, data in enumerate(self.sections):
            imgPath, text = data
            imgBaseName = os.path.basename(imgPath)
            newPath = os.path.join(os.path.join(self.materialName, 'img'), imgBaseName)
            self.sections[index] = (newPath, text)
        # 更改文件夹名字
        os.rename(self.oldMaterialName, self.materialName)

    # 上一句
    def last(self):
        if len(self.allSentence) <= 0 and not self.editFinished():
            return
        if self.nowPos is None:
            self.nowPos = 0
        else:
            self.nowPos = self.nowPos - 1
            if self.nowPos == -1:
                self.nowPos = len(self.allSentence) - 1
        self.ui.singleText.setText(self.allSentence[self.nowPos])
        self.ui.singleText.home(False)
        self.ui.searchText.setText(self.allSentence[self.nowPos])
        self.ui.searchText.home(False)
        # 如果已经设置好了,显示出来;否则就清空
        imgPath, _ = self.sections[self.nowPos]
        if imgPath is not None:
            self.ui.changeVideoImg(path=imgPath)
        else:
            self.ui.delVideoImg()

    # 下一句,详情同上一句
    def next(self):
        if len(self.allSentence) <= 0 and not self.editFinished():
            return
        if self.nowPos is None:
            self.nowPos = -1
        self.nowPos = self.nowPos + 1
        if self.nowPos >= len(self.allSentence):
            self.nowPos = 0
        self.ui.singleText.setText(self.allSentence[self.nowPos])
        self.ui.singleText.home(False)
        self.ui.searchText.setText(self.allSentence[self.nowPos])
        self.ui.searchText.home(False)
        imgPath, _ = self.sections[self.nowPos]
        if imgPath is not None:
            self.ui.changeVideoImg(path=imgPath)
        else:
            self.ui.delVideoImg()

    # 视频字幕实时更改
    def changeThePicText(self, text):
        self.ui.videoText.setText(text)

    # 文案编辑完毕, 分割并加载
    def editFinished(self):
        self.allSentence = self.ui.allText.toPlainText().split('\n')
        self.allSentence = [x.strip() for x in self.allSentence if len(x.strip()) > 0]
        if len(self.allSentence) <= 0:
            return False
        self.sections = [(None, None) for _ in range(len(self.allSentence))]
        return True

    # 将网络表情包加载预览以供选择
    def thread_addImg(self, path):
        self.ui.addImg(path)

    # 搜索表情包,button代表了不同的搜索引擎
    def search(self, button):
        if self.subThread is not None:
            self.subThread.terminate()
            while self.subThread.isRunning() and not self.subThread.isFinished():
                time.sleep(0.1)
        self.ui.delImg()
        self.subThread = addImgThread(self.ui.searchText.text(), button)

        self.subThread.signal.connect(self.thread_addImg)
        self.subThread.start()

    # 将选好的表情包加载到视频预览区
    def imgClicked(self, index):
        if self.nowPos is None:
            return
        _, _, imgPath = self.ui.img[index]
        self.ui.changeVideoImg(path=imgPath)
        # 将表情包复制到material目录
        imgBaseName = os.path.basename(imgPath)
        newPath = '{}.{}'.format(self.nowPos, imgBaseName[imgBaseName.rfind('.') + 1:])
        newPath = os.path.join(os.path.join(self.materialName, 'img'), newPath)
        shutil.copyfile(imgPath, newPath)
        # 保存图片与字幕信息
        self.sections[self.nowPos] = (newPath, self.ui.singleText.text())

    # 生成视频
    def genVideo(self):
        if len(self.allSentence) <= 0:
            QtWidgets.QMessageBox.information(self, '提示', '工作区无内容！', QMessageBox.Ok)
            return
        genVideo_thread = genVideoThread(self.sections, self.materialName, self.ui.filenName.text())
        genVideo_thread.signal.connect(self.genVideoFinished)
        genVideo_thread.start()

    # 视频生成完成
    def genVideoFinished(self, filename):
        QtWidgets.QMessageBox.information(self, '提示', '生成完毕!位置:{}'.format(filename), QMessageBox.Ok)


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
