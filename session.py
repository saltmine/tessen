# -*- coding: utf-8 -*-
""" Like this and like that and like this and uh
"""
import random
import requests


USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
)


def generate_session(*args, **kwargs):
  """Returns session object

  :returns: requests session object
  """
  headers = {}
  headers['User-Agent'] = get_user_agent()
  s = requests.Session(*args, **kwargs)
  s.headers = headers
  return s


def get_user_agent():
  """ Returns a random user agent string.

  :returns: User agent string
  :rtype: str
  """
  return random.choice(USER_AGENTS)
