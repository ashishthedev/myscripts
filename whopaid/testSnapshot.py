#from whopaid.SanityChecks import CreateATestBill
from whopaid.UtilWhoPaid import SingleBillRow

from Util.Misc import ParseDateFromString

import datetime

def CreateATestBill():
  b = SingleBillRow()
  b.compName = "Test"
  b.billingCategory = "Central"
  b.billNumber = 100
  b.invoiceDate = ParseDateFromString("1Jan11")
  b.materialDesc = "100 No TC Dies"
  b.goodsValue = 2
  b.tax = 2
  b.courier = 2
  b.amount = 6
  b.courierName = "Overnite Parcels"
  b.docketNumber = "To be inserted"
  b.docketDate = datetime.date.today()
  b.paymentReceivingDate = datetime.date.today()
  b.paymentStatus = ""
  return b

class TestShipment():
    def __init__(self, testBill):
        from whopaid.Shipments import PersistentShipment
        self.ps = PersistentShipment(testBill)
        self.ps.saveInDB()
    def __enter__(self):
        return self.ps
    def __exit__(self, type, value, traceback):
        self.ps._removeFromDB()

def main():
    bill = CreateATestBill()
    bill.courierName = "Nitco"
    bill.docketNumber = "I725736"
    with TestShipment(bill) as ts:
        ts.Track()
        print("Status: {}".format(ts.status))
        ts.TakeNewSnapshot()


if __name__ == '__main__':
    main()
