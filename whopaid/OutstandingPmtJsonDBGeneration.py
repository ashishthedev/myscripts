import os
import json
from UtilConfig import GetOption
from UtilWhoPaid import SelectUnpaidBillsFrom, GetAllCompaniesDict, datex, RemoveTrackingBills
from UtilMisc import DD_MM_YYYY

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
        bills:[
            { billNumber:"1", billDate:"1-Mar-14", billAmount:"1400"},
            { billNumber:"2", billDate:"2-Mar-14", billAmount:"2400"},
            ]
    },
    {
        name:"CostaCoffee | Omega",
        bills:[
            { billNumber:"3", billDate:"3-Mar-14", billAmount:"3400"},
            { billNumber:"4", billDate:"4-Mar-14", billAmount:"4400"},
            ]
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
        oneCustomerBills = []
        unpaidBillList = sorted(unpaidBillList, key=lambda b: datex(b.invoiceDate))
        for b in unpaidBillList:
            oneBill = {
                    "bn" : b.billNumber,
                    "bd": DD_MM_YYYY(datex(b.invoiceDate)),
                    "cd": b.daysOfCredit,
                    "ba":str(int(b.billAmount))
                    }
            oneCustomerBills.append(oneBill)
        oneCustomer["bills"] = oneCustomerBills

        if len(oneCustomerBills) > 0:
            allCustomers.append(oneCustomer)

    data["customers"] = sorted(allCustomers, key=lambda c: c["name"])

    with open(JSON_FILE_NAME, "w+") as f:
        json.dump(data, f, separators=(',',':'), indent=2)

def UploadPmtData():
    import subprocess
    pushFile = os.path.abspath(os.path.join(PMTAPPDIR, "utils", "push.py"))
    if not os.path.exists(pushFile):
        raise Exception("{} does not exist".format(pushFile))
    e = 'moc.slootdnaseiddradnats@repoleved'
    v='dev'
    cmd = "python {pushFile} --email={e} --version={v} --oauth2".format(pushFile=pushFile, e=e[::-1], v=v)
    subprocess.check_call(cmd)


#if __name__ == "__main__":
#    DumpJSONDB()
# Unforutnately, it is being invoked through child process and name is actually
# _main__. So being invoked twice
