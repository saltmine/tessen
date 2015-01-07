# -*- coding: utf-8 -*-
""" Utilities for parsing HTML pages and rewriting their asset locations
"""
import bs4
import hashlib
import logging
import urlparse

import session


log = logging.getLogger(__name__)
IMAGE_LOCATION_ATTRS = ('src', 'data-src')


class Page(object):
  """ Grabs a webpage from `page_url`, rewrites static asset routes
  """

  def __init__(self, page_url):
    self.url = page_url
    self.parsed = urlparse.urlparse(page_url)
    self.assets = []
    self.session = session.generate_session()
    self.response = self.session.get(page_url)
    self.soup = bs4.BeautifulSoup(self.response.content)
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
    return self.response.content

  def register_and_rename_asset(self, asset_url):
    """Takes an asset url, generates a new name for it (based on md5 hash)
    then adds a dictionary of the new name and url to the assets list.

    We will get the file extension from the MIMETYPE

    :param asset_url: can be schemaless, relative, or fully qualified.
    :type asset_url: basestring
    :returns: the new asset name (hash with file extension)
    :rtype: str
    """
    name = hashlib.md5(asset_url).hexdigest()
    if asset_url.startswith('//'):
      asset_url = ''.join((self.parsed.scheme, ':', asset_url))
    elif not asset_url.startswith('http'):
      asset_url = ''.join((self.url, asset_url))
    self.assets.append(dict(name=name, url=asset_url))
    log.info('Renaming %s to %s', asset_url, name)
    return name

  def rewrite_html(self):
    """ Rewrites asset locations in the HTML, and calls
    `register_and_rename_asset` on each asset url.
    """
    # JS
    for script in self.soup.find_all('script'):
      if 'src' in script.attrs:
        asset_url = script.attrs['src']
        script.attrs['src'] = self.register_and_rename_asset(asset_url)

    # CSS, etc
    for link in self.soup.find_all('link'):
      if link.attrs.get('href'):
        asset_url = link.attrs['href']
        link.attrs['href'] = self.register_and_rename_asset(asset_url)

    # Images
    for img in self.soup.find_all('img'):
      for attr_name in IMAGE_LOCATION_ATTRS:
        if attr_name in img.attrs:
          break
      else:
        attr_name = None
      if attr_name is None:
        continue
      asset_url = img.attrs[attr_name]
      img.attrs[attr_name] = self.register_and_rename_asset(asset_url)
