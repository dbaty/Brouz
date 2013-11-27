from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig

from brouz.models import initialize_sql


def make_app(global_settings, **settings):
    """Set up and return the WSGI application."""
    config = Configurator(settings=settings)

    # Third-party includes
    config.include('pyramid_chameleon')

    # Initialize database and ORM
    db_verbose = settings.get('brouz.db_verbose', 'false').lower() == 'true'
    initialize_sql(settings['brouz.db_url'], echo=db_verbose)

    # Sessions
    session_secret = settings['brouz.secret']
    session_factory = UnencryptedCookieSessionFactoryConfig(session_secret)
    config.set_session_factory(session_factory)

    # Routes and views
    config.add_static_view('static', 'static')
    config.add_static_view('static-deform', 'deform:static')
    config.add_route('home', '/')
    config.add_view('.views.home', route_name='home')
    config.add_route('reports', '/reports')
    config.add_route('reports_specific_year', '/reports/{year}')
    config.add_view('brouz.views.reports', route_name='reports')
    config.add_view('brouz.views.reports', route_name='reports_specific_year')
    config.add_route('add-unique', '/add-unique')
    config.add_view('brouz.views.add_unique_form', route_name='add-unique',
                    request_method='GET')
    config.add_view('brouz.views.add_unique', route_name='add-unique',
                    request_method='POST')
    config.add_route('add-composite', '/add-composite')
    config.add_view('brouz.views.add_composite_form',
                    route_name='add-composite', request_method='GET')
    config.add_view('brouz.views.add_composite', route_name='add-composite',
                    request_method='POST')
    config.add_route('autocomplete', '/autocomplete/{field}')
    config.add_view('brouz.views.autocomplete', route_name='autocomplete',
                    renderer='json')
    config.add_route('edit', '/edit/{transaction_id}')
    config.add_view('brouz.views.edit_form', route_name='edit',
                    request_method='GET')
    config.add_view('brouz.views.edit', route_name='edit',
                    request_method='POST')
    config.add_route('delete', '/delete/{transaction_id}',
                     request_method='POST')
    config.add_view('brouz.views.delete', route_name='delete')

    # Internationalization
    config.add_translation_dirs('brouz:locale')
    config.set_locale_negotiator('brouz.i18n.locale_negotiator')

    return config.make_wsgi_app()
