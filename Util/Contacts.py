import csv
from Util.Config import GetOption, GetAppDir
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
    WORK_PHONE = 38


class Contact(object):
    def __init__(self, row):
        self.firstName = row[COLS.FIRST_NAME]
        self.middleName = row[COLS.MIDDLE_NAME]
        self.lastName = row[COLS.LAST_NAME]
        self.emailAdd = row[COLS.EMAIL_ADDRESS]
        self.homePhone = row[COLS.HOME_PHONE].replace("-","")
        self.homePhone2 = row[COLS.HOME_PHONE2].replace("-","")
        self.mobilePhone = row[COLS.MOBILE_PHONE].replace("-","")
        self.workPhone = row[COLS.WORK_PHONE].replace("-","")

    def __str__(self):
        number = self.mobilePhone or self.homePhone or self.homePhone2 or self.workPhone
        return " ".join([str(number), self.firstName, self.middleName, self.lastName, self.emailAdd])

    def Name(self):
        return " ".join([self.firstName, self.middleName, self.lastName])

    def IsRelatedTo(self, s):
        allValuesConcatenated = "".join(self.__dict__.values())
        allValuesConcatenated = allValuesConcatenated.replace(" ", "").replace("-","").strip().lower()
        oneWordString = s.replace(" ", "").replace("-","").strip().lower()
        if allValuesConcatenated.find(oneWordString) != -1:
            return True
        return False


class AllContacts(object):
    def __init__(self, csvPath):
        self.db = list()
        with open(csvPath, 'rb') as f:
          for row in csv.reader(f):
            self.AddContact(Contact(row))
        return

    def AddContact(self, c):
        self.db.append(c)
        return

    def FindRelatedContacts(self, s):
        return [c for c in self.db if c.IsRelatedTo(s)]

    def ListOfContacts(self):
      return self.db

def main():
  _AK_CONTACT_FILE = "akcon.csv"
  _AK_CSV =  os.path.abspath(os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "ContactsRelativePath"), os.pardir, _AK_CONTACT_FILE))
  print(_AK_CSV)

  #allContacts = AllContacts(CONTACTS_CSV_PATH)
  allContacts = AllContacts(_AK_CSV)
  s = "9971008002"

  relContacts = allContacts.FindRelatedContacts(s)
  for c in relContacts:
      print(c)

if __name__ == "__main__":
    main()
