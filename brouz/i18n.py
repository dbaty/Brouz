"""Define our own locale negotiator that looks at the browser
preferences, as well as the ``_`` translation function.
"""

from pyramid.i18n import TranslationStringFactory

from webob.acceptparse import NilAccept


_ = TranslationStringFactory('brouz')


def locale_negotiator(request):
    """Return a locale name by looking at the ``Accept-Language`` HTTP
    header.
    """
    settings = request.registry.settings
    available_languages = settings['pyramid.available_languages'].split()
    header = request.accept_language
    if isinstance(header, NilAccept):
        # If the header is absent or empty, we get a 'NilAccept'
        # object, whose 'best_match()' method returns the first item
        # in 'available_languages'. This may or may not be our default
        # locale name, so here we will work around this.
        return None
    return header.best_match(available_languages)
