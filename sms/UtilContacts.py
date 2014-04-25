import csv
from UtilConfig import GetOption, GetAppDir
import os
DEBUG_COL_NOS = True
DEBUG_COL_NOS = False

CONTACTS_CSV_PATH = os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "ContactsRelativePath"))

class COLS:
    FIRST_NAME = 0
    MIDDLE_NAME = 1
    LAST_NAME = 2
    EMAIL_ADDRESS = 14
    PRIMARY_PHONE = 17
    HOME_PHONE = 18
    HOME_PHONE2 = 19
    MOBILE_PHONE = 20


class Contact(object):
    def __init__(self, row):
        self.firstName = row[COLS.FIRST_NAME]
        self.middleName = row[COLS.MIDDLE_NAME]
        self.lastName = row[COLS.LAST_NAME]
        self.emailAdd = row[COLS.EMAIL_ADDRESS]
        self.homePhone = row[COLS.HOME_PHONE]
        self.homePhone2 = row[COLS.HOME_PHONE2]
        self.mobilePhone = row[COLS.MOBILE_PHONE]

    def IsRelatedTo(self, s):
        for attr, val in self.__dict__.items():
            if val.startswith("__"): continue
            if val.lower().find(str(s).lower()) != -1:
                return True

        return False


class AllContacts(object):
    def __init__(self, csvPath):
        self.csvPath = csvPath
        self.db = list()
        with open(self.csvPath, 'rb') as f:
            reader = csv.reader(f)
            for row in reader:
                if DEBUG_COL_NOS:
                    for i, col in enumerate(row):
                        print("{:<5} {}").format(i, col)
                    break
                con = Contact(row)
                self.AddContact(con)

    def AddContact(self, c):
        self.db.append(c)

    def FindRelatedContacts(self, s):
        print("Searching for {}".format(s))
        l = [c for c in self.db if c.IsRelatedTo(s)]
        print("returning {}".format(l))
        return l



def main():
    allContacts = AllContacts(CONTACTS_CSV_PATH)
    s = "kosh"

    relContacts = allContacts.FindRelatedContacts(s)
    for c in relContacts:
        print(c.firstName)
if __name__ == "__main__":
    main()
