
from __future__ import unicode_literals
from util_StoreSnapshot import StoreDeliveryProofWithPhantomScript
from Util.Config import GetRawOption
TIMEOUT_IN_SECS=30
import urllib2
from Util.Misc import StripHTMLTags

class DTDCCourier():
  def __init__(self, shipment, bill):
    self.bill = bill
    self.shipment = shipment

  def GetStatus(self):
    self.referer = "http://dtdc.in/tracking/tracking_results.asp"
    self.reqUrl = "http://track.dtdc.com/ctbs-config-admin/customerInterface.tr?submitName=showCITrackingDetails&cType=Consignment&cnNo={self.bill.docketNumber}".format(**locals())
    self.FORM_DATA = ""
    req = urllib2.Request(self.reqUrl)
    req.add_header("Host" , "track.dtdc.com")
    req.add_header('Referer', self.referer)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36")
    resp = urllib2.urlopen(req, self.FORM_DATA, timeout=TIMEOUT_IN_SECS)
    html = resp.read().decode('utf-8')
    if resp.code != 200 :
      raise Exception("Got {} reponse from DTDC server for bill: {}".format(resp.code, self.bill))
    res =  self._get_status_from_dtdc_html_resp(html)
    return res

  def _get_status_from_dtdc_html_resp(self, html):
    lineSucceedingStatus = r'<div id="linkId">'
    last5Lines = ["", "", "", "", ""]
    for eachLine in html.split("\n"):
      if eachLine.find(lineSucceedingStatus) != -1:
        result = StripHTMLTags("".join(last5Lines)).strip()
        return result
      else:
        last5Lines = last5Lines[1:5]
        last5Lines.append(eachLine)
    else:
      raise Exception("Cannot parse dtdc response for bill: {}".format(self.bill))


  def GetStatus2(self):
    self.reqUrl = "http://dtdc.in/tracking/tracking_results.asp"
    self.FORM_DATA = GetRawOption("COURIER_FORM_DATA", "DTDC").format(docket=self.bill.docketNumber)
    req = urllib2.Request(self.reqUrl)
    req.add_header("Host" , "dtdc.in")
    req.add_header("Content-Type" , "application/x-www-form-urlencoded")
    req.add_header('Referer', self.reqUrl)
    req.add_header('Origin', 'http://dtdc.in')
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36")
    resp = urllib2.urlopen(req, self.FORM_DATA, timeout=TIMEOUT_IN_SECS)
    html = resp.read().decode('utf-8')
    if resp.code != 200 :
      raise Exception("Got {} reponse from DTDC server for bill: {}".format(resp.code, self.bill))
    res =  self._get_status_from_dtdc_html_resp2(html)
    return res

  def _get_status_from_dtdc_html_resp2(self, html):
    linePreceedingStatus = r'<td width="25%" nowrap="nowrap" class="click">'
    grabNextLineAsStatus = False
    for eachLine in html.split("\n"):
      if eachLine.find(linePreceedingStatus) != -1:
        grabNextLineAsStatus = True
        continue
      if grabNextLineAsStatus:
        #Return the line which appears after: "Status :"
        print(StripHTMLTags(eachLine.strip()))
        return StripHTMLTags(eachLine.strip())
    else:
      raise Exception("Cannot parse dtdc response for bill: {}".format(self.bill))

  def StoreDeliveryProof(self):
    StoreDeliveryProofWithPhantomScript(self.bill, "courier\\dtdc_snapshot.js", self.FORM_DATA, self.reqUrl)

