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

  for source, foldername in SOURCES:
    finalDestination = os.path.join(destination, foldername)
    PrintInBox("Copying {} \n to \n {}".format(source, finalDestination))
    shutil.copytree(source, finalDestination, ignore=shutil.ignore_patterns(*IGNORE_LIST))
  PrintInBox("Ignored these patterns while copying: {}".format(IGNORE_LIST))
  return

if __name__ == '__main__':
  try:
    main()
  except Exception as ex:
    PrintInBox(str(ex))
