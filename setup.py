#!/usr/bin/env python -u
#
#  Copyright (c) 2016-2017, The OpenThread Authors.
#  All rights reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from setuptools import setup, find_packages
import sys
import os

WiresharkExtcapDir = ''

if sys.platform == 'linux2':
    WiresharkExtcapDir = os.popen('find / -type d -ipath *wireshark*extcap').read()
elif sys.platform == 'darwin':
    WiresharkExtcapDir = os.popen('find /Applications/ -type d -ipath *wireshark*extcap').read()
elif sys.platform == 'win32':
    WiresharkDir = raw_input("Wireshark installation directory: ")
    if WiresharkDir:
        WiresharkExtcapDir = WiresharkDir + '\extcap'

setup(
    name='pyspinel',
    version='1.0.0a3',
    description='A Python interface to the OpenThread Network Co-Processor (NCP)',
    url='https://github.com/openthread/openthread',
    author='The OpenThread Authors',
    author_email='openthread-users@googlegroups.com',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',

        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',

        'License :: OSI Approved :: BSD License',

        'Topic :: System :: Networking',
        'Topic :: System :: Hardware :: Hardware Drivers',
        'Topic :: Software Development :: Embedded Systems',

        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='openthread thread spinel ncp',
    packages=find_packages(),
    install_requires=[
        'pyserial',
        'ipaddress',
    ] if sys.version_info >= (3, 0) else [
        'future',
        'ipaddress',
        'pyserial',
    ],
    scripts=['spinel-cli.py', 'sniffer.py'],
    data_files=[(WiresharkExtcapDir, ['sniffer.py', 'OT_sniffer.py', 'OT_sniffer.bat'])]
)
