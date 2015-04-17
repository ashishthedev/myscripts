##############################################################################
## Filename: PenSync.py
## Date: 2015-Apr-03 Fri 02:50 PM
## Author: Ashish Anand
## Intent: To replicate a predefined folder on pendrive withour fuss.
##############################################################################

import os
import shutil
from Util.Misc import PrintInBox
SOURCE_PATH = os.path.join("b:\\", "Pendrive")
DESTINATION_DRIVE = "D:\\" #TODO: Read programatically?
DESTINATION_PATH = ""

def main():
  global DESTINATION_DRIVE
  global DESTINATION_PATH
  if raw_input("Sync {}\nto {} (y/n)?".format(SOURCE_PATH, DESTINATION_DRIVE)).lower() != 'y':
    DESTINATION_DRIVE = raw_input("Enter drive letter (without colon): ")
    if len(DESTINATION_DRIVE) != 1:
      raise Exception("Please provide a single letter drive without ':'")
    DESTINATION_DRIVE += ":\\"

  DESTINATION_PATH = os.path.join(DESTINATION_DRIVE)

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
