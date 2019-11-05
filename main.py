# Author:尉玉林(Mr.Wei)

# Create Date:2019/10/22

# Edition:V1.0.0

# Python自带库
import sys
import sqlite3
from time import sleep
# 第三方库
from PySide2.QtWidgets import QMainWindow, QApplication, QMessageBox, QSplashScreen, QLabel
from PySide2.QtCore import QThread, Signal, Qt
from PySide2.QtGui import QPixmap, QFont

from PIL import ImageGrab
import pytesseract
import keyboard
import pyautogui as pag
# 自己的包
from UI2PY.MainWindow import Ui_MainWindow
from mycode.HslCommunication import SiemensPLCS, SiemensS7Net
from mycode.config import Config
from mycode.sato import ComThread


class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.Ui_MainWindow = Ui_MainWindow()
        self.Ui_MainWindow.setupUi(self)

        self._thread = MyThread()
        self._thread.signal.connect(self.key_reading)

        # 钥匙是否插到位
        self.key_is_ready = False
        # 钥匙上一次的状态
        self.key_last_status = False
        # 弹子机是否就位
        self.marble_machine_is_ready = False
        # 弹子机上一次的状态
        self.marble_machine_last_status = False
        # 当前生产的产品
        self.product = ''

        self.siemens = SiemensS7Net(SiemensPLCS.S1200, '192.168.0.1')
        self.conf = Config()
        self.com = ComThread()
        self.setup()

    def setup(self):
        ip_plc = self.conf.read_config(product='config', section='plc', name='ip')
        _, self.product = self.get_project()
        self.Ui_MainWindow.lineEdit_IP_PLC.setText(ip_plc)

        self.siemens = SiemensS7Net(SiemensPLCS.S1200, ip_plc)
        self.Ui_MainWindow.label_status.setText('正在初始化，请稍候...')
        self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')
        QApplication.processEvents()

        if self.com.check_com():  # 如果有串口，则打开指定的串口
            if self.com.open_com():  # 如果串口打开成功
                if self.siemens.ConnectServer().IsSuccess:  # 如果PLC连接成功
                    self.Ui_MainWindow.label_status.setText('初始化完成')
                    self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')
                    self._thread.start()
                else:  # 如果PLC连接失败
                    QMessageBox.critical(self, '错误', 'PLC连接失败！')
                    self.Ui_MainWindow.label_status.setText('PLC连接失败！')
                    self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')
            else:  # 如果串口打开失败
                QMessageBox.critical(self, '错误！', '串口打开失败！')
                self.Ui_MainWindow.label_status.setText('串口打开失败！')
                self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')
        else:
            QMessageBox.critical(self, '错误！', '未发现串口！')
            self.Ui_MainWindow.label_status.setText('未发现串口！')
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')

    # 槽函数
    def change_ip_plc(self):
        self._thread.__del__()
        self._thread.quit()
        ip_plc = self.Ui_MainWindow.lineEdit_IP_PLC.text()
        self.conf.update_config(product='config', section='plc', name='ip', value=ip_plc)

    def test_connect_plc(self):
        self._thread.__del__()
        self._thread.quit()
        ip_plc = self.conf.read_config(product='config', section='plc', name='ip')
        self.Ui_MainWindow.lineEdit_IP_PLC.setText(ip_plc)
        self.siemens = SiemensS7Net(SiemensPLCS.S1200, ip_plc)
        self.Ui_MainWindow.label_status.setText('正在连接PLC...')
        self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')
        QApplication.processEvents()
        if self.siemens.ConnectServer().IsSuccess:  # 如果连接成功
            QMessageBox.about(self, 'PLC连接', 'PLC连接成功！')
            self.Ui_MainWindow.label_status.setText('等待读取钥匙号')
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')
        else:
            QMessageBox.about(self, 'PLC连接', 'PLC连接失败！')
            self.Ui_MainWindow.label_status.setText('PLC连接失败！')
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')

    def key_reading(self):
        # self.Ui_MainWindow.label_status.setText('等待读取钥匙号')
        # QApplication.processEvents()
        key_is_ready = self.siemens.ReadBool('I4.5').Content
        if key_is_ready:  # 如果钥匙到位(I4.5)
            if self.key_last_status:  # 如果之前钥匙已经到位，不做任何处理
                pass
            else:  # 如果之前钥匙未到位，则将标志位置为True
                self.key_is_ready = True
        else:  # 如果钥匙未到位，则将标志位置为False
            self.key_is_ready = False
        # 将本次的钥匙是否到位传感器的状态作为下一次状态的上一状态
        self.key_last_status = key_is_ready

        marble_is_ready = self.siemens.ReadBool('M3.4').Content
        if marble_is_ready:  # 如果弹子机就位(M3.4)
            if self.marble_machine_last_status:  # 如果之前弹子机已经就位，不做任何处理
                pass
            else:  # 如果之前弹子机未就位，则将标志位置为True
                self.marble_machine_is_ready = True
        else:  # 如果弹子机未就位，则将标志位置为False
            self.marble_machine_is_ready = False
        # 将本次的弹子机是否到位传感器的状态作为下一次状态的上一状态
        self.marble_machine_last_status = marble_is_ready
        # print(marble_is_ready)
        # print(self.key_is_ready, self.marble_machine_is_ready)
        if self.key_is_ready and self.marble_machine_is_ready:  # 如果钥匙和弹子机都到位，则读取钥匙号
            self.Ui_MainWindow.label_status.setText('正在读取钥匙号')
            self.Ui_MainWindow.label_status.setStyleSheet("background-color: rgb(255, 255, 127);")
            QApplication.processEvents()
            self.key_is_ready = False
            self.marble_machine_is_ready = False
            self.key_read()

    def manual_key_read(self):
        self.Ui_MainWindow.label_status.setText('正在读取钥匙号')
        self.Ui_MainWindow.label_status.setStyleSheet("background-color: rgb(255, 255, 127);")
        QApplication.processEvents()
        self.key_read()

    def start(self):
        ip_plc = self.conf.read_config(product='config', section='plc', name='ip')
        self.Ui_MainWindow.lineEdit_IP_PLC.setText(ip_plc)
        self.Ui_MainWindow.label_status.setText('正在连接PLC...')
        self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')
        QApplication.processEvents()
        if self.siemens.ConnectServer().IsSuccess:  # 如果连接成功
            self.Ui_MainWindow.label_status.setText('等待读取钥匙号')
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')
            self._thread.working = True
            self._thread.start()
        else:
            self.Ui_MainWindow.label_status.setText('PLC连接失败！')
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')

    def pause(self):
        self._thread.__del__()
        self._thread.quit()

    # 选择图片的识别区域
    def select_capture_region(self):
        self._thread.__del__()
        self._thread.quit()
        conf = Config()
        if keyboard.wait(hotkey='ctrl+alt') == None:
            x1, y1 = pag.position()
            print(pag.position())
            if keyboard.wait(hotkey='ctrl+alt') == None:
                x2, y2 = pag.position()
                print(pag.position())
        pos_new = str((x1, y1, x2, y2))
        conf.update_config(product='config', section='image_read_area', name='position', value=pos_new)

    def show_capture(self):
        self._thread.__del__()
        self._thread.quit()
        img, project = self.get_project()
        self.Ui_MainWindow.lineEdit_product.setText(project)
        project = pytesseract.image_to_string(img)
        self.Ui_MainWindow.lineEdit_product.setText(project)
        img.show()

    # 功能函数
    # 获取弹子号
    def key_read(self):
        _, self.product = self.get_project()
        keyid = self.get_keyid()
        res, keycode = self.get_keycode(keyid)
        if res:  # 如果正确获取钥匙号
            self.barcode_print(self.product, keycode)
        else:
            keycode = '----'
            self.Ui_MainWindow.label_status.setText('未正确获取钥匙号')
            self.Ui_MainWindow.label_status.setStyleSheet("background-color: rgb(255, 0, 0);")

        self.Ui_MainWindow.lineEdit.setText(keycode)

    def get_keyid(self):
        keyid = ''
        read = self.siemens.Read('DB3.60', 32)  # 读取8个弹子号格式：弹子号为11111111，则读取为00010001000100010001000100010001
        if read.IsSuccess:  # 如果读取成功
            keys = read.Content[3::4]  # 获取弹子号:从第4个位置开始，每隔4个数读取数据,得到8个弹子号

            for key in keys:
                keyid += str(key)
        else:
            keyid = 'XXXXXXXX'
        return keyid

    # 获取钥匙号
    def get_keycode(self, keyid):
        try:
            with sqlite3.connect('keyid.db') as conn:
                c = conn.cursor()
                rows = c.execute("SELECT keycode FROM '%s' WHERE keyid='%s'" % (self.product, keyid)).fetchall()
                keycode = rows[0][0]
                return True, keycode
        except Exception as e:
            self.Ui_MainWindow.label_status.setText('get_keycode:%s' % str(e))
            self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 0, 0);')
            QMessageBox.critical(self, '错误', str(e))
            return False, '----'

    def get_project(self):
        conf = Config()
        pos = eval(conf.read_config(product='config', section="image_read_area", name="position"))
        img = ImageGrab.grab(pos)
        # img.show()
        # img.save("picture2string.jpg")
        project = pytesseract.image_to_string(img)
        self.Ui_MainWindow.lineEdit_product.setText(project)
        # print(project)
        return img, project.upper()

    # 条码打印
    def barcode_print(self, product, keycode):
        if product == '280B' or product == '281B' or product == '0开头':
            barcode_bytes = keycode.encode("utf-8")  # 转换为字节格式
            send_data = b'\x1bA\x1bN\x1bR\x1bR\x1bH070\x1bV01282\x1bL0202\x1bS\x1bB103080*' + barcode_bytes + b'*\x1bH0200\x1bV01369\x1bL0202\x1bS' + barcode_bytes + b'\x1bQ1\x1bZ'
        self.com.send_data(send_data)
        self.Ui_MainWindow.label_status.setText('等待读取钥匙号')
        self.Ui_MainWindow.label_status.setStyleSheet('background-color: rgb(255, 255, 127);')


class MyThread(QThread):
    signal = Signal()

    def __init__(self):
        super(MyThread, self).__init__()
        self.working = True  # 工作状态标志量

    def __del__(self):
        self.working = False  # 工作状态标志量

    def run(self):
        # 进行线程任务
        while self.working:
            sleep(0.1)
            self.signal.emit()  # 发射信号


if __name__ == '__main__':
    # 创建一个应用程序对象
    app = QApplication(sys.argv)

    splash = QSplashScreen(QPixmap("resource/images/loading.png"))
    splash.showMessage("加载中，请稍后...", Qt.AlignHCenter | Qt.AlignBottom, Qt.cyan)
    splash.setFont(QFont("华文楷体", 10, QFont.Bold))
    splash.show()  # 显示启动界面
    QApplication.processEvents()  # 处理主进程事件

    # 创建控件(容器)
    window = MyWindow()

    # 设置标题
    # window.setWindowTitle('title')

    # window.load_data(splash)  # 加载数据
    # 显示窗口
    window.show()
    splash.finish(window)  # 隐藏启动界面
    # 进入消息循环
    sys.exit(app.exec_())
