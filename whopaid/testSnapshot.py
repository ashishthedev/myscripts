from whopaid.SanityChecks import CreateATestBill

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
    bill.courierName = "Professional Courier"
    bill.docketNumber = "GZB2207318"
    with TestShipment(bill) as ts:
        ts.Track()
        print("Status: {}".format(ts.status))
        ts.TakeNewSnapshot()


if __name__ == '__main__':
    main()
