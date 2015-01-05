"""
AccessorDict provides a dictionary class that allows dot-access to keys, and
supports nested dictionaries

d = dict(x=dict(y=20))
d = AccessorDict(d)
d['x']['y'] == d.x.y
"""
__author__ = "Trey Stout <trey.stout@adkeeper.com>"
__date__ = "Thu Sep 22 09:53:27 PDT 2011"


class AccessorDict(dict):
  def __getattr__(self, attr):
    # if it's a real attr, just give it back
    if attr in self.__dict__.keys():
      return self.__dict__[attr]
    else:
      # just blindly grab the value, let it raise KeyError if it's not there
      try:
        val = self[attr]
      except KeyError as e:
        raise AttributeError(e.message)
      if isinstance(val, dict):
        # magic time! if the value is another dict, wrap it and give it back.
        return AccessorDict(val)
      elif isinstance(val, (tuple, list)):
        # even more magic time! if all vars in this iterable are dicts, then
        # return them as AccessorDicts as well
        if all([isinstance(item, dict) for item in val]):
          if isinstance(val, tuple):
            return (AccessorDict(item) for item in val)
          else:
            return [AccessorDict(item) for item in val]
        else:
          return val
      else:
        return val

  def __setattr__(self, attr, val):
    self[attr] = val

  def getlist(self, k):
    return [self[k]]
