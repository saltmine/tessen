#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Like this and like that and like this and uh
"""
import argparse
import logging
import requests_cache

import page
from storage import store_page


log = logging.getLogger(__name__)
requests_cache.install_cache()
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('url', metavar='url', type=str, nargs='+',
                    help='The URL to crawl and store')


if __name__ == '__main__':
  logging.basicConfig()
  url = parser.parse_args().url[0]
  html = page.get_page_from_webkit(url)
  page = page.Page(url, html=html)
  store_page(page)
