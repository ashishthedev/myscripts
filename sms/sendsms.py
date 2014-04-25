from UtilSms import SendSms, CanSendSmsAsOfNow
from UtilMisc import PrintInBox
import subprocess
import os

def ParseContents(smsContents):
    NEWLINE = "\n"
    lines = smsContents.split(NEWLINE)
    lines = [l.strip() for l in lines if l.strip() != "\n"] #remove blank lines
    fLine = lines[0].lower()
    nos = fLine.replace(',', ';').split(';')


    return tuple(nos) , "\n".join(smsContents.split(NEWLINE)[1:])

def GetDataFromUserAndSendSms():
    toTheseUnprocessedNumbersList = None
    smsContents = None
    TEMP_FILE_NAME = "temp.txt"

    #Open the file and enter the sms contents
    blockingCommandForGvim = [os.path.join(os.path.expandvars("%windir%"),"gvim.bat") , "-f", "+0", TEMP_FILE_NAME]
    subprocess.call(blockingCommandForGvim)
    with open(TEMP_FILE_NAME) as f:
        smsContents = f.read()

    if not smsContents:
        errorMsg = "No sms contents. Bailing out"
        PrintInBox(errorMsg)
        raise Exception(errorMsg)

    toTheseUnprocessedNumbersList, smsContents = ParseContents(smsContents)

    if smsContents and toTheseUnprocessedNumbersList:
        line = "_"*70
        msg = "{l}\nTo: {to}\n{con}{l}\nSend: (y/n)".format(to=toTheseUnprocessedNumbersList, l=line, con=smsContents)
        if not raw_input(msg).lower() == "y":
            print("Not sending message...")
        else:
            SendSameSmsToTheseUnprocessedStrings(smsContents, toTheseUnprocessedNumbersList)


def SendSameSmsToTheseUnprocessedStrings(smsContents, listOfStrings):
    from UtilConfig import GetAppDir, GetOption
    from UtilContacts import AllContacts
    CONTACTS_CSV_PATH = os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "ContactsRelativePath"))
    allContacts = AllContacts(CONTACTS_CSV_PATH)
    finalContacts = list()
    for s in listOfStrings:
        #TODO: THere is a bug. Only serchign for first name. Fix it later. Should be related to generator.
        contacts = allContacts.FindRelatedContacts(s)
        for c in contacts:
            number = c.mobilePhone or c.homePhone or c.homePhone2
            if not number: continue
            displayStr = " ".join([str(number), c.firstName, c.middleName, c.lastName, c.emailAdd, "\n(y/n)?"])
            if raw_input(displayStr).lower() == 'y':
                finalContacts += number

    for singleNumber in finalContacts:
        try:
            SendSms(singleNumber, smsContents)
        except Exception:
            PrintInBox("Could not send to: {}".format(singleNumber))


if __name__ == "__main__":

    print("Checking if sms can be sent ...")
    if not CanSendSmsAsOfNow():
        errorMsg = "Sorry the connection with phone cannot be established..."
        PrintInBox(errorMsg)
        raise Exception(errorMsg)
    else:
        print("Connection established...\nPlease enter the number and text")
        GetDataFromUserAndSendSms()

