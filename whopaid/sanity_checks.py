###############################################################################
## Author: Ashish Anand
## Date: 2012-09-06 Thu 03:07 PM
## Intent: To check if the bills issued to have corresponding name in customer
## table
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from Util.Config import GetOption
from Util.Decorators import timeThisFunction
from Util.Exception import MyException
from Util.Misc import PrintInBox, ParseDateFromString, IsDeliveredAssessFromStatus
from Util.Persistent import Persistent

from whopaid.automatic_notifications import SendAutomaticSmsReportsIfRequired
from whopaid.customers_info import GetAllCustomersInfo
from whopaid.json_data_generator import AskUberObserverToUploadJsons
from whopaid.mark_bills_as_paid import ReportBillWhichShouldBeMarkAsPaid
from whopaid.util_whopaid import GetAllCompaniesDict, SelectBillsAfterDate, ShrinkWorkingArea, GetWorkBookPath

from collections import defaultdict
import os

def SendAutomaticHeartBeat():
  #A heart beat will be sent every now and then whenever this function is called.
  #The receivers should not have any side effects and can expect back to back or no heartbeat at all. They should be resilient enough.
  CheckConsistency()
  AskUberObserverToUploadJsons()
  SendAutomaticSmsReportsIfRequired()
  ShrinkWorkingArea()
  return



class PersistentInfoForConsistencyCheck(Persistent):
  identifier = "LastModifiedTimeForBillsFile"
  def __init__(self):
    super(self.__class__, self).__init__(self.__class__.__name__)

  def isCheckRequired(self):
    if self.identifier not in self:
      return True #This is the first time it is called or persitent file was removed for some reason. Returning true so that check is made.
    return self[self.identifier] != os.path.getmtime(GetWorkBookPath())

  def saveNewFileTimeAtWhichConsistencyCheckWasDone(self):
    self[self.identifier] = os.path.getmtime(GetWorkBookPath())



def CheckConsistency():
  pcc = PersistentInfoForConsistencyCheck()

  if not pcc.isCheckRequired(): return #We successfully ran no need to check again.

  functionList = [
      CheckCustomerExistenceInDB,
      ReportMissingOrDuplicateBillsSince,
      CheckBillingCategory,
      CheckBillsCalculation,
      CheckCancelledAmount,
      CheckIfAnyBillsShouldBeMarkedAsPaid,
      CheckDocketLength,
      ]

  allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
  for eachFunc in functionList:
    eachFunc(allBillsDict)
  pcc.saveNewFileTimeAtWhichConsistencyCheckWasDone()
  return

def CheckIfAnyBillsShouldBeMarkedAsPaid(allBillsDict):
  msg = ReportBillWhichShouldBeMarkAsPaid()
  if msg:
    raise Exception(msg)

def CheckCancelledAmount(allBillsDict):
  for (eachCompName, eachComp) in allBillsDict.iteritems():
    if eachCompName.lower().find("cancel") != -1:
      for eachBill in eachComp:
        if eachBill.amount != 0:
          raise MyException("Bill#{} dated {} is cancelled but has amount {}. It should be 0".format(eachBill.billNumber, str(eachBill.invoiceDate), eachBill.amount))


def CheckDocketLength(allBillsDict):
  MAPPING = {
      "first": 12,
      "overni": 10,
      "vrl": 9,
      "nitco": 11,
      "accura": 7,
      "profes": 10,
      }
  for (eachCompName, eachComp) in allBillsDict.iteritems():
    for eachBill in eachComp:
      if not eachBill.docketNumber: continue
      for courierName, length in MAPPING.items():
        if eachBill.courierName.lower().startswith(courierName):
          if len(eachBill.docketNumber) != length:
            raise MyException("Docket#{} might be wrong as it should have been exactly {} characters and it is {}".format(eachBill.docketNumber, length, len(eachBill.docketNumber)))
  return

def CheckBillingCategory(allBillsDict):
  for (eachCompName, eachComp) in allBillsDict.iteritems():
    eachComp.CheckEachBillsBillingCategory()

def CheckBillsCalculation(allBillsDict):
  for (eachCompName, eachComp) in allBillsDict.iteritems():
    eachComp.CheckEachBillsCalculation()

def ReportMissingOrDuplicateBillsSince(allBillsDict):
  d = defaultdict(list)

  #First sort all bills category wise
  for eachCompName, eachComp in allBillsDict.iteritems():
    for eachBill in eachComp:
      d[eachBill.billingCategory].append(eachBill)

  dateAsString = GetOption("CONSISTENCY_CHECK_SECTION", "CheckMissingBillsSinceDate")
  startDateObject = ParseDateFromString(dateAsString)

  def _GetFinancialYear(bill):
    return bill.invoiceDate.year if (bill.invoiceDate.month > 3) else (bill.invoiceDate.year - 1)

  #In each category try to find missing bills in the permissible date range
  for eachCategory in d:
    if eachCategory.lower() in ["tracking", "gr"]:
      continue
    billList = d[eachCategory]
    billList = SelectBillsAfterDate(billList, startDateObject)
    billList.sort(key=lambda b:b.invoiceDate) #TODO: Remove

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

  return

def CheckCustomerExistenceInDB(allBillsDict):

  """ Execute various checks which cross verify that data entered matches.
      1. Every bill issued should have an existing customer in database
      2. Every payment received should have an existing customer in database.
      3. More to come...
  """
  uniqueCompNames = set([eachComp for eachComp in allBillsDict.keys()])

  allCustInfo = GetAllCustomersInfo()

  for eachComp in uniqueCompNames:
    if eachComp not in allCustInfo.keys():
      raise MyException("M\s {} not found in customer database".format(eachComp))
  return

def CheckCourierStatusAssessmentIsCorrect():
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

#def CreateATestBill():
#  b = SingleBillRow()
#  b.compName = "Test"
#  b.billingCategory = "Central"
#  b.billNumber = 100
#  b.invoiceDate = ParseDateFromString("1Jan11")
#  b.materialDesc = "100 No TC Dies"
#  b.goodsValue = 2
#  b.tax = 2
#  b.courier = 2
#  b.amount = 6
#  b.courierName = "Overnite Parcels"
#  b.docketNumber = "To be inserted"
#  b.docketDate = datetime.date.today()
#  b.paymentReceivingDate = datetime.date.today()
#  return b

@timeThisFunction
def main():
  try:
    CheckConsistency()
    CheckCourierStatusAssessmentIsCorrect()
  except MyException as ex:
    PrintInBox(str(ex))

if __name__ == '__main__':
    main()
