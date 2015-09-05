# -*- coding: utf-8 -*-

"""Utility functions."""

from __future__ import division
import datetime
from decimal import Decimal

from brouz import enums


VAT_INSTALLMENT_DATES = (
    # (label, month, day)
    ("Acompte d'avril", 3, 31),
    ("Acompte de juillet", 6, 30),
    ("Acompte de septembre", 9, 30),
    (u"Acompte de décembre", 11, 30),
    (u"Régularisation année + 1", 12, 31))

MEAL_DEDUCTIONS = {
    # amounts are tax included
    # FIXME: add value for 2012
    2013: {'base': 455, 'max': 1770},
    }


class Price(object):

    def __init__(self, value):
        if isinstance(value, Price):
            eurocents = value.eurocents
        elif isinstance(value, int):
            eurocents = value
        else:
            raise NotImplementedError()
        self.eurocents = eurocents

    def __eq__(self, rhs):
        if not isinstance(rhs, Price):
            raise NotImplementedError()
        return self.eurocents == rhs.eurocents

    def __lt__(self, rhs):
        if not isinstance(rhs, Price):
            raise NotImplementedError()
        return self.eurocents < rhs.eurocents

    def __le__(self, rhs):
        if not isinstance(rhs, Price):
            raise NotImplementedError()
        return self.eurocents <= rhs.eurocents

    def __add__(self, rhs):
        if isinstance(rhs, self.__class__):
            rhs = rhs.eurocents
        elif isinstance(rhs, int):
            pass  # use 'rhs' value
        else:
            raise NotImplementedError()
        return self.__class__(self.eurocents + rhs)

    def __radd__(self, lhs):
        return self.__add__(lhs)

    def __sub__(self, rhs):
        return self.__add__(-rhs)

    def __rsub__(self, lhs):
        return lhs + self.__class__(-self.eurocents)

    def __abs__(self):
        return self.__class__(abs(self.eurocents))

    def __neg__(self):
        return self.__class__(-self.eurocents)

    def __repr__(self):
        return '<Price: %s>' % numeric_eurocents_to_text_euros(self.eurocents)

    def __unicode__(self):
        return numeric_eurocents_to_text_euros(self.eurocents)

    __str__ = __unicode__


class RoundedPrice(Price):

    @property
    def rounded_euros(self):
        return int(round(Decimal(self.eurocents) / 100))

    @property
    def rounded_eurocents(self):
        return self.rounded_euros * 100

    def __repr__(self):
        return '<RoundedPrice: %d (%s)>' % (
            self.rounded_euros,
            numeric_eurocents_to_text_euros(self.eurocents))

    def __html__(self):
        return '<abbr class="rounded-price" title="%s">%s</abbr>' % (self, self.rounded_euros)


def sum_rounded_prices(*prices):
    """Return the sum of ``prices`` as an instance of ``Price``.

    The sum of rounded prices is not the rounded sum of the prices.
    """
    total = RoundedPrice(0)
    for price in prices:
        if isinstance(price, RoundedPrice):
            total += price.rounded_eurocents
        elif isinstance(price, Price):
            total += price.eurocents
        else:
            total += price
    return total


def numeric_euros_to_numeric_eurocents(euros):
    """Convert a numeric amount in euros to a numeric amount in
    eurocents.

    This function always returns an integer.

    >>> numeric_euros_to_numeric_eurocents(12.00)
    1200
    """
    return int(Decimal(u'{0:0.2f}'.format(euros)) * 100)


def numeric_eurocents_to_text_euros(eurocents, separator='.'):
    """Convert a numeric amount in eurocents to a text amount in
    euros.

    ``eurocents`` must be an integer (or something that converts to an
    integer without loss of precision). Otherwise, a ``TypeError`` is
    raised.

    The returned is a string. It always contains two digits after the
    separator. It does *not* contain any currency symbol.

    >>> text_euros_to_numeric_eurocents(1234)
    12.34
    >>> text_euros_to_numeric_eurocents(1200)
    12,00
    >>> text_euros_to_numeric_eurocents(1234, separator=',')
    12,34
    """
    eurocents = int(eurocents)
    s = '{0:0.2f}'.format(Decimal(eurocents) / 100)
    if separator != '.':
        s = s.replace('.', separator)
    return s


def calculate_amortization(asset):
    """Calculate amortization of the given ``asset``.

    This function returns a tuple of amortizations starting from
    ``asset.date``.

    ``amount`` is rounded because this is how it should be displayed
    in the paper form.
    """
    base = asset.net_amount - asset.vat
    amortization = []
    # The rate is fixed, the amortization is linear.
    n_years = 3
    rest = base
    first_prorata = (360 - (30 * (asset.date.month - 1) + asset.date.day - 1)) / 360.0
    prorata = first_prorata
    while rest > 0:
        amount = int((prorata * base) // n_years)
        amount = min(rest, amount)
        rest -= amount
        amortization.append(RoundedPrice(amount))
        prorata = 1.0  # for year 2 and later
    expected_duration = n_years
    if first_prorata != 1.0:
        expected_duration += 1
    if len(amortization) != expected_duration:
        # Adjustment: because of the rounding, we may have a very
        # small amount left to amortize for the last year. For
        # example, on 3 years with an amount of 3001 EUR, we would
        # have three years at 1000 EUR (3001 // 3), and a fourth year
        # with 1 EUR. In this case, we combine the last two years (in
        # this example, that would be 1000, 1000 and 1001 EUR.
        last = amortization.pop(-1)
        amortization[-1] += last
    assert len(amortization) == expected_duration
    assert sum(amortization).eurocents == base
    return tuple(amortization)


def calculate_vat_installments(transactions, year):
    """Given a Transaction query, return a list of VAT installments.

    This function returns a list of dictionaries with the following
    keys: ``total``, ``deductible`` and ``billed``. All amounts are
    instances of ``RoundedPrice``.
    """
    # Avoid circular import of 'brouz.models'
    Transaction = transactions._entities[0].entities[0]
    start = datetime.date(year, 1, 1)
    installments = []
    for label, month, day in VAT_INSTALLMENT_DATES:
        end = datetime.date(year, month, day)
        installment = {
            'label': label,
            'billed': 0,
            'deductible': 0,
            'billed_base': 0,
            'deductible_base': 0,
            'total': 0}
        for txn in transactions.filter(Transaction.date.between(start, end)):
            billed_vat, billed_base = get_billed_vat(txn)
            deductible_vat, deductible_base = get_deductible_vat(txn)
            installment['billed'] += billed_vat
            installment['deductible'] += deductible_vat
            installment['billed_base'] += billed_base
            installment['deductible_base'] += deductible_base
        installment['total'] = installment['billed'] - installment['deductible']
        for key in ('billed', 'deductible', 'billed_base', 'deductible_base', 'total'):
            installment[key] = RoundedPrice(installment[key])
        installments.append(installment)
        start = end + datetime.timedelta(days=1)
    return installments


def get_deductible_vat(transaction):
    if transaction.type != enums.TYPE_EXPENDITURE:
        return 0, 0
    if transaction.is_meal:
        return 0, 0
    # Gotcha: this assumes that VAT is set **only** on transactions
    # where it is deductible.
    if not transaction.vat:
        return 0, 0
    base = abs(transaction.signed_amount - transaction.vat)
    return Price(transaction.vat), Price(base)


def get_billed_vat(transaction):
    if transaction.type != enums.TYPE_INCOME:
        return 0, 0
    base = transaction.signed_amount - transaction.vat
    return Price(transaction.vat), base


def get_meal_deductible(transaction):
    if not transaction.is_meal:
        return transaction.net_amount
    deductible = MEAL_DEDUCTIONS[transaction.date.year]
    return max(min(deductible['max'], transaction.net_amount) - deductible['base'], 0)
