#This files removes some old pods from current file.
#It is assumed that ALL PODS ARE COPED TO A MASTER FOLDER before runnign this
#Once run, pod folder will be left with only recent files.
DIR = "b:\\desktop\\pod"
DIR = "b:\\GDrive\\Appdir\\DocketPODs"

import os

fileList = os.listdir(DIR)
for fileName in fileList:
  s = fileName.find("_Bill")
  found = s != -1

  if found:
    e = fileName.find("_", s+1)
    if e != -1:
      if e-s < 11:
        if fileName[e-1] != "0":
          continue
      newFileName = fileName[:e-1] + fileName[e:]
      if os.path.exists(os.path.join(DIR, newFileName)):
        os.remove(os.path.join(DIR, fileName))
        continue
      os.rename(os.path.join(DIR, fileName), os.path.join(DIR, newFileName))
