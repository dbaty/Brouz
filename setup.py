import os

from setuptools import find_packages
from setuptools import setup


HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst')).read()
CHANGES = ''


REQUIRES = ('babel',
            'deform',
            'pyramid',
            'pyramid_deform',
            'pyramid_tm',
            'sqlalchemy',
            'zope.sqlalchemy')


setup(name='Brouz',
      version='0.1',
      description='Brouz is a very simplified and specialized '
                  'accounting application.',
      long_description='\n\n'.join((README, CHANGES)),
      classifiers=(
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Pyramid',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Natural Language :: English',
        'Natural Language :: French',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Office/Business :: Financial :: Accounting'),
      author='Damien Baty',
      author_email='damien.baty.remove@gmail.com',
      url='http://github.com/dbaty/Brouz',
      keywords='web pyramid accountancy accounting',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=REQUIRES,
      test_suite='brouz.tests',
      entry_points='''\
      [paste.app_factory]
      main = brouz.app:make_app
      ''',
      message_extractors={'.': (
            ('**.py', 'lingua_python', None),
            ('**.pt', 'lingua_xml', None),
            )}
      )
