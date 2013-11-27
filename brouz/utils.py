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
        # FIXME: still needed?
        #self.format_num = format_number_with_trailing_zeroes(locale_name)

    def route_url(self, route_name, *elements, **kw):
        return self.request.route_url(route_name, *elements, **kw)

    def static_url(self, path, **kw):
        if ':' not in path:
            path = 'brouz:%s' % path
        return self.request.static_url(path, **kw)


def format_number_with_trailing_zeroes(locale_name):  # FIXME: probably useless now
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
