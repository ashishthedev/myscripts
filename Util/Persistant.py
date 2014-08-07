from contextlib import closing
from Util.Config import GetOption
import shelve
import os

class Persistant(object):
  """Its a very blunt persistant key value pair.
Usage:
class MyPersistantClass(Persistant):
  def __init__(self):
    super(MyPersistantClass, self).__init__(self.__class__.__name__)

p = MyPersistantClass()
p[key] = obj
key in p
print(p[key])
  """
  def __init__(self, name):
    self.shelfFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), name + ".shelf")

  def put(self, key, value):
    with closing(shelve.open(self.shelfFileName)) as sh:
      sh[str(key)] = value
    return self

  def __setitem__(self, key, value):
    print("Setting m[{}] to {}".format(key, value))
    return self.put(key, value)

  def __getitem__(self, key):
    return self.get(key)

  def __contains__(self, key):
    return key in self.allKeys

  def remove(self, key):
    with closing(shelve.open(self.shelfFileName)) as sh:
      del sh[str(key)]
    return self

  def get(self, key):
    with closing(shelve.open(self.shelfFileName)) as sh:
      return sh[str(key)]

  @property
  def allKeys(self):
    with closing(shelve.open(self.shelfFileName)) as sh:
      return sh.keys()

  @property
  def allValues(self):
    with closing(shelve.open(self.shelfFileName)) as sh:
      return sh.values()



