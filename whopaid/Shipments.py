##############################################################################
## Intent: To store the shipment status by reading from internet
##
## Date: 2013-Jul-30 Tue 12:39 PM
##############################################################################

from __future__ import print_function, division

from Util.Colors import MyColors
from Util.Config import GetOption
from Util.HTML import UnderLine, Bold, PastelOrangeText, TableHeaderRow, TableDataRow
from Util.Misc import PrintInBox, GetMsgInBox, DD_MM_YYYY, DD_MMM_YYYY, IsDeliveredAssessFromStatus

from whopaid.CustomersInfo import GetAllCustomersInfo
from whopaid.courier.couriers import Courier
from whopaid.OffComm import SendOfficialSMS
from whopaid.SanityChecks import SendAutomaticHeartBeat, CheckConsistency
from whopaid.UtilWhoPaid import GetAllBillsInLastNDays, RemoveTrackingBills

from collections import defaultdict
from contextlib import closing
from itertools import repeat
from string import Template
from time import sleep

import argparse
import datetime
import shelve
import random
import os
import urllib2

MAX_IN_TRANSIT_DAYS = 15
MAX_DAYS_FOR_SENDING_NOTIFICATION = 4
IS_DEMO = True
NOT_PROVIDED = "Not provided"

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
    print("_"*70)
    print("Marking shipment mail as sent for : {}".format(self.bill.compName))
    self.shipmentMailSent = True
    return

  def wasShipmentMailEverSent(self):
    return self.shipmentMailSent

  def sendMailForThisShipment(self):
    if self.wasShipmentMailEverSent():
      if str(raw_input("A shipment mail has already been sent to {}. Do you want to send again(y/n)?".format(self.bill.compName))).lower() != 'y':
        print("Not sending mail")
        return
    if self.bill.billingCategory.lower().startswith("tracking"):
      print("_"*70)
      print("This is a tracking shipment. Not sendign any mail")
      print(self)
      #return
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
        str(self.status)])

  @property
  def daysPassed(self):
    return (datetime.date.today() - self.bill.docketDate).days



def SendMaterialDispatchSms(bill):
  optionalAmount = ""
  if IncludeAmountForBillInDispatchInfo(bill):
      optionalAmount = "Amount: Rs." + str(int(bill.amount)) + "/-"

  d = dict()

  d["tBillNo"] = str(int(bill.billNumber))
  d["tDocketNumber"] = bill.docketNumber
  d["tDocketDate"] = DD_MMM_YYYY(bill.docketDate)
  d["tThrough"] = bill.courierName
  d["tMaterialDescription"] = bill.materialDesc
  d["tAmount"] = optionalAmount

  smsTemplate = Template("""
Bill# $tBillNo
Waybill#: $tDocketNumber
Date: $tDocketDate
Through: $tThrough
Material: $tMaterialDescription
$tAmount
Thanks.
""")
  smsContents = smsTemplate.substitute(d)
  SendOfficialSMS(bill.compName, smsContents)
  return


def IncludeAmountForBillInDispatchInfo(bill):
  if bill.billingCategory.lower() not in ["builty", "tracking"]:
    if GetAllCustomersInfo().IncludeBillAmountInEmails(bill.compName):
      return True
  return False

def SendMaterialDispatchMail(bill, ctxt):
  allCustInfo = GetAllCustomersInfo()

  optionalAmount = ""
  if IncludeAmountForBillInDispatchInfo(bill):
    optionalAmount = " Rs." + str(int(bill.amount)) + "/-"

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
  from whopaid.OffComm import SendOfficialEmail
  SendOfficialEmail(ctxt.emailSubject,
      None,
      toMailList,
      ccMailList,
      bccMailList,
      mailBody,
      textType="html",
      fromDisplayName = GetOption(section,"shipmentDetailsName"))
  return


def PrepareShipmentEmailForThisBill(bill, ctxt):
  """
  Given a company, this function will prepare an email for shipment details.
  """

  allCustInfo = GetAllCustomersInfo()
  letterDate = DD_MM_YYYY(datetime.date.today())
  officalCompName = allCustInfo.GetCompanyOfficialName(bill.compName)
  if not officalCompName:
    raise ShipmentException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(bill.compName))

  companyCity = allCustInfo.GetCustomerCity(bill.compName)
  if not companyCity:
    raise ShipmentException("\nM/s {} doesnt have a displayable 'city'. Please feed it in the database".format(bill.compName))

  tableHeadersArgs = ["Bill#", "Dispatched Through", "Tracking Number", "Shipping Date", "Material Description"]
  tableDataRowArgs = [ str(int(bill.billNumber)), str(bill.courierName), str(bill.docketNumber), DD_MM_YYYY(bill.docketDate), bill.materialDesc]

  if IncludeAmountForBillInDispatchInfo(bill):
    tableHeadersArgs.append("Bill Amount")
    tableDataRowArgs.append("Rs.{}/-".format(str(int(bill.amount))))

  tableRows = TableHeaderRow(
      MyColors["BLACK"],
      MyColors["SOLARIZED_GREY"],
      *tableHeadersArgs)

  tableRows += TableDataRow(
      MyColors["BLACK"],
      MyColors["WHITE"],
      *tableDataRowArgs)

  def constant_factory(value):
    return repeat(value).next

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
    Please find below the details of dispatched material:
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

    parser.add_argument("-sus", "--show-undelivered-small", dest='showUndeliveredSmall', action="store_true", default=False,
        help="If present, show undelivered parcels on screen")

    parser.add_argument("-su", "--show-undelivered", dest='showUndeliveredBig', action="store_true", default=False,
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

    parser.add_argument("--complaint", dest="complaintDocket", action="store_true", default=False, help="Will send a complaint to appropriate local courier agent")
    return parser.parse_args()



def _FormceMarkShipmentMailAsSent(docketNumber):
  us = PersistentShipment.GetAllStoredShipments()
  for s in us:
    print(s.bill.docketNumber)
    if s.bill.docketNumber == docketNumber:
      s.markShipmentMailAsSent()
      s.saveInDB()
      print("Marking the mail as sent for docket#: {}".format(docketNumber))
  return


def _ForceMarkDocketAsDelivered(docketNumber):
  for s in PersistentShipment.GetAllUndeliveredShipments():
    if s.bill.docketNumber == docketNumber:
      s.status = "This shipment was force marked as delivered on {}".format(DD_MM_YYYY(datetime.date.today()))
      print(s.status)
      s.markAsDelivered()
      s.saveInDB()
  return

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
  return

def _NewSnapshotForDocket(docketNumber):
  print("About to take a new snapshot for docket: {}".format(docketNumber))
  for s in PersistentShipment.GetAllStoredShipments():
    if s.bill.docketNumber == docketNumber:
      print("Taking snapshot for docket {}".format(docketNumber))
      s.TakeNewSnapshot()
      break
  else:
    print("Could not find the docket {}".format(docketNumber))
  return

def ShowUndeliveredSmalOnScreen():
  shipments = PersistentShipment.GetAllUndeliveredShipments()
  PrintInBox("Following are undelivered shipments:")
  for i, s in enumerate(sorted(shipments, key=lambda s: s.bill.docketDate), start=1):
    print("{}.{:<50} : {:<15} : {}".format(i, s.bill.compName, DD_MMM_YYYY(s.bill.docketDate), s.bill.docketNumber))
  return

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
  return

def SendComplaintMessageForShipment(shipment):
  allCustInfo = GetAllCustomersInfo()
  bill = shipment.bill
  d = dict()

  d["tDocketNumber"] = bill.docketNumber
  d["tDocketDate"] = DD_MMM_YYYY(bill.docketDate)
  d["tDocketDate"] = DD_MMM_YYYY(bill.docketDate)
  d["tOfficialCompanyName"] = allCustInfo.GetCompanyOfficialName(bill.compName)
  d["tDeliveryAddress"] = allCustInfo.GetCustomerDeliveryAddress(bill.compName)
  d["tPhone"] = allCustInfo.GetCustomerPhoneNumber(bill.compName)


  smsTemplate = Template("""The following parcel is not delivered. Kindly get it delivered.
Date: $tDocketDate
Docket: $tDocketNumber
Name: $tOfficialCompanyName
Add: $tDeliveryAddress
Ph: $tPhone
Thanks.
""")

  smsContents = smsTemplate.substitute(d)
  from Util.Sms import SendSms
  smsNo = GetOption("COURIER_COMPLAINT_R", bill.courierName)[::-1]

  PrintInBox(smsContents)
  if raw_input("Send to {} {}: (y/n)".format(bill.courierName, smsNo)).lower() == "y":
    SendSms(smsNo, smsContents)
  else:
    print("Not sending sms...")
  return

def SendComplaintMessageForDocket(docketNumber):
  shipments = PersistentShipment.GetAllUndeliveredShipments()
  for s in shipments:
    if s.bill.docketNumber == docketNumber:
      return SendComplaintMessageForShipment(s)
  else:
    raise ShipmentException("Sorry no such docket is entered in system: {}".format(docketNumber))
  return


def main():
  args = ParseOptions()

  global IS_DEMO
  IS_DEMO = args.isDemo

  if args.complaintDocket:
    complaintDocket = raw_input("Enter the docket for which complaint has to be sent: ")
    SendComplaintMessageForDocket(complaintDocket)
    import sys; sys.exit(0)

  if args.clearDB:
    PrintInBox("Starting afresh")
    os.remove(PersistentShipment.shelfFileName)

  if args.markMailAsSentForDocket:
    _FormceMarkShipmentMailAsSent(args.markMailAsSentForDocket)

  if args.showUndeliveredSmall:
    ShowUndeliveredSmalOnScreen()
    import sys; sys.exit(0)

  if args.showUndeliveredBig:
    ShowUndeliveredOnScreen()

  if args.forceMarkDeliveredDocket:
    _ForceMarkDocketAsDelivered(args.forceMarkDeliveredDocket)

  if args.removeTrackingForDocket:
    _RemoveDocketFromIndex(args.removeTrackingForDocket)
    import sys; sys.exit(0)

  if args.newSnapshotForDocket:
    _NewSnapshotForDocket(args.newSnapshotForDocket)

  FanOutDispatchInfoToAllComapnies(args)

  if args.trackAllUndeliveredCouriers:
    TrackAllShipments(args)

def FanOutDispatchInfoToAllComapnies(args):
  bills = [b for b in GetAllBillsInLastNDays(args.days) if b.docketDate]
  bills = RemoveTrackingBills(bills)
  [PersistentShipment.GetOrCreateShipmentForBill(b) for b in bills]
  shipments = PersistentShipment.GetAllStoredShipments()
  shipments = [s for s in shipments if s.ShouldWeTrackThis()] #Filter our deliverd shipments
  shipments = [s for s in shipments if not s.wasShipmentMailEverSent()]
  shipments = [s for s in shipments if s.daysPassed < MAX_DAYS_FOR_SENDING_NOTIFICATION]
  shipments.sort(key=lambda s: s.bill.docketDate, reverse=True)

  for shipment in shipments:
    try:
      if args.sendMailToAllCompanies and not shipment.wasShipmentMailEverSent():
        if 'y' == raw_input("{}\nSend mail for {} (y/n)?".format("_"*70, shipment)).lower():
          shipment.sendMailForThisShipment()
        else:
          print("Not sending mail...")
      if args.sendDispatchSms and not shipment.wasShipmentSmsEverSent():
        if 'y' == raw_input("{}\nSend sms for {} (y/n)?".format("_"*70, shipment)).lower():
          shipment.sendSmsForThisShipment()
        else:
          print("Not sending sms...")
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

  return

if __name__ == '__main__':
  CheckConsistency()
  main()
  SendAutomaticHeartBeat()
  ShowUndeliveredSmalOnScreen()
