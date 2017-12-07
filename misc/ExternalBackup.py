##############################################################################
## Filename: BDriveBackup.py
## Date: 2013-Jul-22 Mon 11:25 AM
## Author: Ashish Anand
## Intent: To take a copy of Bdrive into an external harddisk
##############################################################################

import datetime
import os
import shutil
from collections import namedtuple
from Util.Misc import PrintInBox

DESTINATION_DRIVE = "G:\\"
SOURCE_DRIVE = "e:\\"
Entry = namedtuple("Entry", ["source", "destination"])
def OneBigLocationsBackup():
  sourceAndDestinations = [
      Entry(os.path.join(SOURCE_DRIVE, "YoutubeVideosDownloaded"), os.path.join(DESTINATION_DRIVE, "YoutubeVideosDownloaded\\")),
      Entry(os.path.join(SOURCE_DRIVE, "Tools"), os.path.join(DESTINATION_DRIVE, "Tools\\")),
      Entry(os.path.join(SOURCE_DRIVE, "iPhoneAkanshaImages"), os.path.join(DESTINATION_DRIVE, "iPhoneAkanshaImages\\")),
      Entry(os.path.join(SOURCE_DRIVE, "Photographs"), os.path.join(DESTINATION_DRIVE, "Photographs\\")),
      Entry(os.path.join(SOURCE_DRIVE, "Watch"), os.path.join(DESTINATION_DRIVE, "Watch\\")),
      Entry(os.path.join(SOURCE_DRIVE, "Songs"), os.path.join(DESTINATION_DRIVE, "Songs\\")),
      Entry(os.path.join(SOURCE_DRIVE, "Read"), os.path.join(DESTINATION_DRIVE, "Read\\")),
      Entry(os.path.join(SOURCE_DRIVE, "Pendrive"), os.path.join(DESTINATION_DRIVE, "Pendrive\\")),
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

def TwoTakeCompleteBackupExceptCertainBigLocations():

  SOURCES = [
      (SOURCE_DRIVE, os.path.join("Gdrive", "Appdir")),
      ]
  IGNORE_LIST = ["YoutubeVideosDownloaded", "Tools", "iPhoneAkanshaImages", "Photographs", "Tools", "Songs", "Read", "Pendrive"]
  destination = os.path.join(DESTINATION_DRIVE, datetime.datetime.now().strftime("%Y-%b-%d"))

  if os.path.exists(destination):
    shutil.rmtree(destination)

  for source, foldername in SOURCES:
    sourceJoined = os.path.join(source, foldername)
    finalDestination = os.path.join(destination, foldername)
    PrintInBox("Copying {} \n to \n {}".format(sourceJoined, finalDestination))
    shutil.copytree(sourceJoined, finalDestination, ignore=shutil.ignore_patterns(*IGNORE_LIST))

  PrintInBox("Ignored these patterns while copying: {}".format(IGNORE_LIST))
  return

if __name__ == '__main__':
  try:
    OneBigLocationsBackup()
    TwoTakeCompleteBackupExceptCertainBigLocations()
  except Exception as ex:
    PrintInBox(str(ex))
