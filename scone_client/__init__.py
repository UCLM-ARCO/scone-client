#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import socket
from functools import lru_cache
import logging
import uuid

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
        self.buff = b''

    def close(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def get_line(self):
        def next_line(where):
            line, self.buff = where.split(b'\n', 1)
            return line

        if b'\n' in self.buff:
            return next_line(self.buff)

        data = bytes()
        while b'\n' not in data:
            data += self.sock.recv(BUFFERSIZE)

        line = next_line(data)
        return line

    def get_reply(self):
        reply = self.get_line()
        if not reply.startswith(b'('):
            return reply

        while not reply.endswith(b')'):
            reply += self.get_line()

        return reply

    @lru_cache(maxsize=512)
    def send(self, sentence):
        line = self.get_line()
        assert line == PROMPT, line

        sentence = sentence.strip()
        if sentence[0] != '(' or sentence[-1] != ')':
            raise SconeError("Bad input format: '{}'".format(sentence))

        logging.debug("S <- '{}'".format(sentence))

        sentence += '\n'
        self.sock.sendall(sentence.encode(encoding))
        response = self.get_reply().decode(encoding)
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
            reply = self.get_line()
            assert reply == b'NIL', "reply was '{}'".format(reply)
            msg = response.split('Error:')[1].strip('.')
            raise SconeError(msg)
