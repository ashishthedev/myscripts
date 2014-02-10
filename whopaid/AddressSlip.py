###############################################################################
## Author: Ashish Anand
## Date: 2014-Feb-10 Mon 02:02 PM
## Intent: To generate address slip for a specific company
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
from UtilMisc import PrintInBox, DD_MM_YYYY, GetConfirmation
from CustomersInfo import GetAllCustomersInfo
from UtilDecorators import timeThisFunction
from UtilConfig import GetOption, GetAppDir
from SanityChecks import CheckConsistency

import datetime
from string import Template
import argparse
import random
import os
from collections import defaultdict


def ParseOptions():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--comp", dest='comp', type=str, default=None,
            help="Company name or part of it.")
    return parser.parse_args()


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
    uniqueCompNames = set([eachCompName for eachCompName in allCompaniesDict])
    for eachCompName in uniqueCompNames:
        if ShouldWeSendEmailToComp(eachCompName, allCompaniesDict, allCustomersInfo):
            print("We should send mail to {}".format(eachCompName))



@timeThisFunction
def main():

    args = ParseOptions()
    chosenComp = GuessCompanyName(args.comp)
    GenerateAddressSlipForThisCompany(chosenComp)



def ShouldWeSendAutomaticEmailForGroup(grpName, allCompaniesDict, allCustomersInfo):
    #TODO: Buggy.
    compsInGrp = allCustomersInfo.GetListOfCompNamesForThisGrp(grpName)
    firstCompInGrp = compsInGrp[0] #TODO: Remove usage of firstCompInGrp as this is a hack. We are working on groups now.
    unpaidBillList = []
    for compName in compsInGrp:
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

    lastDate = EarlierSentOnDateForThisGrp(grpName)
    if lastDate:
        #Perform this check only when an email was ever sent to this company and this is not a demo.
        timeDelta = datetime.date.today() - lastDate
        minDaysGap = int(allCustomersInfo.GetMinDaysGapBetweenMails(grpName))
        if timeDelta.days < minDaysGap:
            return False

    return True


def SendReminderToGrp(grpName, allCompaniesDict, allCustomersInfo, args):
    compsInGrp = allCustomersInfo.GetListOfCompNamesForThisGrp(grpName)
    import pprint
    PrintInBox("Preparing mails for following companies:")
    pprint.pprint(compsInGrp)
    GetConfirmation()
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
    lastDate = EarlierSentOnDateForThisGrp(grpName)
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
            SaveSentOnDateForThisGrp(grpName)
    else:
        PrintInBox("Not sending any email for comp {}".format(grpName))
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

    if args.second_line:
        d['tSecondLine'] = args.second_line + '<br><br>'

    if args.last_line:
        d['tLastLine'] = args.last_line + '<br><br>'

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
        CheckConsistency()
        main()
    except MyException as ex:
        PrintInBox(str(ex))
        raise ex
