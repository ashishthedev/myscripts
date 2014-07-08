#########################################################
## Intent: To have certain utilities that help you debug
## Date 2013-01-25 Fri 01:17 PM
## Author: Ashish Anand
#########################################################

import inspect
import pprint

def PrintStackTraceUptoThisPoint():
    upperFrame = inspect.currentframe().f_back
    print("\nStack trace leading upto function %s\n%s" % (inspect.getframeinfo(upperFrame).function, "_"*60))
    for frame in inspect.stack():
        print(frame)

def PrintArgsForThisFunction():
    upperFrame = inspect.currentframe().f_back
    arginfo = inspect.getargvalues(upperFrame)
    print("\nArguments for func %s\n%s" % (inspect.getframeinfo(upperFrame).function, "_"*60))
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(arginfo.locals)

class DictWatch(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __setitem__(self, key, val):
        print("SET", key, val)
        PrintStackTraceUptoThisPoint()
        super(DictWatch, self).__setitem__(key, val)

    def __getitem__(self, key):
        val = super(DictWatch, self).__getitem__(key)
        print("GET", key)
        return val
