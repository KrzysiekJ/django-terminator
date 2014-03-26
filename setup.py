#!/usr/bin/env python

from setuptools import setup

VERSION = '0.1.0'


def read(file_name):
    with open(file_name, 'r') as f:
        return f.read()

setup(
    name='django-terminator',
    description='''One time method executor for Django models''',
    long_description=read('README.rst'),
    version=str(VERSION),
    author='Krzysztof Jurewicz',
    author_email='krzysztof.jurewicz@gmail.com',
    url='http://github.com/KrzysiekJ/django-terminator',
    packages=['terminator'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)
