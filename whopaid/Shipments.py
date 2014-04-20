##############################################################################
## Intent: To store the shipment status by reading from internet
##
## Date: 2013-Jul-30 Tue 12:39 PM
##############################################################################

from __future__ import print_function, division

from UtilWhoPaid import GetAllBillsInLastNDays, RemoveTrackingBills
from CustomersInfo import GetAllCustomersInfo
from UtilMisc import PrintInBox, GetMsgInBox, DD_MM_YYYY
from UtilConfig import GetOption
from contextlib import closing
from time import sleep
import argparse
import datetime
import shelve
import random
from UtilPythonMail import SendMail
from UtilHTML import UnderLine, Bold, PastelOrangeText
import os
from string import Template
from SanityChecks import SendHeartBeat, CheckConsistency
import urllib2
from UtilSms import SendSms, CanSendSmsAsOfNow

from courier.couriers import Courier
MAX_IN_TRANSIT_DAYS = 15
IS_DEMO = True

#Shipment
# |-ShipmentMail
# |-ShipmentCourier
# |-ShipmentSms

class ShipmentException(Exception):
    pass

class DispatchMailContext(object):
    emailSubject = None
    kaPerson = None
    isDemo = False
    first_line = None
    second_line = None
    last_line = None

class ShipmentTrack(object):
    def __init__(self, shipment, bill):
        self.bill = bill
        self.shipment = shipment #Back reference to parent shipment object
        self.courier = Courier(bill)
        self.status = "Not Tracked Yet"
        self.isDelivered = False
        pass

    def isDeliveredFn(self):
        return self.isDelivered

    def markAsDelivered(self):
        self.isDelivered = True

    def TakeNewSnapshot(self):
        #For whatever reason, take a new snapshot.
        self.courier.StoreSnapshot()

    def ShouldWeTrackThis(self):
        #if self.shipment.daysPassed == 0:
        #    return False

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

        try:
            self.status = self.courier.GetStatus()
        except urllib2.URLError:
            raise ShipmentException("URL Error")
        self.isDelivered  = IsDeliveredAssessFromStatus(self.status)

        if self.isDelivered:
            self.courier.StoreSnapshot()

        self.shipment.saveInDB()

        return self.status


class ShipmentSms(object):
    def __init__(self, shipment, bill):
        self.bill = bill
        self.shipment = shipment #Back reference to parent shipment object
        self.shipmentSmsSent = False

    def markShipmentSmsAsSent(self):
        self.shipmentSmsSent = True

    def wasShipmentSmsEverSent(self):
        return self.shipmentSmsSent

    def sendSmsForThisShipment(self):
        if self.wasShipmentSmsEverSent():
            if str(raw_input("A shipment sms has already been sent to {}. Do you want to send again(y/n)?".format(self.bill.compName))).lower() != 'y':
                print("Not sending sms")
                return
        SendMaterialDispatchSms(self.bill)
        if not IS_DEMO:
            self.markShipmentSmsAsSent()
            self.shipment.saveInDB()

class ShipmentMail(object):
    def __init__(self, shipment, bill):
        self.bill = bill
        self.shipment = shipment #Back reference to parent shipment object
        self.shipmentMailSent = False
        pass

    def markShipmentMailAsSent(self):
        self.shipmentMailSent = True

    def wasShipmentMailEverSent(self):
        return self.shipmentMailSent

    def sendMailForThisShipment(self):
        if self.wasShipmentMailEverSent():
            if str(raw_input("A shipment mail has already been sent to {}. Do you want to send again(y/n)?".format(self.bill.compName))).lower() != 'y':
                print("Not sending mail")
                return
        ctxt = DispatchMailContext()
        ctxt.isDemo = IS_DEMO
        SendMaterialDispatchMail(self.bill, ctxt)
        if not IS_DEMO:
            self.markShipmentMailAsSent()
            self.shipment.saveInDB()


class PersistentShipment(object):
    shelfFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"),
            GetOption("CONFIG_SECTION", "ShipmentStatus"))

    def __init__(self, bill):
        self.bill = bill
        self._mail = ShipmentMail(self, bill)
        self._track = ShipmentTrack(self, bill)
        self._sms = ShipmentSms(self, bill)

    def wasShipmentMailEverSent(self):
        return self._mail.wasShipmentMailEverSent()

    def sendMailForThisShipment(self):
        return self._mail.sendMailForThisShipment()

    def wasShipmentSmsEverSent(self):
        return self._sms.wasShipmentSmsEverSent()

    def isSMSNoAvailable(self):
        if GetAllCustomersInfo().GetSmsDispatchNumber(self.bill.compName):
            return True
        return False

    def sendSmsForThisShipment(self):
        return self._sms.sendSmsForThisShipment()

    @property
    def isDelivered(self):
        return self._track.isDelivered

    def isUndelivered(self):
        return not self.isDelivered

    def markShipmentMailAsSent(self):
        self._mail.markShipmentMailAsSent()

    def markAsDelivered(self):
        self._track.markAsDelivered()

    def TakeNewSnapshot(self):
        self._track.TakeNewSnapshot()

    def ShouldWeTrackThis(self):
        return self._track.ShouldWeTrackThis()

    def Track(self):
        return self._track.Track()

    def saveInDB(self):
        with closing(shelve.open(self.shelfFileName)) as sh:
            sh[self.uid_string] = self

    def _removeFromDB(self):
        with closing(shelve.open(self.shelfFileName)) as sh:
            del sh[self.uid_string]

    @classmethod
    def GetAllStoredShipments(cls):
        with closing(shelve.open(cls.shelfFileName)) as sh:
            return sh.values()

    @classmethod
    def GetAllUndeliveredShipments(cls):
        allShipments = cls.GetAllStoredShipments()
        return [s for s in allShipments if s.isUndelivered()]

    @property
    def uid_string(self):
        return self.bill.uid_string

    @classmethod
    def GetOrCreateShipmentForBill(cls, bill):
        #Only place where it gets instantiated
        with closing(shelve.open(cls.shelfFileName)) as sh:
            obj = None
            key = bill.uid_string
            if sh.has_key(key):
                obj = sh[key]
            else:
                obj = cls(bill)
                obj.saveInDB()
        return obj

    @property
    def status(self):
        return self._track.status

    @status.setter
    def status(self, value):
        self._track.status = value

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



def SendMaterialDispatchSms(bill):
    allCustInfo = GetAllCustomersInfo()
    compName = bill.compName
    smsNo = allCustInfo.GetSmsDispatchNumber(compName)
    if not smsNo:
        raise Exception("No sms no. feeded for customer: {}".format(compName))

    optionalAmount = ""
    if allCustInfo.IncludeBillAmountInEmails(compName):
        optionalAmount = "Amount: Rs." + str(int(bill.instrumentAmount)) + "/-"

    companyOfficialName = allCustInfo.GetCompanyOfficialName(compName)
    if not companyOfficialName:
        raise Exception("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

    d = dict()

    d["tFromName"] = "From: {}".format(GetOption("SMS_SECTION", 'FromDisplayName'))
    d["toName"] = "To: {}".format(companyOfficialName)
    d["tDocketNumber"] = bill.docketNumber
    d["tDocketDate"] = bill.docketDate
    d["tThrough"] = bill.courierName
    d["tMaterialDescription"] = bill.materialDesc
    d["tAmount"] = optionalAmount

    smsTemplate = Template("""$tFromName
_____

$toName
Waybill#: $tDocketNumber
Date: $tDocketDate
Through: $tThrough
Material: $tMaterialDescription
$tAmount
Thanks.
""")
    smsContents = smsTemplate.substitute(d)

    COMMA = ","
    smsNo = smsNo.replace(';', ',').strip()
    listOfNos = [x.strip() for x in smsNo.split(COMMA)]
    anyAdditionalSmsNo = GetOption("SMS_SECTION", "CC_NO")
    if anyAdditionalSmsNo:
        anyAdditionalSmsNo = anyAdditionalSmsNo.replace(';', ',').strip()
        listOfNos.extend([x.strip() for x in anyAdditionalSmsNo.split(COMMA)])

    for x in listOfNos:
        print("Sending to this number: {}".format(x))
        SendSms(x, smsContents)

    return



def SendMaterialDispatchMail(bill, ctxt):
    allCustInfo = GetAllCustomersInfo()

    optionalAmount = ""
    if allCustInfo.IncludeBillAmountInEmails(bill.compName):
        optionalAmount = " Rs." + str(int(bill.instrumentAmount)) + "/-"

    ctxt.emailSubject = ctxt.emailSubject or "Dispatch Details: {} Bill#{} {amt}".format(bill.docketDate.strftime("%d-%b-%Y"), str(int(bill.billNumber)), amt=optionalAmount)


    print("Churning more data...")

    toMailStr = allCustInfo.GetPaymentReminderEmailsForCustomer(bill.compName)
    if not ctxt.kaPerson:
        #If no person was specified at command line then pick one from the database.
        personFromDB = allCustInfo.GetCustomerKindAttentionPerson(bill.compName)
        if personFromDB and 'y' == raw_input("Mention kind attn: {} (y/n)?".format(personFromDB)).lower():
            ctxt.kaPerson = personFromDB

    if not toMailStr:
        raise ShipmentException("\nNo mail feeded. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'")

    #Mails in database are generally split either with semicolons or commas
    #In either case, treat them as separated by , and later split on comma
    toMailStr = toMailStr.replace(';', ',')
    toMailStr = toMailStr.replace(' ', '')

    toMailList = toMailStr.split(',')

    #Remove spaces from eachMail in the list and create a new list
    toMailList = [eachMail.replace(' ', '') for eachMail in toMailList]
    ccMailList = GetOption("EMAIL_REMINDER_SECTION", 'CCEmailList').replace(';', ',').split(','),
    bccMailList = GetOption("EMAIL_REMINDER_SECTION", 'BCCEmailList').replace(';', ',').split(','),

    print("Preparing mail...")
    mailBody = PrepareShipmentEmailForThisBill(bill, ctxt)

    if ctxt.isDemo:
        toMailList = GetOption("EMAIL_REMINDER_SECTION", "TestMailList").split(',')
        ccMailList = None
        bccMailList = None
        ctxt.emailSubject = "[Testing{}]: {}".format(str(random.randint(1, 10000)), ctxt.emailSubject)

    print("Sending to: " + str(toMailList))

    section = "EMAIL_REMINDER_SECTION"
    SendMail(ctxt.emailSubject,
            None,
            GetOption(section, 'Server'),
            GetOption(section, 'Port'),
            GetOption(section, 'FromEmailAddress'),
            toMailList,
            ccMailList,
            bccMailList,
            GetOption(section, 'Mpass'),
            mailBody,
            textType="html",
            fromDisplayName=GetOption(section, "shipmentDetailsName"))

    return


def PrepareShipmentEmailForThisBill(bill, ctxt):
    """Given a company, this function will prepare an email for shipment details."""
    from UtilColors import MyColors
    from UtilHTML import TableHeaderRow, TableDataRow

    allCustInfo = GetAllCustomersInfo()
    letterDate = DD_MM_YYYY(datetime.date.today())
    officalCompName = allCustInfo.GetCompanyOfficialName(bill.compName)
    if not officalCompName:
        raise ShipmentException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(bill.compName))

    companyCity = allCustInfo.GetCustomerCity(bill.compName)
    if not companyCity:
        raise ShipmentException("\nM/s {} doesnt have a displayable 'city'. Please feed it in the database".format(bill.compName))

    includeAmount = allCustInfo.IncludeBillAmountInEmails(bill.compName)
    tableHeadersArgs = ["Bill#", "Dispatched Through", "Tracking Number", "Shipping Date", "Material Description"]
    tableDataRowArgs = [ str(int(bill.billNumber)), str(bill.courierName), str(bill.docketNumber), DD_MM_YYYY(bill.docketDate), bill.materialDesc]

    if includeAmount:
        tableHeadersArgs.append("Bill Amount")
        tableDataRowArgs.append("Rs.{}/-".format(str(int(bill.instrumentAmount))))

    tableRows = TableHeaderRow(
            MyColors["BLACK"],
            MyColors["SOLARIZED_GREY"],
            *tableHeadersArgs)

    tableRows += TableDataRow(
            MyColors["BLACK"],
            MyColors["WHITE"],
            *tableDataRowArgs)

    def constant_factory(value):
        from itertools import repeat
        return repeat(value).next

    from collections import defaultdict
    d = defaultdict(constant_factory(""))

    if ctxt.first_line:
        d['tFirstLine'] = ctxt.first_line + '<br><br>'

    if ctxt.second_line:
        d['tSecondLine'] = ctxt.second_line + '<br><br>'

    if ctxt.last_line:
        d['tLastLine'] = ctxt.last_line + '<br><br>'

    if ctxt.kaPerson:
        d['tPerson'] = Bold("Kind Attention: " + ctxt.kaPerson + '<br><br>')

    d['tLetterDate'] = letterDate
    d['tOfficialCompanyName'] = officalCompName
    d['tCompanyCity'] = companyCity
    d['tTableRows'] = tableRows
    d['tBodySubject'] = PastelOrangeText(Bold(UnderLine(ctxt.emailSubject)))
    d['tSignature'] = GetOption("EMAIL_REMINDER_SECTION", "Signature")

    templateMailBody = Template("""
  <html>
      <head>
      </head>
      <body style=" font-family: Helvetica, Georgia, Verdana, Arial, 'sans-serif'; font-size: 1.1em; line-height: 1.5em;" >
      <p>
      $tLetterDate<br>
      <br>
      To,<br>
      M/s $tOfficialCompanyName,<br>
      $tCompanyCity.<br>
      <br>
      $tBodySubject<br>
      <br>
      $tPerson
      Dear Sir,<br>
      <br>
      $tFirstLine
      $tSecondLine
      Please find below the details of the dispatched material:
      <table border=1 cellpadding=5>
      $tTableRows
      </table>
      </p>
      <br>
      $tLastLine
      <hr>
      <p>
      <font color="grey"> <small>
      $tSignature
      </small></font>
      </p>
      </body>
  </html>
  """)

    finalMailBody = templateMailBody.substitute(d)

    return finalMailBody



def ParseOptions():
    parser = argparse.ArgumentParser()

    parser.add_argument("-mmas", "--mark-mail-as-sent", dest='markMailAsSentForDocket', type=str, default=None,
            help="Mark the mail as sent.")

    parser.add_argument("--show-undelivered", dest='showUndelivered', action="store_true", default=False,
            help="If present, show undelivered parcels on screen")

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

    parser.add_argument("--mail", dest="sendMailToAllCompanies", action="store_true",
            default=False, help="Send shipment mail to eligible companies")

    parser.add_argument("-sms", "--dispatch-sms-all", dest='sendDispatchSms', action="store_true", default=False,
            help="Send the sms to parties about dispatches.")

    parser.add_argument("--track", dest="trackAllUndeliveredCouriers", action="store_true",
            default=False, help="Track all undelivered couriers")

    parser.add_argument("--demo", dest="isDemo", action="store_true", default=False,
            help="Set this for a demo run")

    return parser.parse_args()


def IsDeliveredAssessFromStatus(status):
    yes_words = status.lower().find("delivered") != -1
    no_words = ( status.lower().find("not") != -1 or status.lower().find("undelivered") != -1)
    delivered = yes_words and not no_words #If has the word delivered but not the word not
    return delivered


def _FormceMarkShipmentMailAsSent(docketNumber):
    us = PersistentShipment.GetAllStoredShipments()
    for s in us:
        print(s.bill.docketNumber)
        if s.bill.docketNumber == docketNumber:
            s.markShipmentMailAsSent()
            s.saveInDB()
            print("Marking the mail as sent for docket#: {}".format(docketNumber))


def _ForceMarkDocketAsDelivered(docketNumber):
    for s in PersistentShipment.GetAllUndeliveredShipments():
        if s.bill.docketNumber == docketNumber:
            s.status = "This shipment was force marked as delivered on {}".format(DD_MM_YYYY(datetime.date.today()))
            print(s.status)
            s.markAsDelivered()
            s.saveInDB()

def _RemoveDocketFromIndex(docketNumber):
    us = PersistentShipment.GetAllStoredShipments()
    print("About to remove docket from tracking index: {}".format(docketNumber))
    for s in us:
        print(s.bill.docketNumber)
        if s.bill.docketNumber == docketNumber:
            print("Docket {} removed from tracking index".format(docketNumber))
            s._removeFromDB()
            break
    else:
        print("Could not find the docket {}".format(docketNumber))

def _NewSnapshotForDocket(docketNumber):
    print("About to take a new snapshot for docket: {}".format(docketNumber))
    for s in PersistentShipment.GetAllStoredShipments():
        if s.bill.docketNumber == docketNumber:
            print("Taking snapshot for docket {}".format(docketNumber))
            s.TakeNewSnapshot()
            break
    else:
        print("Could not find the docket {}".format(docketNumber))

def ShowUndeliveredOnScreen():
    print("Following parcels are still underlivered as on {}".format(DD_MM_YYYY(datetime.date.today())))
    shipments = PersistentShipment.GetAllUndeliveredShipments()
    shipments.sort(key=lambda s: s.bill.docketDate, reverse=False)
    coll = set()
    for s in shipments:
        coll.add(s.bill.courierName)

    for c in coll:
        PrintInBox(c)
        print("Kindly provide scanned copy of PODs for following parcels:\n")
        for s in shipments:
            if s.bill.courierName == c:
                print()
                allCustInfo = GetAllCustomersInfo()
                companyOfficialName = allCustInfo.GetCompanyOfficialName(s.bill.compName) or "NA"
                address = allCustInfo.GetCustomerDeliveryAddress(s.bill.compName) or "NA"
                phNo = allCustInfo.GetCustomerPhoneNumber(s.bill.compName) or "NA"
                print("_"*70)
                print(s.bill.compName)
                print(DD_MM_YYYY(s.bill.docketDate))
                print(address)

                print("\n".join([
                    "Docket Date: " + DD_MM_YYYY(s.bill.docketDate),
                    "Docket: " + str(s.bill.docketNumber),
                    "CompName: " + companyOfficialName,
                    "Address: " + address,
                    "Ph: " + str(phNo),
                    ]))


def main():
    args = ParseOptions()

    global IS_DEMO
    IS_DEMO = args.isDemo

    if args.clearDB:
        PrintInBox("Starting afresh")
        os.remove(PersistentShipment.shelfFileName)

    if args.markMailAsSentForDocket:
        _FormceMarkShipmentMailAsSent(args.markMailAsSentForDocket)

    if args.showUndelivered:
        ShowUndeliveredOnScreen()

    if args.forceMarkDeliveredDocket:
        _ForceMarkDocketAsDelivered(args.forceMarkDeliveredDocket)

    if args.removeTrackingForDocket:
        _RemoveDocketFromIndex(args.removeTrackingForDocket)

    if args.newSnapshotForDocket:
        _NewSnapshotForDocket(args.newSnapshotForDocket)

    if args.sendMailToAllCompanies:
        SendMailToAllComapnies(args)

    if args.sendDispatchSms:
        PrintInBox("Preparing to send SMS now")
        SendDispatchSMSToAllCompanies(args)

    if args.trackAllUndeliveredCouriers:
        TrackAllShipments(args)

def SendDispatchSMSToAllCompanies(args):
    bills = [b for b in GetAllBillsInLastNDays(args.days) if b.docketDate]
    bills = RemoveTrackingBills(bills)
    [PersistentShipment.GetOrCreateShipmentForBill(b) for b in bills]
    shipments = PersistentShipment.GetAllStoredShipments()
    shipments = [s for s in shipments if s.ShouldWeTrackThis()] #Filter our deliverd shipments
    shipments = [s for s in shipments if not s.wasShipmentSmsEverSent()]
    shipments = [s for s in shipments if s.isSMSNoAvailable()]
    shipments = [s for s in shipments if s.daysPassed < MAX_IN_TRANSIT_DAYS]
    shipments.sort(key=lambda s: s.bill.docketDate, reverse=True)

    if len(shipments) != 0:
        if not CanSendSmsAsOfNow():
            raise Exception("Sorry. SMS cannot be sent as of now. The phone might not be nearby or not paired with this computer.")
    else:
        PrintInBox("All sms that could have been sent has been sent.")

    try:
        for eachShipment in shipments:
            print("_"*70)
            if 'y' == raw_input("Send sms for {} (y/n)?".format(eachShipment)).lower():
                eachShipment.sendSmsForThisShipment()
            else:
                print("Not sending sms...")
    except ShipmentException as ex:
        print(ex)
        #eat the exception after printing. We have printed our custom exception, its good enough.
    return

def SendMailToAllComapnies(args):
    bills = [b for b in GetAllBillsInLastNDays(args.days) if b.docketDate]
    bills = RemoveTrackingBills(bills)
    [PersistentShipment.GetOrCreateShipmentForBill(b) for b in bills]
    shipments = PersistentShipment.GetAllStoredShipments()
    shipments = [s for s in shipments if s.ShouldWeTrackThis()] #Filter our deliverd shipments
    shipments = [s for s in shipments if not s.wasShipmentMailEverSent()]
    shipments = [s for s in shipments if s.daysPassed < MAX_IN_TRANSIT_DAYS]
    shipments.sort(key=lambda s: s.bill.docketDate, reverse=True)

    try:
        for eachShipment in shipments:
            print("_"*70)
            if 'y' == raw_input("Send mail for {} (y/n)?".format(eachShipment)).lower():
                eachShipment.sendMailForThisShipment()
            else:
                print("Not sending mail...")
    except ShipmentException as ex:
        print(ex)
        #eat the exception after printing. We have printed our custom exception, its good enough.
    return

def TrackAllShipments(args):
    [PersistentShipment.GetOrCreateShipmentForBill(b) for b in GetAllBillsInLastNDays(args.days) if b.docketDate]
    shipments = PersistentShipment.GetAllStoredShipments()
    trackableShipments = [s for s in shipments if s.ShouldWeTrackThis()]
    trackableShipments.sort(key=lambda s: s.bill.docketDate)

    for i, shipment in enumerate(trackableShipments, start=1):
        try:
            old_status = shipment._track.status
            print("{}\n{} of {}| {} days| {}".format("_"*70, i, len(trackableShipments), shipment.daysPassed, shipment))
            new_status = shipment.Track()  #One shipment per bill

            if old_status != new_status:
                PrintInBox("New status: {}".format(new_status), outliner=">")

            if not shipment.isDelivered and shipment.daysPassed > MAX_IN_TRANSIT_DAYS :
                raise ShipmentException("{} days back the following material was shipped but still not delivered\n{}".format(
                    shipment.daysPassed, shipment.description))
            sleep(2)

        except ShipmentException as ex:
            PrintInBox(str(ex), outliner="X")
            pass
            #PrintInBox(str(ex))
            #print(traceback.format_exc())
            #Print the exception and move on to next shipment

if __name__ == '__main__':
    CheckConsistency()
    SendHeartBeat()
    main()
