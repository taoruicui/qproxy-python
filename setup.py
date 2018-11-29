try:
    from setuptools import setup
    from setuptools import find_packages
except ImportError:
    from distutils.core import setup

from pip.req import parse_requirements
import pip.download

config = {
    'description': 'Tornado-based QProxy Client',

    'url': 'https://github.com/ContextLogic/qproxy-python',
    'author': 'Andrew Huang',
    'author_email': 'andrew@wish.com',
    'license': 'MIT',
     'classifiers': [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    'version': '0.0.1',
    'packages': ['qproxy'],
    'scripts': [],
    'name': 'dataman',
    # TODO: unify with requirements.txt
    'install_requires': [str(ir.req) for ir in parse_requirements('requirements.txt', session=pip.download.PipSession())],
}

setup(**config)
