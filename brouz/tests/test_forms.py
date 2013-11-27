from unittest import TestCase


class TestAddTransactionForm(TestCase):

    def setUp(self):
        from brouz.tests.base import get_testing_db_session
        self.session = get_testing_db_session()

    def tearDown(self):
        self.session.remove()

    def _make_one(self, project_id=None, data=None):
        pass  # FIXME

    # FIXME: add tests


class TestCategories(TestCase):

    def test_categories_do_not_overlap(self):
        pass  # FIXME: test that category values are all unique
