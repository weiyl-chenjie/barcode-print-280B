# Author:尉玉林(Mr.Wei)

# Create Date:2019/10/23

# Edition:V1.0.0

# Python自带库

# 第三方库
import serial
import serial.tools.list_ports
# 自己的包
from mycode.config import Config


class ComThread:
    def __init__(self):
        self.ser = serial.Serial()
        self.conf = Config()
        self.port = self.conf.read_config(product='config', section='printer', name='port')  # 端口号
        self.baudrate = int(self.conf.read_config(product='config', section='printer', name='baudrate'))  # 波特率
        self.bytesize = int(self.conf.read_config(product='config', section='printer', name='bytesize'))  # 数据位
        self.parity = self.conf.read_config(product='config', section='printer', name='parity')  # 奇偶校验
        self.stopbits = int(self.conf.read_config(product='config', section='printer', name='stopbits'))  # 停止位
        self.timeout = int(self.conf.read_config(product='config', section='printer', name='timeout'))  # 超时
        self.data = bytes()  # 存放读取的串口数据

    # 检查是否有可用串口
    @staticmethod
    def check_com():
        port_lists = list(serial.tools.list_ports.comports())
        if len(port_lists) == 0:
            print("无可用串口")
            return False
        else:
            print("发现串口:")
            for i in range(0, len(port_lists)):
                print(port_lists[i].device)
            return True

    # 打开串口
    def open_com(self):
        self.ser.port = self.port
        self.ser.baudrate = self.baudrate
        self.ser.bytesize = self.bytesize
        self.ser.stopbits = self.stopbits
        self.ser.parity = self.parity
        self.ser.timeout = 60
        self.ser.open()
        if self.ser.isOpen():
            print("成功打开串口，当前串口为:%s" % self.ser.name)
            return True
        else:
            self.error_message_box("错误", "打开串口"+self.port+"失败！")
            return False

    # 发送数据
    def send_data(self, send):
        self.ser.write(send)

    # 读取数据
    def read_data(self):
        count = self.ser.inWaiting()
        self.data = self.ser.read(count)
        # 清空接收缓冲区
        self.ser.flushInput()

