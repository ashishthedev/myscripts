from Shipments import PersistentShipment
from SanityChecks import CreateATestBill

def main():
    b = CreateATestBill()
    b.courierName = "Professional Courier"
    b.docketNumber = "NDA3290046"
    s = PersistentShipment(b)
    s.Track()
    s._removeFromDB()

    #b2 = CreateATestBill()
    #b2.courierName = "Trackon Courier"
    #b2.docketNumber = "364308506"
    #s2 = PersistentShipment(b2)
    #s2.Track()

    #b3 = CreateATestBill()
    #b3.courierName = "Overnite Courier"
    #b3.docketNumber = "8039413572"
    #s3 = PersistentShipment(b3)
    #s3.Track()

    #b4 = CreateATestBill()
    #b4.courierName = "Bluedart Courier"
    #b4.docketNumber = "50256358073" #WNW
    #b4.docketNumber = "50250786972" #Sys
    #s4 = PersistentShipment(b4)
    #s4.Track()



if __name__ == '__main__':
    main()
