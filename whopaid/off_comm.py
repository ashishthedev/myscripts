##############################################################################
## Intent: To have a single entry point for official communication
##
## Date: 2013-Jul-30 Tue 12:39 PM
##############################################################################
from Util.Config import GetOption
from Util.PythonMail import SendMail
from Util.Sms import SendSms
from Util.Misc import PrintInBox

from whopaid.customers_info import GetAllCustomersInfo


def SendOfficialEmail(emailSubject, zfilename, toMailList, ccMailList, bccMailList, bodyText, textType, fromDisplayName):
    section = "EMAIL_REMINDER_SECTION"
    return SendMail(emailSubject=emailSubject,
            zfilename=zfilename,
            SMTP_SERVER=GetOption(section, 'Server'),
            SMTP_PORT=GetOption(section, 'Port'),
            FROM_EMAIL=GetOption(section, 'FromEmailAddress'),
            TO_EMAIL_LIST=toMailList,
            CC_EMAIL_LIST=ccMailList,
            BCC_EMAIL_LIST=bccMailList,
            MPASS=GetOption(section, 'Mpass'),
            BODYTEXT=bodyText,
            textType=textType,
            fromDisplayName=fromDisplayName)

def SendOfficialSMSAndMarkCC(compName, msg):
  return _SendOfficialSMS(compName, msg, sendToCCNumbers=True)

def SendOfficialSMS(compName, msg):
  return _SendOfficialSMS(compName, msg, sendToCCNumbers=False)

def SendOfficialSMSToMD(compName, msg):
  return _SendOfficialSMSToMD(compName, msg, sendToCCNumbers=False)

def _SendOfficialSMSToMD(compName, msg, sendToCCNumbers=False):
  PrintInBox("Sending to MD", waitForEnterKey=True)
  allCustInfo = GetAllCustomersInfo()
  smsNo = allCustInfo.GetMDPhoneNumbers(compName)

  if not smsNo:
    raise Exception("No MD no. present for customer: {}".format(compName))

  return _SendOfficialSMSToTheseNumbers(compName, msg, sendToCCNumbers, smsNo)

def _SendOfficialSMS(compName, msg, sendToCCNumbers=False):

  PrintInBox("Sending to general people")
  allCustInfo = GetAllCustomersInfo()
  smsNo = ""
  paymentSMSNo = allCustInfo.GetPaymentSMSNumber(compName)
  smsDispatchSMS = allCustInfo.GetSmsDispatchNumber(compName)
  if paymentSMSNo:
    smsNo += ";" + paymentSMSNo
  if smsDispatchSMS:
    smsNo += ";" + smsDispatchSMS

  if not smsNo:
    raise Exception("No sms no. feeded for customer: {}".format(compName))

  return _SendOfficialSMSToTheseNumbers(compName, msg, sendToCCNumbers, smsNo)

def _SendOfficialSMSToTheseNumbers(compName, msg, sendToCCNumbers, targetNumbersCommaSepString):
  from string import Template
  allCustInfo = GetAllCustomersInfo()

  companyOfficialName = allCustInfo.GetCompanyOfficialName(compName)
  if not companyOfficialName:
    raise Exception("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

  d = dict()
  d["tFromName"] = "From: {}".format(GetOption("SMS_SECTION", 'FromDisplayName'))
  d["toName"] = "To: {}".format(companyOfficialName)
  d["msg"] = msg

  smsTemplate = Template("""$tFromName
$toName
$msg"""
)
  smsContents = smsTemplate.substitute(d)

  COMMA = ","
  smsNo = targetNumbersCommaSepString.replace(';', COMMA).strip()
  listOfNos = [x.strip() for x in smsNo.split(COMMA) if x.strip()]

  if sendToCCNumbers:
    additionalSmsNo = GetOption("SMS_SECTION", "CC_NO")
    if additionalSmsNo:
      additionalSmsNo = additionalSmsNo.replace(';', COMMA).strip()
      listOfNos.extend([x.strip() for x in additionalSmsNo.split(COMMA) if x.strip()])

  listOfNos = list(set(listOfNos))

  from Util.Misc import PrintInBox
  PrintInBox(smsContents)
  for x in listOfNos:
    print("Sending to this number: {}".format(x))
    SendSms(x, smsContents)
  return
