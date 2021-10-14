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
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMovie, QStandardItemModel, QStandardItem

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

        self.mainWindow = MainWindow
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

        # 文案以表格的形式展示
        self.model = QStandardItemModel(0, 0)
        # 设置水平方向四个头标签文本内容
        self.model.setHorizontalHeaderLabels(['文案&字幕'])
        self.row = 0
        for x in range(10):
            self.addRow("xxx{}".format(x))
        self.tableView = QtWidgets.QTableView(self.groupBox)
        self.tableView.setGeometry(QtCore.QRect(10, 20, 541, 542))
        self.tableView.setShowGrid(True)
        self.tableView.setModel(self.model)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        # 打开文案/前增一句/后增一句/删除一句/修改一句/导出文案按钮布局
        self.tableButtonWidget = QtWidgets.QWidget(self.groupBox)
        self.tableButtonWidget.setGeometry(QtCore.QRect(10, 561, 541, 40))
        # 水平分布
        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.setGeometry(QtCore.QRect())
        self.hbox.setContentsMargins(10, 0, 10, 0)
        # 打开文案
        self.openText = QtWidgets.QPushButton()
        self.openText.setText('打开')
        self.openText.clicked.connect(MainWindow.loadText)
        self.hbox.addWidget(self.openText)
        # 在前面增加一句
        self.addFrontText = QtWidgets.QPushButton()
        self.addFrontText.setText('前增一句')
        self.addFrontText.clicked.connect(MainWindow.addFrontText)
        self.hbox.addWidget(self.addFrontText)
        # 在后面增加一句
        self.addBehindText = QtWidgets.QPushButton()
        self.addBehindText.setText('后增一句')
        self.addBehindText.clicked.connect(MainWindow.addBehindText)
        self.hbox.addWidget(self.addBehindText)
        # 删除该句
        self.delText = QtWidgets.QPushButton()
        self.delText.setText('删除该句')
        self.delText.clicked.connect(MainWindow.delText)
        self.hbox.addWidget(self.delText)
        # 导出文案
        self.exportText = QtWidgets.QPushButton()
        self.exportText.setText('导出文案')
        self.hbox.addWidget(self.exportText)
        self.tableButtonWidget.setLayout(self.hbox)

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
        self.videoBackgroud.setPixmap(QtGui.QPixmap('background.png'))
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
        self.genVideo.clicked.connect(MainWindow.genVideo)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def delVideoImg(self):
        if self.videoImg is not None:
            self.videoImg.deleteLater()
            self.videoImg = None
        if self.gif is not None:
            self.gif.deleteLater()
            self.gif = None

    def changeVideoImg(self, path: str) -> None:
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
        self.groupBox.setTitle(_translate('MainWindow', 'Put the texts to Here'))
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
        img_label.clicked.connect(self.mainWindow.imgClicked)
        img_label.show()
        self.topFiller.show()
        self.widget.show()

    def delImg(self) -> None:
        """
        清空从网络获取的所有的表情包
        :return: None
        """
        for imgLabel, gif, _ in self.img:
            imgLabel.deleteLater()
            gif.deleteLater()
        self.img = []
        self.widget.show()

    def getImgPathByIndex(self, index: int) -> str:
        """
        通过表情包缓存区的索引获取表情包的实际路径
        :param index: 表情包缓存区的索引
        :return: 表情包的实际位置
        """
        return self.img[index][2]

    def addRow(self, text: str) -> None:
        """
        向表中添加一行新的数据
        :param text:
        :return:
        """
        item = QStandardItem(text)
        self.model.setItem(self.row, 0, item)
        self.row += 1

    def delRow(self, row: int) -> None:
        """
        删除一行表中的数据
        :param row: 删除索引
        :return:
        """
        self.model.removeRow(row)

    def delAllRow(self) -> None:
        """
        删除所有行
        :return:
        """
        map(self.delRow, range(self.model.rowCount()))

    def msgBox(self, msg: str, hasQuery: bool = False) -> bool:
        """
        :param msg: 消息
        :param hasQuery: 是否带询问
        :return: 如果hasQuery为True,返回值为用户是否点击了确定
        """
        if not hasQuery:
            QtWidgets.QMessageBox.information(self.mainWindow, '提示', msg, QtWidgets.QMessageBox.Ok,
                                              QtWidgets.QMessageBox.Ok)
            return True
        reply = QtWidgets.QMessageBox.question(self.mainWindow, '提示', msg,
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                                               QtWidgets.QMessageBox.Cancel)
        return reply == QtWidgets.QMessageBox.Yes

    def getCurrentSelected(self) -> int:
        """
        获取当前选中的表格单元索引
        :return: 前选中的表格单元索引
        """
        selectedIndex = self.tableView.selectedIndexes()
        print(selectedIndex)
        if len(selectedIndex) > 0:
            print(selectedIndex[0].row())
            return selectedIndex[0].row()
        return -1

    def insertRow(self, index: int) -> None:
        """
        增加一行空白行
        :index: 增加的位置索引
        :return: None
        """
        self.model.insertRow(index)

    def getSubtitle(self) -> str:
        """
        获取当前编辑的字幕信息
        :return: 前编辑的字幕
        """
        return self.singleText.text()

    def getSearchText(self) -> str:
        """
        获取搜索框文本信息
        :return: 搜索框文本信息
        """
        return self.searchText.text()

    def setVideoText(self, text: str) -> None:
        """
        设置视频预览区字幕信息
        :param text: 字幕信息
        :return: None
        """
        self.videoText.setText(text)

    def setFileName(self, fileName: str) -> None:
        """
        设置文件名
        :param fileName: 文件名
        :return: None
        """
        self.filenName.setText(fileName)
