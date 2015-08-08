##############################################################################
## Filename: ytfsync.py
## Date: 2015-Apr-23 Thu 07:15 AM
## Author: Ashish Anand
## Intent: To Sync a predefined folder on pendrive withour fuss.
##############################################################################

import os
import shutil
from Util.Misc import PrintInBox

from collections import namedtuple
Entry = namedtuple("Entry", ["source", "destination"])
def main():
  sourceAndDestinations = [
      Entry(os.path.join("b:\\", "YoutubeVideosDownloaded"), os.path.join("D:\\", "YoutubeVideosDownloaded\\")),
      Entry(os.path.join("b:\\", "Tools"), os.path.join("D:\\", "Tools\\")),
      Entry(os.path.join("b:\\", "iPhoneAkanshaImages"), os.path.join("D:\\", "iPhoneAkanshaImages\\")),
      Entry(os.path.join("b:\\", "Photographs"), os.path.join("D:\\", "Photographs\\")),
      Entry(os.path.join("b:\\", "Watch"), os.path.join("D:\\", "Watch\\")),
      Entry(os.path.join("b:\\", "Songs"), os.path.join("D:\\", "Songs\\")),
      Entry(os.path.join("b:\\", "Read"), os.path.join("D:\\", "Read\\")),
      Entry(os.path.join("b:\\", "Pendrive"), os.path.join("D:\\", "Pendrive\\")),
      ]

  ConfirmAndSyncFolders(sourceAndDestinations)
  return


def ConfirmAndSyncFolders(sourceAndDestinations):
  confirmedSourceAndDestinations = []
  for entry in sourceAndDestinations:
    if raw_input("Sync\n{} to\n{} (y/n)?".format(entry.source, entry.destination)).lower() == 'y':
      confirmedSourceAndDestinations.append(entry)

  for entry in confirmedSourceAndDestinations:
    SyncFolders(entry.source, entry.destination)
  return


def SyncFolders(sourcePath, destinationPath):
  sf = []
  for (dirpath, dirnames, filenames) in os.walk(sourcePath):
    for fn in filenames:
      sf.append(os.path.join(dirpath, fn))

  sourceSet = set([x[len(sourcePath) +len("\\"):] for x in sf])

  df = []
  for (dirpath, dirnames, filenames) in os.walk(destinationPath):
    for fn in filenames:
      df.append(os.path.join(dirpath, fn))

  destSet = set([x[len(destinationPath):] for x in df])

  tobeCopied =  sourceSet - destSet
  tobeDeleted = destSet - sourceSet

  for x in tobeDeleted:
    dest = os.path.join(destinationPath, x)
    print("Destpath:{}, X={}, finalPath={}".format(destinationPath, x, dest))
    print("x " + dest)
    os.remove(dest)

  total = len(tobeCopied)
  i=1;
  for x in tobeCopied:
    src = os.path.join(sourcePath, x)
    dest = os.path.join(destinationPath, x)
    print("{} of {} {}".format(i, total, x))
    i+=1
    parentDir = os.path.dirname(dest)
    if not os.path.exists(parentDir):
      os.makedirs(parentDir)
    shutil.copyfile(src, dest)

  return

if __name__ == '__main__':
  try:
    main()
  except Exception as ex:
    PrintInBox(str(ex))
