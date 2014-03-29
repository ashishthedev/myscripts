import os
import json
from UtilConfig import GetOption
from UtilWhoPaid import SelectUnpaidBillsFrom, GetAllCompaniesDict, datex
from UtilMisc import DD_MM_YYYY

PMTAPPDIR = os.getenv("PMTAPPDIR")
DUMPING_DIR = os.path.join(PMTAPPDIR, "static", "dbs")
SMALL_NAME = GetOption("CONFIG_SECTION", "SmallName")
EXT = ".json"
FINAL_JSON_FILE = os.path.join(DUMPING_DIR, SMALL_NAME + EXT)

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
    #TODO: Check from datestamp if dumping is required
    allCompaniesDict = GetAllCompaniesDict()

    if os.path.exists(FINAL_JSON_FILE):
        os.remove(FINAL_JSON_FILE)

    data = {}
    allCustomers = []

    for eachCompName, eachCompBills in allCompaniesDict.items():
        unpaidBillList = SelectUnpaidBillsFrom(eachCompBills)
        oneCustomer = dict()
        oneCustomer["name"] = " {} | {}".format(eachCompName, SMALL_NAME)
        oneCustomerBills = []
        unpaidBillList = sorted(unpaidBillList, key=lambda b: b.billNumber)
        for b in unpaidBillList:
            oneBill = {
                    "bn" : b.billNumber,
                    "bd": DD_MM_YYYY(datex(b.invoiceDate)),
                    "ba":str(int(b.billAmount))
                    }
            oneCustomerBills.append(oneBill)
        oneCustomer["bills"] = oneCustomerBills

        if len(oneCustomerBills) > 0:
            allCustomers.append(oneCustomer)

    data["customers"] = sorted(allCustomers, key=lambda c: c["name"])

    with open(FINAL_JSON_FILE, "w") as f:
        json.dump(data, f, separators=(',',':'), indent=2)

def UploadPmtData():
    #TODO: Decide when to upload
    import subprocess
    PMTAPPDIR
    pushFile = os.path.abspath(os.path.join(PMTAPPDIR, "utils", "push.py"))
    if not os.path.exists(pushFile):
        raise Exception("{} does not exist".format(pushFile))
    e = 'moc.slootdnaseiddradnats@repoleved'
    v='dev'
    cmd = "python {pushFile} --email={e} --version={v} --oauth2".format(pushFile=pushFile, e=e[::-1], v=v)
    print("cmd=\n{}".format(cmd))
    subprocess.check_call(cmd)


if __name__ == "__main__":
    DumpJSONDB()
