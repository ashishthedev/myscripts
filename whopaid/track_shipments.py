##############################################################################
## Intent: To store the shipment status by reading from internet
##
## Date: 2013-Jul-30 Tue 12:39 PM
##############################################################################

##############################################################################
## Assumption: docket number are unique(if and when things get cluttered use
## a combination of date and docket numbers)
##############################################################################

from __future__ import print_function, division

from UtilWhoPaid import GetAllBillsInLastNDays
from UtilMisc import PrintInBox, GetMsgInBox, DD_MM_YYYY
from UtilConfig import GetOption
from contextlib import closing
from time import sleep
import traceback
import argparse
import datetime
import shelve
import os

from courier.couriers import Courier
MAX_IN_TRANSIT_DAYS = 15
IS_DEMO = True

class Shipment(object):
    shelfFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"),
            GetOption("CONFIG_SECTION", "ShipmentStatus"))

    def __init__(self, bill, status, delivered, shipmentMailSent):
        self.bill = bill
        self.status = status
        self.isDelivered = delivered
        self.courier = Courier(bill)
        self.shipmentMailSent = shipmentMailSent

    @property
    def uid_string(self):
        return "{}{}{}".format(str(self.bill.billNumber), DD_MM_YYYY(self.bill.invoiceDate), str(self.bill.docketNumber))

    @classmethod
    def GetShipmentForBill(cls, bill, status="", delivered=False, shipmentMailSent=False):
        #Only place where it gets instantiated
        with closing(shelve.open(cls.shelfFileName)) as sh:
            obj = None
            key = self.uid_string
            if sh.has_key(key):
                obj = sh[key]
            else:
                obj = cls(bill, status, delivered, shipmentMailSent)
        return obj

    @property
    def description(self):
        return GetMsgInBox("\n".join(str(self).split(":")))

    def __str__(self):
        b = self.bill
        return " | ".join([b.compName,
            "Bill# {}".format(str(int(b.billNumber))),
            DD_MM_YYYY(b.docketDate),
            b.docketNumber,
            b.courierName,
            b.materialDesc,
            self.status])

    @property
    def daysPassed(self):
        return (datetime.date.today() - self.bill.docketDate).days

    def _saveInDB(self):
        with closing(shelve.open(self.shelfFileName)) as sh:
            sh[self.uid_string] = self

    def _remove(self):
        with closing(shelve.open(self.shelfFileName)) as sh:
            del sh[self.uid_string]

    def saveAsNOTdelivered(self):
        self.isDelivered = False
        self._saveInDB()
        return

    def saveAsDeliveredWithSnapshot(self):
        self.courier.StoreSnapshot()
        self._markAsDeliveredAndSaveInDB()



    def _markAsDeliveredAndSaveInDB(self):
        if not IsDeliveredAssessFromStatus(self.status):
            raise Exception("Algorithm says undelivered but you are trying to save it as delivered. The original status was: \n{}".format(self.status))
        self.isDelivered = True
        self._saveInDB()
        return

    def _newSanpshot(self):
        #For whatever reason, take a new snapshot.
        self.courier.StoreSnapshot()

    @classmethod
    def GetAllStoredShipments(cls):
        with closing(shelve.open(cls.shelfFileName)) as sh:
            return sh.values()

    @classmethod
    def GetAllUndeliveredShipments(cls):
        allShipments = cls.GetAllStoredShipments()
        return [shipment for shipment in allShipments if not shipment.isDelivered]

    def UpdateAndFetchNetworkDeliveryStatus(self):
        self.status = self.courier.GetStatus()
        return self.status


    def ShouldWeTrackThis(self):
        if self.daysPassed == 0:
            return False

        if not self.bill.docketDate:
            return False

        if not self.bill.courierName:
            return False

        if self.isDelivered:
            return False

        return True

    def Track(self):
        if self.isDelivered:
            return # No need to do anything else

        self.UpdateAndFetchNetworkDeliveryStatus()
        self.isDelivered  = IsDeliveredAssessFromStatus(self.status)

        if self.isDelivered:
            self.saveAsDeliveredWithSnapshot()
        else:
            self.saveAsNOTdelivered()
        return self.status

    def markDispatchMailAsSent(self):
        self.shipmentMailSent = True

    def wasDispatchMailEverSent(self):
        return self.shipmentMailSent

    def sendShipmentMail(self):
        if self.wasDispatchMailEverSent:
            if str(raw_input("A shipment mail has already been sent to {}. Do you want to send again(y/n)?".format(self.bill.compName))).lower() != 'y':
                print("Not sending mail")
                return
        ctxt = DispatchMailContext()
        ctxt.isDemo = IS_DEMO
        SendMaterialDispatchDetails(self.bill, ctxt)
        self.shipmentMailSent = True
        self._saveInDB()



def ParseOptions():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--days", dest='days', type=int, default=MAX_IN_TRANSIT_DAYS,
            help="Last N days in which courier status will be checked.")
    parser.add_argument("--clearDB", dest='clearDB', action='store_true',
            default=False, help="Clears the database")
    parser.add_argument("-ns", "--new-snapshot", dest='newSnapshotForDocket', type=str, default=None,
            help="Take new snapshot for docket")
    parser.add_argument("-rt", "--remove-tracking", dest='removeTrackingForDocket', type=str, default=None,
            help="If you want to temprarily remove a docket from tracking - Use it")

    parser.add_argument("-fmd", "--force-mark-delivered", dest='forceMarkDeliveredDocket', type=str, default=None,
            help="If you want to remove a docket from tracking(for ex/- very old docket). If the docket comes falls under purview of default days, it will be added to tracking index again.")
    parser.add_argument("-ssm", "--send-shipment-mail", dest="sendShipmentMail", action="store_true",
            default=False, help="Send shipment mail to eligible companies")
    parser.add_argument("--demo", dest="isDemo", action="store_true", default=False,
            help="Set this for a demo run")
    return parser.parse_args()


def IsDeliveredAssessFromStatus(status):
    yes_words = status.lower().find("delivered") != -1
    no_words = ( status.lower().find("not") != -1 or status.lower().find("undelivered") != -1)
    delivered = yes_words and not no_words #If has the word delivered but not the word not
    return delivered


def _ForceMarkDocketAsDelivered(docketNumber):
    us = Shipment.GetAllUndeliveredShipments()
    for s in us:
        if s.bill.docketNumber == docketNumber:
            s.status = "This shipment was force marked as delivered on {}".format(DD_MM_YYYY(datetime.datetime.today()))
            print(s.status)
            s._markAsDeliveredAndSaveInDB()

def _RemoveDocketFromIndex(docketNumber):
    us = Shipment.GetAllStoredShipments()
    print("About to remove docket from tracking index: {}".format(docketNumber))
    for s in us:
        print(s.bill.docketNumber)
        if s.bill.docketNumber == docketNumber:
            print("Docket {} removed from tracking index".format(docketNumber))
            s._remove()
            break
    else:
        print("Could not find the docket {}".format(docketNumber))

def _NewSnapshotForDocket(docketNumber):
    us = Shipment.GetAllStoredShipments()
    print("About to take a new snapshot for docket: {}".format(docketNumber))
    for s in us:
        if s.bill.docketNumber == docketNumber:
            print("Taking snapshot for docket {}".format(docketNumber))
            s._newSanpshot()
            break
    else:
        print("Could not find the docket {}".format(docketNumber))

def main():
    args = ParseOptions()

    global IS_DEMO
    IS_DEMO = args.isDemo

    if args.clearDB:
        PrintInBox("Starting afresh")
        os.remove(Shipment.shelfFileName)

    if args.forceMarkDeliveredDocket:
        _ForceMarkDocketAsDelivered(args.forceMarkDeliveredDocket)
        return

    if args.removeTrackingForDocket:
        _RemoveDocketFromIndex(args.removeTrackingForDocket)
        return
    if args.newSnapshotForDocket:
        _NewSnapshotForDocket(args.newSnapshotForDocket)
        return

   if args.sendShipmentMail:


    undeliveredBillsList = [s.bill for s in Shipment.GetAllUndeliveredShipments()]
    undeliveredBillDict = {b.docketNumber: b for b in undeliveredBillsList}

    freshBillList = GetAllBillsInLastNDays(args.days)
    freshBillDict = {b.docketNumber: b for b in freshBillList}

    undeliveredBillDict.update(freshBillDict) #Dict removes duplicate entries

    finalBillList = undeliveredBillDict.values()
    finalBillList = [b for b in finalBillList if b.docketDate]
    finalBillList.sort(key=lambda b: b.docketDate)

    shipments = [Shipment.GetShipmentForBill(b) for b in finalBillList]
    shipments = [s for s in shipments if s.ShouldWeTrackThis()]

    for i, shipment in enumerate(shipments, start=1):
        try:
            if not shipment.ShouldWeTrackThis(): continue #Fail safe mechanism. Although all shipments that have been delivered should not reach here.
            old_status = shipment.status
            print("{}\n{} of {}| {} days| {}".format("_"*70, i, len(shipments), shipment.daysPassed, shipment))
            new_status = shipment.Track()  #One shipment per bill

            if old_status != new_status: PrintInBox("New status: {}".format(new_status))


            if not shipment.isDelivered and shipment.daysPassed > MAX_IN_TRANSIT_DAYS :
                raise Exception("{} days back the following material was shipped but still not delivered\n{}".format(
                    shipment.daysPassed,shipment.description))
            sleep(2)

        except Exception as ex:
            pass
            #PrintInBox(str(ex))
            #print(traceback.format_exc())
            #Print the exception and move on to next shipment

if __name__ == '__main__':
    main()
