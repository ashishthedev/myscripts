##################################################################################################
## Author: Ashish Anand
## Date: 2013-05-27 Mon 03:36 PM
## Intent: To print statements of a company
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
##################################################################################################


from Util.Exception import MyException
from Util.Misc import PrintInBox, DD_MMM_YYYY, ConsoleTable


from whopaid.customers_info import GetAllCustomersInfo
from whopaid.sanity_checks import CheckConsistency
from whopaid.util_whopaid import GetAllCompaniesDict, GuessCompanyGroupName
from whopaid.payment_reminders_for_groups import GetUnpaidBillsAndUnAccSingleAdjForThisComp

from datetime import date
import argparse

ALL_CUST_INFO = GetAllCustomersInfo()

def ParseOptions():

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--comp", dest='comp', type=str, default=None, help="Company name or part of it.")
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

  chosenGrp = GuessCompanyGroupName(args.comp)

  ShowStatementOnTerminal(chosenGrp, allBillsDict, args)

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
  return


def GetMinusOneBills(billList):
  return [b.billNumber for b in billList if b.billNumber!=-1]


def ShowStatementOnTerminal(grpName, allBillsDict, args):
  compsInGrp = ALL_CUST_INFO.GetListOfCompNamesForThisGrp(grpName)
  for compName in compsInGrp:
    unpaidBillsList, singleAdj = GetUnpaidBillsAndUnAccSingleAdjForThisComp(compName)
    Column = ConsoleTable.Column

    billNumbers = [str(b.billNumber) for b in unpaidBillsList]
    invoiceDates = [str(DD_MMM_YYYY(b.invoiceDate)) for b in unpaidBillsList]
    amounts = [str(b.amount) for b in unpaidBillsList]

    if singleAdj:
      billNumbers += [str(singleAdj.billNumber)]
      invoiceDates += [str(singleAdj.invoiceDate)]
      amounts += [str(singleAdj.amount)]

    billNumbers.append("TOTAL")
    invoiceDates.append("")
    amounts.append(str(sum(int(x) for x in amounts)))



    print("")
    print("")
    print(compName)
    print ConsoleTable(
        Column("Bill#", billNumbers),
        Column("Invoice Date", invoiceDates),
        Column("Amount", amounts),
        )
  return


if __name__ == '__main__':
  try:
    main()
    CheckConsistency()
  except MyException as ex:
    PrintInBox(str(ex))
