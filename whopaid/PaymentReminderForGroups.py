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
        GuessCompanyGroupName
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
from collections import defaultdict

MINIMUM_AMOUNT_DUE = 2000
LAST_EMAIL_DATE_DB = GetOption("CONFIG_SECTION", "LastEmailDatesSavedIn")
def constant_factory(value):
    from itertools import repeat
    return repeat(value).next

def GetConfirmation():
    if raw_input("Proceed: (y/n)").lower() != "y":
        raise Exception()

def EarlierSentOnDateForThisGrp(grpName):
    """Returns a dateObject representing the date on which an email was last sent to this company"""
    dateObject = None
    shelfFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), LAST_EMAIL_DATE_DB)

    with closing(shelve.open(shelfFileName)) as d:
        if str(grpName) in d:
            dateObject = d[str(grpName)]
    if type(dateObject) == datetime.datetime:
        dateObject = dateObject.date()
    return dateObject

def SaveSentOnDateForThisGrp(compName):
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
    parser.add_argument("-ol", "--only-list-no-send", dest="onlyListNoSend",
            default=False, action="store_true", help="Only list names, do not "
            "send. To be used with automatic reminders")

    return parser.parse_args()


def AskQuestionsFromUserAndSendMail(args):

    print("Churning data...")
    allCompaniesDict = GetAllCompaniesDict()
    allCustomersInfo = GetAllCustomersInfo()

    grpName = GuessCompanyGroupName(args.comp)

    if not args.kaPerson:
        #If no person was specified at command line then pick one from the database.
        for eachComp in allCustomersInfo.GetListOfCompNamesForThisGrp(grpName):
            personFromDB = allCustomersInfo.GetCustomerKindAttentionPerson(eachComp)
            if personFromDB and 'y' == raw_input("Mention kind attn: {} (y/n)?".format(personFromDB)).lower():
                args.kaPerson = personFromDB
                break
    SendReminderToGrp(grpName, allCompaniesDict, allCustomersInfo, args)


def SendAutomaticReminderToAllCompanies(args):
    PrintInBox("About to send email to all the companies")
    allCompaniesDict = GetAllCompaniesDict()
    allCustomersInfo = GetAllCustomersInfo()
    uniqueCompGrpNames = set([allCustomersInfo.GetCompanyGroupName(eachComp) for eachComp in allCompaniesDict])
    for eachGrp in uniqueCompGrpNames:
        print("Working on {}".format(eachGrp))
        try:
            if ShouldWeSendAutomaticEmailForGroup(eachGrp, allCompaniesDict, allCustomersInfo):
                SendReminderToGrp(eachGrp, allCompaniesDict, allCustomersInfo, args)
        except Exception as ex:
            PrintInBox("Exception while processing: {}\n{}".format(eachGrp, str(ex)))

def OnlyListCompaniesOnScreen(args):
    allCompaniesDict = GetAllCompaniesDict()
    allCustomersInfo = GetAllCustomersInfo()
    uniqueCompGrpNames = set([allCustomersInfo.GetCompanyGroupName(eachComp) for eachComp in allCompaniesDict])
    for eachGrp in uniqueCompGrpNames:
        if ShouldWeSendAutomaticEmailForGroup(eachGrp, allCompaniesDict, allCustomersInfo):
            print("We should send mail to {}".format(eachGrp))



@timeThisFunction
def main():

    args = ParseOptions()

    if args.onlyListNoSend:
        OnlyListCompaniesOnScreen(args)
        return

    if args.allCompanies:
        SendAutomaticReminderToAllCompanies(args)
        return

    AskQuestionsFromUserAndSendMail(args)

def ShouldWeSendAutomaticEmailForGroup(grpName, allCompaniesDict, allCustomersInfo):
    compsInGrp = allCustomersInfo.GetListOfCompNamesForThisGrp(grpName)
    firstCompInGrp = compsInGrp[0]
    unpaidBillList = []
    for compName in compsInGrp:
        if not compName in allCompaniesDict:
            #print("{compName} has no issued bills till date. Ignoring it.".format(compName=compName))
            continue
        unpaidBillList += SelectUnpaidBillsFrom(allCompaniesDict[compName])

    #Unpaid Bills check
    if not unpaidBillList:
        return False # All bills are duly paid; do not send email

    #Advance towards us check
    if int(sum([eachBill.billAmount for eachBill in unpaidBillList])) < MINIMUM_AMOUNT_DUE:
        return False

    #Check if we dont want the customer to be included in automatic mails
    if not allCustomersInfo.IncludeCustInAutomaticMails(firstCompInGrp):
        return False

    #Email present
    if not allCustomersInfo.GetPaymentReminderEmailAsListForCustomer(firstCompInGrp):
        return False

    daysSinceOldestUnpaidBill = max([b.daysOfCredit for b in unpaidBillList])
    allowedDaysOfCredit = int(allCustomersInfo.GetCreditLimitForCustomer(firstCompInGrp))
    if daysSinceOldestUnpaidBill <= allowedDaysOfCredit:
        return False

    lastDate = EarlierSentOnDateForThisGrp(firstCompInGrp)
    if lastDate:
        #Perform this check only when an email was ever sent to this company and this is not a demo.
        timeDelta = datetime.date.today() - lastDate
        minDaysGap = int(allCustomersInfo.GetMinDaysGapBetweenMails(firstCompInGrp))
        if timeDelta.days < minDaysGap:
            return False

    return True


def SendReminderToGrp(grpName, allCompaniesDict, allCustomersInfo, args):
    compsInGrp = allCustomersInfo.GetListOfCompNamesForThisGrp(grpName)
    import pprint
    PrintInBox("Preparing mails for following companies:")
    pprint.pprint(compsInGrp)
    firstCompInGrp = compsInGrp[0] #TODO: Remove usage of firstCompInGrp as this is a hack. We are working on groups now.
    unpaidBillList = []
    for eachComp in compsInGrp:
        unpaidBillList += SelectUnpaidBillsFrom(allCompaniesDict[eachComp])

    if not len(unpaidBillList):
        raise Exception("Alls bills are duly paid by group: {}".format(grpName))

    totalDue = sum([int(eachBill.billAmount) for eachBill in unpaidBillList])

    if totalDue <= MINIMUM_AMOUNT_DUE:
        raise MyException("\nM/s {} has Rs.{} which is less than MINIMUM_AMOUNT_DUE".format(grpName, totalDue))

    toMailList = []
    ccMailList = GetOption("EMAIL_REMINDER_SECTION", 'CCEmailList').replace(';', ',').split(','),
    bccMailList = GetOption("EMAIL_REMINDER_SECTION", 'BCCEmailList').replace(';', ',').split(','),

    for eachComp in compsInGrp:
        toMailList += allCustomersInfo.GetPaymentReminderEmailAsListForCustomer(eachComp)

    toMailList = list(set(toMailList)) # Remove duplicates
    if not toMailList:
        raise MyException("\nNo mail feeded. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'")

    goAhead = True
    lastDate = EarlierSentOnDateForThisGrp(firstCompInGrp)
    if lastDate and not args.isDemo:
        #Perform this check only when an email was ever sent to this company and this is not a demo.
        timeDelta = datetime.date.today() - lastDate
        firstCompInGrp = compsInGrp[0]#TODO: Hack
        minDaysGap = int(allCustomersInfo.GetMinDaysGapBetweenMails(firstCompInGrp))#TODO: Hack
        if timeDelta.days < minDaysGap:
            if 'y' != raw_input("Earlier mail was sent {} days back. Do you still want to send the email?\n(y/n):".format(timeDelta.days)).lower():
                goAhead = False

    daysSinceOldestUnpaidBill = max([b.daysOfCredit for b in unpaidBillList])
    allowedDaysOfCredit = int(allCustomersInfo.GetCreditLimitForCustomer(firstCompInGrp))

    if daysSinceOldestUnpaidBill < allowedDaysOfCredit:
        if 'y' != raw_input("All bills are within allowed range. Do you still want to send email?\n(y/n): ").lower():
            goAhead = False

    if goAhead:
        print("Preparing mail for group M/s {}".format(grpName))
        emailSubject = "Payment Request (Rs.{})".format(str(totalDue))
        if args.isDemo:
            toMailList = GetOption("EMAIL_REMINDER_SECTION", "TestMailList").replace(';', ',').split(',')
            ccMailList = None
            bccMailList = None
            emailSubject = "[Testing{}]: {}".format(str(random.randint(1, 10000)), emailSubject)

        mailBody = PrepareMailContentForThisGrp(grpName, allCompaniesDict, allCustomersInfo, args)
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
            SaveSentOnDateForThisGrp(firstCompInGrp)
    else:
        PrintInBox("Not sending any email for group {}".format(grpName))
    return


def GetHTMLTableBlockForThisComp(compName, allCompaniesDict, allCustomersInfo):
    unpaidBillList = SelectUnpaidBillsFrom(allCompaniesDict[compName])
    unpaidBillList.sort(key=lambda b: datex(b.invoiceDate))
    unpaidBillList = [b for b in unpaidBillList if b.billingCategory.lower() not in ["tracking"]]

    companyOfficialName = allCustomersInfo.GetCompanyOfficialName(compName)
    if not companyOfficialName:
        raise MyException("\nM/s {} doesnt have a displayable 'name'."
        " Please feed it in the database".format(compName))

    companyCity = allCustomersInfo.GetCustomerCity(compName)
    if not companyCity:
        raise MyException("\nM/s {} doesnt have a displayable 'city'."
        " Please feed it in the database".format(compName))

    allowedDaysOfCredit = int(allCustomersInfo.GetCreditLimitForCustomer(compName))

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

    tableFinalRowArgs = [Bold("Total"), "", PastelOrangeText(Big(Bold("Rs." + str(totalDue))))]
    if includeCreditDays:
        tableFinalRowArgs.append(" ")

    tableRows += MakeBillRow(*tableFinalRowArgs)

    caption = "M/s {}, {}".format(companyOfficialName, companyCity) + PastelOrangeText(Bold("<br>Rs.{}".format(str(totalDue))))

    d = defaultdict(constant_factory(""))
    d['tTableRows'] = tableRows
    d['tCaption'] = caption
    tableTemplate = Template("""
            <table border=1 cellpadding=5>
            <caption>
            $tCaption
            </caption>
            $tTableRows
            </table>""")
    htmlTable = tableTemplate.substitute(d)
    return htmlTable


def PrepareMailContentForThisGrp(grpName, allCompaniesDict, allCustomersInfo, args):
    """Given a bill list for a company group, this function will
    prepare mail for the payment reminder."""

    compsInGrp = allCustomersInfo.GetListOfCompNamesForThisGrp(grpName)
    unpaidBillList = []
    for eachComp in compsInGrp:
        unpaidBillList += SelectUnpaidBillsFrom(allCompaniesDict[eachComp])
    totalDue = sum([int(eachBill.billAmount) for eachBill in unpaidBillList])

    htmlTables = ""
    for eachCompName in compsInGrp:
        htmlTables += "<br>" + GetHTMLTableBlockForThisComp(eachCompName, allCompaniesDict, allCustomersInfo)

    letterDate = datetime.date.today().strftime("%A, %d-%b-%Y")
    d = defaultdict(constant_factory(""))

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

    d['tLetterDate'] = letterDate
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
        $tLetterDate<br>
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

if __name__ == '__main__':
    try:
        custDBwbPath = os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "CustDBRelativePath"))
        CheckConsistency()
        main()
    except MyException as ex:
        PrintInBox(str(ex))
        raise ex
