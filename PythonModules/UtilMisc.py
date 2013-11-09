'''
File: UtilMisc.py
Author: Ashish Anand
Description: All misc utility functions
Date: 2012-03-26 Tue 04:46 PM
'''

import datetime
from UtilException import MyException
from UtilConfig import GetOption

import subprocess
import os
import sys
import shutil
import hashlib
import pickle

def GetHash(path):
    """
    Give it a path(directory/file) and this function will give a hash value for it. When the file or dir changes, so will the hash value.
    """
    if os.path.isfile(path):
        return _GetHashForFile(path)
    elif os.path.isdir(path):
        return _GetHashForDir(path)
    else:
        assert "We should not reach here"

def _GetHashForFile(filePath):
    assert os.path.isfile(filePath), "Expecting a file here"
    hashObj = hashlib.md5()
    f = open(filePath, 'rb')
    for chunk in iter(lambda: f.read(65536), b''):
        hashObj.update(chunk)

    return hashObj.hexdigest()

def _GetHashForDir(dir_root):
    assert os.path.isdir(dir_root), "Expecting a directory here."
    hashObj = hashlib.md5()
    for dirPath, dirnames, filenames in os.walk(dir_root, topdown=True):

        dirnames.sort(key=os.path.normcase)
        filenames.sort(key=os.path.normcase)

        for filename in filenames:
            filepath = os.path.join(dirPath, filename)

            f = open(filepath, 'rb')
            for chunk in iter(lambda: f.read(65536), b''):
                hashObj.update(chunk)

    return hashObj.hexdigest()

def GetPickledObject(workbookPath, createrFunction):
    curVer = GetHash(workbookPath)

    pickleDir = GetOption("CONFIG_SECTION", "TempPath")
    if not os.path.exists(pickleDir):
        os.makedirs(pickleDir)

    pickledFile = os.path.join(pickleDir, createrFunction.func_name + ".pkl")
    if os.path.exists(pickledFile):
        with open(pickledFile, "rb") as pf:
            oldVer, oldObj = pickle.load(pf)
            if curVer == oldVer:
                return oldObj
    newObj = createrFunction(workbookPath)
    with open(pickledFile, "wb") as pf:
        pickle.dump((curVer, newObj), pf)
    return newObj


def YYYY_MM_DD(foo):
    do = ParseDateFromString(foo)
    return do.strftime("%Y-%m-%d")


def DD_MM_YYYY(foo):
    do = ParseDateFromString(foo)
    return do.strftime("%d-%b-%Y")


def ParseDateFromString(foo):
    """
    Try to interpret a date from string and return a datetime object
    """

    if not foo:
        #import pdb; pdb.set_trace()
        raise Exception("Got empty argument: {}".format(foo))
    if type(foo) == datetime.datetime: return foo.date()
    elif type(foo) == datetime.date: return foo

    dateObject = None
    formats = ['%d-%m-%Y', '%d/%m/%y', '%d/%m/%Y', '%d-%b-%Y', '%d-%b-%y',
            '%d%b%y', '%d%b%Y', '%Y-%m-%d', "%d%m%y"]
    for eachFormat in formats:
        try:
            dateObject = datetime.datetime.strptime(foo, eachFormat).date()
            break # No exception means we have successfully parsed the date
        except ValueError:
            dateObject = None
    else:
        raise MyException("Could not interpret date from : {}".format(foo))

    return dateObject


def GetMsgInBox(msg, myWidth=79):
    import textwrap
    outline = "_" * myWidth

    wrapper = textwrap.TextWrapper()
    wrapper.replace_whitespace = False
    wrapper.drop_whitespace = True
    wrapper.width = myWidth

    finalText = "\n"
    finalText += outline
    finalText += "\n"
    for eachLine in msg.split("\n"):
        finalText += "{: ^{width}}\n".format(wrapper.fill(eachLine), width=myWidth)
    finalText += outline
    finalText += "\n"
    return finalText

def PrintInBox(msg, waitForEnterKey=False, myWidth=79, fl=sys.stdout):
    """Print a msg in box for greater focus"""

    finalText = GetMsgInBox(msg, myWidth)
    fl.write(finalText)

    sys.stdout.flush()
    if waitForEnterKey:
        raw_input("Press any key to continue...")
    return finalText

def printNow(s):
    print(s)
    sys.stdout.flush()

def OpenFileForViewing(filePath):
    extension = os.path.splitext(filePath)[1]
    if extension == ".txt":
        subprocess.call([os.path.join(os.path.expandvars("%windir%"),"gvim.bat") , "+0", filePath])
    elif extension == ".html":
        subprocess.call([os.path.join(os.path.expandvars("%PROGRAMFILES%"), "Google", "Chrome", "Application", "Chrome.exe") , filePath])
    else:
        PrintInBox("Cannot open files with extension: {}".format(extension))

def EmptyDirectory(path):
    if os.path.exists(path):
        for eachEntry in os.listdir(path):
            entryPath = os.path.join(path, eachEntry)
            if os.path.isfile(entryPath):
                os.remove(entryPath)
            elif os.path.isdir(entryPath):
                shutil.rmtree(entryPath)

def DeleteFileIfExists(AbsolutePath):
    if os.path.exists(AbsolutePath):
        os.remove(AbsolutePath)
    return

def GetSizeOfFileInMB(path):
    return os.path.getsize(path)/(1024*1024)

def MakeSureDirExists(path):
    if os.path.exists(path):
        return
    finalPath = path
    if os.path.isfile(path):
        finalPath = os.path.dirname(path)
    os.makedirs(path)

