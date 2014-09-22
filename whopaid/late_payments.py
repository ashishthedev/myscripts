#######################################################
## Author: Ashish Anand
## Date: 15 Dec 2011
## Intent: To read bills.xlsx and check who has made late payment as per his trackrecord.
## Requirement: Python 3 Interpretor must be installed
## Openpyxl for Python 3 must be installed
#######################################################

from Util.Config import GetOption
from Util.Decorators import timeThisFunction
from Util.Exception import MyException
from Util.HTML import Html, Body, UnderLine, Table, tr, td
from Util.Misc import PrintInBox, OpenFileForViewing

from whopaid.customers_info import GetAllCustomersInfo
from whopaid.sanity_checks import CheckConsistency
from whopaid.util_whopaid import CompaniesDict, GetAllCompaniesDict,\
        SelectUnpaidBillsFrom, floatx ,TotalAmountDueForThisCompany

import os
import argparse

GRACEPERIOD = int(GetOption("CONFIG_SECTION", "GracePeriodInDays"))
DEFAULT_PAYMENT = int(GetOption("CONFIG_SECTION", "DefaultPaymentInDays"))
ANOMALY_STANDARD_DEVIATION = float(GetOption("CONFIG_SECTION", "AnomalyStandardDeviation"))
FILE_PATH_TXT = os.path.join(os.path.expandvars("%temp%"), "PaymentChaseUpList.txt")
FILE_PATH_HTML = os.path.join(os.path.expandvars("%temp%"), "PaymentChaseUpList.html")

class CandidateCompaniesDict(CompaniesDict):
    """This class represents the resultant companies of WhoPaid() operation, i.e companies who can pay the particular amount.
    It is basically a dictonary just like the base class. Key is company and value is its bills that has been paid"""
    def __init__(self):
        super(CandidateCompaniesDict, self).__init__()

    def __str__(self):
        """This function contains all the formatting in which the results should be shown."""
        result = ""
        if(len(self) > 0):
            for eachComp in self.GetAllBillsOfAllCompaniesAsDict().keys():
                result += "\n" + str(eachComp)
        else:
            result += "Cannot detect who paid amount"
        return result


@timeThisFunction
def main():
    print("Churning Data...")
    allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
    defaultersDict = FindDefaulters(allBillsDict)
    defaultedBillsDict = defaultersDict.GetAllBillsOfAllCompaniesAsDict()

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--text", dest='text', type=str, default=None, help="If present, the report will be genertated in text format.")
    parser.add_argument("-v", "--verbose", dest='verbose', action="store_true", default=False, help="If present, the report will be verbose.")
    args = parser.parse_args()

    if args.text or args.verbose:
        filePath = FILE_PATH_TXT
    else:
        filePath = FILE_PATH_HTML

    with open(filePath, "w") as f:
        if args.text:
            f.write("\n{:^60}\n".format("Payment Chase-up list") + "_"*60)
            f.write(DefaultersAsStrWithLessDesc(defaultedBillsDict, allBillsDict))
        elif args.verbose:
            f.write(TotalDefaultersAmount(defaultedBillsDict))
            f.write(DefaultersAsStr(defaultedBillsDict))
        else:
            f.write(DefaultersAsHTMLWithLessDesc(defaultedBillsDict, allBillsDict))

    OpenFileForViewing(filePath)
    CheckConsistency()

    return


def DefaultersAsHTMLWithLessDesc(defaultedBillsDict, allBillsDict):
    """Late Payments as HTML """
    result = "\n"
    result += UnderLine("<H1>Payment Chase-up List</H1>")
    l = list(defaultedBillsDict.iteritems())

    YardStick = DelayInPayment
    YardStick = AmountStuckWithInterest

    #Sort the list of names in the order of delay in payment
    l.sort(key=lambda x:YardStick(x[1]), reverse=True)

    def TableRow(x, y, z):
        return tr(td(x) + td(y) + td(z))

    tableData = ""
    for i, (compName, billList) in enumerate(l):
        tableData += TableRow(i+1, compName, "Rs." + str(TotalAmountDueForThisCompany(allBillsDict, compName)))
    return Html(Body(result + Table(tableData)))

def DefaultersAsStrWithLessDesc(defaultedBillsDict, allBillsDict):
    result = "\n"
    l = list(defaultedBillsDict.iteritems())

    YardStick = DelayInPayment
    YardStick = AmountStuckWithInterest

    #Sort the list of names in the order of delay in payment
    l.sort(key=lambda x:YardStick(x[1]), reverse=True)

    for i, (compName, billList) in enumerate(l):
        result += "\n{:>3}. {} (Rs.{})".format(i, compName, TotalAmountDueForThisCompany(allBillsDict, compName))
    return result

def DefaultersAsStr(defaultedBillsDict):
    result = "\n"
    l = list(defaultedBillsDict.iteritems())#l contains the list of names

    YardStick = AmountStuckWithInterest
    YardStick = DelayInPayment

    #Sort the list of names in the order of delay in payment
    l.sort(key=lambda x:YardStick(x[1]), reverse=True)

    for eachEntry in l:
        billList = eachEntry[1]
        result += "(" + str(int(YardStick(billList))) + ") "
        result += str(billList)
    return result

def TotalDefaultersAmount(defaultedBillsDict):
    amt = 0
    for eachComp in defaultedBillsDict:
        for b in defaultedBillsDict[eachComp]:
            amt += int(b.amount)

    return "{:<.04} lakh is the total amount due towards defaulters".format(str(amt/100000))

def PaymentMadeInDays(bill):
    assert bill.isPaid, "This function should only be called on paid bills"
    timeDelta = (bill.paymentReceivingDate - bill.invoiceDate)
    return timeDelta.days

def AveragePaymentDays(billList):
    """Calculates the average number of days in which payment is made by a customer. Discards the anomalies"""

    days = 0
    ctr = 0
    for b in billList:
        if b.isPaid:
            days += PaymentMadeInDays(b)
            ctr += 1
    if ctr == 0:
        averagePaymentDays = DEFAULT_PAYMENT
    else:
        averagePaymentDays = int(days/ctr)

    #Discard the anomalies now

    days = 0
    ctr = 0
    for b in billList:
        if b.isPaid:
            creditDays = PaymentMadeInDays(b)
            allowedCreditDays = averagePaymentDays * (1 + (ANOMALY_STANDARD_DEVIATION/100))
            if creditDays < allowedCreditDays:
                days+=creditDays
                ctr += 1
    if ctr == 0:
        averagePaymentDays = DEFAULT_PAYMENT#If no bill present, assume the payment in DEFAULT_PAYMENT days
    else:
        averagePaymentDays = int(days/ctr)

    return averagePaymentDays

def DelayInPayment(billList):
    """Calculates the number of days by which the payment is delayed"""

    trust = floatx(GetAllCustomersInfo().GetTrustForCustomer(billList[0].compName))
    if not trust:
        raise MyException("M/s {} have 0 trust. Please fix the database.".format(billList[0].compName))

    noOfDaysSinceFirstUnpaidBill = 1
    averagePaymentDays = AveragePaymentDays(billList)
    for b in billList:
        assert b.isUnpaid, "This function should only be called on unpaid bills"
        delayInExpectedPayment = b.daysOfCredit - averagePaymentDays
        noOfDaysSinceFirstUnpaidBill = max(noOfDaysSinceFirstUnpaidBill, delayInExpectedPayment)

    return (noOfDaysSinceFirstUnpaidBill / trust)

def AmountStuckWithInterest(billList):
    """Gives back a number indicating the amount of liability with amount also accounted for"""
    if not billList:
        return 0

    trust = floatx(GetAllCustomersInfo().GetTrustForCustomer(billList[0].compName))
    if not trust:
        raise MyException("M/s {} have 0 trust. Please fix the database.".format(billList[0].compName))

    amountStuck = 0
    specifiedCreditLimit = int(GetAllCustomersInfo().GetCreditLimitForCustomer(billList[0].compName))
    historicallyPaidInTheseManyDays = AveragePaymentDays(billList)
    averagePaymentDays = (specifiedCreditLimit + historicallyPaidInTheseManyDays) / 2
    for b in billList:
        assert b.isUnpaid, "This function should only be called on unpaid bills"
        delayInExpectedPayment = b.daysOfCredit - averagePaymentDays
        amountStuck += (b.amount * delayInExpectedPayment) / trust
    return amountStuck

def FindDefaulters(allBillsDict):
    """Traverse each company, create a list of all bills and see what is the average number of days in which the payment is made"""
    defaultersDict = CompaniesDict()
    for eachCompName, billList in allBillsDict.iteritems():
        averageDays = AveragePaymentDays(billList) + GRACEPERIOD
        unpaidBillsList = SelectUnpaidBillsFrom(billList)
        if len(unpaidBillsList):
            for b in unpaidBillsList:
                if b.daysOfCredit > averageDays:
                    defaultersDict.AddBill(b)

    return defaultersDict

if __name__ == '__main__':
    try:
        main()
    except MyException as ex:
        PrintInBox(str(ex))
