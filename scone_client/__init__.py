#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import os
import socket
from functools import lru_cache
import logging
import uuid
import re

LOCAL_KNOWLEDGE_DIR = 'scone-knowledge.d'
SNAPSHOT_DIR = 'snapshots'


BUFFERSIZE = 8192
ENCODING = 'utf-8'
PROMPT = '[PROMPT]'
SCONE_ERROR = '*****SCONE-ERROR*****'

__all__ = 'SconeClient SconeError'.split()

logging.getLogger().setLevel(logging.DEBUG)


def iterate_files(path, callback):
    def walk(path):
        for root, dirs, files in os.walk(path):
            files = [x for x in sorted(files) if x.endswith('.lisp')]
            dirs.sort()
            if SNAPSHOT_DIR in dirs:
                del dirs[dirs.index(SNAPSHOT_DIR)]

            for f in files:
                callback(os.path.join(root, f))

    walk(path)
    walk(os.path.join(path, SNAPSHOT_DIR))


class SconeError(Exception):
    def __eq__(self, other):
        return isinstance(other, SconeError) and self.args == other.args

    def __hash__(self):
        return hash(id(self))



class SconeClient:
    def __init__(self, host='localhost', port=6517):
        super().__init__()
        self.buff = ''
        self.sock = socket.socket()
        self.sock.connect((host, port))
        self.load_local_knowledge()

    def close(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def read(self):
        return self.sock.recv(BUFFERSIZE).decode(ENCODING)

    def write(self, msg):
        self.sock.sendall(msg.encode(ENCODING))

    def load_local_knowledge(self):
        print(os.getcwd())
        if not os.path.exists(LOCAL_KNOWLEDGE_DIR):
            return

        logging.info("Uploading local knowledge...")
        iterate_files(LOCAL_KNOWLEDGE_DIR, self.load_local_file)

    def load_local_file(self, fname):
        logging.info("Loading '{}'".format(fname))

        try:
            sentence = '(load-kb "{}")'.format(os.path.abspath(fname))
            print(sentence)
            self.sentence(sentence)
        except SconeError as e:
            logging.error("{} returns '{}'".format(fname, e))
            raise SystemExit("Error loading '{}'.".format(fname))

    def get_line(self):
        self.buff = self.buff.lstrip()

        while '\n' not in self.buff:
            self.buff += self.read()

        line, self.buff = self.buff.split('\n', 1)
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
        assert line == PROMPT, "'{}'".format(line)

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
