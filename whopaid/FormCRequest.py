###############################################################################
## Author: Ashish Anand
## Date: 2012-09-11 Tue 06:16 PM
## Intent: To read database and generate FORM-C Reminders with proper quarters
##         The mail addresses are picked up from CUST_SHEETNAME in the
##         WRKBK_PATH excel file
## Requirement: Python Interpretor must be installed
##              Openpyxl for Python must be installed
###############################################################################

from UtilWhoPaid import GetAllCompaniesDict, SelectBillsAfterDate,\
        SelectBillsBeforeDate, RemoveMinusOneBills, GuessCompanyName
from CustomersInfo import GetAllCustomersInfo
from UtilHTML import UnderLine, Bold, PastelOrangeText
from UtilPythonMail import SendMail
from UtilColors import MyColors
from UtilException import MyException
from UtilMisc import ParseDateFromString, PrintInBox, OpenFileForViewing,\
        MakeSureDirExists
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
    p.add_argument("-c", "--comp", dest='comp', type=str, default=None,
            help="Company name or part of it.")

    p.add_argument("-ka", "--kind-attention", dest='kindAttentionPerson',
            type=str, default=None, help="Name of any specific person."
            "Can be left out")

    p.add_argument("-al", "--additional-line", dest='additional_line',
            type=str, default=None, help="Any additional line that should be"
            "supplied.")

    p.add_argument("-o", "--OpenFileForViewing", dest='open',
            action="store_true", default=False, help="If present, file will"
            " be opened")

    p.add_argument("-l", "--letterHead", dest='letterHead', action="store_true",
            default=False, help="If present, margin will be left on top for"
            " the letterhead.")

    p.add_argument("-e", "--email", dest='sendEmail', action="store_true",
            default=False, help="If present email will be sent to company else"
            " a file will be saved to desktop.")

    p.add_argument("-d", "--demo", "--desktopOnly", "--noEmail", dest='isDemo',
            action="store_true", default=False, help="If present, no email"
            "will be sent. This option will override email option.")

    p.add_argument("-sd", "--start-date", dest='sdate', metavar="Start-date",
            required=False, default=None, type=str,
            help="Starting Date for FORM-C requests.")

    p.add_argument("-ed", "--end-date", dest='edate', metavar="End-date",
            required=False, type=str, default=str(datetime.date.today()),
            help="End Date for Form-C Requests. If ommitted Form-C till date "
            "will be asked for")

    args = p.parse_args()
    return args


@timeThisFunction
def main():
    args = ParseArguments()
    print("Churning data...")

    chosenComp = GuessCompanyName(args.comp)
    GenerateFORMCForCompany(chosenComp, args)
    CheckConsistency()


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

    def SpitTableHTML(self):
        """Will return the full html for form-C"""

        def MakeTable(tableData):
            #TODO: Take Column name as parameters
            """Wraps a boilerplate HTML for table around given data"""
            d = dict()
            d['tTableData'] = tableData
            #Change all the multiple choices to a single final choice
            d['headerBackgroundColor'] = MyColors["WHITE"]
            d['fontColor'] = MyColors["BLACK"]
            html = Template("""
<TABLE border="1" cellpadding=5>
    <thead>
    <tr style="background-color:$headerBackgroundColor; color:$fontColor">
        <th>Info</th>
        <th>Bill#</th>
        <th>Date</th>
        <th>Amount</th>
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
        rowTemplate = Template("""
        <tr>
            $qh
            <td>$bn</td>
            <td>$idate</td>
            <td>Rs.$ba/-</td>
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
                    rowDict['ba'] = int(eachBill.billAmount)
                    tableHTML += rowTemplate.substitute(rowDict)

                totalRowTemplate = Template("""
                <tr>
                    <td colspan="2" align="center"><B>TOTAL</B></td>
                    <td><B>Rs.$quarterTotalAmount/-</B></td>
                </tr>
                """)
                totalRowDict = dict()
                totalRowDict['quarterTotalAmount'] = int(sum([eachBill.billAmount for eachBill in billList]))
                tableHTML += totalRowTemplate.substitute(totalRowDict)

                allTablesHTML += MakeTable(tableHTML) + "<BR>" * 3

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

        d['tTable'] = self.SpitTableHTML()
        d['tLetterDate'] = letterDate
        d['tCompanyName'] = companyOfficialName
        d['tCompanyCity'] = companyCity
        d['tSignature'] = GetOption("EMAIL_REMINDER_SECTION", "Signature")
        d['tBodySubject'] = PastelOrangeText(Bold(UnderLine("Subject: FORM-C request")))

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
            M/s $tCompanyName,<br>
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


def GenerateFORMCForCompany(compName, args):
    billList = RemoveMinusOneBills(GetAllCompaniesDict()[compName])

    #TODO: Remove args and take separate params
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
