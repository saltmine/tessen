# -*- coding: utf-8 -*-
"""Load & manage config data
"""
import logging
import os
import yaml

from lib.accessor_dict import AccessorDict
from lib import utils


log = logging.getLogger(__name__)


basedir = os.path.dirname(os.path.realpath(__file__))
_default_file = os.path.join(basedir, 'etc', 'default.yaml')
_override_file = os.path.join(basedir, 'etc', 'override.yaml')


test_mode = True


G = globals()
settings = {}
if os.path.exists(_default_file):
  with open(_default_file) as f:
    for key, val in yaml.load(f).iteritems():
      settings[key] = val

if os.path.exists(_override_file):
  override_settings = {}
  with open(_override_file) as f:
    for key, val in yaml.load(f).iteritems():
      override_settings[key] = val
  settings = utils.dict_deep_merge(settings, override_settings)


settings = AccessorDict(settings)
