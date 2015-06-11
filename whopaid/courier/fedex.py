from __future__ import unicode_literals
from util_StoreSnapshot import StoreDeliveryProofWithPhantomScript, StoreEDDProofWithPhantomScript
from Util.Config import GetOption
from Util.Misc import ParseDateFromString, DD_MMM_YYYY, PrintInBox
from Util.Sms import SendSms
from whopaid.off_comm import SendOfficialEmail
TIMEOUT_IN_SECS=30

import urllib2

class FedExCourier():
  def __init__(self, shipment, bill):
    self.bill = bill
    self.shipment = shipment
    self.shipment.SetEDD("")

  def GetStatus(self):
    self.FORM_DATA = ""
    self.reqUrl = "https://www.fedex.com/trackingCal/track?" + """action=trackpackages&locale=en_IN&version=1&format=json&data={%22TrackPackagesRequest%22:{%22appType%22:%22WTRK%22,%22uniqueKey%22:%22%22,%22processingParameters%22:{},%22trackingInfoList%22:[{%22trackNumberInfo%22:{%22trackingNumber%22:%22""" + str(self.bill.docketNumber) + """%22,%22trackingQualifier%22:%22%22,%22trackingCarrier%22:%22%22}}]}}&_=1421213504837"""
    self.headers = {
        "Host": "www.fedex.com",
        "Referer": "https://www.fedex.com/fedextrack/WTRK/index.html?action=track&trackingnumber={docket}&cntry_code=in&fdx=1490".format(docket=self.bill.docketNumber),
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        }
    req = urllib2.Request(self.reqUrl)
    for k,v in self.headers.iteritems():
      req.add_header(k, v)
    resp = urllib2.urlopen(req, self.FORM_DATA, timeout=TIMEOUT_IN_SECS)
    if resp.code != 200 :
      raise Exception("Got {} reponse from FedEx server for bill: {}".format(resp.code, self.bill))
    import json
    data = json.load(resp)

    debugJson = True
    debugJson = False
    if debugJson:
      #Set it to true to debug
      import pprint
      logFile = "b:\\desktop\\jsonData.json"
      with open(logFile, "w") as fout:
        pprint.pprint(data, fout)
        print("Json written to {}".format(logFile))

    resCode = data["TrackPackagesResponse"]["packageList"][0]["keyStatusCD"]
    if resCode.lower() == "dl":
      res = data["TrackPackagesResponse"]["packageList"][0]["keyStatus"]
      receiver = data["TrackPackagesResponse"]["packageList"][0]["receivedByNm"]
      self.shipment.actualDeliveryDate = data["TrackPackagesResponse"]["packageList"][0]["displayActDeliveryDt"]
      return res + " Received by: {}".format(receiver)
    else:
      if not self.shipment.GetEDD():
        dt = data["TrackPackagesResponse"]["packageList"][0]["displayEstDeliveryDt"]
        if dt:
          self.shipment.SetEDD(dt)
          snapshotUrl = """https://www.fedex.com/apps/fedextrack/?tracknumbers={docket}&cntry_code=in""".format(docket=self.bill.docketNumber)
          StoreEDDProofWithPhantomScript(self.bill, "courier\\fedex_snapshot.js", self.FORM_DATA, snapshotUrl, ParseDateFromString(self.shipment.GetEDD()))
          PrintInBox("Stored the snapshot for EDD={edd} for docket: {dn} company: {cn}".format(edd=self.shipment.GetEDD(), dn=self.bill.docketNumber, cn=self.bill.compName))

      return data["TrackPackagesResponse"]["packageList"][0]["keyStatus"] + " Estimated Delivery at: " + data["TrackPackagesResponse"]["packageList"][0]["displayEstDeliveryDateTime"]
    return None

  def SendDeliveryDaysMsgToOwners(self):
    print("About to send delivery msg to owners for docket: {}".format(self.bill.docketNumber))
    if not self.shipment.GetEDD():
      print("No EDD present for {}".format(self.bill.docketNumber))
      return
    if not hasattr(self.shipment, 'actualDeliveryDate'):
      print("No ADD present for {}".format(self.bill.docketNumber))
      return

    estimatedDateObj = ParseDateFromString(self.shipment.GetEDD())
    actualDelDateObj = ParseDateFromString(self.shipment.actualDeliveryDate)
    smsNoList = [x[::-1] for x in GetOption("SMS_SECTION", "DelayedDeliveryReportSMSR").split(",") if x.strip()]
    delay = (actualDelDateObj - estimatedDateObj).days
    from string import Template
    smsContentsTemplate = Template("""
      FedEx $tDeliveryNature
      Days Taken: $tDaysTaken
      $tCompName
      Estimated: $tEstDate
      Acutal: $tActDate
      Docket: $tDocketNumber
    """)

    docketDateObj = ParseDateFromString(self.bill.docketDate)
    d = dict()
    d["tCompName"] = self.bill.compName
    d["$tEstDate"] = DD_MMM_YYYY(estimatedDateObj)
    d["tActDate"] = DD_MMM_YYYY(actualDelDateObj)
    d["tDocketNumber"] = self.bill.docketNumber
    d["tDaysTaken"] = (actualDelDateObj - docketDateObj).days

    if delay < 0:
      d["tDeliveryNature"] = "early delivery by {} days".format(-1*delay)
    elif delay == 0:
      d["tDeliveryNature"] = "delivered on exact mentioned date"
    else:
      d["tDeliveryNature"] = "late delivery by {} days".format(delay)

    smsContents = smsContentsTemplate.substitute(d)

    for x in smsNoList:
      SendSms(x, smsContents)
      print("Sending sms to {}\n{}".format(x,smsContents))

    if delay > 0:
      emailSubject = "FedEx Late Delivery: {}".format(self.bill.compName)
      toMailList = [k[::-1] for k in GetOption("SMS_SECTION", "DelayedDeliveryReportMailIdsR").split(",") if k.strip()]
      ccMailList = None
      bccMailList = None
      mailBody = smsContents
      SendOfficialEmail(emailSubject,
          None,
          toMailList,
          ccMailList,
          bccMailList,
          mailBody,
          textType="html",
          fromDisplayName = "FedEx Late Delivery")

    return


  def StoreDeliveryProof(self):
    self.SendDeliveryDaysMsgToOwners()
    snapshotUrl = """https://www.fedex.com/apps/fedextrack/?tracknumbers={docket}&cntry_code=in""".format(docket=self.bill.docketNumber)
    StoreDeliveryProofWithPhantomScript(self.bill, "courier\\fedex_snapshot.js", self.FORM_DATA, snapshotUrl)
    return
