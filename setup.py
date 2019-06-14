#############################################
# File Name: setup.py
# Author: WEN
# Created Time:  2019-06-08 08:11:00
#############################################

from setuptools import setup

setup(
    name        =   "easyrpc",
    description =   "high performace python rpc",
    license     =   "GPLv3",
    version     =   "0.1.0",
    author      =   "WEN",
    author_email=   "test@gmail.com",
    url         =   "https://github.com/NCNU-OpenSource/testrepo",
    packages    =   ['easyrpc'],
    install_requires=[
        'msgpack',
        ''
    ],
    entry_points='''
        [console_scripts]
        easyrpc=easyrpc:easyrpc
    ''',
    classifiers=[
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
    ],
)