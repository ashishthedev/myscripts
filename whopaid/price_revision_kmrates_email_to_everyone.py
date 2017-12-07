
###############################################################################
## Author: Ashish Anand
## Date: 2017-Dec-01 Fri 05:04 PM
## Intent: To send price revision email to each of our customers in bulk.
##         The mail addresses are picked up from CUST_SHEETNAME in the
##         WRKBK_PATH excel file
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from Util.Exception import MyException
from Util.Config import GetOption
from Util.HTML import UnderLine, Bold, PastelOrangeText

from whopaid.util_whopaid import GetAllCompaniesDict
from collections import defaultdict
from string import Template
import datetime

from Util.Config import GetOption, GetAppDir
from Util.Exception import MyException
from Util.Misc import PrintInBox
from Util.Persistent import Persistent
from Util.PythonMail import SendMail

from whopaid.customers_info import GetAllCustomersInfo
from whopaid.customer_group_info import GetToCCBCCListforGroup
from whopaid.off_comm import SendOfficialSMS
from whopaid.sanity_checks import CheckConsistency
from whopaid.util_whopaid import GuessCompanyGroupName


import argparse
import random
import os

class KMPriceRevisionEmailPersistentDates(Persistent):
  def __init__(self):
    super(KMPriceRevisionEmailPersistentDates, self).__init__(self.__class__.__name__)

def EarlierSentOnPriceRevisionForThisGrp(grpName):
  """Returns a dateObject representing the date on which an email was last sent to this company"""
  p = KMPriceRevisionEmailPersistentDates()
  if grpName in p:
    return p[grpName]
  return None

def SaveSentOnDateForThisGrp(grpName):
  """Registers today() as the date on which last email was sent to company."""
  p = KMPriceRevisionEmailPersistentDates()
  p[grpName] = datetime.date.today()
  return


def constant_factory(value):
  from itertools import repeat
  return repeat(value).next

ALL_BILLS_DICT = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
ALL_PAYMENTS_DICT = GetAllCompaniesDict().GetAllPaymentsByAllCompaniesAsDict()
ALL_CUST_INFO = GetAllCustomersInfo()

def ParseOptions():
  parser = argparse.ArgumentParser()
  parser.add_argument("--allCompanies", dest='allCompanies', action="store_true",
      default=False, help="Send payment reminder to all eligible companies.")
  parser.add_argument("-c", "--comp", dest='comp', type=str, default=None,
      help="Company name or part of it.")
  parser.add_argument("-d", "--demo", dest='isDemo', action="store_true",
      default=False, help="If present, emails will only be sent to cc"
      " email and no mail will be sent to customer.")

  parser.add_argument("--sms", dest="sendsms", default=False, action="store_true",
      help="If present, an sms will be sent for payment")

  parser.add_argument("--mail", dest="sendmail", default=False, action="store_true",
      help="If present, a mail will be sent for payment")

  return parser.parse_args()

def SendRequiredEmailToGrp(grpName, args):
  compsInGrp = ALL_CUST_INFO.GetListOfCompNamesInThisGroup(grpName)
  import pprint
  PrintInBox("Preparing mails for following companies:")
  pprint.pprint(compsInGrp)

  toMailList, ccMailList, bccMailList = GetToCCBCCListforGroup(grpName)

  goAhead = True
  if 'y' != raw_input("Want to send\n(y/n): ").lower():
    goAhead = False

  if goAhead:
    print("Preparing mail for group M/s {}".format(grpName))
    emailSubject = "Kennametal Price Revision WED 1Dec2017"
    if args.isDemo:
      toMailList = GetOption("EMAIL_REMINDER_SECTION", "TestMailList").replace(';', ',').split(',')
      ccMailList = None
      bccMailList = None
      emailSubject = "[Testing{}]: {}".format(str(random.randint(1, 10000)), emailSubject)


  d = defaultdict(constant_factory(""))

  letterDate = datetime.date.today().strftime("%A, %d-%b-%Y") + "<br>"
  d['tLetterDate'] = letterDate
  d['tBodySubject'] = "Subject: " + PastelOrangeText(Bold(UnderLine("Price Revision Initimation From Kennametal India Limited(WIDIA)")))
  d['tSignature'] = GetOption("EMAIL_REMINDER_SECTION", "Signature")

  templateMailBody = Template("""
  <html>
      <head>
      </head>
      <body style=" font-family: Helvetica, Georgia, Verdana, Arial, 'sans-serif'; font-size: 1.1em; line-height: 1.5em;" >
      <p>
      $tLetterDate
      <br>
      $tBodySubject<br>
      <br>
      Dear Sir,<br>
      <br>
      This is to inform you that Kennmetal India Lmited has revised their prices WEF 1-Dec-2017. Please find attached the official confirmation regarding the same.
      <br>
      <br>
      Thanks.
      </p><br>

      <hr>
      $tSignature
      </body>
  </html>
  """)

  mailBody = templateMailBody.substitute(d)

  section = "EMAIL_REMINDER_SECTION"
  SendMail(emailSubject,
      "E:\GDrive\Appdir\SDATDocs\SDAT\KennametalAll\NewPriceListKennametal1-Dec-2017\Price Revision Communication Letter - 2017.pdf",
      GetOption(section, 'Server'),
      GetOption(section, 'Port'),
      GetOption(section, 'FromEmailAddress'),
      toMailList,
      ccMailList,
      bccMailList,
      GetOption(section, 'Mpass'),
      mailBody,
      textType="html",
      fromDisplayName=GetOption(section, "unpaidBillsName")
      )

  if not args.isDemo:
    print("Saving date...")
    SaveSentOnDateForThisGrp(grpName)

  if args.isDemo:
    PrintInBox("Not sending any email for group {}".format(grpName))
  return

def AskQuestionsFromUserAndSendMail(args):
  grpName = GuessCompanyGroupName(args.comp)

  if args.sendmail:
    SendRequiredEmailToGrp(grpName, args)

  if args.sendsms:
    #TODO: Take sms out of mail block and use same chosen company may be throgh singleton
    compsInGrp = ALL_CUST_INFO.GetListOfCompNamesInThisGroup(grpName)
    firstCompInGrp = compsInGrp[0]
    SendOfficialSMS(firstCompInGrp, """Dear Sir,
Kennametal has revised their prices. Your are requested to kindly check your email for further information.
Thanks""")
  return

def ShouldWeSendAutomaticEmailForGroup(grpName):
  def ShowReason(reason):
    show = False
    show = True
    if show:
      print("{:<55}| {}".format(grpName, reason))

  lastDate = EarlierSentOnPriceRevisionForThisGrp(grpName)
  if lastDate:
    #Perform this check only when an email was ever sent to this company and this is not a demo.
    timeDelta = datetime.date.today() - lastDate
    MIN_DAYS_GAP = 5
    daysSinceLastEmail = timeDelta.days
    if daysSinceLastEmail < MIN_DAYS_GAP:
      ShowReason("daysSinceLastEmail {} < {}".format(daysSinceLastEmail, MIN_DAYS_GAP))
      return False

  return True


def SendEmailToAllCompanies(args):
  PrintInBox("About to send email to all the companies")
  uniqueCompGrpNames = set([ALL_CUST_INFO.GetCompanyGroupName(eachComp) for eachComp in ALL_BILLS_DICT])
  for eachGrp in uniqueCompGrpNames:
    print("Working on {}".format(eachGrp))
    try:
      if ShouldWeSendAutomaticEmailForGroup(eachGrp):
        SendRequiredEmailToGrp(eachGrp, args)
    except Exception as ex:
      PrintInBox("Exception while processing: {}\n{}".format(eachGrp, str(ex)))
  return

def main():

  args = ParseOptions()

  if args.allCompanies:
    SendEmailToAllCompanies(args)
    return

  if args.sendmail or args.sendsms:
    AskQuestionsFromUserAndSendMail(args)


if __name__ == '__main__':
  try:
    custDBwbPath = os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "CustDBRelativePath"))
    CheckConsistency()
    main()
  except MyException as ex:
    PrintInBox(str(ex))
    raise ex
