# -*- coding: utf-8 -*-
"""Miscellaneous utilities
"""
from datetime import timedelta, datetime, date
from decimal import Decimal
from urlparse import urlparse
from uuid import UUID
import HTMLParser
import json
import os
import random
import re
import string
import urllib
import calendar

import requests


_hashtag_re = re.compile(r'\B#(\w{2,100})', re.I | re.U)


def _json_type_lathe(obj):
  """Used for dumping non-JSON types in a JSON friendly manner.

  :param obj: undocumented
  :type obj: dict

  """
  if isinstance(obj, datetime):
    return obj.isoformat()
  elif isinstance(obj, timedelta):
    return obj.total_seconds()
  elif isinstance(obj, UUID):
    return obj.hex
  elif isinstance(obj, Decimal):
    return float(obj)
  return None


def rename_dict_keys(dictionary, key_name, new_name):
  for k, v in dictionary.items():
    if k == key_name:
      dictionary[new_name] = v
      del dictionary[key_name]
  return dictionary


def to_json(obj):
  """Just turns some_dict into a JSON object with pretty standard params
  including unicode handling, and datetime/uuid support

  :param obj: undocumented
  :type obj: dict

  """
  return json.dumps(obj, indent=2, default=_json_type_lathe,
                    ensure_ascii=False, encoding='utf8', sort_keys=True)


def ping_url(url, params=None):
  """Do a GET request against a url with optional params. Used predominantly
  for conversion and tracking pixels."""
  requests.get(url, params=params)


def apath(*args):
  """Join all arguments into a filesystem path, and make it absolute
  """
  return os.path.abspath(os.path.join(*args))


def random_str(length=20):
  _chars = string.letters + string.digits
  return ''.join([random.choice(_chars) for i in range(length)])


def possessive(in_str):
  if not in_str:  # may be None
    return ''
  suffix = "'s"
  if in_str.endswith('s'):
    suffix = "'"
  return "%s%s" % (in_str, suffix)


def decode_html_entities(text):
  html_parser = HTMLParser.HTMLParser()
  return html_parser.unescape(text)


def titlecase(text):
  if not text or not isinstance(text, basestring):
    return text
  return re.sub(r'\s+([a-z])',
      lambda match: ' ' + string.upper(match.group(1)),
      text.lower().capitalize())  # this takes care of the first letter


def rem_html(text, max_len=None):
    if not text or not isinstance(text, basestring):
      return text
    res = re.sub(r'<[^>]*?>', '', text)
    if max_len:
      res = res[:max_len]
    return res


def trim(val):
  if not val or not isinstance(val, basestring):
    return val
  return val.strip()


RE_hashtag = re.compile(r'\B#(\w{2,100})', re.I | re.U)


def extract_tag_set(corpus):
  """Takes in a string, and finds everything that looks like a hashtag,
  slugs it, and returns a set of all it found

  Regex mostly taken from http://bit.ly/OEj6YD
  """
  return set([c.lower().strip() for c in RE_hashtag.findall(corpus)])


def linkify_hashtags(corpus, link_function):
  def sub(match):
    return '<a href="%s">#%s</a>' % (link_function(match.group(1)),
        match.group(1))
  return RE_hashtag.sub(sub, corpus)


def validate_url(url):
  """Validate a URL, returning false if not using http/https or if there is no
  domain.  If valid, return the recombined version of the url
  """
  if not url:
    return False

  comp = urlparse(url)
  if comp.scheme not in ['http', 'https']:
    return False
  if not comp.netloc:
    return False

  return comp.geturl()


def urlencode(text):
  """ Quote a string for inclusion into a URL
  """
  return urllib.quote(text.encode("utf-8"))


def flatten_dict(d, delim='_', prefix=''):
  """Turns a multi-level dict into a single level dict by turning d['k1']['k2']
  into d['k1_k2').  If you don't like the underscore, send a different delim.
  """
  if not hasattr(d, 'keys'):
    return d
  ret = {}
  for key in d.keys():
    if prefix != '':
      new_key = delim.join((prefix, key))
    else:
      new_key = key
    if hasattr(d[key], 'keys'):
      ret.update(flatten_dict(d[key], delim, new_key))
    else:
      ret[new_key] = d[key]
  return ret


def datetime_to_epoch(dt):
  """Using time.mktime() loses subsecond resolution, so use a timedelta
  from the epoch datetime to get better accuracy
  """
  epoch = datetime.utcfromtimestamp(0)
  delta = dt - epoch
  return delta.total_seconds()


def epoch_to_datetime(epoch_timestamp):
  """despite being a simple oneliner, its the compliments datetime_to_epoch and
  is slightly more specific.
  """
  return datetime.fromtimestamp(epoch_timestamp)


def datetime_to_timegm(dt):
  """Converts instance of datetime to epoch time.
  """
  if dt is None:
    return 0.0
  elif isinstance(dt, int):
    return float(dt)
  elif isinstance(dt, date):
    return float(calendar.timegm(dt.timetuple()))
  elif isinstance(dt, datetime):
    return float(calendar.timegm(dt.utctimetuple()))
  else:
    return dt


def ascend_path(path, n=1):
  """Used to strip off the first n directories on a path. Used as a workaround
  for moving URLs generated by webassets in load_assets
  """
  segments = [seg for seg in path.split('/') if seg]
  return '/%s' % '/'.join(segments[n:])


def dict_deep_merge(old, new):
  """dict.update() just replaces keys wholesale as it finds them, so we need to
  be more lenient in how keys are updated
  """
  for k, v in new.items():
    if k in old and isinstance(v, dict):
      old[k] = dict_deep_merge(old[k] or {}, v)
    else:
      old[k] = v
  return old


def service_response(valid, message=None, desc=None, **kwargs):
  """
  Populates and renders basic template structure for service responses.
  """
  response = {
    "desc": desc,
    "msg": message,
    "valid": bool(valid)
  }

  for key, val in kwargs.items():
    response[key] = val
  return response


def min_mean_max(iterable):
  """Return a tuple (min, mean, max) containing the minimum, mean, and maximum
  of this list. The list is only iterated through once. Elements of list must
  be summable, divisable, and comparable. If no min/max/mean is found 0 is
  returned """
  nmax, nmin = float('-inf'), float('inf')
  nsum, tot, mean = 0, 0, 0
  for n in iterable:
    if n > nmax:
      nmax = n
    if n < nmin:
      nmin = n
    tot += 1
    nsum += n
  if tot:
    mean = nsum / tot
  if nmin == float('inf'):
    nmin = 0
  if nmax == float('-inf'):
    nmax = 0
  return nmin, mean, nmax


def jinja_finalizer(thing):
  """Called for each variable expression in jinja, converts None vals to blank
  strings
  """
  if thing is None:
    return ''
  return thing


def TLD_pair(domain):
  """Return either a 1 or 2 element list of a domain with www. and without

  >>> TLD_pair('google.com')
  ('google.com', 'www.google.com')
  >>> TLD_pair('www.google.com')
  ('google.com', 'www.google.com')
  >>> TLD_pair('something.weird.china.cn')
  ('something.weird.china.cn',)
  """
  d = domain.lower().strip()
  out = [d]
  if d.startswith('www.'):
    # starts with www, assume modern sites support no www as well
    out.append(d.replace('www.', ''))
  elif d.count('.') == 1:
    # looks like a TLD, just return it with a www in front of it
    out.append("www.%s" % d)

  return sorted(out)


def unquote_decode(some_str):
  """take a percent-sign encoded, utf-8 encoded string and correctly unquote
     and decode it into a unicode object.
  """
  if isinstance(some_str, unicode):
    # We got passed a unicode object.  turn it into a string.
    some_str = some_str.encode('utf-8')
  new_str = urllib.unquote(some_str)

  # some browsers do bullshit latin-1 encodings.  what the hell.
  encodings_to_try = ('utf-8', 'latin-1')
  for e in encodings_to_try:
    try:
      return new_str.decode(e)
    except UnicodeError:
      pass # just try the next encoding.
  # none of our encodings worked, just return it.
  return new_str


def dedupe_on(to_dedupe, dedupe_field):
  """given a list of dictionaries, return a list deduped on the given field.
  """
  vals = set()
  deduped = []
  for e in to_dedupe:
    if e[dedupe_field] not in vals:
      vals.add(e[dedupe_field])
      deduped.append(e)
  return deduped


def encode_dict(some_dict, encoding='utf-8'):
  """recursively encode unicode strings in a dictionary as utf-8 strings
     NOTE: if you have nested dictionaries in a loop, this will kill you.
  """
  for k, v in some_dict.items():
    if isinstance(v, unicode):
      some_dict[k] = v.encode(encoding)
    elif isinstance(v, dict):
      encode_dict(v, encoding)
