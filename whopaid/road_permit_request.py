###############################################################################
## Author: Ashish Anand
## Date: 2013-06-04 Tue 12:47 PM
## Intent: To ask for road permit from a paritcular company when the bill is
##         ready
##         The mail addresses are picked up from CUST_SHEETNAME in the
##         WRKBK_PATH excel file
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from Util.Config import GetOption
from Util.Exception import MyException
from Util.HTML import UnderLine, Bold, PastelOrangeText
from Util.Misc import PrintInBox, DD_MM_YYYY
from Util.PythonMail import SendMail

from whopaid.customers_info import GetAllCustomersInfo
from whopaid.sanity_checks import CheckConsistency
from whopaid.util_whopaid import GetAllCompaniesDict, GuessCompanyName
from whopaid.off_comm import SendOfficialSMSAndMarkCC

from datetime import datetime
from string import Template

import argparse
import random
import os


def ParseOptions():
    p = argparse.ArgumentParser(description="Send mail to a company requesting"
            " for a road permit")

    p.add_argument("-c", "--comp", dest='comp', type=str, default=None,
            help="Company name or part of it.")

    p.add_argument('-b', '-billNumber', dest='billNumber', type=str,
            help="Bill Number")

    p.add_argument('-d', '--invoice-date', dest='invoiceDate', type=str,
            help="Date of the Invoice.")

    p.add_argument('-a', '--amount', dest='billAmount', type=str,
            help="Amount of invoice.")

    p.add_argument('-md', '--material-desc', dest='materialDesc', type=str,
            help="Company name or part of it.")

    p.add_argument("-sb", "--scanned-bill", dest="scannedBillPath", type=str,
             help = "If present file will be sent as attachment")


    p.add_argument("--mail", dest='mail', action="store_true",
            default=False, help="If present, an email will be sent if possible.")

    p.add_argument("--sms", dest='sms', action="store_true",
            default=False, help="If present, an sms will also be sent if possible.")

    p.add_argument("--demo", dest='isDemo', action="store_true",
            default=False, help="If present, emails will only be sent to "
            "testm mail ids only.")

    p.add_argument("-ka", "--kindAttentionPerson", dest='kaPerson',
            type=str, default=None, help="If present, a kind attention name "
            "will be placed toemails will be added to the request.")

    p.add_argument("-fl", "--first-line", dest='first_line', type=str,
            default=None, help="If present, emails will be sent with this as "
            "first line.")

    p.add_argument("-sl", "--second-line", dest='second_line', type=str,
            default=None, help="If present, emails will be sent with this as "
            "first line.")

    p.add_argument("-ll", "--last-line", dest='last_line', type=str,
            default=None, help="If present, emails will be sent with this as "
            "last line.")


    args = p.parse_args()
    if not args.invoiceDate: args.invoiceDate = raw_input("Date:")
    if not args.materialDesc: args.materialDesc = raw_input("Material:")
    if not args.billAmount: args.billAmount = raw_input("Amount:")
    if not args.billNumber: args.billNumber = raw_input("Bill#:")
    if not args.scannedBillPath: args.scannedBillPath = raw_input("Scanned Bill Path:")

    return args


def main():
    args = ParseOptions()
    print("Churning data...")
    allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()

    token = args.comp or str(raw_input("Enter company name:"))
    chosenComp = GuessCompanyName(token)

    if chosenComp:
      if args.mail:
        SendRoadPermitRequest(chosenComp, allBillsDict, args)
      if args.sms and not args.isDemo:
        SendOfficialSMSAndMarkCC(chosenComp, """Dear Sir,
Kindly issue the road permit. The details have been sent to your email address.
Thanks.
""")
    else:
      print("Company containing {} does not exist. Try shorter string")
      exit(1)
    return


def SendRoadPermitRequest(compName, allBillsDict, args):
    args.emailSubject = "Road permit required: Bill#{}".format(args.billNumber)

    print("Preparing road permit request mail...")

    allCustInfo = GetAllCustomersInfo()
    toMailStr = allCustInfo.GetPaymentReminderEmailsForCustomer(compName)
    if not args.kaPerson:
      #If no person was specified at command line then pick one from the database.
      personFromDB = allCustInfo.GetCustomerKindAttentionPerson(compName)
      if personFromDB and 'y' == raw_input("Mention kind attn: {} (y/n)?".format(personFromDB)).lower():
        args.kaPerson = personFromDB

    if not toMailStr:
      raise MyException("\nNo mail feeded. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'")

    #Mails in database are generally split either with semicolons or colons.
    #In either case, treat them as separated by , and later split on comma
    toMailStr = toMailStr.replace(';', ',')
    toMailStr = toMailStr.replace(' ', '')

    toMailList = toMailStr.split(',')

    #Remove spaces from eachMail in the list and create a new list
    toMailList = [eachMail.replace(' ', '') for eachMail in toMailList]
    ccMailList = GetOption("EMAIL_REMINDER_SECTION", 'CCEmailList').replace(';', ',').split(','),
    bccMailList = GetOption("EMAIL_REMINDER_SECTION", 'BCCEmailList').replace(';', ',').split(','),

    print("Preparing mail...")
    if args.scannedBillPath:
        if not os.path.exists(args.scannedBillPath):
            raise Exception("{} does not exist. This path is given as an attachment to be sent along with road permit")
    mailBody = PrepareMailContentForThisComp(compName, allBillsDict, args)

    if args.isDemo:
        toMailList = GetOption("EMAIL_REMINDER_SECTION", "TestMailList").split(',')
        ccMailList = None
        bccMailList = None
        args.emailSubject = "[Testing{}]: {}".format(str(random.randint(1, 10000)), args.emailSubject)

    section = "EMAIL_REMINDER_SECTION"
    SendMail(args.emailSubject,
            args.scannedBillPath,
            GetOption(section, 'Server'),
            GetOption(section, 'Port'),
            GetOption(section, 'FromEmailAddress'),
            toMailList,
            ccMailList,
            bccMailList,
            GetOption(section, 'Mpass'),
            mailBody,
            textType="html",
            fromDisplayName=GetOption(section, "roadPermitRequest"))

    return


def PrepareMailContentForThisComp(compName, allBillsDict, args):
    """Given a company, this function will prepare an email for roadpermit."""
    from Util.Colors import MyColors
    from Util.HTML import TableHeaderRow, TableDataRow, TableHeaderCol

    allCustInfo = GetAllCustomersInfo()
    companyName = allCustInfo.GetCompanyOfficialName(compName)
    if not companyName:
        raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

    companyCity = allCustInfo.GetCustomerCity(compName)
    if not companyCity:
        raise MyException("\nM/s {} doesnt have a displayable 'city'. Please feed it in the database".format(compName))

    from collections import OrderedDict
    dictVal = OrderedDict()
    dictVal["Company Name"] = companyName
    dictVal["Bill#"] = int(args.billNumber)
    dictVal["Invoice Date"] = DD_MM_YYYY(args.invoiceDate)
    dictVal["Amount after Tax"] = "Rs." + args.billAmount
    dictVal["Material"]= args.materialDesc
    tableRows = TableHeaderCol(MyColors["BLACK"],
        MyColors["SOLARIZED_GREY"],
        dictVal)

    if False: #Set this to True temporarily to test colors
        args.isDemo = True
        args.emailSubject = "Testing Colors"
        PrintInBox("Executing in test mode")
        from Util.Colors import MyColors
        for eachBGColor in MyColors:
            for eachFGColr in [MyColors["WHITE"], MyColors["BLACK"]]:
                tableRows += "<br>"
                tableRows += TableHeaderRow(
                    eachFGColr,
                    MyColors[eachBGColor],
                    "Company Name",
                    "Bill#",
                    "Invoice Date",
                    "Amount",
                    "Material Description",
                    "Color")

                tableRows += TableDataRow(
                    companyName,
                    int(args.billNumber),
                    DD_MM_YYYY(args.invoiceDate),
                    "Rs." + args.billAmount,
                    args.materialDesc,
                    eachBGColor)

    def constant_factory(value):
        from itertools import repeat
        return repeat(value).next

    from collections import defaultdict
    d = defaultdict(constant_factory(""))

    if args.first_line:
        d['tFirstLine'] = args.first_line + '<br><br>'

    if args.second_line:
        d['tSecondLine'] = args.second_line + '<br><br>'

    if args.last_line:
        d['tLastLine'] = args.last_line + '<br><br>'

    if args.kaPerson:
        d['tPerson'] = Bold("Kind Attention: " + args.kaPerson + '<br><br>')

    if args.scannedBillPath:
      content = "Please find scanned copy of the bill attached with this email."
      d['tIsScannedCopyAttached'] = """<br>
      <table border="0" cellspacing="0" cellpadding="0" width="auto" bgcolor="#ececec">
<tbody>
<tr>
<td style="font-weight:bold;color:#3f3f3f;padding-left:24px; padding-right:24px" height="44" valign="center">{content}</td>
</tr>
</tbody>
</table>
""".format(content=content)

    d['tLetterDate'] = DD_MM_YYYY(datetime.today())
    d['tCompanyName'] = companyName
    d['tCompanyCity'] = companyCity
    d['tTableRows'] = tableRows
    d['tBodySubject'] = PastelOrangeText(Bold(UnderLine(args.emailSubject)))
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
      M/s $tCompanyName,<br>
      $tCompanyCity.<br>
      <br>
      $tBodySubject<br>
      <br>
      $tPerson
      Dear Sir,<br>
      <br>
      $tFirstLine
      $tSecondLine
      You are requested to provide road permit for following material:
      <table border=1 cellpadding=5>
      $tTableRows
      </table>
      </p>
      $tIsScannedCopyAttached
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
