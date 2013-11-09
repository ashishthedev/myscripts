###############################################################################
## Author: Ashish Anand
## Date: 2012-09-04 Tue 03:19 PM
## Intent: To read WRKBK_PATH and send payments reminder emails to customers
##         The mail addresses are picked up from CUST_SHEETNAME in the
##         WRKBK_PATH excel file
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from UtilWhoPaid import datex, GetAllCompaniesDict, SelectUnpaidBillsFrom, \
        GuessCompanyName
from UtilHTML import UnderLine, Bold, Big, PastelOrangeText, TableHeaderRow,\
        TableDataRow
from UtilColors import MyColors
from UtilPythonMail import SendMail
from UtilException import MyException
from UtilMisc import PrintInBox, DD_MM_YYYY
from CustomersInfo import GetAllCustomersInfo
from UtilDecorators import timeThisFunction
from UtilConfig import GetOption, GetAppDir
from SanityChecks import CheckConsistency

import datetime
from string import Template
import argparse
from contextlib import closing
import shelve
import random
import os

MINIMUM_AMOUNT_DUE = 2000
LAST_EMAIL_DATE_DB = GetOption("CONFIG_SECTION", "LastEmailDatesSavedIn")

def EarlierSentOnDateForThisComp(compName):
    """Returns a dateObject representing the date on which an email was last sent to this company"""
    dateObject = None
    shelfFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), LAST_EMAIL_DATE_DB)

    with closing(shelve.open(shelfFileName)) as d:
        if str(compName) in d:
            dateObject = d[str(compName)]
    if type(dateObject) == datetime.datetime:
        dateObject = dateObject.date()
    return dateObject

def SaveSentOnDateForThisComp(compName):
    """Registers today() as the date on which last email was sent to company."""
    shelfFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), LAST_EMAIL_DATE_DB)
    with closing(shelve.open(shelfFileName)) as d:
        d[str(compName)] = datetime.date.today()
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
    parser.add_argument("-sl", "--second-line", dest='second_line', type=str,
            default=None, help="If present, emails will be sent with this as "
            "second line.")
    parser.add_argument("-ll", "--last-line", dest='last_line', type=str,
            default=None, help="If present, emails will be sent with this as "
            "last line.")
    parser.add_argument("-ol", "--only-list-no-send", dest="onlyListNoSend",
            default=False, action="store_true", help="Only list names, do not "
            "send. To be used with automatic reminders")

    return parser.parse_args()


def AskQuestionsFromUserAndSendMail(args):

    print("Churning data...")
    allCompaniesDict = GetAllCompaniesDict()
    allCustomersInfo = GetAllCustomersInfo()

    compName = GuessCompanyName(args.comp)

    if not args.kaPerson:
        #If no person was specified at command line then pick one from the database.
        personFromDB = allCustomersInfo.GetCustomerKindAttentionPerson(compName)
        if personFromDB and 'y' == raw_input("Mention kind attn: {} (y/n)?".format(personFromDB)).lower():
            args.kaPerson = personFromDB
    SendReminderToCompany(compName, allCompaniesDict, allCustomersInfo, args)


def SendAutomaticReminderToAllCompanies(args):
    PrintInBox("About to send email to all the companies")
    allCompaniesDict = GetAllCompaniesDict()
    allCustomersInfo = GetAllCustomersInfo()
    uniqueCompNames = set([eachCompName for eachCompName in allCompaniesDict])
    for eachCompName in uniqueCompNames:
        print("Working on {}".format(eachCompName))
        try:
            if ShouldWeSendEmail(eachCompName, allCompaniesDict, allCustomersInfo):
                SendReminderToCompany(eachCompName, allCompaniesDict, allCustomersInfo, args)
        except Exception as ex:
            PrintInBox("Exception while processing: {}\n{}".format(eachCompName, str(ex)))

def OnlyListCompaniesOnScreen(args):
    allCompaniesDict = GetAllCompaniesDict()
    allCustomersInfo = GetAllCustomersInfo()
    uniqueCompNames = set([eachCompName for eachCompName in allCompaniesDict])
    for eachCompName in uniqueCompNames:
        if ShouldWeSendEmail(eachCompName, allCompaniesDict, allCustomersInfo):
            print("We should send mail to {}".format(eachCompName))



@timeThisFunction
def main():

    args = ParseOptions()

    if args.allCompanies:
        if args.onlyListNoSend:
            OnlyListCompaniesOnScreen(args)
        elif not args.onlyListNoSend:
            SendAutomaticReminderToAllCompanies(args)
        return

    AskQuestionsFromUserAndSendMail(args)


def ShouldWeSendEmail(compName, allCompaniesDict, allCustomersInfo):
    unpaidBillList = SelectUnpaidBillsFrom(allCompaniesDict[compName])
    #Unpaid Bills check
    if not unpaidBillList:
        return False # All bills are duly paid; do not send email

    #Advance towards us check
    if int(sum([eachBill.billAmount for eachBill in unpaidBillList])) < MINIMUM_AMOUNT_DUE:
        return False

    #Check if we dont want the customer to be included in automatic mails
    if not allCustomersInfo.IncludeCustInAutomaticMails(compName):
        return False

    #Email present
    if not allCustomersInfo.GetEmailAsListForCustomer(compName):
        return False

    daysSinceOldestUnpaidBill = max([b.daysOfCredit for b in unpaidBillList])
    allowedDaysOfCredit = int(allCustomersInfo.GetCreditLimitForCustomer(compName))
    if daysSinceOldestUnpaidBill <= allowedDaysOfCredit:
        return False

    lastDate = EarlierSentOnDateForThisComp(compName)
    if lastDate:
        #Perform this check only when an email was ever sent to this company and this is not a demo.
        timeDelta = datetime.date.today() - lastDate
        minDaysGap = int(allCustomersInfo.GetMinDaysGapBetweenMails(compName))
        if timeDelta.days < minDaysGap:
            return False

    return True


def SendReminderToCompany(compName, allCompaniesDict, allCustomersInfo,  args):
    unpaidBillList = SelectUnpaidBillsFrom(allCompaniesDict[compName])
    if not len(unpaidBillList):
        raise Exception("Alls bills are duly paid by company: {}".format(compName))

    totalDue = sum([int(eachBill.billAmount) for eachBill in unpaidBillList])

    if totalDue <= MINIMUM_AMOUNT_DUE:
        raise MyException("\nM/s {} has Rs.{} as ADVANCE towards us".format(compName, totalDue))

    toMailList = allCustomersInfo.GetEmailAsListForCustomer(compName)
    if not toMailList:
        raise MyException("\nNo mail feeded. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'")

    goAhead = True
    lastDate = EarlierSentOnDateForThisComp(compName)
    if lastDate and not args.isDemo:
        #Perform this check only when an email was ever sent to this company and this is not a demo.
        timeDelta = datetime.date.today() - lastDate
        minDaysGap = int(allCustomersInfo.GetMinDaysGapBetweenMails(compName))
        if timeDelta.days < minDaysGap:
            if 'y' != raw_input("Earlier mail was sent {} days back. Do you still want to send the email?\n(y/n):".format(timeDelta.days)).lower():
                goAhead = False

    daysSinceOldestUnpaidBill = max([b.daysOfCredit for b in unpaidBillList])
    allowedDaysOfCredit = int(allCustomersInfo.GetCreditLimitForCustomer(compName))

    if daysSinceOldestUnpaidBill < allowedDaysOfCredit:
        if 'y' != raw_input("All bills are within allowed range. Do you still want to send email?\n(y/n): ").lower():
            goAhead = False

    if goAhead:
        print("Preparing mail for M/s {}".format(compName))
        emailSubject = "Payment Request (Rs." + str(totalDue) + ")"
        if args.isDemo:
            toMailList = GetOption("EMAIL_REMINDER_SECTION", "TestMailList").split(',')
            emailSubject = "[Testing{}]: {}".format(str(random.randint(1, 10000)), emailSubject)

        print("Sending to: " + str(toMailList))

        mailBody = PrepareMailContentForThisComp(compName, allCompaniesDict, allCustomersInfo, args)
        section = "EMAIL_REMINDER_SECTION"
        SendMail(emailSubject,
                None,
                GetOption(section, 'Server'),
                GetOption(section, 'Port'),
                GetOption(section, 'FromEmailAddress'),
                toMailList,
                GetOption(section, 'CCEmailList').split(','),
                GetOption(section, 'Mpass'),
                mailBody,
                textType="html",
                fromDisplayName=GetOption(section, "unpaidBillsName")
                )

        if not args.isDemo:
            print("Saving date...")
            SaveSentOnDateForThisComp(compName)
    else:
        PrintInBox("Not sending any email for comp {}".format(compName))
    return


def PrepareMailContentForThisComp(compName, allCompaniesDict, allCustomersInfo, args):
    """Given a bill list for a company, this function will
    prepare mail for the payment reminder."""

    unpaidBillList = SelectUnpaidBillsFrom(allCompaniesDict[compName])
    unpaidBillList.sort(key=lambda b: datex(b.invoiceDate))
    unpaidBillList = [b for b in unpaidBillList if b.billingCategory.lower() not in ["tracking"]]

    def MakeBillRow(*billRowArgs):
        return TableDataRow(
                MyColors["BLACK"],
                MyColors["WHITE"],
                *billRowArgs)

    if not unpaidBillList:
        raise MyException("This function should not be called on empty lists"
        " for it has to generate the mail content.")

    for eachBill in unpaidBillList:
        assert eachBill.isUnpaid is True,\
            "This function should only be called on unpaid bills of a single\
            company."

    totalDue = int(sum([eachBill.billAmount for eachBill in unpaidBillList]))

    letterDate = datetime.date.today().strftime("%A, %d-%b-%Y")

    companyOfficialName = allCustomersInfo.GetCompanyOfficialName(compName)
    if not companyOfficialName:
        raise MyException("\nM/s {} doesnt have a displayable 'name'."
        " Please feed it in the database".format(compName))

    companyCity = allCustomersInfo.GetCustomerCity(compName)
    if not companyCity:
        raise MyException("\nM/s {} doesnt have a displayable 'city'."
        " Please feed it in the database".format(compName))

    allowedDaysOfCredit = int(allCustomersInfo.GetCreditLimitForCustomer(compName))

    includeCreditDays = True if ("yes" == str(allCustomersInfo.GetIncludeDaysOrNot(compName)).lower()) else False
    tableHeadersArgs = ["Bill#", "Invoice Date", "Amount"]
    if includeCreditDays:
        tableHeadersArgs.append("Days of credit")

    tableRows = TableHeaderRow(
            MyColors["GOOGLE_NEW_INBOX_FOREGROUND"],
            MyColors["GOOGLE_NEW_INBOX_BASE"],
            *tableHeadersArgs)

    sumOfNegativeBillNumbers = int(sum([eachBill.billNumber for eachBill in unpaidBillList if eachBill.billNumber < 0]))

    if sumOfNegativeBillNumbers < -1:
        #Ensure there is at max only one -1 bill for each company in unpaid list
        raise MyException("\nThere are more than one running amount present for this company. Its better to cosolidate and then send the statement. Please club various bills with -1 as bill numbers for this company.")

    for eachBill in unpaidBillList:
        #Single Pass to detect if there was some running unpaid amount.
        if eachBill.billNumber == -1:
            prevBalRowArgs = ["Previous Balance", "", Bold("Rs." + str(int(eachBill.billAmount)))]
            if includeCreditDays:
                prevBalRowArgs.append("")
            tableRows += MakeBillRow(*prevBalRowArgs)

    for b in unpaidBillList:
        #Now add a row for the regular bills
        if b.billNumber == -1:
            continue

        billRowArgs=[int(b.billNumber),
                DD_MM_YYYY(datex(b.invoiceDate)),
                Bold("Rs." + str(int(b.billAmount)))]

        #Add a row to table for each unpaid bill
        if includeCreditDays:
            if b.daysOfCredit > allowedDaysOfCredit:
                billRowArgs.append(Bold(str(b.daysOfCredit) + " days"))
            else:
                billRowArgs.append(" ")

        tableRows += MakeBillRow(*billRowArgs)

    tableRowArgs = [Bold("Total"), "", PastelOrangeText(Big(Bold("Rs." + str(totalDue))))]

    if includeCreditDays:
        tableRowArgs.append(" ")
    tableRows += MakeBillRow(*tableRowArgs)

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

    d['tLetterDate'] = letterDate
    d['tCompanyOfficialName'] = companyOfficialName
    d['tCompanyCity'] = companyCity
    d['tTotalDue'] = totalDue
    d['tTableRows'] = tableRows
    d['tBodySubject'] = PastelOrangeText(Bold(UnderLine("Subject: Payment Request (Rs.{})".format(totalDue))))
    d['tSignature'] = GetOption("EMAIL_REMINDER_SECTION", "Signature")
    d['tBankerDetails'] = GetOption("EMAIL_REMINDER_SECTION", "BankerDetails")

    templateMailBody = Template("""
    <html>
        <head>
        </head>
        <body style=" font-family: Helvetica, Georgia, Verdana, Arial, 'sans-serif'; font-size: 1.1em; line-height: 1.5em;" >
        <p>
        $tLetterDate<br>
        <br>
        To,<br>
        M/s $tCompanyOfficialName,<br>
        $tCompanyCity.<br>
        <br>
        $tBodySubject<br>
        <br>
        $tPerson
        Dear Sir,<br>
        <br>
        $tFirstLine
        $tSecondLine
        You are requested to make the payment for following bills:
        <table border=1 cellpadding=5>
        $tTableRows
        </table>
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

if __name__ == '__main__':
    try:
        custDBwbPath = os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "CustDBRelativePath"))
        CheckConsistency()
        main()
    except MyException as ex:
        PrintInBox(str(ex))
        raise ex
