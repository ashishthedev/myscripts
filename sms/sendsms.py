from UtilSms import SendSms, PrefetchResources
from UtilMisc import PrintInBox
import subprocess
import os
from UtilConfig import GetAppDir, GetOption
from UtilContacts import AllContacts

def _ParseContents(smsContents):
  NEWLINE = "\n"
  lines = smsContents.split(NEWLINE)
  lines = [l.strip() for l in lines if l.strip() != "\n"] #remove blank lines
  fLine = lines[0].lower()
  nos = fLine.replace(',', ';').replace(' ', '').split(';')


  return tuple(nos) , "\n".join(smsContents.split(NEWLINE)[1:])

def _GetDataFromUserAndSendSms():
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
    SendSMSToThisBlobHavingNumbersAndContents(smsContents)
    return

def SendSMSToThisBlobHavingNumbersAndContents(smsContents):
  smsContents = str(smsContents)
  toTheseUnprocessedNumbersSeq, smsContents = _ParseContents(smsContents)

  if smsContents and toTheseUnprocessedNumbersSeq:
    PrintInBox("To: {to}\n{con}".format(to=toTheseUnprocessedNumbersSeq, con=smsContents))
    _SendSameSmsToTheseUnprocessedStrings(smsContents, toTheseUnprocessedNumbersSeq)
  return


def _SendSameSmsToTheseUnprocessedStrings(smsContents, listOfStrings):
  CONTACTS_CSV_PATH = os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "ContactsRelativePath"))
  allContacts = AllContacts(CONTACTS_CSV_PATH)
  singleNumbers = list()
  for s in listOfStrings:
    isNumber = True
    for ch in s:
      if ch not in "+1234567890":
        isNumber = False
        break

    if isNumber:
      if raw_input("{}\n(y/n)?".format(s)).lower() == 'y':
        singleNumbers.append(s)
    else:
      def GetNumberList(c):
        return [n for n in [c.mobilePhone, c.homePhone, c.homePhone2] if n]

      relatedContacts = allContacts.FindRelatedContacts(s)

      relatedContacts = [c for c in relatedContacts if GetNumberList(c)]

      if relatedContacts:
        print("Choose from:\n{}".format("\n".join(str(i) + ". " + str(c) for i, c in enumerate(relatedContacts, start=1))))
        print("_"*30)
        for i, c in enumerate(relatedContacts, start=1):
          numbers = GetNumberList(c)
          for number in numbers:
            displayStr = " ".join([str(i) + ". ", str(number), c.firstName, c.middleName, c.lastName, c.emailAdd, "\n(y/n)?"])
            if raw_input(displayStr).lower() == 'y':
              singleNumbers.append(number)
              break

  singleNumbers = [c for c in singleNumbers if c.strip()]

  for singleNumber in singleNumbers:
    try:
      SendSms(singleNumber, smsContents)
    except Exception:
      PrintInBox("Could not send to: {}".format(singleNumber))
  return

if __name__ == "__main__":
    PrefetchResources()
    _GetDataFromUserAndSendSms()
