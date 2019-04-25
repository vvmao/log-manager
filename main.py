# !/usr/bin/python3

from tail import Tail
from threading import Thread
import sys


def main(file, port):
    t = Tail(file)
    t.websocket_server(port)
    t.follow(s=1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("未输入文件名")
    else:
        main(sys.argv[1], 8000)
