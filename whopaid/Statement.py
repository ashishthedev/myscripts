##################################################################################################
## Author: Ashish Anand
## Date: 2013-05-27 Mon 03:36 PM
## Intent: To print statements of a company
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
##################################################################################################

from UtilWhoPaid import GetAllCompaniesDict, SelectBillsAfterDate,\
        SelectBillsBeforeDate, RemoveMinusOneBills, GuessCompanyName,\
        SelectUnpaidBillsFrom
from UtilException import MyException
from UtilMisc import ParseDateFromString, PrintInBox
from SanityChecks import CheckConsistency

from datetime import date
import argparse

def ParseOptions():

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--comp", dest='comp', type=str, default=None, help="Company name or part of it.")
    parser.add_argument("-d", "--demo", "--desktopOnly", "--noEmail", dest='isDemo', action="store_true", default=False, help="If present, no email will be sent. This option will override email option.")
    parser.add_argument("-u", "--only-unpaid", dest='onlyUnpaid', action="store_true", default=True, help="If present, no email will be sent. This option will override email option.")
    parser.add_argument("-a", "--all", dest='allBills', action="store_true", default=False, help="If present, all the bills will be shown whether no email will be sent. This option will override email option.")
    parser.add_argument("-sd", "--start-date", dest='sdate', metavar="Start-date", default="01-Apr-2010", required=False, type=str, help="Starting Date for FORM-C requests.")
    parser.add_argument("-ed", "--end-date", dest='edate', metavar="End-date", required=False, type=str, default=str(date.today()), help="End Date for Form-C Requests. If ommitted Form-C till date will be asked for")
    args = parser.parse_args()
    return args


def main():
    args = ParseOptions()

    print("Churning data...")
    allCompaniesDict = GetAllCompaniesDict()

    chosenComp = GuessCompanyName(args.comp)

    ShowStatementOnTerminal(chosenComp, allCompaniesDict, args)

    CheckConsistency()
    return

def GetMinusOneBills(billList):
    newBillList = list()
    for b in billList:
        if b.billNumber == -1:
            newBillList.append(b)
    return newBillList

def ShowStatementOnTerminal(compName, allCompaniesDict, args):
    header = [compName]
    if not compName in allCompaniesDict:
        raise Exception("No bill is issued to M/s {}".format(compName))

    billList = allCompaniesDict[compName]

    if args.onlyUnpaid:
        header.append("Only unpaid bills")
        billList = SelectUnpaidBillsFrom(billList)

    for b in GetMinusOneBills(billList):
        header.append(str(b))

    billList = RemoveMinusOneBills(billList)

    sdateObject = ParseDateFromString(args.sdate)  # Start Date Object
    billList = SelectBillsAfterDate(billList, sdateObject)

    if args.edate:
        edateObject = ParseDateFromString(args.edate)  # End Date Object
        billList = SelectBillsBeforeDate(billList, edateObject)

    if not billList:
        raise MyException("\nM/s {} has no bill in between '{}' and '{}'".format(compName, sdateObject, edateObject))

    for b in billList:
        header.append(str(b))
    PrintInBox("\n".join(header))
    return

if __name__ == '__main__':
    try:
        main()
    except MyException as ex:
        PrintInBox(str(ex))
