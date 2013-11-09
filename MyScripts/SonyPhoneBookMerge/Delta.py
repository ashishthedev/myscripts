'''
File: JohnAndKoshiDelta.py
Author: Ashish Anand
Description: Produce a delta straigth from .dbk backup files. No need to unzip and feed to scripts.
Date:  2012-10-09
'''

from UtilLatest import LatestFilePathUnderThisDirectory
from Merge import FindMissingContactsInJohnsBook
from Merge import PrintContactsToFile
from UtilException import MyException
from UtilMisc import PrintInBox
from UtilPythonZip import ExtractFileIntoTempDirFromZippedFile
from UtilConfig import GetAppDir
import os
import datetime
import math

_JOHNBACKUPDIR = os.path.join(GetAppDir(), "Personal\\Phone\\Nano Phone Naite backup")
_KOSHIBACKUPDIR = os.path.join(GetAppDir(), "Personal\\Phone\\Koshi Phone Backup")

_DELTAFILE = "b:\\desktop\\delta.vcf"
_CONTACT_FILE = "contacts.vcf"


def PrintDelta(JohnBackupDir, KoshiBackupDir, deltaFile):
    johnBackupFile = LatestFilePathUnderThisDirectory(JohnBackupDir)
    koshiBackupFile = LatestFilePathUnderThisDirectory(KoshiBackupDir)

    t1 = datetime.datetime.fromtimestamp(os.path.getmtime(johnBackupFile))
    t2 = datetime.datetime.fromtimestamp(os.path.getmtime(koshiBackupFile))
    delta = t1-t2

    print("John Latest Date: {}".format(t1))
    print("Koshi Latest Date: {}".format(t2))
    print("%d days difference in two files" % (math.fabs(delta.days)))

    johnFile = ExtractFileIntoTempDirFromZippedFile(johnBackupFile, _CONTACT_FILE)
    koshiFile = ExtractFileIntoTempDirFromZippedFile(koshiBackupFile, _CONTACT_FILE)


    PrintContactsToFile(deltaFile, FindMissingContactsInJohnsBook(johnFile, koshiFile))


if __name__ == '__main__':
    try:
        PrintDelta(_JOHNBACKUPDIR, _KOSHIBACKUPDIR, _DELTAFILE)
    except MyException as ex:
        PrintInBox(str(ex))
