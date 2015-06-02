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
IGNORE_LIST = ["YoutubeVideosDownloaded", "Tools", "iPhoneAkanshaImages", "Photographs", "Tools", "Songs", "Read", "Pendrive"]
SOURCES = [
    ("b:\\", "Bdrive"),
    ]

def main():
  DESTINATION_DRIVE="D:\\"
  destination = os.path.join(DESTINATION_DRIVE, datetime.datetime.now().strftime("%Y-%b-%d"))

  if os.path.exists(destination):
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
