# -*- coding: utf-8 -*-
""" Helper functions for the storage package. Once we use this in production,
we should probably use some type of threading.
"""
from .backends import storage


def store_page(page):
  """ Takes a `page.Page` object and stores the rewritten static assets
  """
  # First write the page.
  storage.store_file('index.html', str(page.page))

  for asset in page.assets:
    res = page.session.get(asset['url'])
    # TODO: Error handler
    storage.store_file(asset['name'], res.content)
