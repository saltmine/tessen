# -*- coding: utf-8 -*-
""" Helper functions for the storage package. Once we use this in production,
we should probably use some type of threading.
"""
import logging
import mimetypes
import urlparse

from .backends import storage


ADDITIONAL_TYPES = (('text/javascript', '.js'),)


# Add additional, non-standard mime type maps here.
for mime, extension in ADDITIONAL_TYPES:
  mimetypes.add_type(mime, extension)


log = logging.getLogger(__name__)


def store_page(page):
  """ Takes a `page.Page` object and stores the rewritten static assets
  """
  # First write the assets

  for asset in page.assets:
    asset.download(page.session)
    asset.rename()
    storage.store_file(asset.name, asset.content)

  storage.store_file('raw.html', page.raw)
  storage.store_file('index.html', page.rewritten)
  _store_hash_map(page.assets)


def _store_hash_map(assets, name=None):
  """
  """
  data = ['Hashed name, Original Asset URL']
  data.extend(['%s, %s' % (a.name, a.asset_url) for a in assets])
  if name is None:
    name = 'hashmap.txt'
  storage.store_file(name, '\n'.join(data))
