######################################
##Author:  Ashish Anand
##Date:    13 Dec 2011
######################################

import sys

class ContactList(list):
    """
    This class represents a list of single contacts
    """
    def __init__(self):
        super(ContactList, self).__init__(list())

class SingleContact:
    def __init__(self, name=None, actualNo=None, strippedNo=None):
        self.name=name
        self.actualNo = actualNo
        self.strippedNo = strippedNo

    def __str__(self):
        return "PNo.={!r:>16}; Name={!r}".format(self.actualNo, self.name)

    def __eq__(self, other):
        return other.strippedNo == self.strippedNo

    def PrintAsVCard(self, fh=sys.stdout):
        record =\
"""BEGIN:VCARD
VERSION:2.1
N;CHARSET=UTF-8:{0}
FN;CHARSET=UTF-8:{0}
TEL;CELL:{1}
END:VCARD""".format(self.name, self.actualNo)
        fh.write(record)

def ParseVCardFile(filePath):
    KnownTags={ "START":"BEGIN", "END" : "END", "NAME":"FN;", "TEL":"TEL;"}

    myContactList = ContactList()
    with open(filePath) as f:
        insideBlock = False
        actualNo = ""#Actual Contact Number
        name = ""
        strippedNo = ""#Number without codes i.e. +91 and 0
        for each_line in f:
            tagFound=False
            for tag in KnownTags.values():
                if each_line.startswith(tag):
                    tagFound=True
            if not tagFound: continue #We dont know what to do with this tag hence we will skip it

            (field, data) = each_line.split(':', 1)
            if(field == KnownTags["START"]):
                assert insideBlock == False, filePath +  " not in proper format"
                insideBlock=True
            elif(field.startswith(KnownTags["NAME"])):
                name = data.strip()
            elif(field.find(KnownTags["TEL"])!=-1):
                actualNo = data.strip()
                if actualNo.startswith("+91"): strippedNo = actualNo[3:]
                elif actualNo.startswith("0"): strippedNo = actualNo[1:]
                else: strippedNo = actualNo
            elif(field == KnownTags["END"]):
                insideBlock = False
                myContactList.append(SingleContact(name, actualNo, strippedNo))
    return myContactList
