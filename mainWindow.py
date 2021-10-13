# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.
import math
import os.path
import shutil
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QMovie

from conf import DoutulaButton, BaiduButton


class clickedButton(QtWidgets.QPushButton):
    clicked = QtCore.pyqtSignal(int)

    def __init__(self, button, parent=None):
        super(clickedButton, self).__init__(parent)
        self.button = button

    def mouseReleaseEvent(self, QMouseEvent):
        self.clicked.emit(self.button)


class clickedLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal(int)

    def __init__(self, index, parent=None):
        super(clickedLabel, self).__init__(parent)
        self.index = index

    def mouseReleaseEvent(self, QMouseEvent):
        self.clicked.emit(self.index)


class Ui_MainWindow(object):
    def __init__(self):
        self.img = []
        self.gif = None
        self.videoImg = None

    def setupUi(self, MainWindow):
        # 初始设置窗口信息
        MainWindow.setObjectName('MainWindow')
        MainWindow.resize(1890, 702)
        MainWindow.setLayoutDirection(QtCore.Qt.LeftToRight)
        # 表情包点击函数
        self.mainwindow_clicked = MainWindow.imgClicked

        self.centralwidget = QtWidgets.QWidget(MainWindow)

        # 输入文件名标签
        self.fileLabel = QtWidgets.QLabel(self.centralwidget)
        self.fileLabel.setGeometry(QtCore.QRect(10, 23, 121, 16))
        self.fileLabel.setText('Video Filename: ')

        # 文件名
        self.filenName = QtWidgets.QLineEdit(self.centralwidget)
        self.filenName.setGeometry(QtCore.QRect(140, 16, 361, 31))
        self.filenName.setText('{}.avi'.format(int(time.time())))

        # 输入文件名确定按钮
        self.filenameButton = QtWidgets.QPushButton(self.centralwidget)
        self.filenameButton.setGeometry(QtCore.QRect(501, 16, 60, 31))
        self.filenameButton.setText('Set')
        self.filenameButton.clicked.connect(MainWindow.setFilename)

        # 给输入框加个分组box
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(0, 53, 561, 618))

        # 文案的输入框
        self.allText = QtWidgets.QPlainTextEdit(self.groupBox)
        self.allText.setGeometry(QtCore.QRect(10, 20, 541, 581))
        self.allText.setAcceptDrops(False)
        self.allText.setReadOnly(True)

        # 单句字幕
        self.singleText = QtWidgets.QLineEdit(self.centralwidget)
        self.singleText.setGeometry(QtCore.QRect(660, 620, 611, 50))

        # 搜索框文本
        self.searchText = QtWidgets.QLineEdit(self.centralwidget)
        self.searchText.setGeometry(QtCore.QRect(1360, 17, 421, 41))

        # 搜索按钮
        self.search_dou = clickedButton(DoutulaButton, self.centralwidget)
        self.search_dou.setGeometry(QtCore.QRect(1785, 17, 45, 41))
        self.search_bai = clickedButton(BaiduButton, self.centralwidget)
        self.search_bai.setGeometry(QtCore.QRect(1834, 17, 45, 41))

        # 视频背景图
        self.videoBackgroud = QtWidgets.QLabel(self.centralwidget)
        self.videoBackgroud.setGeometry(QtCore.QRect(560, 16, 800, 600))
        self.videoBackgroud.setText('')
        self.videoBackgroud.setPixmap(QtGui.QPixmap('backgroud.png'))
        self.videoBackgroud.setScaledContents(True)

        # 视频字幕
        self.videoText = QtWidgets.QLabel(self.centralwidget)
        self.videoText.setGeometry(QtCore.QRect(560, 526, 801, 51))
        # 视频字幕字体颜色
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        self.videoText.setPalette(palette)
        # 视频字幕字体设置
        font = QtGui.QFont()
        font.setFamily('华文楷体')
        font.setPointSize(20)
        self.videoText.setFont(font)
        self.videoText.setTextFormat(QtCore.Qt.PlainText)
        self.videoText.setScaledContents(False)
        self.videoText.setAlignment(QtCore.Qt.AlignCenter)
        self.videoText.setWordWrap(False)

        # 上一句按钮
        self.last = QtWidgets.QPushButton(self.centralwidget)
        self.last.setGeometry(QtCore.QRect(560, 620, 101, 51))

        # 下一句按钮
        self.next = QtWidgets.QPushButton(self.centralwidget)
        self.next.setGeometry(QtCore.QRect(1270, 620, 91, 51))

        # 生成视频按钮
        self.genVideo = QtWidgets.QPushButton(self.centralwidget)
        self.genVideo.setGeometry(QtCore.QRect(1360, 620, 521, 51))

        # 表情包图片位置布局
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(1349, 48, 540, 579))
        self.topFiller = QtWidgets.QWidget()
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidget(self.topFiller)
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addWidget(self.scroll)
        self.widget.setLayout(self.vbox)

        self.retranslateUi(MainWindow)
        self.last.clicked.connect(MainWindow.last)
        self.next.clicked.connect(MainWindow.next)
        self.search_dou.clicked.connect(MainWindow.search)
        self.search_bai.clicked.connect(MainWindow.search)
        self.singleText.textChanged.connect(MainWindow.changeThePicText)
        # self.allText.textChanged.connect(MainWindow.editFinished)
        self.genVideo.clicked.connect(MainWindow.genVideo)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def delVideoImg(self):
        if self.videoImg is not None:
            self.videoImg.deleteLater()
            self.videoImg = None
        if self.gif is not None:
            self.gif.deleteLater()
            self.gif = None

    def changeVideoImg(self, index=None, path=None):
        if path is None:
            _, _, path = self.img[index]
        # 如果图片不是在tmp目录保存,则转到tmp目录再加载,不然重命名工程会有问题
        if not path.startswith('tmp' + os.path.sep):
            newPath = os.path.join('tmp', os.path.basename(path))
            if not os.path.exists(newPath):
                shutil.copyfile(path, newPath)
            path = newPath
        self.delVideoImg()
        self.videoImg = QtWidgets.QLabel(self.centralwidget)
        self.videoImg.setGeometry(QtCore.QRect(560, 10, 801, 601))
        self.gif = QMovie(path)
        self.videoImg.setMovie(self.gif)
        self.videoImg.setAlignment(QtCore.Qt.AlignCenter)
        self.gif.start()
        self.videoImg.show()
        self.centralwidget.show()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate('MainWindow', 'MainWindow'))
        self.groupBox.setTitle(_translate('MainWindow', 'Put the Subtitles to Here'))
        self.search_dou.setText(_translate('MainWindow', 'Dou'))
        self.search_bai.setText(_translate('MainWindow', 'Bai'))
        self.last.setText(_translate('MainWindow', 'last'))
        self.next.setText(_translate('MainWindow', 'next'))
        self.genVideo.setText(_translate('MainWindow', 'GenVideo'))

    def addImg(self, path):
        # 计算图片框位置
        row = math.ceil((len(self.img) + 1) / 3) - 1
        col = len(self.img) % 3
        img_label = clickedLabel(len(self.img), self.topFiller)
        img_label.setGeometry(QtCore.QRect(1370, 60, 151, 151))
        gif = QMovie(path)
        img_label.setMovie(gif)
        img_label.setScaledContents(True)
        gif.start()
        img_label.move(col * (151 + 10) + 10, row * (151 + 10) + 10)
        self.img.append((img_label, gif, path))
        self.topFiller.setMinimumSize(490, (row + 1) * (151 + 10))
        self.scroll.setWidget(self.topFiller)
        img_label.clicked.connect(self.mainwindow_clicked)
        img_label.show()
        self.topFiller.show()
        self.widget.show()

    def delImg(self):
        for img_label, gif, _ in self.img:
            img_label.deleteLater()
            gif.deleteLater()
        self.img = []
        self.widget.show()

