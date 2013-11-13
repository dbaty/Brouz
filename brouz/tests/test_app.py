from unittest import TestCase


class TestApp(TestCase):

    def test_make_app(self):
        from pyramid.router import Router
        from brouz.app import make_app
        global_settings = {}
        settings = {'brouz.db_url': 'sqlite://',
                    'brouz.secret': 'secret'}
        wsgi_app = make_app(global_settings, **settings)
        self.assertIsInstance(wsgi_app, Router)
