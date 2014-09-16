##################################################################################################
## Author: Ashish Anand
## Date: 2013-05-27 Mon 03:36 PM
## Intent: To print statements of a company
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
##################################################################################################


from Util.Exception import MyException
from Util.Misc import ParseDateFromString, PrintInBox, DD_MMM_YYYY

from whopaid.SanityChecks import CheckConsistency
from whopaid.UtilWhoPaid import GetAllCompaniesDict, SelectBillsAfterDate,\
        SelectBillsBeforeDate, GuessCompanyName, SelectUnpaidBillsFrom

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
    parser.add_argument("-lfp", "--last-few-payments", dest="lastFewPayments", action="store_true", default=False, help="If present, last five payments entered in system will be shown")
    args = parser.parse_args()
    return args


def main():
  args = ParseOptions()

  print("Churning data...")
  allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()

  if args.lastFewPayments:
    ShowLastFewPaymentsOnTerminal()
    return

  chosenComp = GuessCompanyName(args.comp)

  ShowStatementOnTerminal(chosenComp, allBillsDict, args)

  return

def ShowLastFewPaymentsOnTerminal():

  noOfPaymentsToShow = 10
  allPaymentsDict = GetAllCompaniesDict().GetAllPaymentsByAllCompaniesAsDict()
  allPayments = list()
  for compName, paymentList in allPaymentsDict.items():
    for p in paymentList:
      allPayments.append(p)
  for i, p in enumerate(sorted(allPayments, key=lambda p:p.pmtDate, reverse=True)[:noOfPaymentsToShow], start=1):
    print("{}. {:<10} {:<15} {}".format(i, int(p.amount), DD_MMM_YYYY(p.pmtDate), p.compName))


def GetMinusOneBills(billList):
  newBillList = list()
  for b in billList:
    if b.billNumber == -1:
      newBillList.append(b)
  return newBillList

def ShowStatementOnTerminal(compName, allBillsDict, args):
  header = [compName]
  if not compName in allBillsDict.keys():
    raise Exception("No bill is issued to M/s {}".format(compName))

  billList = allBillsDict[compName]

  if args.onlyUnpaid:
    header.append("Only unpaid bills")
    billList = SelectUnpaidBillsFrom(billList)

  for b in GetMinusOneBills(billList):
    header.append(str(b))

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
      CheckConsistency()
    except MyException as ex:
      PrintInBox(str(ex))
