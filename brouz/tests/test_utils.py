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
