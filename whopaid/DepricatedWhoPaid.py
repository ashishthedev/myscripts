from __future__ import print_function, division, absolute_import, unicode_literals
#######################################################
## Author: Ashish Anand
## Date: 15 Dec 2011
## Intent: To read bills.xlsx and check who paid for this amount. Also perform some sanity testing
## Requirement: Python Interpretor must be installed
######################################################
from UtilDecorators import memoize, timeThisFunction
from UtilWhoPaid import SelectUnpaidBillsFrom, GetAllCompaniesDict
from LatePayments import CandidateCompaniesDict
from SanityChecks import CheckConsistency
from UtilMisc import PrintInBox, printNow
from UtilException import MyException
from argparse import ArgumentParser
from UtilConfig import GetOption


@timeThisFunction
def main():

    parser = ArgumentParser()
    parser.add_argument("paymentMade", type=int, help="Amount paid by unknown company.")
    args = parser.parse_args()

    paymentMade = args.paymentMade
    printNow("Churning data...")
    BeginWhoPaid( paymentMade)
    CheckConsistency()


def BeginWhoPaid(paymentMade):
    candidatesDict = WhoPaid(paymentMade)
    PrintInBox(str(candidatesDict))


def WhoPaid(paymentMade):
    """Traverse each company, create a list of unpaid bills and see if it can pay for any combination"""
    candidatesDict = CandidateCompaniesDict()
    allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsList()
    for eachCompName in allBillsDict:
        billsList = allBillsDict[eachCompName]
        unpaidBillsList = SelectUnpaidBillsFrom(billsList)
        if len(unpaidBillsList) > int(GetOption("CONFIG_SECTION", "MaxUnpaidBills")):
            continue

        (can, returnBillsList) = CanThisCompanyPay(unpaidBillsList, paymentMade)
        if can:
            [candidatesDict.AddBill(eachBill) for eachBill in returnBillsList]

    return candidatesDict

@memoize
def CanThisCompanyPay(billsList, paymentMade):
    """
    This function will return True if the paid amount can be a combination of any bills. Also
    If this company can't pay it wil return False
    """
    totalUnpaidAmount = sum([bill.instrumentAmount for bill in billsList])

    if(totalUnpaidAmount == paymentMade):
        return (True, billsList)

    for i in range(len(billsList)):
        #Heart of creating different combinations. Delete each value and call recursively to check the payment feasability
        newBillsList = list(billsList)
        del newBillsList[i]
        (can, returnBillsList) = CanThisCompanyPay(newBillsList, paymentMade)
        if can:
            return (True, returnBillsList)
    return (False, None)

if __name__ == '__main__':
    try:
        main()
    except MyException as ex:
        PrintInBox(str(ex))
