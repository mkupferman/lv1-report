#!/usr/bin/env python3

from setuptools import setup

setup(
    name='lv1-report',
    version='0.0.1',
    py_modules=['lv1report'],
    install_requires=[
        'Click',
        'sqlalchemy',
        'xlsxwriter'
    ],
    entry_points='''
        [console_scripts]
        lv1report=lv1report:lv1report
    ''',
)
