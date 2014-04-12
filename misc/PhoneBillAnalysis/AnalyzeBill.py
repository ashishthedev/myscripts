BILL_PDF_FILE_PATH = "B:\\desktop\\b\\Bill-2014-03.pdf"
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

def CreateRecordFromThisString(recordString):
    if recordString[2] != "-" or recordString[6] != "-":
        #Bare minimum criteria for even attempting to create a record
        raise Exception("Trying to feed an invalid record")

    rcType = TryToDeduceTypeOfRecord(recordString)

    if RECORD_TYPE.CALL == rcType:
        date = recordString[CALL_SEMANTICS.DATE_FROM:CALL_SEMANTICS.DATE_TO]
        time = recordString[CALL_SEMANTICS.TIME_FROM : CALL_SEMANTICS.TIME_TO]
        number = recordString[CALL_SEMANTICS.NUMBER_FROM : CALL_SEMANTICS.NUMBER_TO]
        duration = recordString[CALL_SEMANTICS.DURATION_FROM: CALL_SEMANTICS.DURATION_TO]
        amount = recordString[CALL_SEMANTICS.AMOUNT_FROM: CALL_SEMANTICS.AMOUNT_TO]
        personName = FindName(number)
        return CallRecord(number, date, time, duration, amount, personName)

    elif RECORD_TYPE.MSG == rcType:
        date = recordString[MSG_SEMANTICS.DATE_FROM:MSG_SEMANTICS.DATE_TO]
        time = recordString[MSG_SEMANTICS.TIME_FROM : MSG_SEMANTICS.TIME_TO]
        number = recordString[MSG_SEMANTICS.NUMBER_FROM : MSG_SEMANTICS.NUMBER_TO]
        amount = recordString[MSG_SEMANTICS.AMOUNT_FROM: MSG_SEMANTICS.AMOUNT_TO]
        personName = FindName(number)
        return CallRecord(number, date, time, duration, amount, personName)
    elif RECORD_TYPE.ROAMING == rcType:
        date = recordString[ROAMING_SEMANTICS.DATE_FROM:ROAMING_SEMANTICS.DATE_TO]
        time = recordString[ROAMING_SEMANTICS.TIME_FROM : ROAMING_SEMANTICS.TIME_TO]
        number = recordString[ROAMING_SEMANTICS.NUMBER_FROM : ROAMING_SEMANTICS.NUMBER_TO]
        amount = recordString[ROAMING_SEMANTICS.AMOUNT_FROM: ROAMING_SEMANTICS.AMOUNT_TO]
        personName = FindName(number)
        return CallRecord(number, date, time, duration, amount, personName)

    else:
        print("Cannot understand what is: '{}'".format(recordString))
        return None

class CALL_SEMANTICS:
    """
11-mar-2014 12:00:26 7800662587 04:09 2.50 6
    """
    DATE_FROM = 0
    DATE_TO = 11
    TIME_FROM = 11
    TIME_TO = 19
    NUMBER_FROM = 19
    NUMBER_TO = 29
    DURATION_FROM = 29
    DURATION_TO = 34
    AMOUNT_FROM = 34
    AMOUNT_TO = 38

class MSG_SEMANTICS:
    """
08-mar-2014 10:08:44 9971602777 1 0.30**2
    """
    DATE_FROM = 0
    DATE_TO = 11
    TIME_FROM = 11
    TIME_TO = 19
    NUMBER_FROM = 19
    NUMBER_TO = 29
    DURATION_FROM = 29
    AMOUNT_FROM = 30
    AMOUNT_TO = 34

class ROAMING_SEMANTICS:
"""
05-apr-201420:43:43airtel-upwest9389620396 00:34 0.75**2
"""
    DATE_FROM = 0
    DATE_TO = 11
    TIME_FROM = 11
    TIME_TO = 19
    NUMBER_FROM = 19
    NUMBER_TO = 29
    DURATION_FROM = 29
    AMOUNT_FROM = 30
    AMOUNT_TO = 34

def process_text_and_get_list_of_records(text):
    text = text.lower()
    listOfRecords = list()
    pivots = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    #Everything starts from the name of month. They are the pivots for our parsing mechanism.

    for pivot in pivots:
        pos = text.find(pivot, 0)
        while pos != -1:
            #Continue until you cannot find any more instances of this pivot
            nextPos = text.find(pivot, pos + 1)
            if nextPos == -1: break
            recordString = text[pos-3 : nextPos-3]
            if len(recordString) < 100 :
                interpretedRecord = TryToDeduceTypeOfRecord(recordString)
                if interpretedRecord == RECORD_TYPE.DONT_KNOW:
                    print("Cannot understand what is: {}".format(recordString))
                else:

                    listOfRecords.append(interpretedRecord)
            pos = text.find(pivot, pos+1)
    return listOfRecords


def FindName(number):
    for c in CONTACT_LIST:
        if c.strippedNo == number:
            return c.name
    return None


def TryToDeduceTypeOfRecord(recordString):
    zones = ["east", "west", "north", "south"]
    #The ordering of following if else blocks is important
    if recordString.find(".com") != -1:
        return RECORD_TYPE.GPRS
    elif len([z for z in zones if recordString.find(z) != -1]) >0: #IF any zone is present
        return RECORD_TYPE.ROAMING
    elif recordString.count(":") == 2: #Only 2 colons in time stamps
        return RECORD_TYPE.MSG
    elif recordString.count(":") == 3: #Only 3 colons in time stamp and durations
        return RECORD_TYPE.CALL
    else:
        return RECORD_TYPE.DONT_KNOW
    return


class RECORD_TYPE:
    DONT_KNOW = -1
    TEXT = 1
    CALL = 2
    MSG = 3
    ROAMING = 4
    GPRS = 5


def DebugPDFSemantics(text):
    text = text.lower()
    listOfRecords = list()
    pivots = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    zones = ["east", "west", "north", "south"]
    #Everything starts from the name of month. They are the pivots for our parsing mechanism.

    for pivot in pivots:
        pos = text.find(pivot, 0)

        while pos != -1:
            #Continue until you cannot find any more instances of this pivot
            nextPos = text.find(pivot, pos + 1)
            if nextPos == -1:
                break
            recordString = text[pos-3 : nextPos-3]
            #Sample record is given below
            #Call = 09-Aug-201315:55:34XXXXXXXXXX00:470.00
            #msg  = 12-Aug-201310:39:31997160277710.30**XX
            if len(recordString) < 100:
                rcType = None
                if recordString.find(".com") != -1:
                    rcType = "GPRS"
                elif len([z for z in zones if recordString.find(z) != -1]) >0: #IF any zone is present
                    rcType = "ROAMING"
                elif recordString.count(":") == 2: #Only 2 colons in time stamps
                    rcType = "MESG"
                elif recordString.count(":") == 3: #Only 3 colons in time stamp and durations
                    rcType = "CALL"
                if rcType:
                    print("{} | {}".format(rcType, recordString))
                else:
                    print("Cannot understand: Len: {} | {}".format(len(recordString), recordString))

            pos = text.find(pivot, pos+1)
    return listOfRecords


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

    #DebugPDFSemantics(text); return
    listOfRecords = process_text_and_get_list_of_records(text)
    listOfRecords = sorted(listOfRecords, key = lambda r: (r.date, r.time))

    for r in listOfRecords:
        print(r)

if __name__ == '__main__':
    main()
