import babel.core
import babel.dates
import babel.numbers

from pyramid.i18n import get_locale_name
from pyramid.renderers import get_renderer


class TemplateAPI(object):
    """Provide a master template and various information and utilities
    that can be used in any template.
    """
    def __init__(self, request, current_page):
        self.request = request
        self.layout = get_renderer('templates/layout.pt').implementation()
        self.current_page = current_page
        self.notifications = {
            'success': self.request.session.pop_flash('success'),
            'error': self.request.session.pop_flash('error')}
        locale_name = get_locale_name(request)
        self.format_date = lambda d: babel.dates.format_date(
            d, 'medium', locale_name)
        self.format_num = format_number_with_trailing_zeroes(locale_name)

    def route_url(self, route_name, *elements, **kw):
        return self.request.route_url(route_name, *elements, **kw)

    def static_url(self, path, **kw):
        if ':' not in path:
            path = 'brouz:%s' % path
        return self.request.static_url(path, **kw)


def format_number_with_trailing_zeroes(locale_name):
    """Return a callable that format number and always include two
    digits after the separator.

    By default, Babel removes trailing '0' from formatted numbers
    (e.g., it returns '1.2', not '1.20'). I would like to always have
    2 digits.
    """
    locale = babel.core.Locale.parse(locale_name)
    pattern = locale.decimal_formats.get(None)
    # It must be '(2, 3)', not '(2, 2)'. I am not sure why, but
    # formatting is wrong with the latter. See
    # 'test_bogus_approximation()' for an example.
    # FIXME: still needed?
    pattern.frac_prec = (2, 3)
    def formatter(num):
        num = round(num, 2)
        return pattern.apply(num, locale)
    return formatter


def calculate_amortization(asset):
    """Calculate amortization of the given ``asset``.

    This function returns a tuple of amortizations starting from
    ``asset.date``.
    """
    base = asset.amount - asset.vat
    amortization = []
    # The rate is fixed, the amortization is linear.
    n_years = 3
    rest = base
    prorata = (360 - (30 * (asset.date.month - 1) + asset.date.day - 1)) / 360.0
    while rest > 0:
        amount = (prorata * base) / n_years
        amount = round(amount, 2)
        # only applicable for the first year when it is not complete
        prorata = 1.0 
        if rest <= amount:
            amount = rest
        rest -= amount
        rest = round(rest, 2)
        amortization.append(amount)
    # Adjustment: because of rounding, we may have a very small amount
    # to be left to amortize for the last year. For example, on 3
    # years with an amount of 3001 EUR, we would have three years at
    # 1000 EUR (3001 / 3 rounded), and a fourth year with 1 EUR. In
    # this case, we combine the last two years (in this example, that
    # would be 1000, 1000 and 1001 EUR.
    if amortization[-1] <= 1:
        last = amortization.pop(-1)
        amortization[-1] += last
    assert round(sum(amortization), 2) == round(base, 2)
    return tuple(amortization)
