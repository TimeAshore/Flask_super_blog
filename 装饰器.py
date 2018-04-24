# encoding: utf-8
# Author: Timeashore
# Time: 2018-4-20
# Email: 1274866364@qq.com
class User(object):
    def __init__(self, name='张三'):
        self.name = name
        # self.__name = name  # 私有

    @staticmethod
    def show(self):
        print self.name

    @property
    def display(self):
        '''打印name'''
        print 'Here',self.name

    @display.setter
    def display(self, name):
        print 'Here set'
        self.name = name


if __name__ == '__main__':
    user_1 = User()
    user_1.show(user_1)

    # user_1.display
    # user_1.display = '李四'
    # user_1.display
