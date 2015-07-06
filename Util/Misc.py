'''
File: Misc.py
Author: Ashish Anand
Description: All misc utility functions
Date: 2012-03-26 Tue 04:46 PM
'''

from Util.Exception import MyException
from Util.Config import GetOption

import datetime
import hashlib
import os
import random
import shutil
import subprocess
import sys
import tempfile
import textwrap

try:
  import cPickle as pickle
except:
  import pickle as pickle


class tempCopy(object):
  """ Create a temp copy of file/dir and destroy it after work is done"""
  def __init__(self, origPath, ignorePattern=None):
    self.origPath = origPath
    self.ignorePattern = ignorePattern

  def __enter__(self):
    self.newPath = None
    self.tempdir = tempfile.mkdtemp()
    if os.path.isdir(self.origPath):
      #Its a dir; create a copy in tempdir
      leafDir = os.path.basename(self.origPath)
      leafDirParent = os.path.basename(os.path.dirname(self.origPath))
      self.newPath = os.path.join(self.tempdir, leafDirParent, leafDir)
      shutil.copytree(self.origPath, self.newPath, ignore=self.ignorePattern)
    else:
      #Its a file; just copy in temp dir
      self.newPath = os.path.join(self.tempdir, os.path.basename(self.origPath))
      shutil.copy(self.origPath, self.tempdir)

    assert self.newPath is not None
    return self.newPath

  def __exit__(self, etype, value, traceback):
    shutil.rmtree(self.tempdir)
    return


def CheckRequiredAttribsAndThrowExcIfNotPresent(obj, attribs):
  for a in attribs:
    if not hasattr(obj, a):
      raise Exception("`{}` does not have declared required attribute `{}`.".format(obj.__name__, a))
  return None

class cd(object):
  """Context manager for changing the current working directory"""
  def __init__(self, newPath):
    self.newPath = newPath

  def __enter__(self):
    self.savedPath = os.getcwd()
    os.chdir(self.newPath)

  def __exit__(self, etype, value, traceback):
    os.chdir(self.savedPath)


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
  #TODO: Use time here instead of hashes
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

def DD_MMM_YYYY(foo):
  return DD_MM_YYYY(foo)

def DD_MM_YYYY(foo):
  do = ParseDateFromString(foo)
  return do.strftime("%d-%b-%Y")

def AnyFundooProcessingMsg():
  l = [
      "Admiring the intellect...",
      "Inventing strangeness...",
      "Polishing the code...",
      "Toughening the skeleton...",
      "Fastening seatbelt...",
      "Churning data...",
      "Running at full speed...",
      "Shredding papers...",
      ]
  return l[random.randint(0, len(l)-1)]

def ParseDateFromString(foo):
  """
  Try to interpret a date from string and return a datetime object
  """

  if not foo:
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


def GetMsgInBox(msg, myWidth=79, outliner="_"):
  withBoxBoundaries = False
  withBoxBoundaries = True
  outline = outliner * myWidth
  wrapper = textwrap.TextWrapper()
  wrapper.replace_whitespace = False
  wrapper.drop_whitespace = True
  if withBoxBoundaries:
    wrapper.width = int(myWidth) - 2
  else:
    wrapper.width = myWidth

  finalText = "\n"
  finalText += outline
  finalText += "\n"
  for eachLine in msg.split("\n"):
    if withBoxBoundaries:
      finalText += "|{: ^{width}}|\n".format(wrapper.fill(eachLine), width=wrapper.width)
    else:
      finalText += "{: ^{width}}\n".format(wrapper.fill(eachLine), width=wrapper.width)
  finalText += outline
  finalText += "\n"
  return finalText

def PrintInBox(msg, waitForEnterKey=False, myWidth=79, fl=sys.stdout, outliner="_"):
  """Print a msg in box for greater focus"""

  finalText = GetMsgInBox(msg, myWidth, outliner)
  fl.write(finalText)

  fl.flush()
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
  return

def DeleteFileIfExists(AbsolutePath):
  if os.path.exists(AbsolutePath):
    os.remove(AbsolutePath)
  return

def GetSizeOfFileInMB(path):
  return os.path.getsize(path)/(1024*1024)

def MakeSureDirExists(path):
  if not os.path.exists(path):
    os.makedirs(path)
  return

def flattenList(seq):
  if seq is None: return None
  if seq is str: return seq

  res = []
  for item in seq:
    if isinstance(item, (list, tuple)):
      res.extend(flattenList(item))
    else:
      res.append(item)
  return res

def StripHTMLTags(html):
  from HTMLParser import HTMLParser
  class MLStripper(HTMLParser):
    def __init__(self):
      self.reset()
      self.fed = []
    def handle_data(self, d):
      self.fed.append(d)
    def get_data(self):
      SPACE = ' '
      return SPACE.join(self.fed)

  s = MLStripper()
  s.feed(html)
  return s.get_data()

def GetConfirmation():
  if raw_input("Proceed: (y/n)").lower() != "y":
    raise Exception()

def IsDeliveredAssessFromStatus(status):
  if not status:
    return False
  yes_words = status.lower().find("delivered") != -1
  no_words = ( status.lower().find("not") != -1 or status.lower().find("undelivered") != -1)
  delivered = yes_words and not no_words #If has the word delivered but not the word not
  return delivered

def GetFirstDateOfThisFinancialYear():
  t = datetime.datetime.today()
  month = t.month
  if month in [1, 2, 3]:
    d = datetime.date(t.year-1, 4, 1)
  else:
    d = datetime.date(t.year, 4, 1)
  return d


def EnableCGItb():
  """Calling this function drastically improves the exception description."""
  import cgitb
  cgitb.enable(format="text")


def PrintHTMLOnScreen(html):

  import formatter
  import htmllib

  w = formatter.DumbWriter()
  f = formatter.AbstractFormatter(w)

  p = htmllib.HTMLParser(f)
  p.feed(html)
  p.close()
  return



def _testTable():
    Column = ConsoleTable.Column
    nums = [ '1', '2', '3', '4' ]
    speeds = [ '100', '10000', '1500', '12' ]
    desc = [ '', 'label 1', 'none', 'very long description' ]
    print()
    print ConsoleTable(
        Column('NUM', nums),
        Column('DESC', desc, align=Column.LEFT),
        Column('SPEED', speeds),
        )


class ConsoleTable:
    def __init__(self, *columns):
        self.columns = columns
        self.length = max(len(col.data) for col in columns)

    def get_row(self, rownum=None):
        for col in self.columns:
            if rownum is None:
                yield col.format % col.name
            else:
                yield col.format % col.data[rownum]

    def get_line(self):
        for col in self.columns:
            yield '_' * (col.width + 2)

    def join_n_wrap(self, char, elements):
        return ' ' + char + char.join(elements) + char

    def get_rows(self):
        yield self.join_n_wrap('+', self.get_line())
        yield self.join_n_wrap('|', self.get_row(None))
        yield self.join_n_wrap('+', self.get_line())
        for rownum in range(0, self.length):
            yield self.join_n_wrap('|', self.get_row(rownum))
        yield self.join_n_wrap('+', self.get_line())
    def __str__(self):
        return '\n'.join(self.get_rows())

    class Column():
        LEFT, RIGHT = '-', ''
        def __init__(self, name, data, align=RIGHT):
            self.data = data
            self.name = name
            self.width = max(len(x) for x in data + [name])
            self.format = ' %%%s%ds ' % (align, self.width)

if __name__ == "__main__":
  _testTable()
