
from Util.Config import GetOption
from Util.Misc import DD_MM_YYYY, DD_MMM_YYYY, MyException

from whopaid.customers_info import GetAllCustomersInfo, GetToCCBCCForFORMCforCompany
from whopaid.customer_group_info import GetToCCBCCListforGroup, PrepareMailContentForThisGroup, HasPaymentReminderEmailsForGroup, TotalDueForGroupAsInt, HasPaymentReminderEmailsForCompany, HasFormCReminderEmailsForCompany
from whopaid.km_pending_orders import GetAllKMOrders, GetAllPendingOrders, GetAllReceivedOrders
from whopaid.util_whopaid import GetAllCompaniesDict, datex, GetPayableBillsAndAdjustmentsForThisComp, AllCompanyGroupNamesWhichHaveBeenBilledInPast
from whopaid.util_formc import QuarterlyClubbedFORMC, GetHTMLForFORMCforCompany

from collections import defaultdict

import datetime
import json
import os

ALL_COMPANIES_DICT = GetAllCompaniesDict()
ALL_CUST_INFO = GetAllCustomersInfo()

PMTAPPDIR = os.getenv("PMTAPPDIR")
DUMPING_DIR = os.path.join(PMTAPPDIR, "static", "dbs")
SMALL_NAME = GetOption("CONFIG_SECTION", "SmallName")
EXT = ".json"
PMT_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "PMT" + "_" + SMALL_NAME + EXT))
ORDER_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "ORDER" + "_" + SMALL_NAME + EXT))
KMO_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "KMORDER" + "_" + SMALL_NAME + EXT))
FORMC_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "FORMC" + "_" + SMALL_NAME + EXT))
SHIPMENT_STATUS_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "SHIPSTATUS" + "_" + SMALL_NAME + EXT))
CUST_INFO_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "CUST_INFO" + "_" + SMALL_NAME + EXT))
"""
OrderDB:
data =
[
// Each {} is an object in a list and represents a collection of orders on
// particular date
    {
        date: "21-Apr-2014",
        orders:[
          {
            "custName":"AWT",
            "md":"15x13x.77=30pc; .83=20pc; .90=20pc; PO#AWT/14-15/",
            "oNum":"AWT/14-15/0026"
          },
          {
            "custName":"MWW",
            "md":"13x10x.765=100pc; .96=35",
            "oNum":"PUR-27/14"
          }
        ],
    },
    {
        date: "22-Apr-2014",
        orders:[
          {
            "custName":"AWT",
            "md":"15x13x.77=30pc; .83=20pc; .90=20pc; PO#AWT/14-15/",
            "oNum":"AWT/14-15/0026"
          },
          {
            "custName":"MWW",
            "md":"13x10x.765=100pc; .96=35",
            "oNum":"PUR-27/14"
          }
        ]
        }
  }
]
"""

def _DumpOrdersDB():
  allOrdersDict = ALL_COMPANIES_DICT.GetAllOrdersOfAllCompaniesAsDict()

  if os.path.exists(ORDER_JSON_FILE_NAME):
    os.remove(ORDER_JSON_FILE_NAME)

  data = list() #THis will have one day orders

  for eachCompName, orders in allOrdersDict.iteritems():
    for eachOrder in orders:
      singleOrder = dict()
      singleOrder["compOffName"] = ALL_CUST_INFO.GetCompanyOfficialName(eachOrder.compName)
      singleOrder["materialDesc"] = eachOrder.materialDesc
      singleOrder["orderNumber"] = eachOrder.orderNumber
      singleOrder["orderDate"] = DD_MM_YYYY(eachOrder.orderDate)
      singleOrder["orderDateISOFormat"] = eachOrder.orderDate.isoformat()
      data.append(singleOrder) #Just dump this single order there and we will club them date wise while generating final json

  with open(ORDER_JSON_FILE_NAME, "w+") as f:
    json.dump(data, f, separators=(',',':'), indent=2)
  return



"""
paymentDB
data=
{
    customers:[
    {
        name:"Starbucks | SDAT",
        trust: .5,
        bills:[
            { bn:"1", bd:"1-Mar-14", ba:"1400"},
            { bn:"2", bd:"2-Mar-14", ba:"2400"},
            ],
        trust: .5,
    },
    {
        name:"CostaCoffee | Omega",
        trust: .5,
        bills:[
            { bn:"3", bd:"3-Mar-14", ba:"3400"},
            { bn:"4", bd:"4-Mar-14", ba:"4400"},
            ],
    }
    ]
}

"""

def ProcessAndReturnSingleGroup(grpName):
  singleGroup = dict()
  #singleGroup["grpName"] = grpName
  singleGroup["grpName"] = " {} | {}".format(grpName, SMALL_NAME)
  singleGroup["companies"] = []


  for eachCompName in ALL_CUST_INFO.GetListOfCompNamesInThisGroup(grpName):
    unpaidBillList, adjustmentList = GetPayableBillsAndAdjustmentsForThisComp(eachCompName)

    oneComp = dict()
    #oneComp["name"] = " {} | {}".format(eachCompName, SMALL_NAME)
    oneComp["name"] = eachCompName

    oneCompAdjAndBills = []
    unpaidBillList = sorted(unpaidBillList, key=lambda b: datex(b.invoiceDate))
    for b in unpaidBillList:
      oneBill = {
          "bn": b.billNumber,
          "bd": DD_MM_YYYY(datex(b.invoiceDate)),
          "cd": str(b.daysOfCredit),
          "ba": str(int(b.amount))
          }
      oneCompAdjAndBills.append(oneBill)

    if adjustmentList:
      for a in adjustmentList:
        oneAdjustment = {
            "bn": a.adjustmentNo or "-1",
            "bd": DD_MM_YYYY(datex(a.invoiceDate)),
            "cd": "0",
            "ba": str(int(a.amount))
            }
        oneCompAdjAndBills.append(oneAdjustment) #For all practical purposes, an adjustment is treated as a bill with bill#-1

    oneComp["bills"] = oneCompAdjAndBills
    oneComp["trust"] = ALL_CUST_INFO.GetTrustForCustomer(eachCompName)

    if len(oneCompAdjAndBills) > 0:
      singleGroup["companies"].append(oneComp)

  if len(singleGroup["companies"]) > 0:
    if not HasPaymentReminderEmailsForGroup(grpName):
      singleGroup["noEmailReason"] = "No emails present"
    else:
      args = type('args', (object,), {'first_line': "", 'first_line_bold': False, 'second_line': "", 'last_line': "", 'last_line_bold': False, 'kaPerson': "", 'doNotShowLetterDate': True, 'doNotShowCreditDays': False})
      singleGroup["emailHTML"] = PrepareMailContentForThisGroup(grpName, args)
      singleGroup["toMailList"], singleGroup["ccMailList"], singleGroup["bccMailList"] = GetToCCBCCListforGroup(grpName)
      singleGroup["testToMailList"] = singleGroup["ccMailList"]
      singleGroup["senderCompany"] = GetOption("CONFIG_SECTION", 'SmallName')
      singleGroup["emailSubject"] = "Payment Request (Rs.{})".format(TotalDueForGroupAsInt(grpName))
      singleGroup["testEmailSubject"] = "[Testing] Payment Request (Rs.{})".format(TotalDueForGroupAsInt(grpName))

  return singleGroup

def _DumpPaymentsDB():
  if os.path.exists(PMT_JSON_FILE_NAME):
    os.remove(PMT_JSON_FILE_NAME)

  data = {}
  allGroups = []

  for grpName in AllCompanyGroupNamesWhichHaveBeenBilledInPast():
    singleGroup = ProcessAndReturnSingleGroup(grpName)
    if len(singleGroup["companies"]) > 0:
      allGroups.append(singleGroup)

  data["compGroups"] = allGroups
  allPayments = ALL_COMPANIES_DICT.GetAllPaymentsByAllCompaniesAsDict()
  recentPmtDate = max([p.pmtDate for comp, payments in allPayments.iteritems() for p in payments])
  compSmallName = GetOption("CONFIG_SECTION", "SmallName")
  data ["showVerbatimOnTop"] = "{} last pmt: {}".format(compSmallName, DD_MM_YYYY(recentPmtDate))
  data ["showVerbatimOnTopDateISO"] = { compSmallName : (DD_MM_YYYY(recentPmtDate), recentPmtDate.isoformat())}

  with open(PMT_JSON_FILE_NAME, "w+") as f:
    json.dump(data, f, separators=(',',':'), indent=2)
  return


def _DumpCustData():
  from customers_info import GenerateCustomerInfoJsonNodesFile
  GenerateCustomerInfoJsonNodesFile()
  jsonFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), GetOption("CONFIG_SECTION", "CustomerInfoJson"))

  with open(jsonFileName) as j:
    with open(CUST_INFO_JSON_FILE_NAME, "w") as f:
      json.dump(json.load(j), f, indent=2)
  return

def _DumpKMPendingOrdersDB():
  po = GetAllKMOrders()
  po = GetAllPendingOrders(po)

  if os.path.exists(KMO_JSON_FILE_NAME):
    os.remove(KMO_JSON_FILE_NAME)

  data = dict()
  allKMOrders = defaultdict(list)
  superSmallName = GetOption("CONFIG_SECTION", "SuperSmallName")

  for o in po:
    key =  "{} | {}".format(o.pelletSize, superSmallName)
    singleKMOrder = dict()
    singleKMOrder["poDateISOFormat"] = o.poDate.isoformat()
    singleKMOrder["poDateAsNormalText"] = DD_MMM_YYYY(o.poDate.isoformat())#TODO: Use a different name for this field and fix mobile code too.
    singleKMOrder["pelletSize"] = key
    singleKMOrder["boreSize"] = o.boreSize
    singleKMOrder["grade"] = o.grade
    singleKMOrder["quantity"] = o.quantity
    singleKMOrder["deliveryInstructions"] = o.deliveryInstructions
    singleKMOrder["oaNumber"] = o.oaNumber
    allKMOrders[key].append(singleKMOrder) #Just dump this single order there and we will club them pelletSize wise while generating final json

  ro = GetAllKMOrders()
  ro = GetAllReceivedOrders(ro)

  data['allKMOrders'] = allKMOrders
  lastInvoiceDate = max([o.invoiceDate for o in ro])
  compSmallName = GetOption("CONFIG_SECTION", "SmallName")
  data ["showVerbatimOnTop"] = "{} : {}".format(compSmallName, DD_MM_YYYY(lastInvoiceDate))
  data ["showVerbatimOnTopDateISO"] = { compSmallName : lastInvoiceDate.isoformat()}
  with open(KMO_JSON_FILE_NAME, "w+") as f:
    json.dump(data, f, separators=(',',':'), indent=2)
  return

def _SingleBillDictWithBillNoDateAmount(bill):
  singleBill = dict()
  singleBill["billNumber"] = int(bill.billNumber)
  singleBill["invoiceDateAsText"] = DD_MMM_YYYY(bill.invoiceDate)
  singleBill["invoiceDateIsoFormat"] = bill.invoiceDate.isoformat()
  singleBill["amount"] = str(int(bill.amount))
  return singleBill

def ProcessAndReturnSingleCompFormC(compName, billList):
  #BIllList is not required. Refactor

  superSmallName = GetOption("CONFIG_SECTION", "SuperSmallName")
  key = "{} | {}".format(compName, superSmallName)
  yd = QuarterlyClubbedFORMC(billList).GetYearDict()
  """
  year(dict)
   |--quarter(dict)
       |--bills(list)
  """
  for eachYear, quarters in yd.iteritems():
    for eachQuarter, billList in quarters.iteritems():
      quarters[eachQuarter]  = [_SingleBillDictWithBillNoDateAmount(bill) for bill in billList] #In place replacement of billList with smaller objcets containing only necessary data.

  singleCompFormC = dict()
  singleCompFormC["key"] = key
  singleCompFormC["yd"] = yd
  companyOfficialName = ALL_CUST_INFO.GetCompanyOfficialName(compName)
  if not companyOfficialName:
    raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

  if not HasPaymentReminderEmailsForCompany(compName) and not HasFormCReminderEmailsForCompany(compName):
    singleCompFormC["noEmailReason"] = "No emails present"
  else:

    args = type('args', (object,), {'sdate':"", 'edate': "", 'letterHead': "", "kindAttentionPerson": "", "additional_line":"", "remarksColumn": False,  })
    singleCompFormC["emailHTML"] = GetHTMLForFORMCforCompany(compName, args)
    singleCompFormC["toMailList"], singleCompFormC["ccMailList"], singleCompFormC["bccMailList"] = GetToCCBCCForFORMCforCompany(compName)
    singleCompFormC["senderCompany"] = GetOption("CONFIG_SECTION", 'SmallName')
    singleCompFormC["emailSubject"] = "FORM-C request - M/s {} - from M/s {}".format(companyOfficialName, GetOption("CONFIG_SECTION", 'CompName'))

  return singleCompFormC

def _DumpShipmentStatusData():
  jsonFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), GetOption("CONFIG_SECTION", "ShipmentsJson"))

  jsonData = {}
  with open(jsonFileName) as j:
    jsonData = json.load(j)

  SHOW_STATUS_FOR_LAST_N_DAYS = int(GetOption("CONFIG_SECTION", "ShowShipmentStatusForNDays"))

  jsonData = [x for x in jsonData if int(x["daysPassed"]) <= SHOW_STATUS_FOR_LAST_N_DAYS]

  data = dict()

  compSmallName = GetOption("CONFIG_SECTION", "SmallName")
  firstInvoiceDate = datetime.date.today() - datetime.timedelta(days=SHOW_STATUS_FOR_LAST_N_DAYS)
  data ["showVerbatimOnTop"] = "{} : {}".format(compSmallName, DD_MM_YYYY(firstInvoiceDate))

  data['allShipments'] = jsonData
  with open(SHIPMENT_STATUS_JSON_FILE_NAME, "w") as f:
    json.dump(data, f, indent=2)
  return

def _DumpFormCData():
  allBillsDict = ALL_COMPANIES_DICT.GetAllBillsOfAllCompaniesAsDict()

  lastFormCEnteredOnDate = datetime.date(datetime.date.today().year-100, 1, 1) # Choose a really low date
  for eachComp, billList in allBillsDict.iteritems():
    t = [b.formCReceivingDate for b in billList if isinstance(b.formCReceivingDate, datetime.date)]
    if t:
      lastFormCEnteredOnDate = max(lastFormCEnteredOnDate, max(t))

  from copy import deepcopy
  formCReceivableDict = deepcopy(allBillsDict)
  for eachComp, billList in formCReceivableDict.items():
    formCReceivableDict[eachComp] = [b for b in billList if not b.formCReceivingDate and b.billingCategory.lower() in ["central"]] #inplace removal of bills
    if not formCReceivableDict[eachComp]:
      del formCReceivableDict[eachComp]

  allCompsFormC = list()
  for eachComp, billList in formCReceivableDict.iteritems():
    singleCompFormC = ProcessAndReturnSingleCompFormC(eachComp, billList)
    allCompsFormC.append(singleCompFormC)

  data = dict()
  data["allCompsFormC"] = allCompsFormC
  compSmallName = GetOption("CONFIG_SECTION", "SmallName")
  data ["showVerbatimOnTop"] = "{} : {}".format(compSmallName, DD_MM_YYYY(lastFormCEnteredOnDate))

  with open(FORMC_JSON_FILE_NAME, "w+") as f:
    json.dump(data, f, separators=(',',':'), indent=2)
  return
  return

def _DumpJSONDB():
  _DumpCustData()
  _DumpShipmentStatusData()
  _DumpFormCData()
  _DumpKMPendingOrdersDB()
  _DumpPaymentsDB()
  _DumpOrdersDB()
  return


def AskUberObserverToUploadJsons():
  #TODO:There is an extremely tight coupling within pmtapp and jsongenerator. For ex jsongenerator has to know the path of pushfile to execute it. Need a more elegant way to invoke uploads.
  import subprocess
  pushFile = os.path.abspath(os.path.join(PMTAPPDIR, "utils", "push.py"))
  if not os.path.exists(pushFile):
    raise Exception("{} does not exist".format(pushFile))
  e = 'moc.slootdnaseiddradnats@repoleved'
  v='live'
  cmd = "python \"{pushFile}\" --email={e} --version={v} --oauth2".format(pushFile=pushFile, e=e[::-1], v=v)
  print("Running: {}".format(cmd))
  subprocess.check_call(cmd)
  return

def ShowCoordinates():

  allBillsDict = ALL_COMPANIES_DICT.GetAllBillsOfAllCompaniesAsDict()
  uniqueCompNames = set([eachComp for eachComp in allBillsDict.keys()])

  for eachComp in uniqueCompNames:
      lat = ALL_CUST_INFO.GetCompanyLatitude(eachComp)
      lng = ALL_CUST_INFO.GetCompanyLongitude(eachComp)
      if lat and lng:
          print("{},{}".format(lat, lng))

  return


def ParseOptions():
  import argparse
  parser = argparse.ArgumentParser()

  parser.add_argument("-coords", "--generate-coordinates",
      dest='generateCoordinates', action="store_true",
      default=False, help="If present, coordinates will be generated.")

  parser.add_argument("-gj", "--generate-json",
      dest='generateJson', action="store_true",
      default=False, help="If present, only then json data will be generated.")

  return parser.parse_args()

if __name__ == "__main__":
  args = ParseOptions()
  if args.generateCoordinates:
    ShowCoordinates()
  if args.generateJson:
    _DumpJSONDB()
