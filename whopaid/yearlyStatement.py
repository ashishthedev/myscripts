###############################################################################
## Author: Ashish Anand
## Date: 2012-09-11 Tue 06:16 PM
## Intent: To read database and generate yearly statements
## Requirement: Python Interpretor must be installed
##              Openpyxl for Python must be installed
###############################################################################

from Util.Config import GetOption
from Util.Colors import MyColors
from Util.HTML import UnderLine, Bold, PastelOrangeText, TableHeaderRow, TableDataRow
from Util.Decorators import timeThisFunction
from Util.Exception import MyException
from Util.Misc import ParseDateFromString, PrintInBox, OpenFileForViewing, MakeSureDirExists, DD_MMM_YYYY
from Util.PythonMail import SendMail

from whopaid.customers_info import GetAllCustomersInfo
from whopaid.sanity_checks import CheckConsistency
from whopaid.util_whopaid import GetAllCompaniesDict, SelectBillsAfterDate,\
        SelectBillsBeforeDate, GuessCompanyName, RemoveTrackingBills, RemoveGRBills


from string import Template
import argparse
import datetime
import os

DEST_FOLDER = "B:\\Desktop\\Statements"

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
            action="store_true", default=True, help="If present, file will"
            " be opened")

    p.add_argument("-l", "--letterHead", dest='letterHead', action="store_true",
            default=False, help="If present, margin will be left on top for"
            " the letterhead.")

    p.add_argument("-s", "--sms", dest='sendSMS', action="store_true",
            default=False, help="If present email will be sent to company else"
            " a file will be saved to desktop.")

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
            required=True, default=None, type=str,
            help="Starting Date for yearly statement requests.")

    args = p.parse_args()
    return args


@timeThisFunction
def main():
  args = ParseArguments()
  print("Churning data...")

  chosenComp = GuessCompanyName(args.comp)
  SendYearlyStatementMailToCompany(chosenComp, args)
  SendYearlyStatementSMSToCompany(chosenComp, args)


def ShouldSendEmail(args):
  PrintInBox("Remove this"); return False
  return False if args.isDemo else args.sendEmail

def ShouldSendSMS(args):
  return False if args.isDemo else args.sendSMS



def SendYearlyStatementSMSToCompany(compName, args):
  if not ShouldSendSMS(args):
    PrintInBox("Not sending SMS to company")
    return

  from whopaid.off_comm import SendOfficialSMSAndMarkCC
  SendOfficialSMSAndMarkCC(compName, """Dear Sir,
This is to inform you that the accounts statement has been emailed to your account just now. Please verify and let us know if you have any queries.
Thanks.
""")
  return


def SendYearlyStatementMailToCompany(compName, args):
  sdate = ParseDateFromString(args.sdate)
  if sdate.day != 1 or sdate.month != 4:
    raise MyException("Starting date should of format 1AprYYYY. Currently it is {}".format(sdate))

  sdateObject = ParseDateFromString(sdate)  # Start Date Object
  edateObject = sdateObject + datetime.timedelta(days=365)
  edateObject = datetime.date(sdateObject.year+1, 3, 31)

  companyOfficialName = GetAllCustomersInfo().GetCompanyOfficialName(compName)

  if ShouldSendEmail(args):
    mailBody = GenerateYearlyStatementMailContent(args, compName, sdateObject, edateObject)
    print("Sending mail...")
    #First prefrence to FormCEmails. If not present use payment emails.
    toMailList = GetAllCustomersInfo().GetFormCEmailAsListForCustomer(compName) or GetAllCustomersInfo().GetPaymentReminderEmailAsListForCustomer(compName)
    if not toMailList:
      raise  Exception("\nNo mail feeded. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'")

    print("Sending to: " + str(toMailList))


    section = "EMAIL_REMINDER_SECTION"
    requestingCompanyName = GetOption("CONFIG_SECTION", 'CompName')
    emailSubject = "Statement from {} to {} - M/s {} - from M/s {}".format(DD_MMM_YYYY(sdateObject), DD_MMM_YYYY(edateObject), companyOfficialName, requestingCompanyName)
    SendMail(emailSubject=emailSubject,
        zfilename=None,
        SMTP_SERVER=GetOption(section, 'Server'),
        SMTP_PORT=GetOption(section, 'Port'),
        FROM_EMAIL=GetOption(section, 'FromEmailAddress'),
        TO_EMAIL_LIST=toMailList,
        CC_EMAIL_LIST=GetOption(section, 'CCEmailList').split(','),
        BCC_EMAIL_LIST=GetOption(section, 'BCCEmailList').split(','),
        MPASS=GetOption(section, 'Mpass'),
        BODYTEXT=mailBody,
        textType="html",
        fromDisplayName = GetOption(section, "formCRequest")
        )
  else:
    mailBody = GenerateYearlyStatementMailContent(args, compName, sdateObject, edateObject)
    #Save to an html file

    MakeSureDirExists(DEST_FOLDER)
    smallName = GetOption("CONFIG_SECTION", "SuperSmallName")
    if not smallName:
      raise Exception("Small name not present for company")
    filePath = os.path.join(DEST_FOLDER, companyOfficialName + "-Stmt-" + DD_MMM_YYYY(sdateObject)) + "-" + smallName + ".html"
    print("Saving statement of a/c to local file: " + filePath)

    with open(filePath, "w") as f:
      f.write(mailBody)

    if args.open: OpenFileForViewing(filePath)
  return

def GenerateYearlyStatementMailContent(args, compName, sdateObject, edateObject):
  letterDate = datetime.date.today().strftime("%A, %d-%b-%Y")

  companyCity = GetAllCustomersInfo().GetCustomerCity(compName)
  if not companyCity:
    raise MyException("\nM/s {} doesnt have a displayable 'city'. Please feed it in the database".format(compName))

  d = dict()
  if args.letterHead:
      d['topMargin'] = "8.0cm"
  else:
      d['topMargin'] = "0cm"

  if args.kindAttentionPerson:
      d['tOptPerson'] = UnderLine(Bold("<br>Kind attention: " + args.kindAttentionPerson + "<br>"))
  else:
      d['tOptPerson'] = ""

  if args.additional_line:
      d['tOptAdditionalLine'] = args.additional_line + "<br><br>" #<br><br> will add a new line.
  else:
      d['tOptAdditionalLine'] = ""

  companyOfficialName = GetAllCustomersInfo().GetCompanyOfficialName(compName)
  d['tTable'] = GetHTMLStatementTable(compName, sdateObject, edateObject)
  d['tLetterDate'] = letterDate
  d['tCompanyName'] = Bold("M/s " + companyOfficialName)
  d['tCompanyCity'] = companyCity
  d['tSignature'] = GetOption("ACCOUNTS_SECTION", "Signature")
  requestingCompanyTinNo = GetOption("CONFIG_SECTION", "TinNo")
  d['tBodySubject'] = PastelOrangeText(Bold(UnderLine("Subject: Statement of accounts from {} to {}".format(DD_MMM_YYYY(sdateObject), DD_MMM_YYYY(edateObject), requestingCompanyTinNo))))

  htmlTemplate = Template(
      """
      <HTML>
      <HEAD>
      <style type="text/css">
          BODY
          {
              margin-top: $topMargin
          }
      </style>
      </HEAD>
      <BODY>
      $tLetterDate<br>
      <br>
      To,<br>
      $tCompanyName,<br>
      $tCompanyCity.<br>
      <br>
      $tBodySubject<br>
      $tOptPerson
      <br>
      Dear Sir,<br>
      <br>

      $tOptAdditionalLine

      Please find below for your kind reference the statement of accounts for aforementioned period.
      <br>
      <br>
      <br>
      $tTable
      <br>
      <br>
      Please let us know if you have any queries.<br>
      <br>
      Thanks.
      <hr>
      $tSignature
      </BODY>
      </HTML>
      """)
  html = htmlTemplate.substitute(d)

  return html

def GetHTMLStatementTable(compName, sdateObject, edateObject):
  #1. Fetch opening Balance
  allCompaniesDict = GetAllCompaniesDict()
  openingBalanceList = allCompaniesDict.GetOpeningBalanceListForCompany(compName)
  if not openingBalanceList:
    raise MyException("\nM/s {} has no opening balance".format(compName))

  obe = None
  for x in openingBalanceList:
    if x.openingBalanceDate == sdateObject:
      obe = x
      obe.interestingDate = obe.openingBalanceDate
      obe.particulars = "Opening Balance"
      obe.interestingAmount = int(x.amount)
      if obe.interestingAmount > 0:
        obe.creditAmount = ""
        obe.debitAmount = "&#8377; {}".format(obe.interestingAmount)
        print(obe.interestingAmount)
      else:
        obe.creditAmount = "&#8377; {}".format(-1*obe.interestingAmount)
        obe.debitAmount = ""
        print(obe.interestingAmount)

  if obe == None:
    raise MyException("\nM/s {} has no opening balance for {}".format(compName, DD_MMM_YYYY(sdateObject)))

  #2. Find Bills List
  billList = allCompaniesDict.GetBillsListForThisCompany(compName)
  if not billList:
    raise MyException("\nM/s {} has no bills".format(compName))

  billList = SelectBillsAfterDate(billList, sdateObject)
  billList = SelectBillsBeforeDate(billList, edateObject)
  billList = RemoveTrackingBills(billList)
  billList = RemoveGRBills(billList)

  for b in billList:
    b.interestingDate = b.invoiceDate
    b.particulars = "Invoice# {}".format(str(int(b.billNumber)))
    b.interestingAmount = int(b.amount)
    b.debitAmount = "&#8377; {}".format(b.interestingAmount)
    b.creditAmount = ""
    print(obe.interestingAmount)

  #3. Find Payments list
  paymentList = allCompaniesDict.GetPaymentsListForThisCompany(compName)
  paymentList = [p for p in paymentList if p.pmtDate >= sdateObject]
  paymentList = [p for p in paymentList if p.pmtDate <= edateObject]

  for p in paymentList:
    p.interestingDate = p.pmtDate
    p.particulars = "Ch# {}".format(p.chequeNumber)
    p.interestingAmount = int(-1 * p.amount)
    p.creditAmount = "&#8377; {}".format(int(p.amount))
    p.debitAmount = ""
    print(obe.interestingAmount)

  if not billList and not paymentList:
    raise MyException("\nM/s {} has neither bill nor payment in said period".format(compName))

  #4. Mash them up in a table.
  allCustInfo = GetAllCustomersInfo()
  companyOfficialName = allCustInfo.GetCompanyOfficialName(compName)
  if not companyOfficialName:
    raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

  totalList = []
  totalList.append(obe)
  totalList.extend(billList)
  totalList.extend(paymentList)

  totalList = sorted(totalList, key=lambda x:x.interestingDate)

  tableRows = TableHeaderRow(
      MyColors["BLACK"],
      MyColors["SOLARIZED_GREY"],
     "Date", "Particulars", "Debit", "Credit")

  for x in totalList:
    tableRows += TableDataRow(
      MyColors["BLACK"],
      MyColors["WHITE"],
        DD_MMM_YYYY(x.interestingDate), x.particulars, x.debitAmount, x.creditAmount)

  closingBalance = 0
  for x in totalList:
    closingBalance += x.interestingAmount
    print(x.interestingAmount)
  tableRows += "<tr><td colspan='3'>Closing Balance</td><b><td>&#8377; {}</td></b>".format(closingBalance)

  PrintInBox("Add caption")
  return """
<TABLE border="1" cellpadding=5>
{}
</TABLE>
  """.format(tableRows)


if __name__ == '__main__':
  CheckConsistency()
  try:
    main()
  except MyException as ex:
    PrintInBox(str(ex))
