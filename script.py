#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Like this and like that and like this and uh
"""
import logging
import requests_cache

from page import Page


log = logging.getLogger(__name__)
requests_cache.install_cache()
URL = 'https://www.etsy.com/'


if __name__ == '__main__':
  logging.basicConfig()
  page = Page(URL)
  import IPython
  IPython.embed()
