"""Base utilities and classes for our tests."""


from unittest import TestCase

from pyramid import testing
from pyramid.testing import DummyRequest as BaseRequest


def get_testing_db_session():
    from brouz.models import DBSession
    from brouz.models import initialize_sql
    initialize_sql('sqlite://')
    return DBSession


class DummyRequest(BaseRequest):
    # Override 'route_url()' because the one in 'testing.DummyRequest'
    # requires a route mapper to be registered.
    def route_url(self, route_name, *elements, **kwargs):
        return route_name

    # A short cut to access flash messages in tests.
    def get_flash(self, queue):
        return self.session.get('_f_%s' % queue, [])


class TestCaseForViews(TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.session = get_testing_db_session()

    def tearDown(self):
        testing.tearDown()
        self.session.remove()

    def _make_renderer(self, template_under_test):
        return self.config.testing_add_renderer(template_under_test)

    def _make_request(self, post=None, get=None, matchdict=None):
        if post is not None:
            from webob.multidict import MultiDict
            post = MultiDict(post)
        request = DummyRequest(params=get, post=post)
        if matchdict is not None:
            request.matchdict = matchdict
        return request
