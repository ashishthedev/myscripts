BILL_PDF_FILE_PATH = "B:\\desktop\\b\\Bill-2013-05.pdf"
#########################
## This file is meant to extract meaningful information from the text file converted directly from mobile bill pdf
##
## Date: 2013-Sep-11 Wed 02:26 PM
#########################

from UtilSonyPhoneBook import ParseVCardFile
from UtilPythonZip import ExtractFileIntoTempDirFromZippedFile
from UtilLatest import LatestFilePathUnderThisDirectory
from UtilConfig import GetAppDir
from UtilMisc import DD_MM_YYYY, ParseDateFromString
import os
import pyPdf


_CONTACT_FILE = "contacts.vcf"
_JOHNBACKUPDIR = os.path.join(GetAppDir(), "..\\Personal\\Phone\\Nano Phone Naite backup")
CONTACT_LIST = ParseVCardFile(
        ExtractFileIntoTempDirFromZippedFile(
            LatestFilePathUnderThisDirectory(_JOHNBACKUPDIR), _CONTACT_FILE))

class CallRecord(object):
    def __init__(self, number, date, time, duration, amount, personName):
        self.number = number
        self.date = ParseDateFromString(date)
        self.time = time
        self.duration = duration
        self.amount = amount
        self.personName = personName
        self.isMessage = True if (duration == "1") else False
        self.isCall = not self.isMessage

    def __str__(self):
        if self.personName:
            identification = self.personName
        else:
            identification = self.number + "<<<<<<<<<<<<<<<<<<<<"

        if self.isMessage:
            duration = "SMS"
        else:
            duration = self.duration

        return "{:<15} {:<10} {:<10} {:<10}".format(
                DD_MM_YYYY(self.date),
                self.time,
                duration,
                identification,
                )

def CreateRecordFromThisString(record):
    if record[2] != "-" or record[6] != "-":
        #Bare minimum criteria for even attempting to create a record
        raise Exception("Trying to feed an invalid record")

    def isCallRecord(record):
        thirtyFirstChar = record[31]
        return thirtyFirstChar == ":"

    def isMsgRecord(record):
        thirtyFirstChar = record[31]
        twentyNinthChar = record[29]
        return (thirtyFirstChar == "." and twentyNinthChar == "1")

    if isCallRecord(record):
        date = record[0:11]
        time = record[11:19]
        number= record[19:29]
        duration = record[29:34]
        amount = record[34:38]
        personName = FindName(number)
        return CallRecord(number, date, time, duration, amount, personName)

    elif isMsgRecord(record):
        date = record[0:11]
        time = record[11:19]
        number= record[19:29]
        duration = record[29]
        amount = record[30:34]
        personName = FindName(number)
        return CallRecord(number, date, time, duration, amount, personName)
    else:
        print("Cannot understand what is: '{}'".format(record))
        return None

def process_text_and_get_list_of_records(text):
    text = text.lower()
    listOfRecords = list()
    pivots = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    #Everything starts from the name of month. They are the pivots for our parsing mechanism.

    for pivot in pivots:
        pos = text.find(pivot, 0)

        while pos != -1:
            #Continue until you cannot find any more instances of this pivot
            record = text[pos-3:pos+35]
            #Sample record is given below
            #Call = 09-Aug-201315:55:34XXXXXXXXXX00:470.00
            #msg  = 12-Aug-201310:39:31997160277710.30**XX
            if (record[2] == "-") and (record[6] == "-"):
                #Its a date - confirmed
                rec = CreateRecordFromThisString(record)
                if rec:
                    listOfRecords.append(rec)

            pos = text.find(pivot, pos+1)
    return listOfRecords


def FindName(number):
    for c in CONTACT_LIST:
        if c.strippedNo == number:
            return c.name
    return None




def main():

    import sys
    text = ""
    if len(sys.argv)>1:
        fileName = sys.argv[1]
    else:
        fileName = BILL_PDF_FILE_PATH
    with open(fileName, "rb") as f:
        pdf = pyPdf.PdfFileReader(f)
        pdf.decrypt(raw_input("Enter password: "))
        for page in pdf.pages:
            text += page.extractText()

    listOfRecords = process_text_and_get_list_of_records(text)

    listOfRecords = sorted(listOfRecords, key = lambda r: (r.date, r.time))

    for r in listOfRecords:
        print(r)

if __name__ == '__main__':
    main()
