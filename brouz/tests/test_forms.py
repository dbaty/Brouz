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


class TestOrderInSchemas(TestCase):

    def _test_order(self, schema, expected):
        nodes = [node.name for node in schema.nodes]
        self.assertEqual(nodes, expected)

    def test_unique_transaction_schema_in_order(self):
        from brouz.forms import UniqueTransactionSchema
        self._test_order(
            UniqueTransactionSchema,
            ['csrf_token', 'party', 'title', 'date', 'category', 'amount',
             'vat', 'mean', 'invoice'])

    def test_composite_transaction_schema_in_order(self):
        from brouz.forms import CompositeTransactionSchema
        self._test_order(
            CompositeTransactionSchema,
            ['csrf_token', 'party', 'title', 'date', 'mean',
             'invoice', 'lines'])


class TestPermissiveFloat(TestCase):
    def _make_one(self):
        from brouz.forms import PermissiveFloat
        return PermissiveFloat()

    def test_remove_whitespaces(self):
        typ = self._make_one()
        node = None  # fake it
        self.assertEqual(typ.deserialize(node, ' 1 '), 1.0)
        self.assertEqual(typ.deserialize(node, '1 234.56'), 1234.56)

    def test_replace_comma(self):
        typ = self._make_one()
        node = None  # fake it
        self.assertEqual(typ.deserialize(node, '123,45'), 123.45)


class Clonable(object):
    def __init__(self, value, order):
        self._order = order
        self.value = value

    def clone(self):
        clone = Clonable('clone of %s' % self.value, self._order)
        return clone


class TestClone(TestCase):
    def _call_fut(self, to_clone, counter):
        from brouz.forms import clone
        return clone(to_clone, counter)

    def test_basics(self):
        from itertools import count
        counter = count(1)
        orig = Clonable('foo', next(counter))
        c = self._call_fut(orig, counter)
        self.assertEqual(c.value, 'clone of foo')
        self.assertEqual(c._order, 1 + orig._order)


class TestCategories(TestCase):

    def test_categories_do_not_overlap(self):
        pass  # FIXME: test that category values are all unique
