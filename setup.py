#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2013 Ralph Bean

from setuptools import setup

setup(
    name='trac-fedmsg-plugin',
    version='0.4.0',
    description='Emit fedmsg messages',
    author="Ralph Bean",
    author_email="rbean@redhat.com",
    license='MIT',
    url='http://github.com/fedora-infra/trac-fedmsg-plugin',
    py_modules=['trac_fedmsg_plugin'],
    entry_points={
        'trac.plugins': [
            'trac_fedmsg_plugin = trac_fedmsg_plugin',
        ]
    }
)
