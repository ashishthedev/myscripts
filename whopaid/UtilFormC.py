###############################################################################
## Author: Ashish Anand
## Date: 2012-09-11 Tue 06:16 PM
## Intent: To read database and generate FORM-C Reminders with proper quarters
##         The mail addresses are picked up from CUST_SHEETNAME in the
##         WRKBK_PATH excel file
## Requirement: Python Interpretor must be installed
##              Openpyxl for Python must be installed
###############################################################################

from Util.Config import GetOption
from Util.HTML import UnderLine, Bold, PastelOrangeText
from Util.Colors import MyColors
from Util.Exception import MyException

from whopaid.CustomersInfo import GetAllCustomersInfo

from string import Template
from collections import defaultdict

import datetime

class QuarterlyClubbedFORMC(object):
    """Takes a list of bills and clubs into quarters for each year."""
    def __init__(self, billList):
        super(QuarterlyClubbedFORMC, self).__init__()
        self.billList = billList
        assert len(set(b.compName for b in billList)) == 1, "More than one company is there in the bill List. {}".format([b.compName for b in billList])

    def _GetCompName(self):
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
        for eachYear, quarterDict in sorted(yearDict.iteritems()):
            for eachQuarter, billList in sorted(quarterDict.iteritems()):
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
        compName = self._GetCompName()
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
            Greetings!<br>
            I hope you have received this mail in the best of spirit.<br>

            $tOptAdditionalLine

            Please find below for your kind reference the list of pending bills for which C-FORMS is yet to be issued.<br>
            We request you to take immediate steps to issue the same and oblige.<br>
            For any query or assistance, please feel free to contact us.<br>
            We wish to hear from you as soon as possible.<br>
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
