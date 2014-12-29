######################################
## Author:  Ashish Anand
## Date:    13 Dec 2011
## Intent: Feed a sony ericsson vcf phonebook and find duplicate entries.
######################################
from UtilLatest import LatestFilePathUnderThisDirectory
from UtilPythonZip import ExtractFileIntoTempDirFromZippedFile
from UtilSonyPhoneBook import ParseVCardFile
from UtilConfig import GetAppDir
import os

_JOHNBACKUPDIR = os.path.join(GetAppDir(), "Personal\\Phone\\Nano Phone Naite backup")
_KOSHIBACKUPDIR = os.path.join(GetAppDir(), "Personal\\Phone\\Koshi Phone Backup")
_CONTACT_FILE = "contacts.vcf"


def FindAndPrintDupNumbersInContactFile(contactsFile):
    contacts = ParseVCardFile(contactsFile)
    #Sort the list on the basis of numbers and look for duplicate entries in adjacent rows
    sorted(contacts, key=lambda c:c.strippedNo)#Sort by actual number
    for i in range (0, len(contacts)-1):
        if(contacts[i].strippedNo == contacts[i+1].strippedNo):
            print(contacts[i])
            print(contacts[i+1])
    return

def main():

    johnBackupFile = LatestFilePathUnderThisDirectory(_JOHNBACKUPDIR)
    koshiBackupFile = LatestFilePathUnderThisDirectory(_KOSHIBACKUPDIR)

    johnFile = ExtractFileIntoTempDirFromZippedFile(johnBackupFile, _CONTACT_FILE)
    koshiFile = ExtractFileIntoTempDirFromZippedFile(koshiBackupFile, _CONTACT_FILE)

    raw_input("Duplicate John Contacts...")
    FindAndPrintDupNumbersInContactFile(johnFile)
    raw_input("Duplicate Koshi Contacts...")
    FindAndPrintDupNumbersInContactFile(koshiFile)

    return

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, IOError) as err:
        print("Exception caught in main()-> {}".format(str(err)))
        raise
    finally:
        raw_input("Press Enter to continue...")
        pass
