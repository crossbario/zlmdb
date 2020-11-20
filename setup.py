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
    'cbor2>=5.2.0',
    'click>=7.1.2',
    'flatbuffers>=1.12',
    'lmdb>=1.0.0',
    'pynacl>=1.4.0',
    'pyyaml>=5.3.1',
    'txaio>=20.4.1',
    'numpy>=1.19.4',
]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="Object-relational zero-copy in-memory database layer for LMDB.",
    entry_points={
        'console_scripts': [
            'zlmdb=zlmdb.cli:main',
        ],
    },
    # numpy 1.19.4 requires python 3.6+ (https://github.com/numpy/numpy/blob/360ba0572483457837992d711a0a00580741fc88/setup.py#L29)
    python_requires='>=3.6',
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords='zlmdb',
    name='zlmdb',
    packages=packages,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/crossbario/zlmdb',
    version=__version__,
    zip_safe=False,
)
