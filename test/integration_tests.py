# -*- coding: utf-8; mode: python -*-

from unittest import TestCase
from scone_client import SconeClient, SconeError

from doublex import assert_that, is_


class ClientTests(TestCase):
    @classmethod
    def setupClass(self):
        SconeClient().query('(new-indv {checkpoint} {thing})')

    @classmethod
    def tearDownClass(self):
        SconeClient().query('(remove-elements-after {checkpoint})')
        SconeClient().query('(remove-last-element)')

    def setUp(self):
        self.sut = SconeClient()

    def test_close(self):
        self.sut.close()

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
        expected_msg = 'The function COMMON-LISP-USER::MISSING-FUNCTION is undefined.'

        try:
            self.sut.predicate('(missing-function)')
            self.fail('exception should be raised!')
        except SconeError as e:
            assert_that(str(e), is_(expected_msg))

    def test_new_indv(self):
        response = self.sut.query('(new-indv {Marta} {elephant})')
        assert_that(response, is_('{Marta}'))

    def test_new_is_a_OK(self):
        response = self.sut.query('(new-indv {Carlos} {thing})')
        assert_that(response, is_('{Carlos}'))

        response = self.sut.query('(new-is-a {Carlos} {bird})')
        assert_that(response[:8], is_('{Is-A 0-'))

    def test_new_is_a_FAIL(self):
        response = self.sut.query('(new-indv {Daniel} {elephant})')
        assert_that(response, is_('{Daniel}'))

        expected_msg = '{Daniel} cannot be a {bird}.'

        try:
            response = self.sut.query('(new-is-a {Daniel} {bird})')
            self.fail('exception should be raised!')
        except SconeError as e:
            assert_that(str(e), is_(expected_msg))
