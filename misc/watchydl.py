##############################################################################
## Date: 2014-Aug-14 Thu 12:17 PM
## Author: Ashish Anand
## Intent: To take a str and show all the files that live in those directory
## having that str in the filename and then execute a particular file
##############################################################################

from Util.Misc import PrintInBox
from Util.Latest import TopLevelFilesInThisDirectory
import os

def parse_arguments():
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("-s", dest='keyword', type=str, default=None, help="Substring which is to be looked for")
  args = parser.parse_args()
  return args

def main():
  args = parse_arguments()
  DESTINATION_DIR="B:\\YoutubeVideosDownloaded\\"
  allFiles = TopLevelFilesInThisDirectory(DESTINATION_DIR)
  kw = args.keyword.lower()
  filteredFiles = [sf for sf in allFiles if sf.path.lower().find(kw) != -1]
  for i, sf in enumerate(filteredFiles):
    if sf.path.lower().find(kw) != -1:
      print("{} {}".format(i, sf.path))
  index = raw_input("Enter the number: ")
  if index:
    os.startfile(filteredFiles[int(index)].path)


if __name__ == '__main__':
  try:
    main()
  except Exception as ex:
    PrintInBox(str(ex))
