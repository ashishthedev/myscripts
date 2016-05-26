#######################################################
## Author: Ashish Anand
## Date: 2015-Jul-03 Fri 12:40 PM
## Intent: To read bills.xlsx and store company info
## Requirement: Python Interpretor must be installed
## Openpyxl must be installed
#######################################################
from Util.Exception import MyException
from Util.Config import GetOption
from Util.Colors import MyColors
from Util.HTML import UnderLine, Bold, Big, PastelOrangeText, TableHeaderRow, TableDataRow
from Util.Misc import DD_MM_YYYY

from itertools import repeat
from whopaid.util_whopaid import GetAllCompaniesDict, SelectUnpaidBillsFrom, RemoveTrackingBills, GetPayableBillsAndAdjustmentsForThisComp
from collections import defaultdict
from string import Template
import datetime

def constant_factory(value):
  return repeat(value).next


from whopaid.customers_info import GetAllCustomersInfo
ALL_CUST_INFO = GetAllCustomersInfo()
ALL_BILLS_DICT = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()

def HasFormCReminderEmailsForCompany(compName):
    return ALL_CUST_INFO.GetFormCEmailAsListForCustomer(compName) != None

def HasPaymentReminderEmailsForCompany(compName):
    return ALL_CUST_INFO.GetPaymentReminderEmailAsListForCustomer(compName) != None

def HasPaymentReminderEmailsForGroup(grpName):
  for eachComp in ALL_CUST_INFO.GetListOfCompNamesInThisGroup(grpName):
    if HasPaymentReminderEmailsForCompany(eachComp):
      #IF any company has email it means group has email.
      return True
  return False

def GetToCCBCCListforGroup(grpName):
  toMailList = []
  for eachComp in ALL_CUST_INFO.GetListOfCompNamesInThisGroup(grpName):
    if HasPaymentReminderEmailsForCompany(eachComp):
      toMailList += ALL_CUST_INFO.GetPaymentReminderEmailAsListForCustomer(eachComp)

  toMailList = list(set(toMailList)) # Remove duplicates
  if not toMailList:
    raise MyException("\nNo mail feeded. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'")

  ccMailList = GetOption("EMAIL_REMINDER_SECTION", 'CCEmailList').replace(';', ',').split(','),
  bccMailList = GetOption("EMAIL_REMINDER_SECTION", 'BCCEmailList').replace(';', ',').split(','),

  return toMailList, ccMailList, bccMailList

def TotalDueForCompAsInt(compName):
  billsList = GetAllCompaniesDict().GetBillsListForThisCompany(compName)
  billsList = RemoveTrackingBills(billsList)
  dba = sum([b.amount for b in SelectUnpaidBillsFrom(billsList)])

  unaccountedAdjustmentsList = GetAllCompaniesDict().GetUnAccountedAdjustmentsListForCompany(compName)
  daa = sum([a.amount for a in unaccountedAdjustmentsList])

  totalDue = int(dba + daa)

  adjustmentAmount = 0
  billsAmount = 0

  if billsList:
    billsList = SelectUnpaidBillsFrom(billsList)
    billsAmount = sum([b.amount for b in billsList])

  if unaccountedAdjustmentsList:
    adjustmentAmount = sum([int(a.amount) for a in unaccountedAdjustmentsList])
  totalDue2 = int(billsAmount) + int(adjustmentAmount)

  assert totalDue2 == totalDue

  return int(billsAmount) + int(adjustmentAmount)

def TotalDueForGroupAsInt(grpName):
  return sum(TotalDueForCompAsInt(eachComp) for eachComp in ALL_CUST_INFO.GetListOfCompNamesInThisGroup(grpName))


def PrepareMailContentForThisGroup(grpName, args):
  """Given a bill list for a company group, this function will
  prepare mail for the payment reminder."""

  totalDue = TotalDueForGroupAsInt(grpName)

  htmlTables = GetHTMLTableBlockForThisGrp(grpName, doNotShowCreditDays=args.doNotShowCreditDays)

  d = defaultdict(constant_factory(""))

  if not args.doNotShowLetterDate:
    letterDate = datetime.date.today().strftime("%A, %d-%b-%Y") + "<br>"
    d['tLetterDate'] = letterDate


  if args.first_line:
    d['tFirstLine'] = args.first_line + '<br><br>'

  if args.first_line_bold:
    d['tFirstLine'] = Bold(args.first_line_bold) + '<br><br>'

  if args.second_line:
    d['tSecondLine'] = args.second_line + '<br><br>'

  if args.last_line:
    d['tLastLine'] = args.last_line + '<br><br>'

  if args.last_line_bold:
    d['tLastLine'] = Bold(args.last_line_bold) + '<br><br>'

  if args.kaPerson:
    d['tPerson'] = Bold("Kind Attention: " + args.kaPerson + '<br><br>')

  d['tTotalDue'] = totalDue
  d['tTables'] = htmlTables
  d['tBodySubject'] = PastelOrangeText(Bold(UnderLine("Subject: Payment Request (Rs.{})".format(totalDue))))
  d['tSignature'] = GetOption("EMAIL_REMINDER_SECTION", "Signature")
  d['tBankerDetails'] = GetOption("EMAIL_REMINDER_SECTION", "BankerDetails")

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
      $tPerson
      Dear Sir,<br>
      <br>
      $tFirstLine
      $tSecondLine
      Please find below the list of pending invoices for the supplies made till date. You are requested to kindly arrange the payment for due bills:
      <br>
      $tTables
      </p>
      <br>
      $tLastLine
      <U>Banker details are as under:</U><br>

      <p style="background-color:#F0F0F0;">
      $tBankerDetails
      </p><br>

      <hr>
      $tSignature
      </body>
  </html>
  """)

  finalMailBody = templateMailBody.substitute(d)

  return finalMailBody

def MakeBillRow(*billRowArgs):
  return TableDataRow(
      MyColors["BLACK"],
      MyColors["WHITE"],
      *billRowArgs)

def GetHTMLTableBlockForThisGrp(grpName, doNotShowCreditDays=False):
  htmlTables = ""
  compsInGrp = ALL_CUST_INFO.GetListOfCompNamesInThisGroup(grpName)
  for eachCompName in compsInGrp:
    if not eachCompName in ALL_BILLS_DICT: continue
    if not SelectUnpaidBillsFrom(ALL_BILLS_DICT[eachCompName]): continue
    htmlTables += "<br>" + _GetHTMLTableBlockForThisComp(eachCompName, doNotShowCreditDays=doNotShowCreditDays)
  return htmlTables

def _GetHTMLTableBlockForThisComp(compName, doNotShowCreditDays=False):
  unpaidBillsList, adjustmentList = GetPayableBillsAndAdjustmentsForThisComp(compName)

  companyOfficialName = ALL_CUST_INFO.GetCompanyOfficialName(compName)
  if not companyOfficialName:
    raise MyException("\nM/s {} doesnt have a displayable 'name'."
        " Please feed it in the database".format(compName))

  companyCity = ALL_CUST_INFO.GetCustomerCity(compName)
  if not companyCity:
    raise MyException("\nM/s {} doesnt have a displayable 'city'."
        " Please feed it in the database".format(compName))

  allowedDaysOfCredit = int(ALL_CUST_INFO.GetCreditLimitForCustomer(compName))

  if not unpaidBillsList:

    raise MyException("There is no unpaid bill list for {}. This function should not be called on empty lists"
        " for it has to generate the mail content.".format(compName))

  for eachBill in unpaidBillsList:
    assert eachBill.isUnpaid is True,\
        "This function should only be called on unpaid bills of a single\
        company."

  totalDueLiterally = int(sum([eachBill.amount for eachBill in unpaidBillsList]))

  includeCreditDays = not doNotShowCreditDays
  if includeCreditDays:
    #Having this inside if block gives prefrence to command line argument.
    includeCreditDays = str(ALL_CUST_INFO.GetIncludeDaysOrNot(compName)).lower()=="yes"
  tableHeadersArgs = ["Bill#", "Invoice Date", "Amount"]
  if includeCreditDays:
    tableHeadersArgs.append("Days of credit")

  tableRows = TableHeaderRow(
      MyColors["GOOGLE_NEW_INBOX_FOREGROUND"],
      MyColors["GOOGLE_NEW_INBOX_BASE"],
      *tableHeadersArgs)

  for b in unpaidBillsList:
    billRowArgs=[int(b.billNumber),
        DD_MM_YYYY(b.invoiceDate),
        Bold("Rs." + str(int(b.amount)))]

    #Add a row to table for each unpaid bill
    if includeCreditDays:
      if b.daysOfCredit > allowedDaysOfCredit:
        billRowArgs.append(PastelOrangeText(Bold(str(b.daysOfCredit) + " days")))
      else:
        billRowArgs.append(str(b.daysOfCredit) + " days")

    tableRows += MakeBillRow(*billRowArgs)

  for a in adjustmentList:
    adjRowArgs=[int(a.billNumber),
        DD_MM_YYYY(a.invoiceDate),
        Bold("Rs." + str(int(a.amount)))]

    totalDueLiterally += int(a.amount)

    if includeCreditDays:
      adjRowArgs.append(" ")
    tableRows += MakeBillRow(*adjRowArgs)

  totalDue = TotalDueForCompAsInt(compName)
  if totalDueLiterally != totalDue:
    raise Exception ("For {} totalDueLiterally:{} != totalDue:{}, these should be equal".format(compName, totalDueLiterally, totalDue))
  tableFinalRowArgs = [Bold("Total"), "", PastelOrangeText(Big(Bold("Rs." + str(totalDue))))]

  if includeCreditDays:
    tableFinalRowArgs.append(" ")

  tableRows += MakeBillRow(*tableFinalRowArgs)

  caption = "M/s {}, {}<br>{}<br>as on {}".format(
      companyOfficialName,
      companyCity,
      Bold("Rs.{}".format(str(totalDue))),
      DD_MM_YYYY(datetime.date.today()))

  d = defaultdict(constant_factory(""))
  d['tTableRows'] = tableRows
  d['tCaption'] = caption
  tableTemplate = Template("""<table border=1 cellpadding=5>
  <caption>
  $tCaption
  </caption>
  $tTableRows
  </table>""")
  htmlTable = tableTemplate.substitute(d)
  return htmlTable

