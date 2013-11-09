###############################################################################
## Author: Ashish Anand
## Date: 2012-09-04 Tue 03:19 PM
## Intent: To ask for road permit from a paritcular company when the bill is
##         ready
##         The mail addresses are picked up from CUST_SHEETNAME in the
##         WRKBK_PATH excel file
## Requirement: Python Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from UtilWhoPaid import GetAllCompaniesDict, GuessCompanyName, \
        RemoveMinusOneBills, SelectBillsAfterDate, GetAllBillsInLastNDays
from UtilHTML import UnderLine, Bold, PastelOrangeText
from UtilPythonMail import SendMail
from UtilException import MyException
from UtilMisc import PrintInBox, DD_MM_YYYY
from CustomersInfo import GetAllCustomersInfo
from UtilConfig import GetOption
from SanityChecks import CheckConsistency

import datetime
from string import Template
import argparse
import random

def ParseOptions():
    #TODO Add an option to send email directly from command line without
    # referring to the database
    p = argparse.ArgumentParser(description="Send dispatch details to a"
            " company")

    p.add_argument("-l", "--last", dest='lastFewDays', type=int, default=5,
            help="No of days to look back from today.")

    p.add_argument("-c", "--comp", dest='comp', type=str, default=None,
            help="Company name or part of it.")

    p.add_argument("--demo", dest='isDemo', action="store_true",
            default=False, help="If present, emails will only be sent to "
            "test mail ids only.")

    p.add_argument("-ka", "--kindAttentionPerson", dest='kaPerson',
            type=str, default=None, help="If present, a kind attention name "
            "will be placed toemails will be added to the request.")

    p.add_argument("-fl", "--first-line", dest='first_line', type=str,
            default=None, help="If present, emails will be sent with this as "
            "first line.")

    p.add_argument("-sl", "--second-line", dest='second_line', type=str,
            default=None, help="If present, emails will be sent with this as "
            "second line.")

    p.add_argument("-ll", "--last-line", dest='last_line', type=str,
            default=None, help="If present, emails will be sent with this as "
            "last line.")

    args = p.parse_args()
    return args

from contextlib import closing
DISPATCH_MAIL_DB_NAME = GetOption("CONFIG_SECTION", "DispatchMailsDBName")
DISPATCH_INFO_PATH = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), DISPATCH_MAIL_DB_NAME)
def _MarkBillAsDispatchMailSent(bill):
    with closing(shelve.open(DISPATCH_INFO_PATH)) as d:
        if b.uid_string in d:
            raise Exception("Dispatch mail was already sent for this bill: {}".format(str(bill)))


def _WasDispatchMailSentForBill(bill):
    with closing


def ChooseBill(chosenComp, allCompaniesDict, args):
    daysRange = args.lastFewDays
    daysRange += 1

    if chosenComp:
        billList = allCompaniesDict[chosenComp]
    else:
        billList =  GetAllBillsInLastNDays(daysRange)

    billList = RemoveMinusOneBills(billList)

    from datetime import timedelta
    billList = SelectBillsAfterDate(billList, datetime.date.today() - timedelta(days=daysRange))
    billList.sort(key=lambda b: DD_MM_YYYY(b.invoiceDate), reverse=True)

    if len(billList) == 0:
        raise MyException("{} has no bills in last {} days".format(chosenComp, daysRange))

    def billDesc(b):
        return " | ".join([b.compName,
            "Bill# {}".format(str(int(b.billNumber))),
            DD_MM_YYYY(b.docketDate),
            b.docketNumber,
            b.courierName,
            b.materialDesc,
            ])

    for x in billList:
        print(billDesc(x))

    print("_"*70)

    for x in billList:
        if raw_input("{}(y/n)".format(billDesc(x))).lower() == 'y':
            SendMaterialDispatchDetails(x, args)
    else:
        raise MyException("Oops! You did not select any bill.")


def main():
    args = ParseOptions()

    print("Churning data...")
    allCompaniesDict = GetAllCompaniesDict()

    chosenComp = None if not args.comp or GuessCompanyName(args.comp)

    ctxt = DispatchMailContext()
    ctxt.first_line = args.first_line
    ctxt.second_line = args.second_line
    ctxt.last_line = args.last_line
    ctxt.kaPerson = args.kaPerson
    ctxt.isDemo = args.isDemo

    chosenBill = ChooseBill(chosenComp, allCompaniesDict, ctxt)
    return


class DispatchMailContext(object):
    emailSubject = None
    kaPerson = None
    isDemo = False
    first_line = None
    second_line = None
    last_line = None

def SendMaterialDispatchDetails(bill, ctxt):
    ctxt.emailSubject = "Dispatch Details - Date: {}".format(bill.docketDate.strftime("%d-%b-%Y"))

    print("Churning more data...")

    allCustInfo = GetAllCustomersInfo()
    toMailStr = allCustInfo.GetCustomerEmail(bill.compName)
    if not ctxt.kaPerson:
        #If no person was specified at command line then pick one from the database.
        personFromDB = allCustInfo.GetCustomerKindAttentionPerson(bill.compName)
        if personFromDB and 'y' == raw_input("Mention kind attn: {} (y/n)?".format(personFromDB)).lower():
            ctxt.kaPerson = personFromDB

    if not toMailStr:
        raise MyException("\nNo mail feeded. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'")

    #Mails in database are generally split either with semicolons or colons.
    #In either case, treat them as separated by , and later split on comma
    toMailStr = toMailStr.replace(';', ',')
    toMailStr = toMailStr.replace(' ', '')

    toMailList = toMailStr.split(',')

    #Remove spaces from eachMail in the list and create a new list
    toMailList = [eachMail.replace(' ', '') for eachMail in toMailList]

    print("Preparing mail...")
    mailBody = PrepareShipmentEmailForThisBill(bill, ctxt)

    if ctxt.isDemo:
        toMailList = GetOption("EMAIL_REMINDER_SECTION", "TestMailList").split(',')
        ctxt.emailSubject = "[Testing{}]: {}".format(str(random.randint(1, 10000)), ctxt.emailSubject)

    print("Sending to: " + str(toMailList))

    section = "EMAIL_REMINDER_SECTION"
    SendMail(ctxt.emailSubject,
            None,
            GetOption(section, 'Server'),
            GetOption(section, 'Port'),
            GetOption(section, 'FromEmailAddress'),
            toMailList,
            GetOption(section, 'CCEmailList').split(','),
            GetOption(section, 'Mpass'),
            mailBody,
            textType="html",
            fromDisplayName=GetOption(section, "shipmentDetailsName"))

    return


def PrepareShipmentEmailForThisBill(bill, ctxt):
    """Given a company, this function will prepare an email for shipment details."""
    from UtilColors import MyColors
    from UtilHTML import TableHeaderRow, TableDataRow

    allCustInfo = GetAllCustomersInfo()
    letterDate = DD_MM_YYYY(datetime.date.today())
    officalCompName = allCustInfo.GetCompanyOfficialName(bill.compName)
    if not officalCompName:
        raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(bill.compName))

    companyCity = allCustInfo.GetCustomerCity(bill.compName)
    if not companyCity:
        raise MyException("\nM/s {} doesnt have a displayable 'city'. Please feed it in the database".format(bill.compName))


    tableRows = TableHeaderRow(
            MyColors["BLACK"],
            MyColors["SOLARIZED_GREY"],
            "Bill No.",
            "Dispatched Through",
            "Tracking Number",
            "Shipping Date",
            "Material Description",)

    tableRows += TableDataRow(
            MyColors["BLACK"],
            MyColors["WHITE"],
            str(int(bill.billNumber)),
            str(bill.courierName),
            str(bill.docketNumber),
            DD_MM_YYYY(bill.docketDate),
            bill.materialDesc)

    def constant_factory(value):
        from itertools import repeat
        return repeat(value).next

    from collections import defaultdict
    d = defaultdict(constant_factory(""))

    if ctxt.first_line:
        d['tFirstLine'] = ctxt.first_line + '<br><br>'

    if ctxt.second_line:
        d['tSecondLine'] = ctxt.second_line + '<br><br>'

    if ctxt.last_line:
        d['tLastLine'] = ctxt.last_line + '<br><br>'

    if ctxt.kaPerson:
        d['tPerson'] = Bold("Kind Attention: " + ctxt.kaPerson + '<br><br>')

    d['tLetterDate'] = letterDate
    d['tOfficialCompanyName'] = officalCompName
    d['tCompanyCity'] = companyCity
    d['tTableRows'] = tableRows
    d['tBodySubject'] = PastelOrangeText(Bold(UnderLine(ctxt.emailSubject)))
    d['tSignature'] = GetOption("EMAIL_REMINDER_SECTION", "Signature")

    templateMailBody = Template("""
  <html>
      <head>
      </head>
      <body style=" font-family: Helvetica, Georgia, Verdana, Arial, 'sans-serif'; font-size: 1.1em; line-height: 1.5em;" >
      <p>
      $tLetterDate<br>
      <br>
      To,<br>
      M/s $tOfficialCompanyName,<br>
      $tCompanyCity.<br>
      <br>
      $tBodySubject<br>
      <br>
      $tPerson
      Dear Sir,<br>
      <br>
      $tFirstLine
      $tSecondLine
      Your material has been dispatched. Please find the details below::
      <table border=1 cellpadding=5>
      $tTableRows
      </table>
      </p>
      <br>
      $tLastLine
      <hr>
      <p>
      <font color="grey"> <small>
      $tSignature
      </small></font>
      </p>
      </body>
  </html>
  """)

    finalMailBody = templateMailBody.substitute(d)

    return finalMailBody

if __name__ == '__main__':
    try:
        CheckConsistency()
        main()
    except MyException as ex:
        PrintInBox(str(ex))
