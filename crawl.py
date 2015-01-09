#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Like this and like that and like this and uh
"""
import logging
import requests_cache

from page import Page
from storage import store_page


log = logging.getLogger(__name__)
requests_cache.install_cache()
URL = 'https://www.jcrew.com/womens_feature/NewArrivals/PRD~B8448/B8448.jsp?intcmp=cathead_w_newarrivals'
URL = 'http://google.com'


if __name__ == '__main__':
  logging.basicConfig()
  page = Page(URL)
  import IPython; IPython.embed()
  store_page(page)
