from contextlib import closing
from Util.Config import GetOption
import shelve
import os

class Persistant(object):
  """Its a very blunt persistant key value pair.
Declaration:
class MyPersistantClass(Persistant):
  def __init__(self):
    super(MyPersistantClass, self).__init__(self.__class__.__name__)
    #done

Usage:
p = MyPersistantClass()
p[key] = obj
key in p
print(p[key])
del p[key]
  """
  def __init__(self, name):
    self.shelfFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), name + ".shelf")

  def __setitem__(self, key, value):
    with closing(shelve.open(self.shelfFileName)) as sh:
      sh[str(key)] = value
    return self

  def __getitem__(self, key):
    with closing(shelve.open(self.shelfFileName)) as sh:
      return sh[str(key)]

  def __contains__(self, key):
    return str(key) in self.allKeys

#  def __del__(self, key):
#    with closing(shelve.open(self.shelfFileName)) as sh:
#      del sh[str(key)]
#    return self
#
  def __iter__(self):
    with closing(shelve.open(self.shelfFileName)) as sh:
      return iter([str(k) for k in sh.keys()])

  @property
  def allKeys(self):
    with closing(shelve.open(self.shelfFileName)) as sh:
      return sh.keys()

  @property
  def allValues(self):
    with closing(shelve.open(self.shelfFileName)) as sh:
      return sh.values()
