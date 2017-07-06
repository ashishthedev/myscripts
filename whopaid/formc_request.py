###############################################################################
## Author: Ashish Anand
## Date: 2012-09-11 Tue 06:16 PM
## Intent: To read database and generate FORM-C Reminders with proper quarters
##         The mail addresses are picked up from CUST_SHEETNAME in the
##         WRKBK_PATH excel file
## Requirement: Python Interpretor must be installed
##              Openpyxl for Python must be installed
###############################################################################

from Util.Config import GetOption
from Util.Decorators import timeThisFunction
from Util.Exception import MyException
from Util.Misc import PrintInBox, OpenFileForViewing, MakeSureDirExists, DD_MMM_YYYY
from Util.PythonMail import SendMail

from whopaid.customers_info import GetAllCustomersInfo, GetToCCBCCForFORMCforCompany
from whopaid.sanity_checks import CheckConsistency
from whopaid.util_whopaid import GuessCompanyName, GetAllCompaniesDict
from whopaid.util_formc import GetHTMLForFORMCforCompany


import argparse
import datetime
import os

DEST_FOLDER = "e:\\FCR"
ALL_CUST_INFO = GetAllCustomersInfo()
ALL_BILLS_DICT = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()

def ParseArguments():
    p = argparse.ArgumentParser()

    p.add_argument("-c", "--comp", dest='comp', type=str, default=None,
            help="Company name or part of it.")

    p.add_argument("-ka", "--kind-attention", dest='kindAttentionPerson',
            type=str, default=None, help="Name of any specific person."
            "Can be left out")

    p.add_argument("-al", "--additional-line", dest='additional_line',
            type=str, default=None, help="Any additional line that should be"
            "supplied.")

    p.add_argument("-o", "--OpenFileForViewing", dest='open',
            action="store_true", default=False, help="If present, file will"
            " be opened")

    p.add_argument("-l", "--letterHead", dest='letterHead', action="store_true",
            default=False, help="If present, margin will be left on top for"
            " the letterhead.")

    p.add_argument("-s", "--sms", dest='sendSMS', action="store_true",
            default=False, help="If present email will be sent to company else"
            " a file will be saved to desktop.")

    p.add_argument("-tlq", "--till-last-quarter", dest='tillLastQuarter', action="store_true",
            default=False, help="If present email will be sent for bill upto last quarter")

    p.add_argument("-all", "--all-companies", dest='allCompanies', action="store_true",
            default=False, help="If present email will be sent to all companes")

    p.add_argument("-e", "--email", dest='sendEmail', action="store_true",
            default=False, help="If present email will be sent to company else"
            " a file will be saved to desktop.")

    p.add_argument("-rem", "--remarks-column", dest='remarksColumn',
            action="store_true", default=False, help="If present, an additional"
            "column for remarks will be added")

    p.add_argument("-d", "--demo", "--desktopOnly", "--noEmail", dest='isDemo',
            action="store_true", default=False, help="If present, no email"
            "will be sent. This option will override email option.")

    p.add_argument("-sd", "--start-date", dest='sdate', metavar="Start-date",
            required=False, default=None, type=str,
            help="Starting Date for FORM-C requests.")

    p.add_argument("-ed", "--end-date", dest='edate', metavar="End-date",
            required=False, type=str, default=str(datetime.date.today()),
            help="End Date for Form-C Requests. If ommitted Form-C till date "
            "will be asked for")
    p.add_argument("-start", "--start-from", dest="startFromNumber", type=int, 
        default = 0, help="If you want to start execution after a number,"
        " give that number here. THat number will be included.")

    p.add_argument("-endAt", "--end-at", dest="endAtNumber", type=int, 
        default = None, help="If you want to start execution after a number,"
        " give that number here. THat number will be included.")

    args = p.parse_args()
    return args


def SendFormcRequestToAllCompanies(args):
  print("Will send mail to all companies")

  allBills = list()
  for c, billList in ALL_BILLS_DICT.iteritems():
      allBills.extend(billList)

  allBills = [b for b in allBills if b.billingCategory.lower() in ["central"] and not b.formCReceivingDate]
  uniqueCompNames = set(b.compName for b in allBills)
  for i, uniqueComp in enumerate(uniqueCompNames):
    if uniqueComp.lower() == "test":
      continue
    if i < args.startFromNumber:
      print("{} Not sending as per instructions startFromNumber={} Comp:{}".format(i, args.startFromNumber, uniqueComp))
      continue
    if args.endAtNumber and i > args.endAtNumber:
      print("{} Not sending as per instructions endAtNumber={} Comp:{}".format(i, args.endAtNumber, uniqueComp))
      continue
    print i, "Sending mail and SMS to {}".format(uniqueComp)
    SendFORMCMailToCompany(uniqueComp, args, specialContentRegardingNotice=True)
    SendFORMCSMSToCompany(uniqueComp, args, specialContentRegardingNotice=True)

    #if args.isDemo and i >= 1: return #Just do the demo on 2 comps show 2 companies

def GetLastDateOfPreviousQuarterAsDateObj():
  today = datetime.date.today()
  month = today.month
  year = today.year

  if month < 4:
    year -= 1

  d = {
      "1": "12",
      "2": "12",
      "3": "12",
      "4": "2",
      "5": "2",
      "6": "2",
      "7": "3",
      "8": "4",
      "9": "4",
      "10": "4",
      "11": "4",
      "12": "4",
      }

  month = int(d[str(month)])
  import calendar
  _, noOfDays = calendar.monthrange(year, month)
  lastDate = datetime.date(year, month, noOfDays)
  return lastDate

@timeThisFunction
def main():
    args = ParseArguments()
    print("Churning data...")

    if args.tillLastQuarter:
      args.edate = GetLastDateOfPreviousQuarterAsDateObj()
      print("End Date is now automatically set to: {}".format(args.edate))

    if args.allCompanies:
      #args.isDemo = True
      raw_input("About to send FORM-C request to all companies for bills upto. Press Ctrl-C to quit")
      SendFormcRequestToAllCompanies(args)
      return

    chosenComp = GuessCompanyName(args.comp)
    SendFORMCMailToCompany(chosenComp, args)
    SendFORMCSMSToCompany(chosenComp, args)
    CheckConsistency()


def ShouldSendEmail(args):
  return False if args.isDemo else args.sendEmail

def ShouldSendSMS(args):
  return False if args.isDemo else args.sendSMS


def SendFORMCSMSToCompany(compName, args, specialContentRegardingNotice=False):

  if not ALL_CUST_INFO.CanSendSMS(compName):
    PrintInBox("No SMS number available for {}".format(compName), waitForEnterKey=True)
    return

  if not ShouldSendSMS(args):
    PrintInBox("Not sending SMS to company")
    return

  from whopaid.off_comm import SendOfficialSMSAndMarkCC
  if specialContentRegardingNotice:
    content = """Dear Sir,
We have received a Sales Tax Notice for immediate submission of FORM-C upto {}. You are requested to kindly provide the same. The details have been sent to your usual email address.
Thanks.
""".format(DD_MMM_YYYY(GetLastDateOfPreviousQuarterAsDateObj()))
  else:
    content = """Dear Sir,
Kindly issue the FORM-C. The details have been sent to your email address.
Thanks.
"""
  SendOfficialSMSAndMarkCC(compName, content)
  return



def SendFORMCMailToCompany(compName, args, specialContentRegardingNotice=False):
  print(GetToCCBCCForFORMCforCompany(compName))
  if not ALL_CUST_INFO.CanSendEmail(compName):
    PrintInBox("No email available for {}".format(compName), waitForEnterKey=True)
    return

  companyOfficialName = GetAllCustomersInfo().GetCompanyOfficialName(compName)
  if not companyOfficialName:
    raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

  if ShouldSendEmail(args):
    mailBody = GetHTMLForFORMCforCompany(compName, args, specialContentRegardingNotice=specialContentRegardingNotice)
    print("Sending mail...")

    toMailList, ccMailList, bccMailList = GetToCCBCCForFORMCforCompany(compName)
    print("Sending to: " + str(toMailList))

    section = "EMAIL_REMINDER_SECTION"
    requestingCompanyName = GetOption("CONFIG_SECTION", 'CompName')
    formName = GetAllCustomersInfo().GetFormName(compName)
    emailSubject = "{} request - M/s {} - from M/s {}".format(formName, companyOfficialName, requestingCompanyName)
    if specialContentRegardingNotice:
      emailSubject = "URGENT: " + emailSubject

    zfilename = None

    if specialContentRegardingNotice:
      noticePath = os.path.normpath(GetOption("CONFIG_SECTION", "SaleTaxNoticePath"))
      if not os.path.exists(noticePath):
        raise Exception("{} is not present".format(noticePath))
      zfilename = noticePath

    SendMail(emailSubject=emailSubject,
        zfilename=zfilename,
        SMTP_SERVER=GetOption(section, 'Server'),
        SMTP_PORT=GetOption(section, 'Port'),
        FROM_EMAIL=GetOption(section, 'FromEmailAddress'),
        TO_EMAIL_LIST=toMailList,
        CC_EMAIL_LIST=ccMailList,
        BCC_EMAIL_LIST=bccMailList,
        MPASS=GetOption(section, 'Mpass'),
        BODYTEXT=mailBody,
        textType="html",
        fromDisplayName = GetOption(section, "formCRequest")
        )
  else:
    fileHTMLContent = GetHTMLForFORMCforCompany(compName, args, specialContentRegardingNotice=specialContentRegardingNotice)
    #Save to an html file
    MakeSureDirExists(DEST_FOLDER)
    filePath = os.path.join(DEST_FOLDER, companyOfficialName) + ".html"
    print("Saving FORM-C to local file: " + filePath)

    with open(filePath, "w") as f:
      f.write(fileHTMLContent)

    if args.open:
      OpenFileForViewing(filePath)
  return


if __name__ == '__main__':
    try:
        main()
    except MyException as ex:
        PrintInBox(str(ex))
