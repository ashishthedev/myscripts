'''
File: UtilLatest.py
Author: Ashish Anand
Date: 31-Aug-2012
Description: To find the latest file that has been modified under this directory
'''
IGNORE_EXTENSIONS=[".pyc", ".!ut"] #Take these parameters from calling function
IGNORE_DIRS=[".git"]
import os
from UtilMisc import printNow

class SingleFile(object):
    """This class represents a entity having filename and last modified time."""
    def __init__(self, path, lastModTime):
        super(SingleFile, self).__init__()
        self.path = path
        self.lastModTime = lastModTime
    def __lt__(self, other):
        return self.lastModTime < other.lastModTime


def AllFilesInThisDirectory(directory):
    """It all starts here."""
    allFiles = list()
    for dirpath, dirnames, filenames in os.walk(directory):
        for eachDIR in dirnames:
            if eachDIR in IGNORE_DIRS:
                dirnames.remove(eachDIR)
        for eachFile in filenames:
            if os.path.splitext(eachFile)[1] in IGNORE_EXTENSIONS:
                continue
            path = os.path.join(dirpath, eachFile)
            try:
                mtime = os.stat(path).st_atime
            except WindowsError:
                print("Eating exception while getting modified time for file: " + path)

            allFiles.append(SingleFile(path, mtime))

    return allFiles

def LatestNFilesUnderThisDirectory(directory, noOfFiles):
    allFiles = AllFilesInThisDirectory(os.curdir)
    allFiles.sort()

    result = [eachFile.path for eachFile in allFiles[-1 * noOfFiles:]]
    return result

def LatestFilePathUnderThisDirectory(directory):
    allFiles = AllFilesInThisDirectory(directory)
    allFiles.sort(reverse=True)
    recentFile = allFiles[0]
    return recentFile.path

if __name__ == '__main__':
    allFiles = AllFilesInThisDirectory(os.curdir)
    allFiles.sort()

    for eachFile in allFiles:
        printNow(eachFile.path)

