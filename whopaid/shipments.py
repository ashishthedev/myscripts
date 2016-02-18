##############################################################################
## Intent: To store the shipment status by reading from internet
##
## Date: 2013-Jul-30 Tue 12:39 PM
##############################################################################

from __future__ import print_function, division

from Util.Colors import MyColors
from Util.Config import GetOption
from Util.HTML import UnderLine, Bold, PastelOrangeText, TableHeaderRow,\
    TableDataRow
from Util.Misc import PrintInBox, GetMsgInBox, DD_MM_YYYY, DD_MMM_YYYY,\
    IsDeliveredAssessFromStatus
from Util.Persistent import Persistent

from whopaid.customers_info import GetAllCustomersInfo
from whopaid.courier.couriers import Courier
from whopaid.off_comm import SendOfficialSMS, SendOfficialSMSAndMarkCC
from whopaid.sanity_checks import SendAutomaticHeartBeat, CheckConsistency
from whopaid.util_whopaid import GetAllBillsInLastNDays

from collections import defaultdict
from itertools import repeat
from string import Template
from time import sleep

import argparse
import datetime
import json
import os
import random

MAX_IN_TRANSIT_DAYS = 15
MAX_DAYS_FOR_SENDING_NOTIFICATION = 4
IS_DEMO = True

LIST_OF_SHIPMENTS_IN_THIS_SCAN = list()
NO_OF_DAYS = int(GetOption("CONFIG_SECTION", "ShowShipmentStatusForNDays"))
ALL_BILLS_IN_LAST_N_DAYS = GetAllBillsInLastNDays(NO_OF_DAYS)
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
    self.shipment = shipment  # Back reference to parent shipment object
    self.courier = Courier(shipment, bill)
    self.status = "Not Tracked Yet"
    self.isDelivered = False

  def TakeNewSnapshot(self):
    #For whatever reason, take a new snapshot.
    self.courier.StoreDeliveryProof()

  def ShouldWeTrackThis(self):
    if not self.bill.docketDate:
        return False

    if not self.bill.courierName:
        return False

    if self.isDelivered:
        return False

    return True

  def TrackAndSave(self):
    if self.isDelivered:
        return  # No need to do anything else

    freshlyCalculatedPaidBillUids = [bill.uid_string for bill in ALL_BILLS_IN_LAST_N_DAYS if bill.isPaid]
    undeliveredButPaid = not self.isDelivered and (self.bill.uid_string in freshlyCalculatedPaidBillUids)
    if undeliveredButPaid:
      PrintInBox("Going out of the way")
      self.status = "Shipment in transit as per courier internet status but payment made by customer. Marking as delivered."
      self.shipment.psMarkShipmentDelivered()
    else:
      self.status = self.courier.GetStatus()
      if IsDeliveredAssessFromStatus(self.status):
        self.courier.StoreDeliveryProof()
        if self.IsSnapshotSaved():
          self.shipment.psMarkShipmentDelivered()

    self.shipment.save()

    return self.status

  def IsSnapshotSaved(self):
    return self.courier.IsSnapshotSaved()

class ShipmentSms(object):
  def __init__(self, shipment, bill):
    self.bill = bill
    self.shipment = shipment  # Back reference to parent shipment object
    self.shipmentSmsSent = False

  def wasShipmentSmsEverSent(self):
    return self.shipmentSmsSent

  def sendSmsForThisShipment(self):
    if self.wasShipmentSmsEverSent():
      if str(raw_input("A shipment sms has already been sent to {}.\
          Do you want to send again(y/n)?".format(
          self.bill.compName))).lower() != 'y':
        print("Not sending sms")
        return
    SendMaterialDispatchSms(self.bill)
    if not IS_DEMO:
      self.shipment.psMarkSmsAsSent()
    return

class ShipmentMail(object):
  def __init__(self, shipment, bill):
    self.bill = bill
    self.shipment = shipment  # Back reference to parent shipment object
    self.shipmentMailSent = False
    return

  def wasShipmentMailEverSent(self):
    return self.shipmentMailSent

  def sendMailForThisShipment(self):
    if self.wasShipmentMailEverSent():
      if str(raw_input("A shipment mail has already been sent to {}.\
        Do you want to send again(y/n)?".format(self.bill.compName))).lower() != 'y':
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
      self.shipment.psMarkMailAsSent()
    return


class SingleShipment():
  ssn = GetOption("CONFIG_SECTION", "SuperSmallName")
  def __init__(self, bill):
    self.bill = bill
    self._mail = ShipmentMail(self, bill)
    self._track = ShipmentTrack(self, bill)
    self._sms = ShipmentSms(self, bill)
    self.SetEDD(None)

  def psWasShipmentMailEverSent(self):
    return self._mail.wasShipmentMailEverSent()

  def psSendMailForThisShipment(self):
    return self._mail.sendMailForThisShipment()

  def psWasShipmentSmsEverSent(self):
    return self._sms.wasShipmentSmsEverSent()

  def isSMSNoAvailable(self):
    if ALL_CUST_INFO.GetSmsDispatchNumber(self.bill.compName):
      return True
    return False

  def isPaymentReminderEmailAddressAvailable(self):
    if ALL_CUST_INFO.GetPaymentReminderEmailsForCustomer(self.bill.compName):
      return True
    return False

  def psSendSmsForThisShipment(self):
    return self._sms.sendSmsForThisShipment()

  def IsSnapshotSaved(self):
    return self._track.IsSnapshotSaved()

  @property
  def isDelivered(self):
    return self._track.isDelivered

  def isUndelivered(self):
    return not self.isDelivered

  def psMarkSmsAsSent(self):
    self._sms.shipmentSmsSent = True
    self.save()

  def psMarkMailAsSent(self):
    self._mail.shipmentMailSent = True
    self.save()

  def psMarkShipmentDelivered(self):
    self._track.isDelivered = True
    LIST_OF_SHIPMENTS_IN_THIS_SCAN.append(self)
    self.save()

  def TakeNewSnapshot(self):
    self._track.TakeNewSnapshot()

  def ShouldWeTrackThis(self):
    return self._track.ShouldWeTrackThis()

  def TrackAndSave(self):
    return self._track.TrackAndSave()

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
  def trackUrl(self):
    if self.bill.courierName.lower().startswith("fedex"):
      return "https://www.fedex.com/apps/fedextrack/?tracknumbers={docket}&cntry_code=in".format(docket=self.bill.docketNumber)
    return None

  @property
  def daysPassed(self):
    return (datetime.date.today() - self.bill.docketDate).days

  @property
  def actualDDIfPresent(self):
    return self.actualDeliveryDate if hasattr(self, 'actualDeliveryDate') else None

  @property
  def estimatedDDIfPresent(self):
    return self.estimatedDeliveryDate if hasattr(self, 'estimatedDeliveryDate') else None

  def SetEDD(self, dd):
    PrintInBox("setting DD for docket#{} to {}".format(self.bill.docketNumber, dd))
    self.estimatedDeliveryDate = dd
    self.save()

  def GetEDD(self):
    return self.estimatedDeliveryDate

  def save(self):
    k = self.bill.uid_string
    PersistentShipments()[k]=self
    return self

  def _removeFromDB(self):
    ps = PersistentShipments()
    k = self.bill.uid_string
    if k in ps:
      del ps[k]
    return

  @property
  def jsonNode(self):
    b = self.bill
    s = self
    singleShipment = dict()
    singleShipment["compName"] = b.compName
    singleShipment["compOffName"] = ALL_CUST_INFO.GetCompanyOfficialName(b.compName)
    singleShipment["ourSuperSmallName"] = self.ssn
    singleShipment["docketNumber"] = b.docketNumber
    singleShipment["courier"] = b.courierName
    singleShipment["docketDate"] = DD_MMM_YYYY(b.docketDate)
    singleShipment["invoiceDateISOFormat"] = b.invoiceDate.isoformat()
    singleShipment["invoiceDate"] = DD_MMM_YYYY(b.invoiceDate)
    singleShipment["shipmentStatus"] = s.status
    singleShipment["billNumber"] = b.billNumber
    singleShipment["amount"] = b.amount
    singleShipment["materialDesc"] = b.materialDesc
    singleShipment["isDelivered"] = s.isDelivered
    singleShipment["daysPassed"] = s.daysPassed
    singleShipment["trackUrl"] = s.trackUrl
    singleShipment["estimatedDeliveryDate"] = s.estimatedDDIfPresent
    singleShipment["actualDeliveryDate"] = s.actualDDIfPresent
    singleShipment["uid_string"] = b.uid_string#TODO: Check if really required in json
    return singleShipment

class PersistentShipments(Persistent):
  def __init__(self):
    super(self.__class__, self).__init__(self.__class__.__name__)

  def GetOrCreateShipmentForBill(self, bill):
    key = bill.uid_string
    if key in self:
      return self[key]
    return SingleShipment(bill).save()

  def GetAllStoredShipments(self):
    return self.allValues

  def GetAllUndeliveredShipments(self):
    allShipments = self.GetAllStoredShipments()
    return [s for s in allShipments if s.isUndelivered()]

  def PurgeRedundantAwaitedShipments(self):
    us = self.GetAllUndeliveredShipments()
    awss = [s for s in us if s.bill.docketNumber.lower().startswith("awaited")]
    allShipments = [s for s in self.GetAllStoredShipments() if s.daysPassed <= 30]
    for aws in awss:
      for s in allShipments:
        if s.bill.compName == aws.bill.compName and s.bill.billNumber == aws.bill.billNumber and s.bill.invoiceDate == aws.bill.invoiceDate:
          aws._removeFromDB()
          break
    return self

  def PurgeShipmentsOlderThan(self, days):
    allShipments = self.GetAllStoredShipments()
    for s in allShipments:
      if s.daysPassed > days:
        s._removeFromDB()
    return

def SendMaterialDispatchSms(bill):
  optionalAmount = ""
  if IncludeAmountForBillInDispatchInfo(bill) and bill.amount != 0:
    optionalAmount = "Amount: Rs." + str(int(bill.amount)) + "/-"

  d = dict()

  d["tBillNo"] = str(int(bill.billNumber))
  d["tDocketNumber"] = bill.docketNumber
  d["tDocketDate"] = DD_MMM_YYYY(bill.docketDate)
  d["tThrough"] = bill.courierName
  d["tMaterialDescription"] = bill.materialDesc
  d["tAmount"] = optionalAmount

  smsTemplate = Template("""Bill# $tBillNo
Waybill#: $tDocketNumber
Date: $tDocketDate
Through: $tThrough
Material: $tMaterialDescription
$tAmount
Thanks.
""")
  smsContents = smsTemplate.substitute(d)

  sendToCCNumbers = GetOption("SMS_SECTION", "IncludeCCNo").lower().strip() == "true"

  if sendToCCNumbers:
    SendOfficialSMSAndMarkCC(bill.compName, smsContents)
  else:
    SendOfficialSMS(bill.compName, smsContents)

  return

ALL_CUST_INFO = GetAllCustomersInfo()

def IncludeAmountForBillInDispatchInfo(bill):
  if bill.billingCategory.lower() not in ["gr", "tracking"]:
    if ALL_CUST_INFO.IncludeBillAmountInEmails(bill.compName):
      return True
  return False


def SendMaterialDispatchMail(bill, ctxt):

  optionalAmount = ""
  if IncludeAmountForBillInDispatchInfo(bill) and bill.amount != 0:
    optionalAmount = " Rs." + str(int(bill.amount)) + "/-"

  ctxt.emailSubject = ctxt.emailSubject or "Dispatch Details: {} Bill#{} {amt}".format(bill.docketDate.strftime("%d-%b-%Y"), str(int(bill.billNumber)), amt=optionalAmount)

  print("Churning more data...")

  toMailStr = ALL_CUST_INFO.GetPaymentReminderEmailsForCustomer(bill.compName)
  if not ctxt.kaPerson:
    #If no person was specified at command line then pick one from the database.
    personFromDB = ALL_CUST_INFO.GetCustomerKindAttentionPerson(bill.compName)
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
  toMailList = [eachMail.replace(' ', '') for eachMail in toMailList if eachMail]
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
  from whopaid.off_comm import SendOfficialEmail
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

  letterDate = DD_MM_YYYY(datetime.date.today())
  officalCompName = ALL_CUST_INFO.GetCompanyOfficialName(bill.compName)
  if not officalCompName:
    raise ShipmentException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(bill.compName))

  companyCity = ALL_CUST_INFO.GetCustomerCity(bill.compName)
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

    parser.add_argument("-dbm", "--deleted_by_mistake",
        dest='dbDeletedByMistake', action="store_true", default=False,
        help="Will try to bring the shipments status back to normal as much as possible.")

    parser.add_argument("-msas", "--mark-sms-as-sent", dest='markSMSAsSentForDocket', type=str, default=None,
        help="Mark the sms as sent.")

    parser.add_argument("-mmas", "--mark-mail-as-sent", dest='markMailAsSentForDocket', type=str, default=None,
        help="Mark the mail as sent.")

    parser.add_argument("-maias", "--mark-all-info-as-sent", dest='markAllInfoAsSentForAllDockets', action="store_true", default=False, help="Mark the mail as sent.")

    parser.add_argument("-sus", "--show-undelivered-small", dest='showUndeliveredSmall', action="store_true", default=False,
        help="If present, show undelivered parcels on screen")

    parser.add_argument("-nd", "--notify-days", dest='notifyDays', type=int, default=MAX_DAYS_FOR_SENDING_NOTIFICATION,
        help="Last N days in which courier status will be checked.")

    parser.add_argument("-td", "--track-days", dest='trackDays', type=int, default=MAX_IN_TRANSIT_DAYS,
        help="Last N days in which courier status will be checked.")

    parser.add_argument("-ns", "--new-snapshot", dest='newSnapshotForDockets', nargs="+", type=str, default=None,
        help="Take new snapshot for docket")

    parser.add_argument("-rt", "--remove-tracking", dest='removeTrackingForDockets', nargs="+", type=str, default=None,
        help="If you want to remove a list of dockets from tracking - Use it")

    parser.add_argument("-fmd", "--force-mark-delivered", dest='forceMarkDeliveredDocket', type=str, default=None,
        help="If you want to remove a docket from tracking(for ex/- very old docket). If the docket comes falls under purview of default days, it will be added to tracking index again.")

    parser.add_argument("--mail", dest="sendMailToAllCompanies", action="store_true",
        default=False, help="Send shipment mail to eligible companies")

    parser.add_argument("-sms", "--dispatch-sms-all", dest='sendDispatchSms', action="store_true", default=False,
        help="Send the sms to parties about dispatches.")

    parser.add_argument("-rds", "--resend-dispatch-sms", dest="resendDispatchSms", action="store_true", default=False,
        help="Resend dispatch sms for selected docket")

    parser.add_argument("-ssmsg", "--send-scheduled-msgs", dest="sendScheduledMsgs", action="store_true",
        default=False, help="Send scheduled msgs")

    parser.add_argument("--generate-shipments-json", dest="generateShipmentsJson", action="store_true",
        default=True, help="Generate Shipments Json")

    parser.add_argument("-sah", "--send-automatic-heartbeat", dest="sendAutomaricHeartBeat", action="store_true",
        default=False, help="Send Automatic Heartbeat")

    parser.add_argument("--track", dest="trackAllUndeliveredCouriers", action="store_true",
        default=False, help="Track all undelivered couriers")

    parser.add_argument("-hrows", "--hideReportofAwaitedShipments", dest="hideReportofAwaitedShipments", action="store_true",
        default=False, help="Track all undelivered couriers")

    parser.add_argument("-fdi", "--fanout-dispatch-info", dest="FanoutDispatchInfo", action="store_true",
        default=True, help="Fanout Dispatch Info to all companies through email and sms")

    parser.add_argument("--demo", dest="isDemo", action="store_true", default=False,
        help="Set this for a demo run")

    parser.add_argument("--complaint", dest="complaintDocket", action="store_true", default=False, help="Will send a complaint to appropriate local courier agent")

    parser.add_argument("--p60", dest="purgeOlderThan60Days", action="store_true", default=False, help="Purge shipmenents older than 60 days")

    return parser.parse_args()


def _FormceMarkShipmentSMSAsSent(docketNumber):
  for s in PersistentShipments().GetAllStoredShipments():
    if s.bill.docketNumber == docketNumber:
      s.psMarkSmsAsSent()
      print("Marking SMS as sent for: " + s.bill.docketNumber)
  return

def _FormceMarkShipmentMailAsSent(docketNumber):
  for s in PersistentShipments().GetAllStoredShipments():
    if s.bill.docketNumber == docketNumber:
      s.psMarkMailAsSent()
      print("Marking mail as sent for: " + s.bill.docketNumber)
  return


def _ForceMarkDocketAsDelivered(docketNumber):
  for s in PersistentShipments().GetAllUndeliveredShipments():
    if s.bill.docketNumber == docketNumber:
      s.status = "This shipment was force marked as delivered on {}".format(DD_MM_YYYY(datetime.date.today()))
      print(s.status)
      s.psMarkShipmentDelivered()
  return

def _ResendDispatchSMSForDocketNumbers(docketNumbers):
  ss = PersistentShipments().GetAllStoredShipments()
  for d in docketNumbers:
    print("About to send dispatch sms for docket number: {}".format(d))
    for s in ss:
      if s.bill.docketNumber == d:
        if 'y' == raw_input("{}\nSend sms for {} (y/n)?".format("_"*70, s)).lower():
          s.psSendSmsForThisShipment()
          break
    else:
      print("Could not find the docket {}".format(d))
  return

def _RemoveDocketFromIndex(docketNumbers):
  ss = PersistentShipments().GetAllStoredShipments()
  for d in docketNumbers:
    print("About to remove docket from tracking index: {}".format(d))
    for s in ss:
      if s.bill.docketNumber == d:
        print("Docket {} removed from tracking index".format(d))
        s._removeFromDB()
        break
    else:
      print("Could not find the docket {}".format(d))
  return

def _NewSnapshotForDocket(docketNumbers):
  for docketNumber in docketNumbers:
    print("About to take a new snapshot for docket: {}".format(docketNumber))
    for s in PersistentShipments().GetAllStoredShipments():
      if str(s.bill.docketNumber) == str(docketNumber):
        print("Taking snapshot for docket {}".format(docketNumber))
        s.TakeNewSnapshot()
        break
    else:
      print("Could not find the docket {}".format(docketNumber))
  return

def _PurgeShipmentsOlderThan60Days():
  ps = PersistentShipments()
  PrintInBox("Size before cleanup: {}MB".format(ps.sizeInMB))
  ps.PurgeShipmentsOlderThan(60)
  PrintInBox("Size after cleanup: {}MB".format(ps.sizeInMB))
  ps.shrink()
  PrintInBox("Size after shrinking: {}MB".format(ps.sizeInMB))
  return


def ShowAwaitedShipmentsOnScreen():
  us = PersistentShipments().GetAllUndeliveredShipments()
  shipments = [s for s in us if s.bill.docketNumber.lower().startswith("awaited")]
  if len(shipments) <= 0:
    return
  PrintInBox("Need to get Waybill numbers for these shipments ASAP:")
  for i, s in enumerate(sorted(shipments, key=lambda s: s.bill.docketDate), start=1):
    print("{}.{:<50} | {:<15} | {}".format(i, s.bill.compName, DD_MMM_YYYY(s.bill.docketDate), s.bill.docketNumber))
  return

def ShowUndeliveredSmalOnScreen():
  shipments = PersistentShipments().GetAllUndeliveredShipments()
  PrintInBox("Following are undelivered shipments:")
  for i, s in enumerate(sorted(shipments, key=lambda s: s.bill.docketDate), start=1):
    print("{}.{:<50} | {:<15} | {}".format(i, s.bill.compName, DD_MMM_YYYY(s.bill.docketDate), s.bill.docketNumber))
  return

def SendComplaintMessageForShipment(shipment):
  bill = shipment.bill
  d = dict()

  d["tDocketNumber"] = bill.docketNumber
  d["tDocketDate"] = DD_MMM_YYYY(bill.docketDate)
  d["tDocketDate"] = DD_MMM_YYYY(bill.docketDate)
  d["tOfficialCompanyName"] = ALL_CUST_INFO.GetCompanyOfficialName(bill.compName)
  d["tDeliveryAddress"] = ALL_CUST_INFO.GetCustomerDeliveryAddress(bill.compName)
  d["tDeliveryPinCode"] = ALL_CUST_INFO.GetDeliveryPinCode(bill.compName)
  d["tPhone"] = ALL_CUST_INFO.GetDeliveryPhoneNumber(bill.compName)
  if isinstance(d["tPhone"], float):
    d["tPhone"] = str(int(d["tPhone"])) #Removing .0 in the end if its an integer


  smsTemplate = Template("""The following parcel is not delivered. Kindly get it delivered.
Date: $tDocketDate
Docket: $tDocketNumber
Name: $tOfficialCompanyName
Add: $tDeliveryAddress - $tDeliveryPinCode
Ph: $tPhone
Thanks.
""")

  smsContents = smsTemplate.substitute(d)
  from Util.Sms import SendSms
  #smsNo = GetOption("COURIER_COMPLAINT_R", bill.courierName)[::-1]
  smsNumbersBunch = GetOption("COURIER_COMPLAINT", bill.courierName)
  smsNoList = smsNumbersBunch.split("\n")
  smsNoAndNameList = []
  for x in smsNoList:
    if not x: continue
    y = x.replace(",", ";").split(";")
    smsNoAndNameList.append((y[0], y[1]))
  PrintInBox(str(smsNoAndNameList), waitForEnterKey=True)
  smsNoAndNameList = [(x.strip(), y) for (x, y) in smsNoAndNameList]


  PrintInBox(smsContents)
  print("Will send complaint to {}".format(smsNoAndNameList))
  for x in smsNoAndNameList:
    if raw_input("Send to {} (y/n)".format(x)).lower() == "y":
      SendSms(x, smsContents)
    else:
      print("Not sending sms...")
  return

def SendComplaintMessageForDocket(docketNumber):
  shipments = PersistentShipments().GetAllUndeliveredShipments()
  for s in shipments:
    if s.bill.docketNumber == docketNumber:
      return SendComplaintMessageForShipment(s)
  else:
    raise ShipmentException("Sorry no such docket is entered in system: {}".format(docketNumber))
  return


def main(args):
  global IS_DEMO
  IS_DEMO = args.isDemo

  if args.dbDeletedByMistake:
    DBDeletedDoWhatEverIsNecessary();
    import sys; sys.exit(0)

  if args.resendDispatchSms:
    docketNumbers = raw_input("Enter the docket numbers for which dispatch sms has to be resent: ")
    _ResendDispatchSMSForDocketNumbers(docketNumbers.split())
    import sys; sys.exit(0)

  if args.purgeOlderThan60Days:
    _PurgeShipmentsOlderThan60Days()
    import sys; sys.exit(0)

  if args.complaintDocket:
    complaintDocket = raw_input("Enter the docket for which complaint has to be sent: ")
    SendComplaintMessageForDocket(complaintDocket)
    import sys; sys.exit(0)

  if args.markSMSAsSentForDocket:
    _FormceMarkShipmentSMSAsSent(args.markSMSAsSentForDocket)

  if args.markMailAsSentForDocket:
    _FormceMarkShipmentMailAsSent(args.markMailAsSentForDocket)

  if args.markAllInfoAsSentForAllDockets:
    _MarkAllDispatchInfoAsSent()

  if args.forceMarkDeliveredDocket:
    _ForceMarkDocketAsDelivered(args.forceMarkDeliveredDocket)

  if args.newSnapshotForDockets:
    _NewSnapshotForDocket(args.newSnapshotForDockets)

  if args.sendScheduledMsgs:
    from whopaid.sendScheduledSMS import SendScheduledSMS
    SendScheduledSMS()

  if args.generateShipmentsJson:
    GenerateShipmentJsonNodes(int(GetOption("CONFIG_SECTION", "ShowShipmentStatusForNDays")))


  if args.FanoutDispatchInfo:
    FanOutDispatchInfoToAllComapnies(args)

  if args.trackAllUndeliveredCouriers:
    TrackAllShipments(args.trackDays)
    if LIST_OF_SHIPMENTS_IN_THIS_SCAN:
      PrintInBox("Following were delivered in this scan:")
      for i, s in enumerate(sorted(LIST_OF_SHIPMENTS_IN_THIS_SCAN, key=lambda s: s.bill.docketDate), start=1):
        print("{}.{:<50} : {:<15} : {}".format(i, s.bill.compName, DD_MMM_YYYY(s.bill.docketDate), s.bill.docketNumber))

  if args.showUndeliveredSmall:
    ShowUndeliveredSmalOnScreen()

  if args.sendAutomaricHeartBeat:
    SendAutomaticHeartBeat()

  if not args.hideReportofAwaitedShipments:
    ShowAwaitedShipmentsOnScreen()


def FanOutDispatchInfoToAllComapnies(args):
  ps = PersistentShipments()
  bills = GetAllBillsInLastNDays(args.trackDays)
  bills = [b for b in bills if b.docketDate]
  for b in bills:
    ps.GetOrCreateShipmentForBill(b)

  shipments = ps.GetAllStoredShipments()
  shipments = [s for s in shipments if s.ShouldWeTrackThis()] #Filter our deliverd shipments
  shipments = [s for s in shipments if not all([s.psWasShipmentMailEverSent(), s.psWasShipmentSmsEverSent()])]
  shipments = [s for s in shipments if s.daysPassed < max(MAX_DAYS_FOR_SENDING_NOTIFICATION, args.notifyDays)]
  shipments.sort(key=lambda s: s.bill.docketDate, reverse=True)

  cmds = []
  for shipment in shipments:
    try:
      if args.sendMailToAllCompanies and \
          not shipment.psWasShipmentMailEverSent() and \
          shipment.bill.billingCategory.lower() not in ["tracking"] and \
          shipment.isPaymentReminderEmailAddressAvailable():
        if 'y' == raw_input("{}\nSend mail for {} (y/n)?".format("_"*70, shipment)).lower():
          cmd = shipment.psSendMailForThisShipment
          cmds.append(cmd)
        else:
          print("Not sending mail...")
      if args.sendDispatchSms and \
         not shipment.psWasShipmentSmsEverSent() and \
         shipment.isSMSNoAvailable():
        if 'y' == raw_input("{}\nSend sms for {} (y/n)?".format("_"*70, shipment)).lower():
          cmd=shipment.psSendSmsForThisShipment
          cmds.append(cmd)
        else:
          print("Not sending sms...")
    except ShipmentException as ex:
      print(ex)
      #eat the exception after printing. We have printed our custom exception, its good enough. Move onto the next shipment.

  #To expedite the process. Otherwise the human sitting will have to wait long enough for all the inputs.
  for cmd in cmds:
    cmd()
  return

def TrackAllShipments(trackDays):
  ps = PersistentShipments()
  for b in GetAllBillsInLastNDays(trackDays):
    if b.docketDate:
      ps.GetOrCreateShipmentForBill(b)
  shipments = ps.GetAllStoredShipments()
  trackableShipments = [s for s in shipments if s.ShouldWeTrackThis()]
  trackableShipments.sort(key=lambda s: s.bill.docketDate)

  for i, shipment in enumerate(trackableShipments, start=1):
    try:
      old_status = shipment._track.status
      print("{}\n{} of {}| {} days| {}".format("_"*70, i, len(trackableShipments), shipment.daysPassed, shipment))
      new_status = shipment.TrackAndSave()  #One shipment per bill

      if old_status != new_status:
        PrintInBox("New status: {}".format(new_status), outliner=">")

      if not shipment.isDelivered and shipment.daysPassed > MAX_IN_TRANSIT_DAYS :
        raise ShipmentException("{} days back the following material was shipped but still not delivered\n{}".format(
          shipment.daysPassed, old_status))
      sleep(2)

    except ShipmentException as ex:
      PrintInBox(str(ex), outliner="X")
      pass

  return

def _MarkAllDispatchInfoAsSent():
  for s in  PersistentShipments().GetAllStoredShipments():
    s.psMarkSmsAsSent()
    s.psMarkMailAsSent()
  return


def DBDeletedDoWhatEverIsNecessary():
  """This will help when the db is accidently deleted. In that case, just mark all the information as already sent"""
  if raw_input("All the dockets will be marked as information_sent. Do you want to proceed (y/n)").lower()!='y':
    return
  NO_OF_DAYS = int(GetOption("CONFIG_SECTION", "ShowShipmentStatusForNDays"))
  bills = [b for b in GetAllBillsInLastNDays(NO_OF_DAYS) if b.docketDate]
  ps = PersistentShipments()
  for b in bills:
    ps.GetOrCreateShipmentForBill(b)
  shipments = ps.GetAllStoredShipments()
  for s in shipments:
    if s.isDelivered: continue
    s.psMarkSmsAsSent()
    s.psMarkMailAsSent()
    if s.IsSnapshotSaved() or not Courier.KnowHowToTrack(s.bill):
      s.psMarkShipmentDelivered()
  return

def GenerateShipmentJsonNodes(days):
  ps = PersistentShipments()
  shipments = [s for s in ps.GetAllStoredShipments() if s.daysPassed <= days]
  shipments.sort(key=lambda s: s.bill.docketDate, reverse=True)
  jsonData = [s.jsonNode for s in shipments]
  jsonFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), GetOption("CONFIG_SECTION", "ShipmentsJson"))
  with open(jsonFileName, "w") as j:
    json.dump(jsonData, j, indent=2)
  return


def ChangeCompName(fr, to):
  ps = PersistentShipments()
  for s in ps.GetAllStoredShipments():
    if s.bill.compName == fr:
      s.bill.compName = to
      s.save()
  return

if __name__ == '__main__':
  args = ParseOptions()

  if args.removeTrackingForDockets:
    _RemoveDocketFromIndex(args.removeTrackingForDockets)
    import sys; sys.exit(0)

  CheckConsistency()
  PersistentShipments().PurgeRedundantAwaitedShipments().shrink()
  main(args)
