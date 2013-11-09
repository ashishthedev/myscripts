#######################################################
## Author: Ashish Anand
## Date: 15 Dec 2011
## Intent: To read bills.xlsx and check who has made late payment as per his trackrecord.
## Requirement: Python 3 Interpretor must be installed
## Openpyxl for Python 3 must be installed
#######################################################

from UtilDecorators import timeThisFunction
from UtilWhoPaid import CandidateCompaniesDict, GetAllCompaniesDict,\
        SelectUnpaidBillsFrom, floatx, \
        TotalAmountDueForThisCompany, RemoveMinusOneBills
from UtilException import MyException
from UtilMisc import PrintInBox, OpenFileForViewing
from UtilHTML import Html, Body, UnderLine, Table, tr, td
from SanityChecks import CheckConsistency
from UtilConfig import GetOption

import os
import argparse
from CustomersInfo import GetAllCustomersInfo

GRACEPERIOD = int(GetOption("CONFIG_SECTION", "GracePeriodInDays"))
DEFAULT_PAYMENT = int(GetOption("CONFIG_SECTION", "DefaultPaymentInDays"))
ANOMALY_STANDARD_DEVIATION = float(GetOption("CONFIG_SECTION", "AnomalyStandardDeviation"))
FILE_PATH_TXT = os.path.join(os.path.expandvars("%temp%"), "PaymentChaseUpList.txt")
FILE_PATH_HTML = os.path.join(os.path.expandvars("%temp%"), "PaymentChaseUpList.html")


@timeThisFunction
def main():
    print("Churning Data...")
    allCompaniesDict = GetAllCompaniesDict()
    defaultersDict = FindDefaulters(allCompaniesDict)

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
            f.write(DefaultersAsStrWithLessDesc(defaultersDict, allCompaniesDict))
        elif args.verbose:
            f.write(TotalDefaultersAmount(defaultersDict))
            f.write(DefaultersAsStr(defaultersDict))
        else:
            f.write(DefaultersAsHTMLWithLessDesc(defaultersDict, allCompaniesDict))

    OpenFileForViewing(filePath)
    CheckConsistency()

    return


def DefaultersAsHTMLWithLessDesc(defaultersDict, allCompaniesDict):
    """Late Payments as HTML """
    result = "\n"
    result += UnderLine("<H1>Payment Chase-up List</H1>")
    l = list(defaultersDict.items())

    YardStick = DelayInPayment
    YardStick = AmountStuckWithInterest

    #Sort the list of names in the order of delay in payment
    l.sort(key=lambda x:YardStick(x[1]), reverse=True)

    def TableRow(x, y, z):
        return tr(td(x) + td(y) + td(z))

    tableData = ""
    for i, (compName, billList) in enumerate(l):
        tableData += TableRow(i+1, compName, "Rs." + str(TotalAmountDueForThisCompany(allCompaniesDict, compName)))
    return Html(Body(result + Table(tableData)))

def DefaultersAsStrWithLessDesc(defaultersDict, allCompaniesDict):
    result = "\n"
    l = list(defaultersDict.items())

    YardStick = DelayInPayment
    YardStick = AmountStuckWithInterest

    #Sort the list of names in the order of delay in payment
    l.sort(key=lambda x:YardStick(x[1]), reverse=True)

    for i, (compName, billList) in enumerate(l):
        result += "\n{:>3}. {} (Rs.{})".format(i, compName, TotalAmountDueForThisCompany(allCompaniesDict, compName))
    return result

def DefaultersAsStr(defaultersDict):
    result = "\n"
    l = list(defaultersDict.items())#l contains the list of names

    YardStick = AmountStuckWithInterest
    YardStick = DelayInPayment

    #Sort the list of names in the order of delay in payment
    l.sort(key=lambda x:YardStick(x[1]), reverse=True)

    for eachEntry in l:
        billList = eachEntry[1]
        result += "(" + str(int(YardStick(billList))) + ") "
        result += str(billList)
    return result

def TotalDefaultersAmount(defaultersDict):
    amt = 0
    for eachComp in defaultersDict:
        for b in defaultersDict[eachComp]:
            amt += int(b.billAmount)

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
        amountStuck += (b.billAmount * delayInExpectedPayment) / trust
    return amountStuck

def FindDefaulters(allCompaniesDict):
    """Traverse each company, create a list of all bills and see what is the average number of days in which the payment is made"""
    defaultersDict = CandidateCompaniesDict()
    for eachCompName in allCompaniesDict:
        billList = allCompaniesDict[eachCompName]
        billList = RemoveMinusOneBills(billList)
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
