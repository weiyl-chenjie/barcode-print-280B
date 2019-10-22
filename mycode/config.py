import configparser


class Config:
    def __init__(self):
        self.conf = configparser.ConfigParser()

    # 读取ini文件
    def read_config(self, product, section, name):
        filename = product + '.ini'
        self.conf.read(filename, encoding='UTF-8')
        # get()函数读取section里的参数值
        # position = eval(self.conf.get(section, name))  # 把元组格式的字符串转换为元组
        data = self.conf.get(section, name)
        return data

    # 修改ini文件
    def update_config(self, product, section, name, value):
        # 修改指定的section的参数值
        filename = product + '.ini'
        self.conf.read(filename, encoding='UTF-8')
        self.conf.set(section, name, value)
        self.conf.write(open(filename, 'w+', encoding='UTF-8'))