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
  # First write the page.
  storage.store_file('raw.html', page.raw)
  storage.store_file('index.html', page.rewritten)

  for asset in page.assets:
    res = page.session.get(asset['url'])
    # TODO: Error handler
    content_string = res.headers.get('content-type', '')
    if content_string:
      # Some sites return "content/type; encoding info". Isolate content type
      content_type = content_string.split(';')[0]
      file_extension = mimetypes.guess_extension(content_type)
    else:
      # Fall back on filename extensions
      uri = urlparse.urlparse(asset['url']).path
      file_extension = uri.split('.')[-1]
      name = ''.join((asset['name'], file_extension))
      log.warn('Content type is empty, found "%s" in url', file_extension)

    if file_extension:
      name = ''.join((asset['name'], file_extension))
    else:
      log.warn('Content type "%s" did not return an extension', content_string)
      continue
    storage.store_file(name, res.content)

  _store_hash_map(page.assets)


def _store_hash_map(assets, name=None):
  """
  """
  data = ['Hashed name, Original Asset URL']
  data.extend(['%s, %s' % (a['name'], a['url']) for a in assets])
  if name is None:
    name = 'hashmap.txt'
  storage.store_file(name, '\n'.join(data))
