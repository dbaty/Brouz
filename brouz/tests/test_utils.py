from unittest import TestCase


class TestFormatNumber(TestCase):

    def _get_formatter(self, locale_name):
        from brouz.utils import format_number_with_trailing_zeroes
        return format_number_with_trailing_zeroes(locale_name)

    def test_fr(self):
        format = self._get_formatter('fr')
        self.assertEqual(format(0), '0,00')
        self.assertEqual(format(0.0), '0,00')
        self.assertEqual(format(0.4), '0,40')
        self.assertEqual(format(123.45), '123,45')
        self.assertEqual(format(1123.45), u'1\xa0123,45')

    def test_en(self):
        format = self._get_formatter('en')
        self.assertEqual(format(0), '0.00')
        self.assertEqual(format(0.0), '0.00')
        self.assertEqual(format(0.4), '0.40')
        self.assertEqual(format(123.45), '123.45')
        self.assertEqual(format(1123.45), '1,123.45')

    def test_bogus_approximations(self):
        format = self._get_formatter('fr')
        self.assertEqual(format(2389.97), u'2\xa0389,97')        


class TestCalculateAmortization(TestCase):

    def _call_fut(self, asset):
        from brouz.utils import calculate_amortization
        return calculate_amortization(asset)

    def _make_asset(self, amount, vat, date):
        class DummyAsset(object):
            def __init__(self, amount, vat, date):
                self.amount = amount
                self.vat = vat
                self.date = date
        return DummyAsset(amount, vat, date)

    def test_first_year_is_full(self):
        from datetime import date
        asset = self._make_asset(3001, 1, date(2012, 1, 1))
        self.assertEqual(self._call_fut(asset), (1000.0, 1000.0, 1000.0))

    def test_adjustment(self):
        from datetime import date
        asset = self._make_asset(3002, 1, date(2012, 1, 1))
        self.assertEqual(self._call_fut(asset), (1000.33, 1000.33, 1000.34))

    def test_first_year_is_partial(self):
        from datetime import date
        asset = self._make_asset(459, 59, date(2012, 7, 5))
        self.assertEqual(self._call_fut(asset),
                         (65.19, 133.33, 133.33, 68.15))
