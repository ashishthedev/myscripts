###############################################################################
## Author: Ashish Anand
## Date: 2012-09-04 Tue 03:19 PM
## Intent: To read WRKBK_PATH and send payments reminder emails to customers
##         The mail addresses are picked up from CUST_SHEETNAME in the
##         WRKBK_PATH excel file
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from Util.Config import GetOption, GetAppDir
from Util.Decorators import timeThisFunction
from Util.Exception import MyException
from Util.Misc import PrintInBox, AnyFundooProcessingMsg
from Util.Persistent import Persistent
from Util.PythonMail import SendMail

from whopaid.customers_info import GetAllCustomersInfo
from whopaid.customer_group_info import GetToCCBCCListforGroup, TotalDueForGroupAsInt, PrepareMailContentForThisGroup
from whopaid.off_comm import SendOfficialSMS, SendOfficialSMSToMD
from whopaid.sanity_checks import CheckConsistency
from whopaid.util_whopaid import GetAllCompaniesDict, SelectUnpaidBillsFrom, GuessCompanyGroupName


import argparse
import datetime
import random
import os

MINIMUM_AMOUNT_DUE = 2000
ALL_BILLS_DICT = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
ALL_PAYMENTS_DICT = GetAllCompaniesDict().GetAllPaymentsByAllCompaniesAsDict()
ALL_CUST_INFO = GetAllCustomersInfo()


def constant_factory(value):
    from itertools import repeat
    return repeat(value).next

class LastEmailSentOnPersistentDates(Persistent):
  def __init__(self):
    super(LastEmailSentOnPersistentDates, self).__init__(self.__class__.__name__)

def EarlierSentOnDateForThisGrp(grpName):
  """Returns a dateObject representing the date on which an email was last sent to this company"""
  p = LastEmailSentOnPersistentDates()
  if grpName in p:
    return p[grpName]
  return None

def SaveSentOnDateForThisGrp(grpName):
  """Registers today() as the date on which last email was sent to company."""
  p = LastEmailSentOnPersistentDates()
  p[grpName] = datetime.date.today()
  return

def ParseOptions():
  parser = argparse.ArgumentParser()
  parser.add_argument("--allCompanies", dest='allCompanies', action="store_true",
      default=False, help="Send payment reminder to all eligible companies.")
  parser.add_argument("-c", "--comp", dest='comp', type=str, default=None,
      help="Company name or part of it.")
  parser.add_argument("-d", "--demo", dest='isDemo', action="store_true",
      default=False, help="If present, emails will only be sent to cc"
      " email and no mail will be sent to customer.")
  parser.add_argument("-ka", "--kindAttentionPerson", dest='kaPerson',
      type=str, default=None, help="If present, a kind attention name"
      " will be placed toemails will be added to the request.")
  parser.add_argument("-fl", "--first-line", dest='first_line', type=str,
      default=None, help="If present, emails will be sent with this as "
      "first line.")
  parser.add_argument("-flb", "--first-line-bold", dest='first_line_bold', type=str,
      default=None, help="If present, emails will be sent with this as "
      "first line.")
  parser.add_argument("-sl", "--second-line", dest='second_line', type=str,
      default=None, help="If present, emails will be sent with this as "
      "second line.")
  parser.add_argument("-ll", "--last-line", dest='last_line', type=str,
      default=None, help="If present, emails will be sent with this as "
      "last line.")
  parser.add_argument("-llb", "--last-line-bold", dest='last_line_bold', type=str,
      default=None, help="If present, emails will be sent with this as "
      "last line.")

  parser.add_argument("--sms", dest="sendsms", default=False, action="store_true",
      help="If present, an sms will be sent for payment")

  parser.add_argument("--md", dest="sendsmstoMD", default=False, action="store_true",
      help="If present, an sms will be sent for payment to MDs")

  parser.add_argument("--mail", dest="sendmail", default=False, action="store_true",
      help="If present, a mail will be sent for payment")

  parser.add_argument("-ol", "--only-list-no-send", dest="onlyListNoSend",
      default=False, action="store_true", help="Only list names, do not "
      "send. To be used with automatic reminders")

  parser.add_argument("-ncd", "--no-credit-days", dest="doNotShowCreditDays", default=False,
      action="store_true", help="If present, credit days will not be shown against bills")

  return parser.parse_args()


def AskQuestionsFromUserAndSendMail(args):
  PrintInBox(AnyFundooProcessingMsg())

  grpName = GuessCompanyGroupName(args.comp)

  if not args.kaPerson:
    #If no person was specified at command line then pick one from the database.
    for eachComp in ALL_CUST_INFO.GetListOfCompNamesForThisGrp(grpName):
      personFromDB = ALL_CUST_INFO.GetCustomerKindAttentionPerson(eachComp)
      if personFromDB and 'y' == raw_input("Mention kind attn: {} (y/n)?".format(personFromDB)).lower():
        args.kaPerson = personFromDB
        break

  if args.sendmail:
    SendReminderToGrp(grpName, args)

  if args.sendsms:
    #TODO: Take sms out of mail block and use same chosen company may be throgh singleton
    compsInGrp = ALL_CUST_INFO.GetListOfCompNamesForThisGrp(grpName)
    firstCompInGrp = compsInGrp[0]
    totalDue = TotalDueForGroupAsInt(grpName)
    if args.sendsmstoMD:
      smsFunc = SendOfficialSMSToMD
    else:
      smsFunc = SendOfficialSMS
    smsFunc(firstCompInGrp, """Dear Sir,
You are requested to kindly release the payment. The total due amount is: Rs.{totalDue}. The details have been sent to your mail address.
Thanks""".format(totalDue=totalDue))
  return




def SendAutomaticReminderToAllCompanies(args):
  PrintInBox("About to send email to all the companies")
  uniqueCompGrpNames = set([ALL_CUST_INFO.GetCompanyGroupName(eachComp) for eachComp in ALL_BILLS_DICT])
  for eachGrp in uniqueCompGrpNames:
    print("Working on {}".format(eachGrp))
    try:
      if ShouldWeSendAutomaticEmailForGroup(eachGrp):
        SendReminderToGrp(eachGrp, args)
    except Exception as ex:
      PrintInBox("Exception while processing: {}\n{}".format(eachGrp, str(ex)))
  return

def OnlyListCompaniesOnScreen(args):
  uniqueCompGrpNames = set([ALL_CUST_INFO.GetCompanyGroupName(eachComp) for eachComp in ALL_BILLS_DICT])
  uniqueCompGrpNames = list(sorted(uniqueCompGrpNames))
  for eachGrp in uniqueCompGrpNames:
    if ShouldWeSendAutomaticEmailForGroup(eachGrp):
      print("We should send mail to {}".format(eachGrp))
  return


@timeThisFunction
def main():

  args = ParseOptions()

  if args.onlyListNoSend:
    OnlyListCompaniesOnScreen(args)
    return

  if args.allCompanies:
    SendAutomaticReminderToAllCompanies(args)
    return

  if args.sendmail or args.sendsms:
    AskQuestionsFromUserAndSendMail(args)

def ShouldWeSendAutomaticEmailForGroup(grpName):
  def ShowReason(reason):
    show = True
    show = False
    if show:
      print("{:<55}| {}".format(grpName, reason))

  compsInGrp = ALL_CUST_INFO.GetListOfCompNamesForThisGrp(grpName)
  firstCompInGrp = compsInGrp[0]
  unpaidBillsList = []
  paymentsList = []
  for compName in compsInGrp:
    if not compName in ALL_BILLS_DICT:
      #print("{compName} has no issued bills till date. Ignoring it.".format(compName=compName))
      continue
    unpaidBillsList += SelectUnpaidBillsFrom(ALL_BILLS_DICT[compName])

  for compName in compsInGrp:
    if not compName in ALL_PAYMENTS_DICT:
      continue
    paymentsList += [p for p in ALL_PAYMENTS_DICT[compName] if p.paymentAccountedFor]

  #Unpaid Bills check
  if not unpaidBillsList:
    ShowReason("No unpaid bills")
    return False # All bills are duly paid; do not send email

  #Advance towards us check
  if int(sum([eachBill.amount for eachBill in unpaidBillsList])) < MINIMUM_AMOUNT_DUE:
    ShowReason("Due amount is less than: {}".format(MINIMUM_AMOUNT_DUE))
    return False

  #Check if we dont want the customer to be included in automatic mails
  #if not ALL_CUST_INFO.IncludeCustInAutomaticMails(firstCompInGrp):
  #  return False

  #Email present
  if not ALL_CUST_INFO.GetPaymentReminderEmailAsListForCustomer(firstCompInGrp):
    ShowReason("No email present")
    return False

  #Dont send email immediately after receiving payment.
  if paymentsList:
    recentPmtDate = max([p.pmtDate for p in paymentsList])
    daysSinceLastPmt = (datetime.date.today()-recentPmtDate).days
    minDays = ALL_CUST_INFO.GetMinDaysGapBetweenMails(firstCompInGrp)
    if daysSinceLastPmt < minDays:
      ShowReason("daysSinceLastPmt={} < {}".format(daysSinceLastPmt, minDays))
      return False

  #Check any bill should have elapsed minimum days
  daysSinceOldestUnpaidBill = max([b.daysOfCredit for b in unpaidBillsList])
  allowedDaysOfCredit = int(ALL_CUST_INFO.GetCreditLimitForCustomer(firstCompInGrp))
  if daysSinceOldestUnpaidBill <= allowedDaysOfCredit:
    ShowReason("daysSinceOldestUnpaidBill={} <= {}".format(daysSinceOldestUnpaidBill, allowedDaysOfCredit))
    return False

  lastDate = EarlierSentOnDateForThisGrp(grpName)
  if lastDate:
    #Perform this check only when an email was ever sent to this company and this is not a demo.
    timeDelta = datetime.date.today() - lastDate
    minDaysGap = int(ALL_CUST_INFO.GetMinDaysGapBetweenMails(firstCompInGrp))
    daysSinceLastEmail = timeDelta.days
    if daysSinceLastEmail < minDaysGap:
      ShowReason("daysSinceLastEmail {} < {}".format(daysSinceOldestUnpaidBill, minDaysGap))
      return False

  return True




def SendReminderToGrp(grpName, args):
  compsInGrp = ALL_CUST_INFO.GetListOfCompNamesForThisGrp(grpName)
  import pprint
  PrintInBox("Preparing mails for following companies:")
  pprint.pprint(compsInGrp)
  firstCompInGrp = compsInGrp[0] #TODO: Remove usage of firstCompInGrp as this is a hack. We are working on groups now. To remove it all the functionality has to be ported from single company to a group of companies.
  unpaidBillsList = []
  for eachComp in compsInGrp:
    if eachComp in ALL_BILLS_DICT:
      unpaidBillsList += SelectUnpaidBillsFrom(ALL_BILLS_DICT[eachComp])

  if not len(unpaidBillsList):
    raise Exception("Alls bills are duly paid by group: {}".format(grpName))

  totalDue = TotalDueForGroupAsInt(grpName)

  if totalDue <= MINIMUM_AMOUNT_DUE:
    raise MyException("\nM/s {} has Rs.{} which is less than MINIMUM_AMOUNT_DUE".format(grpName, totalDue))

  toMailList, ccMailList, bccMailList = GetToCCBCCListforGroup(grpName)

  goAhead = True
  lastDate = EarlierSentOnDateForThisGrp(grpName)
  if lastDate and not args.isDemo:
    #Perform this check only when an email was ever sent to this company and this is not a demo.
    timeDelta = datetime.date.today() - lastDate
    firstCompInGrp = compsInGrp[0]#TODO: Hack
    minDaysGap = int(ALL_CUST_INFO.GetMinDaysGapBetweenMails(firstCompInGrp))#TODO: Hack
    if timeDelta.days < minDaysGap:
      if 'y' != raw_input("Earlier mail was sent {} days back. Do you still want to send the email?\n(y/n):".format(timeDelta.days)).lower():
        goAhead = False

  daysSinceOldestUnpaidBill = max([b.daysOfCredit for b in unpaidBillsList])
  allowedDaysOfCredit = int(ALL_CUST_INFO.GetCreditLimitForCustomer(firstCompInGrp))

  if daysSinceOldestUnpaidBill < allowedDaysOfCredit:
    if 'y' != raw_input("All bills are within allowed range. Do you still want to send email?\n(y/n): ").lower():
      goAhead = False

  if goAhead:
    print("Preparing mail for group M/s {}".format(grpName))
    emailSubject = "Payment Request (Rs.{})".format(totalDue)
    if args.isDemo:
      toMailList = GetOption("EMAIL_REMINDER_SECTION", "TestMailList").replace(';', ',').split(',')
      ccMailList = None
      bccMailList = None
      emailSubject = "[Testing{}]: {}".format(str(random.randint(1, 10000)), emailSubject)

    mailBody = PrepareMailContentForThisGroup(grpName, args)
    section = "EMAIL_REMINDER_SECTION"
    SendMail(emailSubject,
        None,
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
  else:
    PrintInBox("Not sending any email for group {}".format(grpName))
  return



if __name__ == '__main__':
  try:
    custDBwbPath = os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "CustDBRelativePath"))
    CheckConsistency()
    main()
  except MyException as ex:
    PrintInBox(str(ex))
    raise ex
