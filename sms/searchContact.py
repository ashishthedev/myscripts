from Util.Misc import PrintInBox
from Util.Config import GetAppDir, GetOption
from Util.Contacts import AllContacts

import argparse
import os

def ParseOptions():
    parser = argparse.ArgumentParser()

    parser.add_argument(dest='searchStr', nargs="+", default=None, help="Name substring")
    return parser.parse_args()

def ProcessAndShowRelatedContacts(listOfStrings):
  CONTACTS_CSV_PATH = os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "ContactsRelativePath"))
  allContacts = AllContacts(CONTACTS_CSV_PATH)
  for s in listOfStrings:
    def GetNumberList(c):
      return [n for n in [c.mobilePhone, c.homePhone, c.homePhone2, c.workPhone] if n]

    relatedContacts = allContacts.FindRelatedContacts(s)

    relatedContacts = [c for c in relatedContacts if GetNumberList(c)]

    if relatedContacts:
      for i, c in enumerate(relatedContacts, start=1):
        numbers = GetNumberList(c)
        for number in numbers:
          displayStr = " ".join([str(i) + ". ", str(number), c.firstName, c.middleName, c.lastName, c.emailAdd])
          print(displayStr)
    else:
      PrintInBox("No contact exists for {}".format(s))
  return

def main():
  args = ParseOptions()
  ProcessAndShowRelatedContacts(args.searchStr)

if __name__ == "__main__":
  main()
