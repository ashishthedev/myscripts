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
from UtilHTML import UnderLine, Bold, PastelOrangeText
from UtilPythonMail import SendMail
from UtilColors import MyColors
from UtilException import MyException
from UtilMisc import ParseDateFromString, PrintInBox, OpenFileForViewing,\
        MakeSureDirExists, DD_MM_YYYY
from SanityChecks import CheckConsistency
from UtilConfig import GetOption
from UtilDecorators import timeThisFunction

from string import Template
import datetime
from collections import defaultdict
import argparse
import os

DEST_FOLDER = "B:\\Desktop\\FCR"

def ParseArguments():
    p = argparse.ArgumentParser()

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


class QuarterlyClubbedFORMC(object):
    """Takes a list of bills and clubs into quarters for each year."""
    def __init__(self, billList):
        super(QuarterlyClubbedFORMC, self).__init__()
        self.billList = billList
        assert len(set(b.compName for b in billList)) == 1, "More than one company is there in the bill List"

    def GetCompName(self):
        return self.billList[0].compName

    def _GetDisplayableYear(self, bill):
        """Gets the display string for year of a particular bill"""
        month = bill.invoiceDate.month
        year1 = 0
        year2 = 0
        if month < 4:
            year1 = bill.invoiceDate.year - 1
            year2 = bill.invoiceDate.year
        else:
            year1 = bill.invoiceDate.year
            year2 = bill.invoiceDate.year + 1
        finalYear = "{}-{}".format(year1, year2)
        return finalYear

    def _GetQuarterForThisBill(self, bill):
        """Given a bill returns the quarter in string form"""
        d = {
                "1": "4",
                "2": "4",
                "3": "4",
                "4": "1",
                "5": "1",
                "6": "1",
                "7": "2",
                "8": "2",
                "9": "2",
                "10": "3",
                "11": "3",
                "12": "3",
                }
        return "Quarter" + d[str(bill.invoiceDate.month)]

    def SpitTableHTML(self, args):
        """Will return the full html for form-C"""

        def MakeTable(tableHeadersList, tableData):
            #TODO: Take Column name as parameters
            """Wraps a boilerplate HTML for table around given data"""
            d = dict()
            d['tTableData'] = tableData
            #Change all the multiple choices to a single final choice
            d['headerBackgroundColor'] = MyColors["WHITE"]
            d['fontColor'] = MyColors["BLACK"]
            tableHeadersString = ""
            for x in tableHeadersList:
                tableHeadersString += "<th>{}</th>".format(x)
            d['tTableHeaders'] = tableHeadersString
            html = Template("""
<TABLE border="1" cellpadding=5>
    <thead>
    <tr style="background-color:$headerBackgroundColor; color:$fontColor">
        $tTableHeaders
    </tr>
    </thead>
    $tTableData
</TABLE>
            """)
            return html.substitute(d)

        #There is a collection of tables, 1 for each quarter or you can say 1 for each FORMC
        #This way the customer doesnt have to mess up his mind as to which bill will go in which FORMC
        #1 table = 1 FORMC
        #And we can requrest multiple FORMCs too! Therefore an uber html containing we defined tables
        allTablesHTML = ""
        tableHeadersList = ["Info", "Bill#", "Date", "Amount"]
        tTdRemarks = ""
        if args.remarksColumn:
            tableHeadersList.append("Remarks")
            tTdRemarks = "<td></td>"
        rowTemplate = Template("""
        <tr>
            $qh
            <td>$bn</td>
            <td>$idate</td>
            <td>Rs.$ba/-</td>
            $tTdRemarks
        </tr>
        """)

        yearDict = self.GetYearDict()
        for eachYear, quarterDict in sorted(yearDict.items()):
            for eachQuarter, billList in sorted(quarterDict.items()):
                tableHTML = ""
                rowSpanAdded = False
                for eachBill in sorted(billList):
                    #Quarter need special customization in the sense of rowspan and colors
                    quarterBackground = MyColors["SOLARIZED_GREY"]
                    quarterForeground = MyColors["BLACK"]

                    quarterHTML = ""
                    if not rowSpanAdded:
                        quarterHTML = """
                        <th rowspan = "{rs}" style="background-color:{bg};
                            color:{fg}">
                        {ey} <br> <B>{eq}</B>
                        </th>""".format(rs=len(billList) + 1, bg=quarterBackground, fg=quarterForeground, ey=eachYear, eq=eachQuarter)
                        rowSpanAdded = True
                    rowDict = dict()
                    rowDict['qh'] = quarterHTML
                    rowDict['bn'] = int(eachBill.billNumber)
                    rowDict['idate'] = eachBill.invoiceDate.strftime("%d-%b-%y")
                    rowDict['ba'] = int(eachBill.amount)
                    rowDict['tTdRemarks'] = tTdRemarks
                    tableHTML += rowTemplate.substitute(rowDict)

                totalRowTemplate = Template("""
                <tr>
                    <td colspan="2" align="center"><B>TOTAL</B></td>
                    <td><B>Rs.$quarterTotalAmount/-</B></td>
                    $tTdRemarks
                </tr>
                """)
                totalRowDict = dict()
                totalRowDict['quarterTotalAmount'] = int(sum([eachBill.amount for eachBill in billList]))
                totalRowDict['tTdRemarks'] = tTdRemarks
                tableHTML += totalRowTemplate.substitute(totalRowDict)

                allTablesHTML += MakeTable(tableHeadersList, tableHTML) + "<BR>" * 3

        return allTablesHTML

    def GenerateFORMCMailContent(self, args):

        letterDate = datetime.date.today().strftime("%A, %d-%b-%Y")
        compName = self.GetCompName()
        allCustInfo = GetAllCustomersInfo()
        companyOfficialName = allCustInfo.GetCompanyOfficialName(compName)
        if not companyOfficialName:
            raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

        companyCity = allCustInfo.GetCustomerCity(compName)
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

        d['tTable'] = self.SpitTableHTML(args)
        d['tLetterDate'] = letterDate
        d['tCompanyName'] = Bold("M/s " + companyOfficialName)
        d['tCompanyCity'] = companyCity
        d['tSignature'] = GetOption("EMAIL_REMINDER_SECTION", "Signature")
        requestingCompanyName = GetOption("CONFIG_SECTION", 'CompName')
        d['tBodySubject'] = PastelOrangeText(Bold(UnderLine("Subject: FORM-C required by M/s {}".format(requestingCompanyName))))

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
            You are requested to provide FORM-C for following quarters:<br>
            <br>
            $tTable
            <hr>
            $tSignature
            </BODY>
            </HTML>
            """)
        html = htmlTemplate.substitute(d)

        return html

    def GetYearDict(self):
        """Returns a dict of dict.
        year(dict)
         |--quarter(dict)
             |--bills(list)
         """
        yearDict = defaultdict(dict)

        for eachBill in self.billList:
            disYear = self._GetDisplayableYear(eachBill)
            disQuarter = self._GetQuarterForThisBill(eachBill)
            quarterDict = yearDict[disYear]
            if disQuarter in quarterDict:
                quarterDict[disQuarter].append(eachBill)
            else:
                quarterDict[disQuarter] = [ eachBill ]
        return yearDict


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
    html += "<small>{}</small>".format(GetOption("CONFIG_SECTION", "SmallName"))
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
