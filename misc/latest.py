#####################################################################
##
## Intent: To display the latest file from all files under this 
##         directory
## Date:  2013-03-06 Wed 11:57 AM
#####################################################################

from Util.Latest import AllFilesInThisDirectory
from Util.Misc import PrintInBox
import os
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("count", type=int, nargs='?', default=50, help="No of latest files that you want to see.")
    args = parser.parse_args()

    noOfFiles = args.count
    PrintInBox("Displaying latest " + str(noOfFiles) + " files")

    allFiles = AllFilesInThisDirectory(os.curdir)
    allFiles.sort()

    for eachFile in allFiles[-1 * noOfFiles:]:
        print(eachFile.path)

