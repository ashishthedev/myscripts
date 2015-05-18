##############################################################################
## Filename: BDriveBackup.py
## Date: 2013-Jul-22 Mon 11:25 AM
## Author: Ashish Anand
## Intent: To take a copy of Bdrive into an external harddisk
##############################################################################

import os
import shutil
from Util.Misc import PrintInBox
import datetime
IGNORE_LIST = ["Watch", "Wedding", "YoutubeVideosDownloaded", "Photographs", "Tools"]
SOURCES = [
    ("b:\\", "Bdrive"),
    ]

def main():
  DESTINATION_DRIVE="D:\\" #TODO: Read programatically?
  if raw_input("Take backup of \n{}\nto {} (y/n)?".format(SOURCES, DESTINATION_DRIVE)).lower() != 'y':
    DESTINATION_DRIVE = raw_input("Enter drive letter (without colon): ")
    if len(DESTINATION_DRIVE) != 1:
      raise Exception("Please provide a single letter drive without ':'")
    DESTINATION_DRIVE += ":\\"

  destination = os.path.join(DESTINATION_DRIVE, datetime.datetime.now().strftime("%Y-%b-%d"))

  if os.path.exists(destination):
    if raw_input("You want to delete everything in {} and start again? (y/n)".format(destination)).lower() == 'y':
      shutil.rmtree(destination)

  newVersionCopy = False
  if newVersionCopy:
    Replicate(SOURCES, destination)
  else:
    for source, foldername in SOURCES:
      finalDestination = os.path.join(destination, foldername)
      PrintInBox("Copying {} \n to \n {}".format(source, finalDestination))
      shutil.copytree(source, finalDestination, ignore=shutil.ignore_patterns(*IGNORE_LIST))
    PrintInBox("Ignored these patterns while copying: {}".format(IGNORE_LIST))
  return

def Replicate(sourcePath, destinationPath):
  print("You have asked to replicate {} to {}".format(sourcePath, destinationPath))
  return
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
    dest = os.path.join(DESTINATION_PATH, x)
    print("x " + dest)
    os.remove(dest)

  total = len(tobeCopied)
  i=1;
  for x in tobeCopied:
    src = os.path.join(SOURCE_PATH, x)
    dest = os.path.join(DESTINATION_PATH, x)
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
