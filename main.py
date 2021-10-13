# TODO
# 0. 生成视频放入线程中 done
# 1. 增加百度图片搜索接口 done
# 2. 增加本地图片选择 done
# 3. 优化gif显示
# 4. 配音,文字->语音 done
# 5. 表情包尺寸的统一问题
# 6. 编辑保存防止异常退出工作丢失

import base64
import hashlib
import json
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
def getBaiDuAudio(text):
    url = 'https://cloud.baidu.com/aidemo'
    data = 'type=tns&per=4105&spd=8&pit=7&vol=5&aue=6&tex=' + quote(text)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
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
    filename = md5.hexdigest() + '.mp3'
    filename = os.path.join('tmp', filename)
    with open(filename, 'wb') as f:
        f.write(data)
    return filename


# 生成视频线程
class genVideoThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, sections):
        super().__init__()
        self.sections = sections

    def __del__(self):
        self.wait()

    def run(self):
        screensize = (800, 600)
        videoClips = []
        for imgPath, text in self.sections:
            texts = text.strip().split('\n')
            duration_time = 2
            if imgPath.endswith('.gif'):
                clip = VideoFileClip(imgPath)
                duration_time = clip.duration / len(texts)
            else:
                clip = ImageClip(imgPath)
            for txt in texts:
                txtClip = TextClip(txt, color='white', font='STKaiti', kerning=5, fontsize=50, align='South')
                txtAudio = getBaiDuAudio(txt)
                if txtAudio is None:
                    print('get the audio of {} failed!'.format(txt))
                    continue
                txtAudio = AudioFileClip(txtAudio)
                cvc = CompositeVideoClip([clip.set_position(('center', 'center')),
                                          txtClip.set_position(('center', 0.85), relative=True)],
                                         size=screensize).subclip(0, txtAudio.duration)
                cvc = cvc.set_audio(txtAudio)
                videoClips.append(cvc)
        final_clip = concatenate_videoclips(videoClips)
        # 获取原视频声音
        audio = final_clip.audio

        # 整体背景音乐
        audioClip = AudioFileClip(backgroundMusic)
        if audioClip.duration > final_clip.duration:
            audioClip = audioClip.subclip(0, audio.duration)
        elif audioClip.duration < final_clip.duration:
            audioClip = afx.audio_loop(audioClip, duration=audio.duration)

        # 声音结合起来
        audio = CompositeAudioClip([audio, audioClip])
        final_clip = final_clip.set_audio(audio)
        filename = os.path.join('out', '{}.avi'.format(int(time.time())))
        final_clip.write_videofile(filename, fps=25, codec='mpeg4')
        self.signal.emit(filename)


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
                filename = md5.hexdigest() + '.gif' if is_gif else md5.hexdigest() + '.png'
                path = os.path.join('tmp', filename)
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
        self.all_sentence = []
        # 获取表情包线程句柄
        self.subThread = None
        # 已经设定好的句子以及表情包
        self.sections = []
        # 当前选择的图片
        self.ImgPath = None

        self.setAcceptDrops(True)

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
        self.ImgPath = filePath.replace('file:///', '', 1)
        if self.nowPos is None:
            return
        self.ui.changeVideoImg(path=self.ImgPath)
        self.sections[self.nowPos] = (self.ImgPath, self.ui.singleText.text())

    # 上一句
    def last(self):
        if len(self.all_sentence) <= 0:
            return
        if self.nowPos is None:
            self.nowPos = 0
        else:
            self.nowPos = self.nowPos - 1
            if self.nowPos == -1:
                self.nowPos = len(self.all_sentence) - 1
        self.ui.singleText.setText(self.all_sentence[self.nowPos])
        self.ui.singleText.home(False)
        self.ui.searchText.setText(self.all_sentence[self.nowPos])
        self.ui.searchText.home(False)
        # 如果已经设置好了,显示出来;否则就清空
        imgPath, _ = self.sections[self.nowPos]
        if imgPath is not None:
            self.ui.changeVideoImg(path=imgPath)
        else:
            self.ui.delVideoImg()

    # 下一句,详情同上一句
    def next(self):
        if len(self.all_sentence) <= 0:
            return
        if self.nowPos is None:
            self.nowPos = -1
        self.nowPos = self.nowPos + 1
        if self.nowPos >= len(self.all_sentence):
            self.nowPos = 0
        self.ui.singleText.setText(self.all_sentence[self.nowPos])
        self.ui.singleText.home(False)
        self.ui.searchText.setText(self.all_sentence[self.nowPos])
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
        self.all_sentence = self.ui.allText.toPlainText().split('\n')
        self.all_sentence = [x.strip() for x in self.all_sentence if len(x.strip()) > 0]
        self.sections = [(None, None) for _ in range(len(self.all_sentence))]

    # 将网络表情包加载预览以供选择
    def thread_addImg(self, path):
        self.ui.addImg(path)

    # 搜索表情包,button代表了不同的搜索引擎
    def search(self, button):
        if self.subThread is not None:
            self.subThread.terminate()
            time.sleep(1)
        self.ui.delImg()
        self.subThread = addImgThread(self.ui.searchText.text(), button)
        self.subThread.signal.connect(self.thread_addImg)
        self.subThread.start()

    # 将选好的表情包加载到视频预览区
    def ImgClicked(self, index):
        if self.nowPos is None:
            return
        self.ui.changeVideoImg(index=index)
        _, _, self.ImgPath = self.ui.img[index]
        self.sections[self.nowPos] = (self.ImgPath, self.ui.singleText.text())

    # 生成视频
    def genVideo(self):
        genVideo_thread = genVideoThread(self.sections)
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
