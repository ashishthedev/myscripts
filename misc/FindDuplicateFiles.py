#########################################################################
## Author: Ashish Anand
## Date: 12-Jan-2013
## Intent: Find Duplicate Files in the directory
## Usage: Just execute this file. Change the drive in the code itself.
##########################################################################
import os

from collections import defaultdict


def main(basePath, ignList):
  d = defaultdict(list)
  for root, dirs, files in os.walk(basePath):
    for eachIgnEntry in ignList:
      if eachIgnEntry in dirs:
        dirs.remove(eachIgnEntry)

    for eachFileName in files:
      filePath = os.path.join(root, eachFileName)
      hashVal = os.path.getsize(os.path.normpath(filePath))
      d[hashVal].append(filePath)

  dups = {k:v for (k,v) in d.items() if len(v)>1}
  for i, (k, v) in enumerate(dups.items()):
    print("---------------------------------------")
    for eachPath in v:
      print("{}. {}".format(i, eachPath))

if __name__ == '__main__':
    main(os.getcwd(), [".git"])
