# -*- coding: utf-8; mode: python -*-

import os
import io
import signal
from pathlib import Path

from unittest import TestCase
from scone_client import SconeClient, SconeError

from commodity.os_ import SubProcess, PIPE
from commodity.testing import SubProcessMixin, assert_that, wait_that, is_not
from commodity.net import localhost, listen_port
from hamcrest import is_


class ServerMixin(TestCase, SubProcessMixin):
    port = 6517

    def tearDown(self):
        self.sut.sentence('(remove-elements-after {checkpoint})')
        self.sut.sentence('(remove-last-element)')
        self.sut.close()

    def start_server(self, cwd=None):
        pid_file = Path(cwd) / Path('.scone/server.pid')
        pid_file.unlink(missing_ok=True)
        assert_that(localhost, is_not(listen_port(self.port)))

        self.scone = SubProcess('scone-server',
                                stdout=io.BytesIO(), stderr=io.BytesIO(),
                                signal=signal.SIGINT,
                                cwd=cwd)
        self.addSubProcessCleanup(self.scone)
        wait_that(localhost, listen_port(self.port))

        self.sut = SconeClient()
        self.sut.sentence('(new-indv {checkpoint} {thing})')


class ClientTests(ServerMixin):
    def setUp(self):
        self.start_server()

    def test_predicate_yes(self):
        self.sut.predicate('(is-x-a-y? {bird} {animal})')

    def test_predicate_redundant_blanks(self):
        response = self.sut.predicate('\n\n\n(is-x-a-y? {bird} {animal})\n\n\n')
        assert_that(response, is_('YES'))

    def test_predicate_no(self):
        response = self.sut.predicate('(is-x-a-y? {bird} {mammal})')
        assert_that(response, is_('NO'))

    def test_predicate_maybe(self):
        response = self.sut.predicate('(is-x-a-y? {broom} {air transport})')
        assert_that(response, is_('MAYBE'))

    def test_predicate_error(self):
        expected_msg = 'The function COMMON-LISP-USER::MISSING-FUNCTION is undefined'

        try:
            self.sut.predicate('(missing-function)')
            self.fail('exception should be raised!')
        except SconeError as e:
            assert_that(str(e), is_(expected_msg))

    def test_new_indv(self):
        response = self.sut.sentence('(new-indv {Marta} {elephant})')
        assert_that(response, is_('{Marta}'))

    def test_new_is_a_OK(self):
        response = self.sut.sentence('(new-indv {Carlos} {thing})')
        assert_that(response, is_('{Carlos}'))

        response = self.sut.sentence('(new-is-a {Carlos} {bird})')
        assert_that(response[:8], is_('{Is-A 0-'))

    def test_new_is_a_FAIL(self):
        response = self.sut.sentence('(new-indv {Daniel} {elephant})')
        assert_that(response, is_('{Daniel}'))

        expected_msg = '{Daniel} cannot be a {bird}'

        try:
            response = self.sut.sentence('(new-is-a {Daniel} {bird})')
            self.fail('exception should be raised!')
        except SconeError as e:
            assert_that(str(e), is_(expected_msg))

    def test_multi_sentence(self):
        sentences = '''
        (new-indv {Maria} {tiger})
        (new-indv {Oscar} {bat})
        (new-indv {Felix} {monkey})
        (is-x-a-y? {Maria} {lion})
        (is-x-a-y? {Oscar} {mammal})
        (is-x-a-y? {Julio} {bird})
        '''

        responses = self.sut.multi_sentence(sentences)

        expected = [
            '{Maria}',
            '{Oscar}',
            '{Felix}',
            'NO',
            'YES',
            'MAYBE',
        ]

        assert_that(responses, is_(expected))

    def test_multi_sentence_FAIL(self):
        sentences = '''
        (new-indv {Lucia} {tiger})
        (new-is-a {Lucia} {bird})
        '''

        try:
            self.sut.multi_sentence(sentences)
            self.fail('exception should be raised')
        except SconeError as e:
            expected = "The sentence '(new-is-a {Lucia} {bird})' raises '{Lucia} cannot be a {bird}'"
            self.assertEquals(expected, str(e))

        self.assertEquals('MAYBE',
                          self.sut.sentence('(is-x-a-y? {Lucia} {tiger})'))

    def test_checkpoint(self):
        response = self.sut.sentence('(new-indv {Mork} {mammal})')
        assert_that(response, is_('{Mork}'))

        response = self.sut.sentence('(checkpoint-new "/tmp/kkk.lisp")')
        assert_that(response, is_('NIL'))

    def test_query(self):
        assert self.scone
        self.assertEquals(
            self.sut.send('(is-x-a-y? {elephant} {mammal})'), 'YES')

    def test_exception(self):
        assert self.scone

        try:
            self.sut.send('(new-is-a {elephant} {bird})')
            self.fail('exception should be raised')
        except SconeError as e:
            self.assertEquals('{elephant} cannot be a {bird}', str(e))


class LocalKnowledgeTest(ServerMixin):
    def test_local_knowledge_ok(self):
        self.start_server(cwd='test/knowledge_ok')
        self.assertEquals(
            self.sut.predicate('(is-x-a-y? {Felix} {monkey})'), 'YES')

    def test_local_knowledge_error(self):
        self.start_server(cwd='test/knowledge_error')

        expected = b"Error loading 'scone-knowledge.d/martin.lisp'"
        actual = self.scone.errsink.getvalue()
        print(actual.decode('utf-8'))
        self.assertIn(expected, actual)

#    def test_checkpoint_save_and_restore(self):
#        test_dir = 'test/knowledge_ok/'
#        checkpoint_path = os.path.join(os.getcwd(), test_dir,
#                                       'scone-knowledge.d/snapshots')
#        checkpoint_file = os.path.join(checkpoint_path, 'birds.lisp')
#
#        if os.path.exists(checkpoint_file):
#            os.remove(checkpoint_file)
#
#        self.server = Popen(self.cmd.split(), cwd=test_dir)
#        wait_that(localhost, listen_port(5001))
#        self.addCleanup(self.server.terminate)
#
#        self.scone.request('(new-indv {Jesus} {bird})')
#        self.scone.checkpoint('birds')
#        os.system('sync')
#
#        print(os.getcwd())
#        print(checkpoint_file)
#        self.assert_(os.path.exists(checkpoint_file))
#        self.addCleanup(partial(os.remove, checkpoint_file))
#
#        self.server.terminate()
#        wait_that(localhost, is_not(listen_port(5001)))
#
#        self.server = Popen(self.cmd.split(), cwd=test_dir)
#        wait_that(localhost, listen_port(5001))
#        self.addCleanup(self.server.terminate)
#
#        self.assertEquals(
#            self.scone.request('(is-x-a-y? {Jesus} {bird})'), 'YES')
#
#    def test_overwrite_checkpoint(self):
#        test_dir = 'test/knowledge_ok/'
#        checkpoint_path = os.path.join(os.getcwd(), test_dir,
#                                       'scone-knowledge.d/snapshots')
#        checkpoint_file = os.path.join(checkpoint_path, 'birds.lisp')
#
#        if os.path.exists(checkpoint_file):
#            os.remove(checkpoint_file)
#
#        self.server = Popen(self.cmd.split(), cwd=test_dir)
#        wait_that(localhost, listen_port(5001))
#        self.addCleanup(self.server.terminate)
#
#        self.scone.request('(new-indv {Jesus} {bird})')
#        self.scone.checkpoint('birds')
#
#        self.scone.request('(new-indv {Paco} {bird})')
#
#        try:
#            self.scone.checkpoint('birds')
#            self.fail('exception should was raised')
#        except Semantic.FileError:
#            pass
#
