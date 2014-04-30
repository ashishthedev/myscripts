from contextlib import closing
import shelve
from UtilConfig import GetOption
import os

class Persistant(object):
    def __init__(self, name):
        self.shelfFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), name + ".shelf")

    def put(self, key, value):
        with closing(shelve.open(self.shelfFileName)) as sh:
            sh[str(key)] = value
        return self

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



