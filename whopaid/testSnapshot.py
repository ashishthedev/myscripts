#from whopaid.SanityChecks import CreateATestBill

from Util.Misc import ParseDateFromString, IsDeliveredAssessFromStatus, PrintInBox

from whopaid.util_whopaid import SingleBillRow

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
    bill.courierName = "FedEx Express"

    bill.docketNumber = "805854193624"
    bill.docketNumber = "805854195513"
    with TestShipment(bill) as ts:
      ts.Track()
      print("Status of test shipment: {}".format(ts.status))
      ts.status = "Delivered testing"
      if IsDeliveredAssessFromStatus(ts.status):
        PrintInBox("Taking Snapshot")
        ts.TakeNewSnapshot()
      else:
        PrintInBox("Test shipment not delivered. Not taking snapshot")


if __name__ == '__main__':
    main()
