#!/usr/bin/env python
#-*- coding:utf-8 -*-
#auther = Alan
import sys
import socket
import select
import paramiko
import threading

try:
    import termios
    import tty
    has_termios = True
except ImportError:
    has_termios = False

host_dict = {
    '192.168.3.53':[22,'root','jinher!@#'],
    '192.168.3.49':[22,'root','11qq```']
}

host_list=[]
for i in host_dict:
    host_list.append(i)

print ''.ljust(60,'-')
print 'Welcome TO OSFM'.center(60)
print ''.ljust(60,'-')

for i,host in enumerate(host_list,1):
    print i,'.',host

class Ssh_Conn(object):
    def __init__(self):
        data =int(raw_input('Please change your connection host id:'))
        self.address = host_list[data-1]
        self.port = host_dict.get(self.address)[0]
        self.name = host_dict.get(self.address)[1]
        self.passwd = host_dict.get(self.address)[2]
        self.base_shell()
    def base_shell(self):
        #创建一个socket句柄
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #连接到远程主机ssh服务
        self.sock.connect((self.address,self.port))
        #将sock传递给transport创建一个ssh对象
        self.transport = paramiko.Transport(self.sock)
        #打开ssh连接
        self.transport.start_client()
        #进行ssh认证
        self.transport.auth_password(username=self.name,password=self.passwd)
        #开启session通道（建立一个持久连接）
        self.chan = self.transport.open_session()
        #获取一个终端 将持久连接加持到一个终端
        self.chan.get_pty()
        #请求终端（激活）
        self.chan.invoke_shell()
        if has_termios:
            self.linux_shell()
        else:
            self.windows_shell()
    #windows终端
    def windows_shell(self):
        def write_all(chan):
            while True:
                #如果返回值为空跳出循环
                data = chan.recv(2048)
                if not data:
                    pass
                else:
                    #如果返回值不为空则输出到终端
                    sys.stdout.write(data)
                    sys.stdout.flush()
        #单独创建一个线程进行后台处理终端
        thread = threading.Thread(target=write_all,args=(self.chan,))
        #启动线程
        thread.start()
        try:
            while True:
                #判断用户输入
                data = sys.stdin.read(1)
                #如果输入为空则退出循环
                if not data:
                    break
                else:
                    #如果不为空则将用户输入发送到远程主机
                    self.chan.send(data)
        except EOFError:
            pass
        self.chan.close()
        self.transport.close()
    #linux终端
    def linux_shell(self):
        oldtty = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            self.chan.settimeout(0.0)
            while True:
                #输出
                r,w,e = select.select([self.chan,sys.stdin],[],[],1)
                if self.chan in r:
                    try:
                        data = self.chan.recv(2048)
                        if not data:
                            break
                        sys.stdout.write(data)
                        sys.stdout.flush()
                    except socket.timeout:
                        pass
                #输入
                if sys.stdin in r:
                    data = sys.stdin.read(1)
                    if not data:
                        break
                    self.chan.send(data)
        finally:
            #将本地终端状态修改回原来的终端状态
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
if __name__ == '__main__':
    ssh_conn = Ssh_Conn()
