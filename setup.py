#!/usr/bin/env python

from setuptools import setup

setup(
  name = 'licant',
  packages = ['licant'],
  version = '0.11',
  license='MIT',
  description = 'licant make system',
  author = 'Sorokin Nikolay',
  author_email = 'mirmikns@yandex.ru',
  url = 'https://github.com/mirmik/licant',
  keywords = ['testing', 'make'],
  classifiers = [],

  scripts = ["configurator/licant-config"]
)