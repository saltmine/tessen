# -*- coding: utf-8 -*-
""" Utilities for parsing HTML pages and rewriting their asset locations
"""
import bs4
import hashlib
import json
import logging
import mimetypes
import os
import subprocess
import urlparse

import config as cfg
import session


log = logging.getLogger(__name__)
IMAGE_LOCATION_ATTRS = ('src', 'data-src')


# TODO: Get this phantom stuff somewhere else
PHANTOM_BIN = '/usr/local/bin/phantomjs'
PHANTOM_SCRIPT = os.path.join(cfg.basedir, 'js-src', 'pageScraper.js')
PHANTOM_SWITCHES = ['--ssl-protocol=tlsv1', '--ignore-ssl-errors=true']


def get_page_from_webkit(url):
  """Call the page scraper phantomjs module with given URL.

  NOTE: this function should probably be deprecated in favor of alternative
  page scrapers.
  """
  cmd = [PHANTOM_BIN] + PHANTOM_SWITCHES + [PHANTOM_SCRIPT, url]
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  out, _ = proc.communicate()
  results = json.loads(out)
  return results['html'].encode('utf8')


class Page(object):
  """ Grabs a webpage from `page_url`, provides interface to download and
  rewrite static assets.

  The `Page` class scans through an HTML document, registering static assets
  under `Page.assets`.
  """

  def __init__(self, page_url, html=None):
    self.url = page_url
    self.parsed = urlparse.urlparse(page_url)
    self.assets = []
    self.session = session.generate_session()
    if html is None:
      self._response = self.session.get(page_url)
      self._html = self._response.content
    else:
      self._response = None
      self._html = html
    self.soup = bs4.BeautifulSoup(self._html)
    self.rewrite_html()

  @property
  def rewritten(self):
    """HTML with asset locations rewritten
    """
    return str(self.soup)

  @property
  def raw(self):
    """Untouched HTML response
    """
    return self._html

  def register_asset(self, asset, url_attr, default_file_extension=None):
    """Takes an asset (BeautifulSoup node) discovers it's absolute url (if a
    scheme-less or relative URL is provided), and creates an `Asset` instance
    and appends to self.assets.

    :param asset: BeautifulSoup node
    :param url_attr: the name of the HTML attribute that holds the asset name
                     location. (e.g., 'href' or 'src'). Allows us to rewrite
                     the url later on
    :param default_file_extension: the fall back file extension in case one
                                   can't be inferred.
    """
    # If the URL is scheme-less or relative, rewrite as fully qualified. This
    # needs to happen here so we can use the parsed url of the base page.
    asset_url = asset.attrs[url_attr]
    if asset_url.startswith('//'): # Scheme less
      asset_url = ':'.join((self.parsed.scheme, asset_url))
    elif not asset_url.startswith('http'): # Relative
      asset_url = urlparse.urljoin(self.url, asset_url)

    _asset = Asset(asset, asset_url, url_attr, default_file_extension)
    self.assets.append(_asset)

  def rewrite_html(self):
    """ Rewrites asset locations in the HTML, and calls
    `register_and_rename_asset` on each asset url.
    """
    # JS
    for script in self.soup.find_all('script'):
      if script.attrs.get('src'):
        script.attrs['src'] = self.register_asset(script, 'src', '.js')

    # CSS, etc
    for link in self.soup.find_all('link'):
      if link.attrs.get('href'):
        link.attrs['href'] = self.register_asset(link, 'href', '.css')

    # Iframes
    for iframe in self.soup.find_all('iframe'):
      if iframe.attrs.get('src'):
        iframe.attrs['src'] = self.register_asset(iframe, 'src', '.html')

    # Images
    for img in self.soup.find_all('img'):
      for attr_name in IMAGE_LOCATION_ATTRS:
        if attr_name in img.attrs:
          break
      else:
        attr_name = None
      if attr_name is None:
        continue
      self.register_asset(img, attr_name, '.jpeg')


class Asset(object):
  """Wraps the beautifulsoup (asset) node object providing an interface to
  download its content and update its url.

  We infer the file extension based on Content Type header returned from the
  HTTP request. The Asset object provides a proxy for updating the HTML page.
  """
  def __init__(self, asset, asset_url, url_attr, default_file_extension=None):
    # Note: even though we can get the asset url from the asset, it is often
    # scheme-less or relative. Therefore, we expect the `asset_url` param to be
    # fully qualified.
    self._asset = asset
    self._url_attr = url_attr
    self._response = None
    self._file_extension = None
    self._default_file_extension = default_file_extension
    self.name = None
    self.hash = hashlib.md5(self._asset[self._url_attr]).hexdigest()
    self.asset_url = asset_url

  @property
  def content(self):
    """ Return the request content (to save to file)
    """
    return self._response.content

  def download(self, session_):
    """Requests and stores asset. We pass in the session object explicitly here
    in case we need to modify headers/cookies later on in the storage cycle.
    """
    self._response = session_.get(self.asset_url)

  def _get_file_extension(self):
    """Determine file extension in the following precedence order:
        (1) inspecting content type header,
        (2) inspecting the file extension in the URL, or
        (3) using the optional default file extension.
    """
    content_string = self._response.headers.get('content-type', '')
    if content_string:
      # Some sites return "content/type; encoding info". Isolate content type
      content_type = content_string.split(';')[0]
      file_extension = mimetypes.guess_extension(content_type)
    else:
      # Fall back on filename extensions in URL
      uri = urlparse.urlparse(self.asset_url).path
      if '.' in uri:
        file_extension = uri.split('.')[-1]
        if len(file_extension) <= 10:
          # Make sure file extension isn't too long, add the leading period
          file_extension = '.%s' % file_extension
          log.info('Content type is empty, found "%s" in url', file_extension)
        else:
          # too long, unset
          file_extension = None

      # Check that we have a file extension
      if not file_extension and self._default_file_extension:
        log.info('Using default file extnsion "%s"',
                 self._default_file_extension)
        file_extension = self._default_file_extension
      elif not file_extension:
        log.warn('Could not determine file extension for asset "%s", '
                 'content_type "%s"', self.asset_url, content_string)

    self._file_extension = file_extension

  def rename(self):
    """Rename the static asset. Should only be run _after_ `self.download` is
    called. If file extension exists, join it to the hash, otherwise, rename
    asset with hash value only.
    """
    self._get_file_extension()
    if self._file_extension:
      self.name = ''.join((self.hash, self._file_extension))
    else:
      self.name = self.hash
    self._asset[self._url_attr] = self.name
