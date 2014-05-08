import os
import json
from UtilConfig import GetOption
from UtilWhoPaid import SelectUnpaidBillsFrom, GetAllCompaniesDict, datex, RemoveTrackingBills
from UtilMisc import DD_MM_YYYY
from CustomersInfo import GetAllCustomersInfo

PMTAPPDIR = os.getenv("PMTAPPDIR")
DUMPING_DIR = os.path.join(PMTAPPDIR, "static", "dbs")
SMALL_NAME = GetOption("CONFIG_SECTION", "SmallName")
EXT = ".json"
PMT_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "PMT_" + SMALL_NAME + EXT))
ORDER_JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, "ORDER_" + SMALL_NAME + EXT))
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

    for eachCompName, orders in allOrdersDict.items():
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

    for eachCompName, eachCompBills in allBillsDict.items():
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

    with open(PMT_JSON_FILE_NAME, "w+") as f:
        json.dump(data, f, separators=(',',':'), indent=2)
    return

def _DumpJSONDB():
    _DumpPaymentsDB()
    _DumpOrdersDB()


def UploadAppWithNewData():
    import subprocess
    pushFile = os.path.abspath(os.path.join(PMTAPPDIR, "utils", "push.py"))
    if not os.path.exists(pushFile):
        raise Exception("{} does not exist".format(pushFile))
    e = 'moc.slootdnaseiddradnats@repoleved'
    v='live'
    cmd = "python {pushFile} --email={e} --version={v} --oauth2".format(pushFile=pushFile, e=e[::-1], v=v)
    subprocess.check_call(cmd)



if __name__ == "__main__":
  _DumpJSONDB()
