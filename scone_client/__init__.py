#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import socket
from functools import lru_cache
import logging

BUFFERSIZE = 8192
encoding = 'utf-8'
PROMPT = b'[PROMPT]'
SCONE_ERROR = '*****SCONE-ERROR*****'

__all__ = 'SconeClient SconeError'.split()


class SconeError(Exception):
    def __eq__(self, other):
        return isinstance(other, SconeError) and self.args == other.args

    def __hash__(self):
        return hash(id(self))


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
        return line

    @lru_cache(maxsize=512)
    def send(self, sentence):
        assert self.get_line() == PROMPT
        sentence = sentence.strip()
        logging.debug("S <- '{}'".format(sentence))

        sentence += '\n'
        self.sock.sendall(sentence.encode(encoding))
        response = self.get_line().decode(encoding)
        logging.debug("S -> '{}'".format(response))

        self.check_error(response)
        return response

    def predicate(self, sentence):
        response = self.send(sentence)

        assert response in ['YES', 'NO', 'MAYBE']
        return response

    def query(self, sentence):
        return self.send(sentence)

    def sentence(self, sentence):
        self.send.cache_clear()
        return self.send(sentence)

    def multi_sentence(self, sentences):
        retval = []
        for sentence in [x.strip() for x in sentences.split('\n')]:
            if not sentence:
                continue

            try:
                retval.append(self.send(sentence))
            except SconeError as e:
                retval.append(e)

        return retval

    def check_error(self, response):
        if response.startswith(SCONE_ERROR):
            reply = self.get_line()
            assert reply == b'NIL', "reply was <<{}>>".format(reply)
            msg = response.split('Error:')[1].strip('.')
            raise SconeError(msg)
