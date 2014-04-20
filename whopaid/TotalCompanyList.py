###############################################################################
## Author: Ashish Anand
## Date: 2014-Mar-04 Tue 01:57 PM
## Intent: To read database and generate list of companies
## Requirement: Python Interpretor must be installed
##              Openpyxl for Python must be installed
###############################################################################

from UtilWhoPaid import GetAllCompaniesDict, SelectBillsAfterDate,\
        SelectBillsBeforeDate, RemoveMinusOneBills
from CustomersInfo import GetAllCustomersInfo
from UtilMisc import ParseDateFromString, OpenFileForViewing, MakeSureDirExists
from SanityChecks import CheckConsistency

import datetime
import argparse
import os

DEST_FOLDER = "B:\\Desktop\\FCR"

def ParseArguments():
    p = argparse.ArgumentParser()

    p.add_argument("-sd", "--start-date", dest='sdate', metavar="Start-date",
            required=False, default=None, type=str,
            help="Starting Date for FORM-C requests.")

    p.add_argument("-ed", "--end-date", dest='edate', metavar="End-date",
            required=False, type=str, default=str(datetime.date.today()),
            help="End Date for Form-C Requests. If ommitted Form-C till date "
            "will be asked for")

    args = p.parse_args()
    return args


def main():
    args = ParseArguments()
    print("Churning data...")

    CheckConsistency()
    GenerateListOfComanies(args)


def GenerateListOfComanies(args):
    sdateObject = ParseDateFromString(args.sdate)  # Start Date Object
    edateObject = ParseDateFromString(args.edate)  # End Date Object
    allCustInfo = GetAllCustomersInfo()

    uniqueCompNames = set()
    billList = list()
    allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
    for eachComp in allBillsDict.keys():
        billList += [b for b in allBillsDict[eachComp]]
    billList = RemoveMinusOneBills(billList)
    billList = SelectBillsAfterDate(billList, sdateObject)
    billList = SelectBillsBeforeDate(billList, edateObject)
    billList = [b for b in billList if b.billingCategory.lower() not in ["up", "jobwork"]]
    billList = [b for b in billList if not b.formCReceivingDate ]
    billList = sorted(billList)

    for b in billList:
        officalCompName = allCustInfo.GetCompanyGroupName(b.compName)
        unOffName = b.compName
        uniqueCompNames.add((unOffName, officalCompName))
    uniqueCompNames = [(u, o) for u, o in uniqueCompNames if not u.startswith("starbu") and not u.startswith("test")]
    uniqueCompNames = sorted(uniqueCompNames, key=lambda (x, y): y)

    MakeSureDirExists(DEST_FOLDER)
    fileName = "AllCompaniesName.html"
    filePath = os.path.join(DEST_FOLDER, fileName)

    with open(filePath, "w") as f:
        f.write("<b><u>{} to {}</u></b><br></br>".format(args.sdate, args.edate))
        for i, (unOffName, officalCompName) in enumerate(uniqueCompNames):
            count = len([x for x in billList if x.compName == unOffName])
            tab = "    "
            f.write("{}. {} bills {}<br>".format(i+1, count, officalCompName))
            for b in billList:
                if b.compName == unOffName:
                    f.write("<pre>" + tab + " {} Rs.{} Bill#{} </pre>".format(b.invoiceDate, int(b.instrumentAmount), b.billNumber))

    OpenFileForViewing(filePath)

if __name__ == "__main__":
    main()
