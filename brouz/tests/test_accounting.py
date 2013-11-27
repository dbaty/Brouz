from unittest import TestCase

from brouz import accounting


class TestPrice(TestCase):

    def test_repr(self):
        p = accounting.Price(1234)
        self.assertEqual(repr(p), '<Price: 12.34>')

    def test_text_repr(self):
        p = accounting.Price(1234)
        self.assertEqual(str(p), '12.34')

    def test_addition(self):
        p1 = accounting.Price(1234)
        p2 = accounting.Price(2345)
        summ = p1 + p2
        self.assertEqual(summ.eurocents, 3579)


class TestRoundedPrice(TestCase):

    def test_repr(self):
        p = accounting.RoundedPrice(1234)
        self.assertEqual(repr(p), '<RoundedPrice: 12 (12.34)>')

    def test_unicode_repr(self):
        p = accounting.RoundedPrice(1234)
        self.assertEqual(
            p.__html__(),
            '<abbr class="rounded-price" title="12.34">12</abbr>')


class TestSumRoundedPrices(TestCase):

    def _call_fut(self, *args):
        return accounting.sum_rounded_prices(*args)

    def test_it(self):
        self.assertEqual(self._call_fut(), accounting.Price(0))
        self.assertEqual(
            self._call_fut(accounting.RoundedPrice(2156),
                           accounting.RoundedPrice(2156)),
            accounting.Price(4400))


class TestCalculateAmortization(TestCase):

    def _call_fut(self, asset):
        return accounting.calculate_amortization(asset)

    def _make_asset(self, net_amount, vat, date):
        class DummyAsset(object):
            def __init__(self, net_amount, vat, date):
                self.net_amount = net_amount
                self.vat = vat
                self.date = date
        return DummyAsset(net_amount, vat, date)

    def test_first_year_is_full(self):
        from datetime import date
        asset = self._make_asset(3001, 1, date(2012, 1, 1))
        self.assertEqual(
            self._call_fut(asset),
            (accounting.RoundedPrice(1000),
             accounting.RoundedPrice(1000),
             accounting.RoundedPrice(1000)))

    def test_adjustment(self):
        from datetime import date
        asset = self._make_asset(3002, 1, date(2012, 1, 1))
        self.assertEqual(
            self._call_fut(asset),
            (accounting.RoundedPrice(1000),
             accounting.RoundedPrice(1000),
             accounting.RoundedPrice(1001)))

    def test_first_year_is_partial(self):
        from datetime import date
        asset = self._make_asset(459, 59, date(2012, 7, 5))
        self.assertEqual(
            self._call_fut(asset),
            (accounting.RoundedPrice(65),
             accounting.RoundedPrice(133),
             accounting.RoundedPrice(133),
             accounting.RoundedPrice(69)))
