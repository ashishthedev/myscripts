#####################################################################
## Internt: To read the configuration file and supply parameters to
## scripts spread all over the place.
##
## Author: Ashish Anand
## Date: 2013-01-28 Mon 02:31 PM
#####################################################################

from ConfigParser import SafeConfigParser
from Util.Exception import MyException
import os

CONFIG_FILE_NAME = "pycrm.cfg"

def _GetConfigFilePath(currentPath):
    savedOriginalPath = currentPath
    oldPath = currentPath
    result = None
    for i in range(1,100):
        if CONFIG_FILE_NAME in os.listdir(currentPath):
            result = os.path.abspath(os.path.join(currentPath, CONFIG_FILE_NAME))
            break
        currentPath = os.path.abspath(os.path.join(currentPath, ".."))

        if oldPath == currentPath:
            break  # i.e. we have reached root of the directory

        oldPath = currentPath

    if not result:
        raise MyException("Fatal: Not a pyCrm repository. No %s found in any of the ancestors of %s" % (CONFIG_FILE_NAME, savedOriginalPath))
    return os.path.abspath(result)

def GetAppDir():
    #Assumption: The pycrm.cfg is always one level down of APPDIR
    return os.path.dirname(_GetConfigFilePath(os.getcwd()))

def GetAppDirPath():
    return GetAppDir()

def GetConfigFilePath():
    return _GetConfigFilePath(os.getcwd())

def GetOption(sectionName, optionName):
    configFilePath = _GetConfigFilePath(os.getcwd())
    parser = SafeConfigParser()
    parser.read(configFilePath)

    if not parser.has_section(sectionName):
        raise MyException("'%s' does not have any section named '%s'" % (configFilePath, sectionName))

    if not parser.has_option(sectionName, optionName):
        raise MyException("'%s' does not have any option named '%s' under section '%s'" % (configFilePath, optionName, sectionName))

    return parser.get(sectionName, optionName)
