#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import socket

BUFFERSIZE = 8192
encoding = 'utf-8'
PROMPT = b'[PROMPT]'
SCONE_ERROR = '*****SCONE-ERROR*****'

__all__ = 'SconeClient SconeError'.split()


class SconeError(Exception):
    pass


class SconeClient:
    def __init__(self, host='localhost', port=6517):
        self.sock = socket.socket()
        self.sock.connect((host, port))
        self.buffer = b''

    def close(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def get_line(self):
        def next_line(where):
            line, self.buffer = where.split(b'\n', 1)
            return line

        if b'\n' in self.buffer:
            return next_line(self.buffer)

        data = bytes()
        while b'\n' not in data:
            data += self.sock.recv(BUFFERSIZE)

        line = next_line(data)
        # print("get-line rest:", self.buffer)
        return line

    def send(self, sentence):
        assert self.get_line() == PROMPT
        sentence = sentence.strip() + '\n'
        self.sock.sendall(sentence.encode(encoding))
        response = self.get_line().decode(encoding)
        self.check_error(response)
        return response

    def predicate(self, sentence):
        response = self.send(sentence)

        assert response in ['YES', 'NO', 'MAYBE']
        return response

    def query(self, sentence):
        return self.send(sentence)

    def check_error(self, response):
        if response.startswith(SCONE_ERROR):
            assert self.get_line() == b'NIL'
            msg = response.split('Error:')[1]
            raise SconeError(msg)
