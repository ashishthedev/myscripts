'''
File: JohnAndKoshiDelta.py
Author: Ashish Anand
Description: Produce a delta straigth from .dbk backup files. No need to unzip and feed to scripts.
Date:  2012-10-09
'''

from Util.Latest import LatestFilePathUnderThisDirectory
from Merge import FindMissingContactsInJohnsBook
from Merge import PrintContactsToFile
from Util.Exception import MyException
from Util.Misc import PrintInBox
from Util.PythonZip import ExtractFileIntoTempDirFromZippedFile
from Util.Config import GetAppDir
import os
import datetime
import math

_JOHNBACKUPDIR = os.path.join(GetAppDir(), "Personal\\Phone\\Nano Phone Naite backup")
_KOSHIBACKUPDIR = os.path.join(GetAppDir(), "Personal\\Phone\\Koshi Phone Backup")

_DELTAFILE = "b:\\desktop\\delta.vcf"



def PrintDelta(JohnBackupDir, KoshiBackupDir, deltaFile):
    _CONTACT_FILE = "contacts.vcf"
    johnFile = os.path.join("b:\\desktop","c", "m", _CONTACT_FILE)
    koshiFile = os.path.join("b:\\desktop","c", "p", _CONTACT_FILE)
    PrintContactsToFile(deltaFile, FindMissingContactsInJohnsBook(johnFile, koshiFile))
    return

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

    _KOSHIBACKUPDIR = os.path.join("b:\\desktop","c", "p")

    _DELTAFILE = "b:\\desktop\\delta.vcf"
    _CONTACT_FILE = "contacts.vcf"

    johnFile = os.path.join(_JOHNBACKUPDIR, _CONTACT_FILE)
    koshiFile = os.path.join(_KOSHIBACKUPDIR, _CONTACT_FILE)

    PrintContactsToFile(deltaFile, FindMissingContactsInJohnsBook(johnFile, koshiFile))


if __name__ == '__main__':
    try:
        PrintDelta(_JOHNBACKUPDIR, _KOSHIBACKUPDIR, _DELTAFILE)
    except MyException as ex:
        PrintInBox(str(ex))
