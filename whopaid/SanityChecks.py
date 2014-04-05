###############################################################################
## Author: Ashish Anand
## Date: 2012-09-06 Thu 03:07 PM
## Intent: To check if the bills issued to have corresponding name in customer 
## table
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from UtilWhoPaid import GetAllCompaniesDict, SelectBillsAfterDate, RemoveMinusOneBills
from CustomersInfo import GetAllCustomersInfo
from UtilException import MyException
from UtilMisc import PrintInBox, ParseDateFromString
from UtilDecorators import timeThisFunction
from UtilConfig import GetOption
from collections import defaultdict

def SendHeartBeat():
    #A new concept of heartbeat. Only limited to json uploads
    from OutstandingPmtJsonDBGeneration import UploadPmtData
    UploadPmtData()


def CheckConsistency():
    functionList = [
                    CheckCustomerExistenceInDB,
                    ReportMissingOrDuplicateBillsSince,
                    CheckBillingCategory,
                    CheckBillsCalculation,
                    CheckCancelledAmount,
                   ]

    allCompaniesDict = GetAllCompaniesDict()
    for eachFunc in functionList:
        eachFunc(allCompaniesDict)
    return

def CheckCancelledAmount(allCompaniesDict):
    for (eachCompName, eachComp) in allCompaniesDict.items():
        if eachCompName.lower().find("cancel") != -1:
            for eachBill in eachComp:
                if eachBill.billAmount != 0:
                    raise MyException("Bill#{} dated {} is cancelled but has amount {}. It should be 0".format(eachBill.billNumber, str(eachBill.invoiceDate), eachBill.billAmount))


def CheckBillingCategory(allCompaniesDict):
    for (eachCompName, eachComp) in allCompaniesDict.items():
        eachComp.CheckEachBillsBillingCategory()

def CheckBillsCalculation(allCompaniesDict):
    for (eachCompName, eachComp) in allCompaniesDict.items():
        eachComp.CheckEachBillsCalculation()

def ReportMissingOrDuplicateBillsSince(allCompaniesDict):
    d = defaultdict(list)

    #First sort all bills category wise
    for eachCompName, eachComp in allCompaniesDict.items():
        for eachBill in eachComp:
            d[eachBill.billingCategory].append(eachBill)

    dateAsString = GetOption("CONSISTENCY_CHECK_SECTION", "CheckMissingBillsSinceDate")
    startDateObject = ParseDateFromString(dateAsString)

    def _GetFinancialYear(bill):
        return bill.invoiceDate.year if (bill.invoiceDate.month > 3) else (bill.invoiceDate.year - 1)

    #In each category try to find missing bills in the permissible date range
    for eachCategory in d:
        if eachCategory.lower() in ["tracking", ]:
            continue
        billList = RemoveMinusOneBills(d[eachCategory])
        billList = SelectBillsAfterDate(billList, startDateObject)
        billList.sort(key=lambda b:b.billNumber) #TODO: Remove

        if len(billList) < 1:
            continue  # i.e. if there is only one bill

        #Categorize bills year wise
        yearwiseDict = defaultdict(list)
        for eachBill in billList:
            yearwiseDict[_GetFinancialYear(eachBill)].append(int(eachBill.billNumber))

        #Try to find a missing bills in one year financial year span
        for eachYear in yearwiseDict:
            listOfBillsInOneYear = yearwiseDict[eachYear]
            minBill = min(listOfBillsInOneYear)
            maxBill = max(listOfBillsInOneYear)

            for billNumber in range(int(minBill) + 1, int(maxBill)):
                if billNumber not in listOfBillsInOneYear:
                    raise MyException("Bill Number: %s missing in category %s in year starting from 1-Apr-%s" % (str(billNumber), eachCategory, eachYear))
                if listOfBillsInOneYear.count(billNumber) > 1:
                    raise MyException("Bill Number: %s is entered twice in category %s in year starting from 1-Apr-%s" % (str(billNumber), eachCategory, eachYear))


def CheckCustomerExistenceInDB(allCompaniesDict):

    """ Execute various checks which cross verify that data entered matches.
        1. Every bill issued should have an existing customer in database
        2. Every payment received should have an existing customer in database.
        3. More to come...
    """
    uniqueCompNames = set([eachComp for eachComp in allCompaniesDict])

    allCustInfo = GetAllCustomersInfo()

    for eachComp in uniqueCompNames:
        if eachComp not in allCustInfo.keys():
            raise MyException("M\s {} not found in customer database".format(eachComp))
    return

def CheckCourierStatusAssessmentIsCorrect():
    from track_shipments import IsDeliveredAssessFromStatus
    test_base = [
            ("Parcel was not delivered", False),
            ("Parcel was delivered", True),
            ("Status of awb no not updated", False),
            ("Parcel returned back to origin", False),
            ("Parcel returned back to origin", False),
            ("Delivered Friday", True),
            ("Undelivered: Thursday", False),
            ]
    for eachStr, expectedDeliveryStatus in test_base:
        if expectedDeliveryStatus != IsDeliveredAssessFromStatus(eachStr):
            raise Exception("Our algorithm is faulty for the following string:\n{}".format(eachStr))

class TestShipment():
    def __init__(self, testBill):
        from Shipments import PersistentShipment
        self.ps = PersistentShipment(testBill)
        self.ps.saveInDB()
    def __enter__(self):
        return self.ps
    def __exit__(self, type, value, traceback):
        self.ps._removeFromDB()

def CreateATestBill():
    from UtilWhoPaid import SingleBill
    import datetime
    b = SingleBill()
    b.compName = "Test"
    b.billingCategory = "Central"
    b.billNumber = 100
    b.invoiceDate = ParseDateFromString("1Jan11")
    b.materialDesc = "100 No TC Dies"
    b.goodsValue = 2
    b.tax = 2
    b.courier = 2
    b.billAmount = 6
    b.courierName = "Overnite Parcels"
    b.docketNumber = "8037705351"
    b.docketDate = datetime.date.today()
    return b

@timeThisFunction
def main():
    try:
        CheckConsistency()
        CheckCourierStatusAssessmentIsCorrect()
    except MyException as ex:
        PrintInBox(str(ex))

if __name__ == '__main__':
    main()
