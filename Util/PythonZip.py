#############################################################
##This file contains a routine to zip a directory and a file
##
##Author: Ashish Anand
##Date: 4-Apr-2012
##
#############################################################

import zipfile
import os
from Util.Exception import MyException

def CreateZipDir(folderPath, zipFileAbsPath):
    '''This function will zip the folder and create file with absolute path'''
    with zipfile.ZipFile(zipFileAbsPath, mode='w') as zf:
        for root, dirs, files in os.walk(folderPath):
            for eachfile in files:
                eachFilePath = os.path.join(root, eachfile)
                zf.write(eachFilePath, compress_type=zipfile.ZIP_DEFLATED)

def ExtractFileIntoTempDirFromZippedFile(zippedFile, destFileName):
    """ Extracts a file and places it in the tempdir and gives back a handle for normal usage"""
    if not zipfile.is_zipfile(zippedFile):
        raise MyException(zippedFile + " is not a proper zip file.")

    with zipfile.ZipFile(zippedFile, "r") as zf:
        if destFileName not in zf.namelist():
            raise MyException(destFileName + " not not present in " + zippedFile)
        from tempfile import mkdtemp
        tempdir = mkdtemp()
        newPath = os.path.join(tempdir, destFileName)
        zi = zf.getinfo(destFileName)
        zf.extract(zi, tempdir)
    return newPath
