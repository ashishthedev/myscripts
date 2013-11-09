######################################
##Author:  Ashish Anand
##Date:    13 Dec 2011
## Intent: Feed two sony ericssons vcf phonebooks and find those contacts which are present in others pb and not in John's contacts
######################################
_JOHNFILE="John.vcf"
_KOSHIFILE="koshi.vcf"
_DELTAFILE="B:\\Desktop\\DeltaContacts.vcf"

from UtilSonyPhoneBook import ParseVCardFile
from UtilSonyPhoneBook import ContactList

def main():
    missingContacts = FindMissingContactsInJohnsBook(_JOHNFILE, _KOSHIFILE)
    PrintContactsToFile(_DELTAFILE, missingContacts)

def PrintContactsToFile(filePath, missingContacts):
    with open(filePath, "w") as f:
        ctr = 0
        for contact in missingContacts:
            contact.PrintAsVCard(f)
            ctr+=1
            print("Adding an entry for: " + contact.name)
        print(str(ctr) + " new entries written in " + str(filePath))
    return



def FindMissingContactsInJohnsBook(johnFile, KoshiFile):
    johnContacts = ParseVCardFile(johnFile)
    koshiContacts = ParseVCardFile(KoshiFile)
    missingContacts = ContactList()
    for cn in koshiContacts:
        if cn not in johnContacts:
            missingContacts.append(cn)
    return missingContacts

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, IOError) as err:
        print("Exception caught in main()-> {}".format(str(err)))
        raise
    finally:
        #input("Press Enter to continue...")
        pass
