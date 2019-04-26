# !/usr/bin/env python3

from websocket_server import WebsocketServer
from tail import Tail
import logging, os
import json

"""
客户端 message 限定
1 结构为 {'type':0,'command':'','args':[]}
type int 值 1 心跳包维持 2 事件维持 3 暂定保留
command str 值为方法名
"""


class Server(WebsocketServer):
    tails: list = []

    def __init__(self, port, host='127.0.0.1', loglevel=logging.WARNING):
        super().__init__(port, host, loglevel)
        self.set_fn_message_received(self.c_message_received)

    def new_client(self, client, server):
        server.c_send_message(client, Server.getReturnMessage(0, 'connect success'))

    @staticmethod
    def getReturnMessage(status, msg, data=None):
        if data is None:
            data = {}
        return {'status': status, 'msg': msg, 'data': data}

    def c_send_message(self, client, msg):
        if isinstance(msg, dict):
            msg = json.dumps(msg)
        elif isinstance(msg, list):
            msg = json.dumps(msg)
        else:
            pass
        self.send_message(client, msg)

    def c_send_message_to_all(self, msg):
        for client in self.clients:
            self._unicast_(client, msg)

    def c_send_message_for_tags(self, tags, msg):
        for client in self.clients:
            if client['tags'].find(tags) == -1:
                self._unicast_(client, msg)

    def c_message_received(self, client, server, message):
        try:
            message = json.dumps(message)
        except Exception as e:
            server.send_message(self, client, Server.getReturnMessage(-1, '参数错误'))
        if isinstance(message, dict):
            server.send_message(self, client, Server.getReturnMessage(-1, '参数错误'))

        if message['command'] == 'addDirectory':
            return self.addDirectory(client, *message['args'])
        elif message['command'] == 'addFilename':
            return self.addFilename(client, *message['args'])
        else:
            self.c_send_message(client, self.getReturnMessage(-2, 'method not found', []))

    def addDirectory(self, client, path):
        path = os.path.abspath(path)
        for filename in os.listdir(path):
            pathname = os.path.join(path, filename)
            if os.path.isfile(pathname) and not filename.find('log') == -1:
                if not client['tags'].find(pathname) == -1:
                    client['tags'].append(pathname)
                is_in = False
                for tail in self.tails:
                    if tail.tailed_file == pathname:
                        is_in = True
                        break
                if not is_in:
                    self.tails.append(Tail(pathname, self))

    def addFilename(self, client, filepath):
        filepath = os.path.abspath(filepath)
        if not filepath.find('log') == -1:
            if not client['tags'].find(filepath) == -1:
                client['tags'].append(filepath)
            is_in = False
            for tail in self.tails:
                if tail.tailed_file == filepath:
                    is_in = True
                    break
            if not is_in:
                self.tails.append(Tail(filepath, self))


if __name__ == '__main__':
    server = Server(8000)
    server.run_forever()
