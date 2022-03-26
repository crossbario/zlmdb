#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

"""The setup script."""

import os
from setuptools import setup

with open('zlmdb/_version.py') as f:
    exec(f.read())  # defines __version__

with open('README.rst') as readme_file:
    readme = readme_file.read()

# enforce use of CFFI for LMDB
# os.environ['LMDB_FORCE_CFFI'] = '1'

# enforce use of bundled libsodium with PyNaCl
os.environ['SODIUM_INSTALL'] = 'bundled'

requirements = [
    'cffi>=1.14.5',
    'cbor2>=5.2.0',
    'click>=7.1.2',
    'flatbuffers>=2.0',
    'lmdb>=1.2.1',
    'pynacl>=1.4.0',
    'pyyaml>=5.4.1',
    'txaio>=21.2.1',
    'numpy>=1.20.1',
]

extras_require = {
    'dev': []
}

with open('requirements-dev.txt') as f:
    for line in f.read().splitlines():
        extras_require['dev'].append(line.strip())

# setup_requirements = ['pytest-runner']
test_requirements = ['pytest', 'pytest-runner']

packages = [
    'flatbuffers',
    'zlmdb',
    'zlmdb.flatbuffers',
    'zlmdb.flatbuffers.reflection',
]

setup(
    author="Crossbar.io Technologies GmbH",
    author_email='contact@crossbario.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    description="Object-relational zero-copy in-memory database layer for LMDB.",
    entry_points={
        'console_scripts': [
            'zlmdb=zlmdb.cli:main',
        ],
    },
    # NumPy 1.19.0+ requires Py 3.6+
    # NumPy 1.20.0+ requires Py 3.7+
    python_requires='>=3.7',
    install_requires=requirements,
    extras_require=extras_require,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords='zlmdb',
    name='zlmdb',
    packages=packages,
    # setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/crossbario/zlmdb',
    version=__version__,
    zip_safe=True,
)
