##############################################################################
## Filename: ytfsync.py
## Date: 2015-Apr-23 Thu 07:15 AM
## Author: Ashish Anand
## Intent: To replicate a predefined folder on pendrive withour fuss.
##############################################################################

import os
import shutil
from Util.Misc import PrintInBox
SOURCE_PATH = os.path.join("b:\\", "YoutubeVideosDownloaded")
DESTINATION_PATH = os.path.join("D:\\", "YoutubeVideosDownloaded\\")

def main():
  ConfirmAndReplicate(SOURCE_PATH, DESTINATION_PATH)

def ConfirmAndReplicate(sourcePath, destinationPath):
  if raw_input("Sync {}\nto {} (y/n)?".format(sourcePath, destinationPath)).lower() != 'y':
    raise Exception("Please provide correct destination path")

  Replicate(SOURCE_PATH, DESTINATION_PATH)

def Replicate(sourcePath, destinationPath):
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
    src = os.path.join(SOURCE_PATH, x)
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
