from contextlib import closing
from Util.Config import GetOption
import shelve
import os

class Persistent(object):
  """Its a very blunt Persistent key value pair.
Declaration:
class MyPersistentClass(Persistent):
  def __init__(self):
    super(self.__class__, self).__init__(self.__class__.__name__)
    #done

Usage:
p = MyPersistentClass()
p[key] = obj
key in p
print(p[key])
del p[key]
p.allKeys
  """
  def __init__(self, name):
    self.shelfFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), name + ".shelf")
    if not os.path.exists(self.shelfFileName):
      with closing(shelve.open(self.shelfFileName)) as sh:
        pass #Just create it

  def __setitem__(self, key, value):
    with closing(shelve.open(self.shelfFileName)) as sh:
      sh[str(key)] = value
    return self

  def __getitem__(self, key):
    with closing(shelve.open(self.shelfFileName)) as sh:
      return sh[str(key)]

  def __contains__(self, key):
    return str(key) in self.allKeys

  def __delitem__(self, key):
    with closing(shelve.open(self.shelfFileName)) as sh:
      del sh[str(key)]
    return self

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

  def spitOnScreen(self):
    for k in self.allKeys:
      print("{:<30}:{:<30}".format(k, self[k]))

