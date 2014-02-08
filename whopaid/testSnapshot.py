from SanityChecks import TestShipment, CreateATestBill

def main():


    bill = CreateATestBill()
    bill.courierName = "Lalji mulji"
    bill.docketNumber = "10246635"
    with TestShipment(bill) as ts:
        ts.Track()
        print("Status: {}".format(ts.status))
        #s.TakeNewSnapshot()


if __name__ == '__main__':
    main()
