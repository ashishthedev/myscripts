#from whopaid.SanityChecks import CreateATestBill

from Util.Misc import ParseDateFromString, IsDeliveredAssessFromStatus, PrintInBox

from whopaid.util_whopaid import SingleBillRow

import datetime

def CreateATestBill():
  b = SingleBillRow()
  b.compName = "Test"
  b.billingCategory = "Central"
  b.billNumber = 100
  b.invoiceDate = datetime.date.today()
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
        from whopaid.shipments import PersistentShipments
        ps = PersistentShipments()
        self.ps = ps.GetOrCreateShipmentForBill(testBill)
        self.ps.save()
    def __enter__(self):
        return self.ps
    def __exit__(self, type, value, traceback):
        self.ps._removeFromDB()

def main():
    bill = CreateATestBill()
    bill.courierName = "DTDC"
    bill.docketNumber = "D28336181"
    bill.docketNumber = "Z89989669"
    #8051692143
    with TestShipment(bill) as ts:
      #ts.SetEDD("26/03/2015")
      ts.TrackAndSave()
      print("Status of test shipment: {}".format(ts.status))
      from pprint import pprint; pprint("ts: {}".format(vars(ts)))
      print("IS Delivered:{}".format(ts.isDelivered))
      #if IsDeliveredAssessFromStatus(ts.status):
      #  PrintInBox("Taking Snapshot")
      #  ts.TakeNewSnapshot()
      #else:
      #  PrintInBox("Test shipment not delivered. Not taking snapshot")


if __name__ == '__main__':
    main()
