from Shipments import PersistentShipment
from SanityChecks import CreateATestBill

def main():
    b = CreateATestBill()
    b.courierName = "Overnite Courier"
    b.docketNumber = "8039920840"
    s = PersistentShipment(b)
    s.Track()

    #b2 = CreateATestBill()
    #b2.courierName = "Trackon Courier"
    #b2.docketNumber = "364308506"
    #s2 = PersistentShipment(b2)
    #s2.Track()

    b3 = CreateATestBill()
    b3.courierName = "Overnite Courier"
    b3.docketNumber = "8039413572"
    s3 = PersistentShipment(b3)
    s3.Track()



if __name__ == '__main__':
    main()
