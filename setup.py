# coding=utf8
""" A command line tool to use evernote locally
See:
https://github.com/luabish/LocalEverNote
"""

from codecs import open
from os import path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='localevernote',

    version='0.1',

    description='Use Evernote Locally.为印象笔记增加本地化的使用方式',

    long_description=long_description,

    url='https://github.com/luabish/LocalEverNote',

    author='Luabish',
    author_email='',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='evernote markdown python',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(),

    install_requires=['requests', 'markdown', 'evernote', 'chardet', 'html2text', 'lxml', 'selenium'],
    # TODO:selenium need additional webdriver
    # List additional groups of dependencies here
    extras_require={},

    entry_points={
        'console_scripts': [
            'len = localevernote.main:main'
        ]
    },
)
