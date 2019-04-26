#!/usr/bin/env python

"""
Python-Tail - Unix tail follow implementation in Python.

python-tail can be used to monitor changes to a file.

Example:
    import tail

    # Create a tail instance
    t = tail.Tail('file-to-be-followed')

    # Register a callback function to be called when a new line is found in the followed file.
    # If no callback function is registerd, new lines would be printed to standard out.
    t.register_callback(callback_function)

    # Follow the file with 5 seconds as sleep time between iterations.
    # If sleep time is not provided 1 second is used as the default time.
    t.follow(s=5) """

# Author - Kasun Herath <kasunh01 at gmail.com>
# Source - https://github.com/kasun/python-tail

import os
import sys
import time
from websocket_server import WebsocketServer
from threading import Thread


class Tail(object):
    """ Represents a tail command. """

    def __init__(self, tailed_file, server):
        """ Initiate a Tail instance.
            Check for file validity, assigns callback function to standard out.

            Arguments:
                tailed_file - File to be followed. """

        self.check_file_validity(tailed_file)
        self.tailed_file = tailed_file
        self.callback = sys.stdout.write
        self.queue = []
        self.ws = None

    def follow(self, s=1):
        """ Do a tail follow. If a callback function is registered it is called with every new line.
        Else printed to standard out.

        Arguments:
            s - Number of seconds to wait between each iteration; Defaults to 1. """
        self.getLine()
        with open(self.tailed_file) as file_:
            file_.seek(0, 2)
            # Go to the end of file
            while True:
                curr_position = file_.tell()
                line = file_.readline()
                if not line:
                    file_.seek(curr_position)
                    time.sleep(s)
                else:
                    self.callback(line)

    def getLine(self, n=10):
        PAGE = 4096
        with open(self.tailed_file, 'rb') as f:
            f_len = f.seek(0, 2)
            rem = f_len % PAGE
            r_len = rem if rem else PAGE
            while True:
                # 如果读取的页大小>=文件大小，直接读取数据输出
                if r_len >= f_len:
                    f.seek(0)
                    lines = f.readlines()[::-1]
                    print(lines)
                    break
                else:
                    f.seek(-r_len, 2)
                    count = f.read(r_len).decode().count("\n")
                    if count > n:  # 如果读取到的行数>=指定行数，则退出循环读取数据
                        f.seek(-r_len, 2)
                        lines = f.readlines()[-10:]
                        for x in lines:
                            self.getNewLine(x.decode().replace("\n", ""))
                        break
                    else:  # 如果读取行数不够，载入更多的页大小读取数据
                        r_len += PAGE

    def getNewLine(self, line):
        self.queue.append(line)
        self.ws.send_message_to_all(line)
        if len(self.queue) > 10:
            self.queue.pop(1)

    def new_client(self, client, server):
        for x in self.queue:
            self.ws.send_message(client, x)

    def websocket_server(self, port):
        self.ws = WebsocketServer(port, "0.0.0.0")
        self.ws.set_fn_new_client(self.new_client)
        t = Thread(target=self.ws.run_forever)
        t.setDaemon(True)
        t.start()
        print("websocket started listen at 8000")
        self.register_callback(self.getNewLine)

    def register_callback(self, func):
        """ Overrides default callback function to provided function. """
        self.callback = func

    def check_file_validity(self, file_):
        """ Check whether the a given file exists, readable and is a file """
        if not os.access(file_, os.F_OK):
            raise TailError("File '%s' does not exist" % file_)
        if not os.access(file_, os.R_OK):
            raise TailError("File '%s' not readable" % file_)
        if os.path.isdir(file_):
            raise TailError("File '%s' is a directory" % file_)


class TailError(Exception):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return self.message
