# -*- coding: utf-8; mode: python -*-

import sys
from unittest import TestCase

sys.path.append('src')
from scone_client import iterate_files


class ProcessKnowledge(TestCase):
    def test_iterate_alphabetic_order(self):
        visited = []
        iterate_files('test/knowledge1', visited.append)

        self.assertEquals(visited,
                          ['test/knowledge1/00.lisp',
                           'test/knowledge1/02.lisp',
                           'test/knowledge1/01/03.lisp',
                           'test/knowledge1/03/05.lisp',
                           'test/knowledge1/03/01/02.lisp',
                           'test/knowledge1/zz/00.lisp',
                           'test/knowledge1/snapshots/00.lisp'])
