'''
File: UtilTemp.py
Author: Ashish Anand
Description: Helper functions related to Temp Files
Date: 24-Nov-2011
'''


import os, tempfile, shutil


def MakeTempCopy(filePath):
    #Let the exceptions propagate through. We dont want to proceed if all the files are not readable
    #The intent of this function is to create a copy of files in a temporary directory thereby freeing the user to continue his work while the backup is being zipped and uploaded.
    tempdir = tempfile.mkdtemp()
    shutil.copy(filePath, tempdir)
    newPath = os.path.join(tempdir, os.path.basename(filePath))
    return newPath

def CreateTempFileForTheseLinesAndReturnNewFilePath(lines, desiredFileName):
    tempdir = tempfile.mkdtemp()
    newPath = os.path.join(tempdir, desiredFileName)
    with open(newPath, "wb") as f:
        for eachLine in lines:
            f.write(eachLine)
    print (newPath)

    return newPath

