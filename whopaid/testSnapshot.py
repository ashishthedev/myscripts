from Courier.courier_status import Shipment
from SanityChecks import CreateATestBill

def main():
    b = CreateATestBill()
    b.courierName = "Overnite Courier"
    b.docketNumber = "8037705270"
    s = Shipment(b)
    s.status = "Delivered to someone"
    s.saveAsDeliveredWithSnapshot()

    b2 = CreateATestBill()
    b2.courierName = "Trackon Courier"
    b2.docketNumber = "351288100"
    s2 = Shipment(b2)
    s2.status = "Delivered to someone"
    s2.saveAsDeliveredWithSnapshot()



if __name__ == '__main__':
    main()
