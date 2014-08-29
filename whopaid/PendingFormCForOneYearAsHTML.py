###############################################################################
## Author: Ashish Anand
## Date: 2014-Apr-24 Thu 04:31 PM
## Intent: To read database and generate FORM-C list which are still pending
## Requirement: Python Interpretor must be installed
##              Openpyxl for Python must be installed
###############################################################################

from UtilWhoPaid import GetAllCompaniesDict, SelectBillsAfterDate,\
        SelectBillsBeforeDate
from CustomersInfo import GetAllCustomersInfo
from whopaid.UtilFormC import QuarterlyClubbedFORMC
from Util.PythonMail import SendMail
from Util.Exception import MyException
from Util.Misc import ParseDateFromString, PrintInBox, OpenFileForViewing,\
        MakeSureDirExists, DD_MM_YYYY
from SanityChecks import CheckConsistency
from Util.Config import GetOption
from Util.Decorators import timeThisFunction

import datetime
import argparse
import os

DEST_FOLDER = "B:\\Desktop\\FCR"

def ParseArguments():
    p = argparse.ArgumentParser()

    p.add_argument("-o", "--OpenFileForViewing", dest='open',
            action="store_true", default=False, help="If present, file will"
            " be opened")
    p.add_argument("-sd", "--start-date", dest='sdate', metavar="Start-date",
            required=True, default=None, type=str,
            help="Starting Date for FORM-C requests.")

    p.add_argument("-ed", "--end-date", dest='edate', metavar="End-date",
            required=True, type=str, default=None,
            help="End Date for Form-C Requests.")

    args = p.parse_args()
    return args


@timeThisFunction
def main():
    args = ParseArguments()
    print("Churning data...")

    CheckConsistency()
    html = GenerateFORMCForAllCompanies(args)
    fileName = "PendingFormC{}-{}.html".format(args.sdate, args.edate)
    filePath = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), fileName)
    print("Saving FORM-C to local file: " + filePath)

    with open(filePath, "w") as f:
        f.write(html)

    OpenFileForViewing(filePath)

    return


def ShouldSendEmail(args):
    return False if args.isDemo else args.sendEmail


def GenerateFORMCForAllCompanies(args):
    sdateObject = ParseDateFromString(args.sdate)  # Start Date Object
    edateObject = ParseDateFromString(args.edate)  # End Date Object

    html = """
    <style>
    .fw {
    margin-left: 20px;
    font-family: serif, monospace;
    width: 100px;
    display: inline-block;
    };
    </style>

    """
    html += "<small>{} as on {}</small>".format(GetOption("CONFIG_SECTION", "SmallName"), DD_MM_YYYY(datetime.date.today()))
    html += "<h2>Pending FORMC-C from {} to {}<br> as on {}</h2>".format(DD_MM_YYYY(sdateObject), DD_MM_YYYY(edateObject), DD_MM_YYYY(datetime.datetime.today()))

    allCompaniesDict = GetAllCompaniesDict()
    allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
    interestingCategories = ["central"]

    for eachComp in sorted(allBillsDict.keys()):
        billList = allCompaniesDict.GetBillsListForThisCompany(eachComp)
        if not billList: continue

        billList = SelectBillsAfterDate(billList, sdateObject)
        if not billList: continue

        billList = SelectBillsBeforeDate(billList, edateObject)
        if not billList: continue

        billList = [b for b in billList if not b.formCReceivingDate]
        if not billList: continue

        billList = [b for b in billList if b.billingCategory.lower() in interestingCategories]
        if not billList: continue

        billList = sorted(billList, key=lambda b:b.invoiceDate)
        html += "<h3>{}</h3>".format(eachComp)
        totalAmount = 0
        for b in billList:
            totalAmount += int(b.amount)
            for i in ["Bill# {}".format(int(b.billNumber)),
                    DD_MM_YYYY(b.invoiceDate),
                    "Rs.{}".format(int(b.amount))]:
                html += "<span class='fw'>{}</span>".format(i)
            html += "<br>"
        html += "_____________________________________________________________<br>"
        html += "<span class='fw'>Total:</span>"
        html += "<span class='fw'></span>"
        html += Bold("<span class='fw'>Rs.{}</span>".format(totalAmount))
        html += "<br>"

    return html



def GenerateFormCForThisCompany(compName, args):
    billList = GetAllCompaniesDict().GetBillsListForThisCompany(compName)
    sdate = args.sdate or min([b.invoiceDate for b in billList if not b.formCReceivingDate])
    edate = args.edate or max([b.invoiceDate for b in billList if not b.formCReceivingDate])

    sdateObject = ParseDateFromString(sdate)  # Start Date Object
    edateObject = ParseDateFromString(edate)  # End Date Object

    FORMCBillList = SelectBillsAfterDate(billList, sdateObject)
    FORMCBillList = SelectBillsBeforeDate(FORMCBillList, edateObject)

    if not FORMCBillList:
        raise MyException("\nM/s {} has no FORM-C due".format(compName))

    FORMCBillList = [b for b in FORMCBillList if not b.formCReceivingDate]

    formC = QuarterlyClubbedFORMC(FORMCBillList)
    companyOfficialName = GetAllCustomersInfo().GetCompanyOfficialName(compName)
    if not companyOfficialName:
        raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

    if ShouldSendEmail(args):
        mailBody = formC.GenerateFORMCMailContent(args)
        print("Sending mail...")
        #First prefrence to FormCEmails. If not present use payment emails.
        toMailList = GetAllCustomersInfo().GetFormCEmailAsListForCustomer(compName) or GetAllCustomersInfo().GetPaymentReminderEmailAsListForCustomer(compName)
        if not toMailList:
            raise  Exception("\nNo mail feeded. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'")

        print("Sending to: " + str(toMailList))

        section = "EMAIL_REMINDER_SECTION"
        emailSubject = "FORM-C request - M/s {}".format(companyOfficialName)
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
        fileHTMLContent = formC.GenerateFORMCMailContent(args)
        #Save to an html file

        MakeSureDirExists(DEST_FOLDER)
        filePath = os.path.join(DEST_FOLDER, companyOfficialName) + ".html"
        print("Saving FORM-C to local file: " + filePath)

        with open(filePath, "w") as f:
            f.write(fileHTMLContent)

        if args.open: OpenFileForViewing(filePath)
    return


if __name__ == '__main__':
    try:
        main()
    except MyException as ex:
        PrintInBox(str(ex))










"""
Sample output of this script
<!DOCTYPE html>
<html>
    <body>
        <table border="1" cellpadding=5>
            <tr style="background-color:#6C7A95; color:white">
                <th>Info</th>
                <th>Bill#</th>
                <th>Date</th>
                <th>Amount</th>
            </tr>
            <tr>
                <tr>
                    <th rowspan="2" style="background-color:#2C9B00; color:white">2011-2012 <br> Qtr3</th>
                    <td>1</td>
                    <td>1-Aug-11</td>
                    <td>100</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>2-Aug-11</td>
                    <td>200</td>
                </tr>
            </tr>
        </table>

    </body>
</html>

"""
