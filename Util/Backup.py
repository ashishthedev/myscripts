#####################################################################
## This Python script is intended to zip certain folders and send
## them over designated emails.
## Requirements: Python interpretor must be installed.
## Author: Ashish Anand
## Date: 24-Nov-2011

import os, tempfile, shutil
from Util.Misc import printNow, PrintInBox, GetHash
from datetime import datetime
import Util.PythonMail

HASH_SECTION = "DEFAULT"

class Config:
    def __init__(self, server, port, username, toEmail, ccEmail, mpass, successNotification, fromDisplayName):
        self.SMTP_SERVER = server
        self.SMTP_PORT   = port
        self.USERNAME    = username
        self.FROM_EMAIL  = username
        self.TO_EMAIL    = toEmail
        self.CC_EMAIL    = ccEmail
        self.MPASS       = mpass
        self.SUCCESS_NOTIFICATION_MAIL = successNotification
        self.fromDisplayName = fromDisplayName

class SingleBackupLocation:
    def __init__(self, sub, path, config):
        self.emailSubject = sub
        self.path = path
        self.config = config

class AllBackupLocations(list):
    def __init__(self):
        super(AllBackupLocations, self).__init__(list())
        self.successMsg = "To be updated"


def Backup(backupLocations, ignorePatternList=None):
    tempdir = tempfile.mkdtemp()
    try:
        print("Wait...\n")
        startTime = datetime.now()

        if ignorePatternList:
            print("Ignoring the following files")
            print(ignorePatternList)

        #Make a temp copy while ignoring undesirable files
        tempBackupLocations = MakeTempCopyOfFiles(backupLocations, tempdir, shutil.ignore_patterns(*ignorePatternList))

        print("You can resume your work now...\n")

        print("Temporary Backup Directory: " + tempdir)

        i=0
        for eachItem in tempBackupLocations:
            a = datetime.now()
            i += 1
            printNow("{} of {}: {}...".format(str(i), str(len(tempBackupLocations)), eachItem.emailSubject));
            if isHashSame(eachItem.path):
                print("Same as before not sending again")
                continue
            ZipAndEmail(str(i) + " of " +  str(len(tempBackupLocations)) + ": " + eachItem.emailSubject, eachItem.path, eachItem.config)
            SaveNewHash(eachItem.path)
            b = datetime.now() - a
            print("{:.0f} minutes and {} seconds".format(b.seconds/60, b.seconds%60))
        totalTime = datetime.now() - startTime
        print(
        """
        __________________________________________________________________
        _____________________________SUCCESS______________________________
        __________________________________________________________________
        """)
        c = tempBackupLocations[0].config
        Util.PythonMail.SendMail(
                "Backup Successful",
                None,
                c.SMTP_SERVER,
                c.SMTP_PORT,
                c.FROM_EMAIL,
                c.SUCCESS_NOTIFICATION_MAIL,
                None,
                None,
                c.MPASS,
                BODYTEXT=backupLocations.successMsg,
                fromDisplayName = c.fromDisplayName
                )

        print("Total time taken : {:.0f} minutes and {} seconds".format(totalTime.seconds/60, totalTime.seconds%60))
    except Exception as ex:
        print(
        """
        __________________________________________________________________
        _____________________________FAILURE______________________________
        __________________________________________________________________
        """)
        print("Backup Failed...")
        PrintInBox(str(ex))
        raise
    finally:
        shutil.rmtree(tempdir, ignore_errors=False)

    assert not os.path.exists(tempdir), str(tempdir) + " still exists"  #Just before returning make sure, that we are not leaving any litter in tempdir
    return

def MakeTempCopyOfFiles(backupLocations, tempdir, ignorePattern=None):
    #Let the exceptions propagate through. We dont want to proceed if all the files are not readable
    #The intent of this function is to create a copy of files in a temporary directory thereby freeing the user to continue his work while the backup is being zipped and uploaded.
    newBackupLocations = AllBackupLocations()
    for eachLocation in backupLocations:
        newPath=None
        if os.path.isdir(eachLocation.path):
            #Its a dir; create a copy in tempdir
            leafDir = os.path.basename(eachLocation.path)
            leafDirParent = os.path.basename(os.path.dirname(eachLocation.path))
            newPath = os.path.join(tempdir, leafDirParent, leafDir)
            shutil.copytree(eachLocation.path, newPath, ignore=ignorePattern)
        else:
            #Its a file; just copy in temp file
            newPath = os.path.join(tempdir, os.path.basename(eachLocation.path))
            shutil.copy(eachLocation.path, tempdir)

        assert newPath is not None
        #Update the new location
        newBackupLocations.append(SingleBackupLocation(eachLocation.emailSubject, newPath, eachLocation.config))

    return newBackupLocations

def ZipAndEmail(emailSubject, path, config):
    if os.path.isdir(path):
        DirZipAndEmail(emailSubject, path, config)
    elif os.path.isfile(path):
        EmailFile(emailSubject, path, config)
    else:
        assert "Should not reach here"
    return

def DirZipAndEmail(emailSubject, folderPath, config):
    """
    This function will create a zip file for the provided folder path in tempdir, email that zipped file and then clean up any files that were created in the process and delete that tempdir.
    """
    assert os.path.isdir(folderPath), folderPath + " should be a directory"
    from Util.PythonZip import CreateZipDir
    tempdir = tempfile.mkdtemp()
    try:
        zfilename = os.path.join(tempdir, emailSubject + '_zip')
        CreateZipDir(folderPath, zfilename)
        EmailFile(emailSubject, zfilename, config)
    finally:
        shutil.rmtree(tempdir, ignore_errors=False)

    assert not os.path.exists(tempdir), str(tempdir) + "should be empty"
    return

def EmailFile(emailSubject, path, config):
    from Util.Misc import GetSizeOfFileInMB
    print("Size of file: " + str(GetSizeOfFileInMB(path)) + " Mb")
    return Util.PythonMail.SendMail(
            emailSubject = emailSubject,
            zfilename = path,
            SMTP_SERVER = config.SMTP_SERVER,
            SMTP_PORT = config.SMTP_PORT,
            FROM_EMAIL = config.FROM_EMAIL,
            TO_EMAIL_LIST = config.TO_EMAIL,
            CC_EMAIL_LIST = config.CC_EMAIL,
            BCC_EMAIL_LIST = None,
            MPASS = config.MPASS,
            fromDisplayName=config.fromDisplayName)

def DeleteFileIfExists(AbsolutePath):
  if os.path.exists(AbsolutePath):
    os.remove(AbsolutePath)
  return

def PersistentEmailBackupHashes():
  def __init__(self):
    super(self.__class__.__name__, self).__init__(self.__class__.__name__)

def isHashSame(dirPath):
  p = PersistentEmailBackupHashes()
  freshHash = GetHash(dirPath)
  if dirPath not in p:
    #The directory is newly created, Set the hash for this directory to 0
    print(dirPath + " is being backed up for the first time")
    return False
  oldHash = p[dirPath]
  return freshHash == oldHash


def SaveNewHash(dirPath):
  #A hash is strored to detect if the directory has changed.
  p = PersistentEmailBackupHashes()
  p[dirPath] = GetHash(dirPath)
  return
