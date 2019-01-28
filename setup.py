try:
    from setuptools import setup
    from setuptools import find_packages
except ImportError:
    from distutils.core import setup

with open('requirements.txt') as f:
    install_requires = f.read().strip().split("\n")

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
    'name': 'qproxy',
    # TODO: unify with requirements.txt
    'install_requires': install_requires,
}

setup(**config)
