
from Util.Config import GetOption
from Util.Misc import DD_MM_YYYY, DD_MMM_YYYY

from whopaid.CustomersInfo import GetAllCustomersInfo
from whopaid.KMPendingOrders import GetAllKMOrders, GetAllPendingOrders, GetAllReceivedOrders
from whopaid.UtilWhoPaid import SelectUnpaidBillsFrom, GetAllCompaniesDict, datex, RemoveTrackingBills
from whopaid.UtilFormC import QuarterlyClubbedFORMC

from collections import defaultdict
from pprint import pprint

import datetime
import json
import os

PMTAPPDIR = os.getenv("PMTAPPDIR")
DUMPING_DIR = os.path.join(PMTAPPDIR, "static", "dbs")
SMALL_NAME = GetOption("CONFIG_SECTION", "SmallName")
EXT = ".json"
PMT_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "PMT_" + SMALL_NAME + EXT))
ORDER_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "ORDER_" + SMALL_NAME + EXT))
KMO_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "KMORDER_" + SMALL_NAME + EXT))
FORMC_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "FORMC_" + SMALL_NAME + EXT))
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
  allOrdersDict = GetAllCompaniesDict().GetAllOrdersOfAllCompaniesAsDict()

  if os.path.exists(ORDER_JSON_FILE_NAME):
    os.remove(ORDER_JSON_FILE_NAME)

  data = list() #THis will have one day orders

  for eachCompName, orders in allOrdersDict.iteritems():
    for eachOrder in orders:
      singleOrder = dict()
      singleOrder["custName"] = eachOrder.compName
      singleOrder["md"] = eachOrder.materialDesc
      singleOrder["oNum"] = eachOrder.orderNumber
      singleOrder["oDate"] = DD_MM_YYYY(eachOrder.orderDate)
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
def _DumpPaymentsDB():
  allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
  allAdjustmentsDict = GetAllCompaniesDict().GetAllAdjustmentsOfAllCompaniesAsDict()
  allCustInfo = GetAllCustomersInfo()

  if os.path.exists(PMT_JSON_FILE_NAME):
    os.remove(PMT_JSON_FILE_NAME)

  data = {}
  allCustomers = []

  for eachCompName, eachCompBills in allBillsDict.iteritems():
    adjustmentList = allAdjustmentsDict.get(eachCompName, [])
    unpaidBillList = SelectUnpaidBillsFrom(eachCompBills)
    unpaidBillList = RemoveTrackingBills(unpaidBillList)
    oneCustomer = dict()
    oneCustomer["name"] = " {} | {}".format(eachCompName, SMALL_NAME)

    oneCustomerBills = []
    unpaidBillList = sorted(unpaidBillList, key=lambda b: datex(b.invoiceDate))
    for b in unpaidBillList:
      oneBill = {
          "bn" : b.billNumber,
          "bd": DD_MM_YYYY(datex(b.invoiceDate)),
          "cd": str(b.daysOfCredit),
          "ba":str(int(b.amount))
          }
      oneCustomerBills.append(oneBill)

    for a in adjustmentList:
      if a.adjustmentAccountedFor: continue
      oneAdjustment = {
          "bn": a.adjustmentNo or "-1",
          "bd": DD_MM_YYYY(datex(a.invoiceDate)),
          "cd": "0",
          "ba":str(int(a.amount))
          }
      oneCustomerBills.append(oneAdjustment) #For all practical purposes, an adjustment is treated as a bill with bill#-1

    oneCustomer["bills"] = oneCustomerBills
    oneCustomer["trust"] = allCustInfo.GetTrustForCustomer(eachCompName)

    if len(oneCustomerBills) > 0:
      allCustomers.append(oneCustomer)

  data["customers"] = allCustomers
  allPayments = GetAllCompaniesDict().GetAllPaymentsByAllCompaniesAsDict()
  recentPmtDate = max([p.pmtDate for comp, payments in allPayments.iteritems() for p in payments])
  compSmallName = GetOption("CONFIG_SECTION", "SmallName")
  data ["showVerbatimOnTop"] = "{} last pmt: {}".format(compSmallName, DD_MM_YYYY(recentPmtDate))

  with open(PMT_JSON_FILE_NAME, "w+") as f:
    json.dump(data, f, separators=(',',':'), indent=2)
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
  with open(KMO_JSON_FILE_NAME, "w+") as f:
    json.dump(data, f, separators=(',',':'), indent=2)
  return

def _DumpFormCData():
  allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()

  lastFormCEnteredOnDate = datetime.date(datetime.date.today().year-100, 1, 1) # Choose a really low date
  for eachComp, billList in allBillsDict.iteritems():
    t = [b.formCReceivingDate for b in billList if isinstance(b.formCReceivingDate, datetime.date)]
    if t:
      lastFormCEnteredOnDate = max(lastFormCEnteredOnDate, max(t))

  from copy import deepcopy
  formCReceivableDict = deepcopy(allBillsDict)
  for eachComp, billList in formCReceivableDict.items():
    newList = [b for b in billList if not b.formCReceivingDate and b.billingCategory.lower() in ["central"]] #inplace removal of bills
    if newList:
      formCReceivableDict[eachComp] = [b for b in billList if not b.formCReceivingDate and b.billingCategory.lower() in ["central"]] #inplace removal of bills
    else:
      del formCReceivableDict[eachComp]


  superSmallName = GetOption("CONFIG_SECTION", "SuperSmallName")

  def BillNoDateAmountDict(bill):
    singleBill = dict()
    singleBill["billNumber"] = int(bill.billNumber)
    singleBill["invoiceDateAsText"] = DD_MMM_YYYY(bill.invoiceDate)
    singleBill["invoiceDateIsoFormat"] = bill.invoiceDate.isoformat()
    singleBill["amount"] = str(int(bill.amount))
    return singleBill

  data = dict()
  allCompsFormC = list()
  for eachComp, billList in formCReceivableDict.iteritems():
    key = "{} | {}".format(eachComp, superSmallName)
    yd = QuarterlyClubbedFORMC(billList).GetYearDict()
    """
    year(dict)
     |--quarter(dict)
         |--bills(list)
    """
    for eachYear, quarters in yd.iteritems():
      for eachQuarter, billList in quarters.iteritems():
        quarters[eachQuarter]  = [BillNoDateAmountDict(bill) for bill in billList] #In place replacement of billList with smaller objcets containing only necessary data.
    singleCompFormC = {
        "key":key,
        "yd":yd,
        }

    allCompsFormC.append(singleCompFormC)

  data["allCompsFormC"] = allCompsFormC
  compSmallName = GetOption("CONFIG_SECTION", "SmallName")
  data ["showVerbatimOnTop"] = "{} : {}".format(compSmallName, DD_MM_YYYY(lastFormCEnteredOnDate))

  with open(FORMC_JSON_FILE_NAME, "w+") as f:
    json.dump(data, f, separators=(',',':'), indent=2)
  return
  return

def _DumpJSONDB():
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


def ParseOptions():
  import argparse
  parser = argparse.ArgumentParser()

  parser.add_argument("-gj", "--generate-json",
      dest='generateJson', action="store_true",
      default=False, help="If present, only then json data will be generated.")

  return parser.parse_args()

if __name__ == "__main__":
  args = ParseOptions()
  if args.generateJson:
    _DumpJSONDB()
