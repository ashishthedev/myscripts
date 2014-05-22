from SanityChecks import TestShipment, CreateATestBill

def main():


    bill = CreateATestBill()
    bill.courierName = "Professional Courier"
    bill.docketNumber = "GZB2207318"
    with TestShipment(bill) as ts:
        ts.Track()
        print("Status: {}".format(ts.status))
        ts.TakeNewSnapshot()


if __name__ == '__main__':
    main()
