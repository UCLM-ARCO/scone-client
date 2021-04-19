#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import socket
from functools import lru_cache
import logging
import uuid
import re

BUFFERSIZE = 8192
ENCODING = 'utf-8'
PROMPT = '[PROMPT]'
SCONE_ERROR = '*****SCONE-ERROR*****'

__all__ = 'SconeClient SconeError'.split()


class SconeError(Exception):
    def __eq__(self, other):
        return isinstance(other, SconeError) and self.args == other.args

    def __hash__(self):
        return hash(id(self))


class BaseSconeClient:
    def __init__(self):
        self.buff = ''

    def get_line(self):
        def next_line(where):
            line, self.buff = where.split('\n', 1)
            return line

        self.buff = self.buff.lstrip()

        if '\n' in self.buff:
            return next_line(self.buff)

        data = ""
        while '\n' not in data:
            data += self.read()

        line = next_line(data)
        return line

    def get_reply(self):
        reply = self.get_line()
        if not reply.startswith('('):
            return reply

        while not reply.endswith(')'):
            reply += self.get_line()

        return reply

    def read_until(self, flag):
        while flag not in self.buff:
            self.buff += self.read()

        retval, self.buff = self.buff.split(flag, 1)
        return retval

    @lru_cache(maxsize=512)
    def send(self, sentence):
        line = self.get_line()
        assert line == PROMPT, line

        sentence = sentence.strip()
        if sentence[0] != '(' or sentence[-1] != ')':
            raise SconeError("Bad input format: '{}'".format(sentence))

        logging.debug("S <- '{}'".format(sentence))

        sentence += '\n'
        self.write(sentence)
        response = self.get_reply()
        logging.debug("S -> '{}'".format(response))

        self.check_error(response)
        return response

    def predicate(self, sentence):
        response = self.send(sentence)

        if response not in ['YES', 'NO', 'MAYBE']:
            reason = "Sentence '{}' was not a predicate: '{}'".format(
                sentence, response)
            raise SconeError(reason)

        return response

    def query(self, sentence):
        return self.send(sentence)

    def sentence(self, sentence):
        self.send.cache_clear()
        return self.send(sentence)

    def multi_sentence(self, sentences):
        checkpoint = 'checkpoint-{}'.format(uuid.uuid1())
        self.sentence('(new-indv {%s} {thing})' % checkpoint)

        retval = []
        for sentence in [x.strip() for x in sentences.split('\n')]:
            if not sentence:
                continue

            try:
                retval.append(self.send(sentence))
            except SconeError as e:
                self.sentence('(remove-elements-after {%s})' % checkpoint)
                self.sentence('(remove-last-element)')

                reason = "The sentence '{}' raises '{}'".format(sentence, str(e))
                raise SconeError(reason)

        return retval

    def check_error(self, response):
        if response.startswith(SCONE_ERROR):
            reply = response + self.read_until('NIL')
            reply = re.sub('\s+',' ', reply.strip())
            msg = reply.split('Error:')[1].strip('.')
            raise SconeError(msg)

    def read(self):
        raise NotImplementedError

    def write(self, msg):
        raise NotImplementedError

    def close(self):
        pass


class PipeSconeClient(BaseSconeClient):
    def __init__(self, stdin, stdout):
        super().__init__()
        self.stdin = stdin
        self.stdout = stdout

    def read(self):
        return self.stdin.read()

    def write(self, msg):
        written = 0
        while written < len(msg):
            written += self.stdout.write(msg[written:])


class SconeClient(BaseSconeClient):
    def __init__(self, host='localhost', port=6517):
        super().__init__()
        self.sock = socket.socket()
        self.sock.connect((host, port))

    def close(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def read(self):
        return self.sock.recv(BUFFERSIZE).decode(ENCODING)

    def write(self, msg):
        self.sock.sendall(msg.encode(ENCODING))
