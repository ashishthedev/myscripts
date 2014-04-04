import os
import json
from UtilConfig import GetOption
from UtilWhoPaid import SelectUnpaidBillsFrom, GetAllCompaniesDict, datex, RemoveTrackingBills, floatx
from UtilMisc import DD_MM_YYYY
from CustomersInfo import GetAllCustomersInfo

PMTAPPDIR = os.getenv("PMTAPPDIR")
DUMPING_DIR = os.path.join(PMTAPPDIR, "static", "dbs")
SMALL_NAME = GetOption("CONFIG_SECTION", "SmallName")
EXT = ".json"
JSON_FILE_NAME = os.path.abspath(os.path.join(DUMPING_DIR, SMALL_NAME + EXT))

"""
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
def DumpJSONDB():
    allCompaniesDict = GetAllCompaniesDict()

    if os.path.exists(JSON_FILE_NAME):
        os.remove(JSON_FILE_NAME)

    data = {}
    allCustomers = []

    for eachCompName, eachCompBills in allCompaniesDict.items():
        unpaidBillList = SelectUnpaidBillsFrom(eachCompBills)
        unpaidBillList = RemoveTrackingBills(unpaidBillList)
        oneCustomer = dict()
        oneCustomer["name"] = " {} | {}".format(eachCompName, SMALL_NAME)

        oneCustomer["trust"] = str(floatx(GetAllCustomersInfo().GetTrustForCustomer(eachCompName)))
        if not oneCustomer["trust"]: raise Exception("M/s {} have 0 trust. Please fix the database.".format(eachCompName))

        oneCustomerBills = []
        unpaidBillList = sorted(unpaidBillList, key=lambda b: datex(b.invoiceDate))
        for b in unpaidBillList:
            oneBill = {
                    "bn" : b.billNumber,
                    "bd": DD_MM_YYYY(datex(b.invoiceDate)),
                    "cd": str(b.daysOfCredit),
                    "ba":str(int(b.billAmount))
                    }
            oneCustomerBills.append(oneBill)
        oneCustomer["bills"] = oneCustomerBills

        if len(oneCustomerBills) > 0:
            allCustomers.append(oneCustomer)

    data["customers"] = sorted(allCustomers, key=lambda c: c["name"])

    with open(JSON_FILE_NAME, "w+") as f:
        json.dump(data, f, separators=(',',':'), indent=2)
    return

#def UploadPmtData():
#    import subprocess
#    pushFile = os.path.abspath(os.path.join(PMTAPPDIR, "utils", "push.py"))
#    if not os.path.exists(pushFile):
#        raise Exception("{} does not exist".format(pushFile))
#    e = 'moc.slootdnaseiddradnats@repoleved'
#    v='dev'
#    cmd = "python {pushFile} --email={e} --version={v} --oauth2".format(pushFile=pushFile, e=e[::-1], v=v)
#    subprocess.check_call(cmd)
#

if __name__ == "__main__":
    DumpJSONDB()
