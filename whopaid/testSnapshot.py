from SanityChecks import TestShipment

def main():

    with TestShipment() as s:
        s.bill.courierName = "Bluedart"
        s.bill.docketNumber = "50256453052"
        s.Track()
        print("status: {}".format(s.status))
        #s.TakeNewSnapshot()


if __name__ == '__main__':
    main()
