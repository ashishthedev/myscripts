
from Util.Config import GetAppDir, GetOption, GetRawOption
from Util.Misc import YYYY_MM_DD, StripHTMLTags

from HTMLParser import HTMLParser
import os
import subprocess
import urllib2

MAPPING = dict()
class Courier():
  """
  If a new courier gets added, implement that class and instantiate in __init__
  All the sublclasses will implement methods. Ideally it should be an ABC
  """
  def __init__(self, b):
    for courierInitials, class_ in MAPPING.iteritems():
      if b.courierName.lower().strip().startswith(courierInitials):
        self.courier = class_(b)
        break
    else:
      print("We do not know how to track: {}. Will mark it as delivered".format(b.courierName))
      self.courier = DummyCourier(b)

  @classmethod
  def KnowHowToTrack(cls, b):
    for courierInitials, class_ in MAPPING.iteritems():
      if b.courierName.lower().strip().startswith(courierInitials.lower()):
        return True
    return False


  def GetStatus(self):
    try:
      return self.courier.GetStatus()
    except urllib2.URLError as e:
      if hasattr(e, 'reason'):
        print("We failed to reach the server.\nReason {}".format(self.courier.bill.courierName, e.reason))
      elif hasattr(e, 'code'):
        print("The server couldn't fulfil the request\nError code: {}".format(e.code))
    except Exception as e:
      print(str(e))
      return ""

  def StoreSnapshot(self):
    self.courier.StoreSnapshot()

  def IsSnapshotSaved(self):
    if hasattr(self.courier, 'bill'):
      return True if os.path.exists(FullPathForSnapshotOfBill(self.courier.bill)) else False
    else:
      return True if os.path.exists(FullPathForSnapshotOfBill(self.courier.b)) else False



class DummyCourier():
  def __init__(self, bill):
    self.bill = bill

  def GetStatus(self):
    return "Dummy Courier is delivered" #This status should have the word delivered

  def StoreSnapshot(self):
    return None

def FullPathForSnapshotOfBill(b):
  """All the information considered in filename is immutable"""
  PREFERRED_FILEFORMAT = ".jpeg"
  fileName = "{date}_{compName}_BillNo#{billNumber}_{docketNumber}".format(date=YYYY_MM_DD(b.docketDate),
      compName=b.compName, billNumber=b.billNumber, docketNumber = b.docketNumber)
  fileName.replace(" ", "_")
  fileName = "".join([x for x in fileName if x.isalnum() or x in['_', '-']])
  fileName = fileName + PREFERRED_FILEFORMAT
  fullPath = os.path.normpath(os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "DocketSnapshotsRelPath"),fileName))
  return fullPath

def StoreSnapshotWithPhantomScript(b, scriptPath, formData, reqUrl):
  #TODO: Remove hardcoding of path
  PHANTOM = "B:\\Tools\\PhantomJS\\phantomjs-1.9.1-windows\\phantomjs.exe"
  fullPath = FullPathForSnapshotOfBill(b)

  if os.path.exists(fullPath):
    i = fullPath.rfind(".")
    fullPath ="{}_new{}".format(fullPath[:i], fullPath[i:])

  for p in [PHANTOM, scriptPath]:
    if not os.path.exists(p): raise Exception("Path not present : {}".format(p))

  args = [PHANTOM, scriptPath, fullPath, b.docketNumber, formData, reqUrl]
  subprocess.check_call(args)

  if not os.path.exists(fullPath):
    raise Exception("Could not store the snapshot at location: {}".format(fullPath))

class TrackonCourier():
  def __init__(self, bill):
    self.bill = bill
    self.reqUrl = "http://trackoncourier.com/TrackonConsignment.aspx"

  def GetStatus(self):
    self.FORM_DATA = GetRawOption("COURIER_FORM_DATA", "Trackon").format(docket=self.bill.docketNumber)
    req = urllib2.Request(self.reqUrl)
    req.add_header("Content-Type" , "application/x-www-form-urlencoded")
    req.add_header('Referer', 'http://trackoncourier.com/Default.aspx')
    req.add_header('Origin', 'http://trackoncourier.com')
    resp = urllib2.urlopen(req, self.FORM_DATA)
    html = resp.read()
    if resp.code != 200 :
      raise Exception("Got {} reponse from Trackon server for bill: {}".format(resp.code, self.bill))
    res =  self._get_status_from_trackon_html_resp(html)
    return res

  def _get_status_from_trackon_html_resp(self, html):
    class MLStripper(HTMLParser):
      def __init__(self):
        self.reset()
        self.fed = []
        self.recording = False
      def handle_data(self, d):
        if self.recording:
          d = "".join([x.strip() for x in d.splitlines() if x])
          self.fed.append(d)

      def get_data(self):
        return ''.join(self.fed)
      def handle_starttag(self, tag, att):
        if tag == "h3":
          self.recording = True
      def handle_endtag(self, tag):
        if tag == "h3":
          self.recording = False

    s = MLStripper()
    s.feed(html)
    return s.get_data()

  def StoreSnapshot(self):
    StoreSnapshotWithPhantomScript(self.bill, "courier\\trackon_snapshot.js", self.FORM_DATA, self.reqUrl)

class ProfessionalCourier():
  def __init__(self, bill):
    self.bill = bill
    self.reqUrl = "http://www.tpcindia.com/Tracking2014.aspx?id={docket}&type=0&service=0".format(docket=self.bill.docketNumber.strip())

  def GetStatus(self):
    self.FORM_DATA = ""
    if not hasattr(self, "reqUrl"):
      self.reqUrl = "http://www.tpcindia.com/Tracking2014.aspx?id={docket}&type=0&service=0".format(docket=self.bill.docketNumber.strip())
    req = urllib2.Request(self.reqUrl)
    req.add_header('Host', 'www.tpcindia.com')
    req.add_header('Referer', 'http://www.tpcindia.com/')
    resp = urllib2.urlopen(req)
    html = resp.read()
    if resp.code != 200 :
      raise Exception("Got {} reponse from Professinal server for bill: {}".format(resp.code, self.bill))
    res =  self._get_status_from_professional_html_resp(html)
    return res

  def _get_status_from_professional_html_resp(self, html):
    #Logic: The bareline with resultsId will have the status
    resultsId = "ctl00_ContentPlaceHolder1_lbl_track"
    for eachLine in html.split("\n"):
      if eachLine.find(resultsId) != -1:
        return StripHTMLTags(eachLine.strip())
    else:
      raise Exception("Cannot parse ProfessionalCourier response for bill: {}".format(self.bill))

  def StoreSnapshot(self):
    StoreSnapshotWithPhantomScript(self.bill, "courier\\professional_snapshot.js", self.FORM_DATA, self.reqUrl)

class NitcoTransport():
  def __init__(self, bill):
    self.bill = bill
    self.reqUrl ="http://202.177.175.171/customer_track/grinformation.aspx?id={docket}" .format(docket=self.bill.docketNumber.strip())

  def GetStatus(self):
    self.FORM_DATA = GetRawOption("COURIER_FORM_DATA", "Nitco").format(docket=self.bill.docketNumber)
    req = urllib2.Request(self.reqUrl)
    req.add_header('Host', '202.177.175.171')
    req.add_header('Origin', 'http://202.177.175.171')
    req.add_header("Content-Type" , "application/x-www-form-urlencoded")
    req.add_header('Referer', self.reqUrl)
    resp = urllib2.urlopen(req, self.FORM_DATA)
    html = resp.read()
    if resp.code != 200 :
      raise Exception("Got {} reponse from Nitco server for bill: {}".format(resp.code, self.bill))
    res =  self._get_status_from_nitco_html_resp(html)
    return res

  def _get_status_from_nitco_html_resp(self, html):
    resultsId = "ctl00_ContentPlaceHolder1_Label7".lower()
    for eachLine in html.split("\n"):
      if eachLine.lower().find(resultsId) != -1:
        return StripHTMLTags(eachLine.strip())
    else:
      raise Exception("Exception: Cannot parse Nitco response for bill: {}".format(self.bill))

  def StoreSnapshot(self):
    StoreSnapshotWithPhantomScript(self.bill, "courier\\nitco.js", self.FORM_DATA, self.reqUrl)

class VRLLogistics():
  def __init__(self, bill):
    self.bill = bill

  def GetStatus(self):
    self.FORM_DATA = ""
    self.reqUrl = "http://vrlgroup.in/vrlwebs/lrtrack.aspx?lno={docket}".format(docket=self.bill.docketNumber.strip())
    req = urllib2.Request(self.reqUrl)
    req.add_header('Host', 'vrlgroup.in')
    resp = urllib2.urlopen(req)
    html = resp.read()
    if resp.code != 200 :
      raise Exception("Got {} reponse from VRL for bill: {}".format(resp.code, self.bill))
    res =  self._get_status_from_vrl_html_resp(html)
    return res

  def _get_status_from_vrl_html_resp(self, html):
    html = html.replace("><", ">\n<")
    resultsId="<span class='style4b'>Delivery Details".lower()
    for eachLine in html.split("\n"):
      if eachLine.lower().find(resultsId) != -1:
        return StripHTMLTags(eachLine.strip())
    else:
      raise Exception("Exception: Cannot parse vrl response for : {}".format(self.bill))

  def StoreSnapshot(self):
    StoreSnapshotWithPhantomScript(self.bill, "courier\\vrl_snapshot.js", self.FORM_DATA, self.reqUrl)


class LaljiMuljiTransport():
  def __init__(self, bill):
    self.bill = bill
    self.FORM_DATA = ""
    self.reqUrl = "http://lmterp.com/ivcargo/Ajax.do?pageId=9&eventId=3&wayBillNumber={docket}&accountGroupId=201" .format(docket=self.bill.docketNumber.strip())

  def GetStatus(self):
    req = urllib2.Request(self.reqUrl)
    req.add_header('Host', 'lmterp.com')
    req.add_header('Referer', 'http://lmtco.com/')
    resp = urllib2.urlopen(req)
    html = resp.read()
    if resp.code != 200 :
      raise Exception("Got {} reponse from LaljiMuljiTransport server for bill: {}".format(resp.code, self.bill))
    res =  self._get_status_from_lalajiMuljiTr_html_resp(html)
    return res

  def _get_status_from_lalajiMuljiTr_html_resp(self, html):
    #Logic: Find line having "lr status"
    status=""
    sentinel = "lr status".lower()
    for eachLine in html.split("\n"):
      eachLine = StripHTMLTags(eachLine).lower()
      recording = False
      for x in eachLine.split(":"):
        if x.find(sentinel) != -1:
          recording = True
          if recording:
            status += x
    return status

  def StoreSnapshot(self):
    StoreSnapshotWithPhantomScript(self.bill, "courier\\laljimulji_snapshot.js", self.FORM_DATA, "http://lmtco.com/")

class FirstFlightCourier():
  def __init__(self, bill):
    self.bill = bill
    self.FORM_DATA = ""

  def GetStatus(self):
    self.reqUrl = "http://www.firstflight.net/n_contrac_new_12Digit_New.asp?tracking1={docket}".format(docket=self.bill.docketNumber.strip())
    req = urllib2.Request(self.reqUrl)
    req.add_header('Host', 'www.firstflight.net')
    resp = urllib2.urlopen(req)
    html = resp.read()
    if resp.code != 200 :
      raise Exception("Got {} reponse from First Flight server for bill: {}".format(resp.code, self.bill))
    res =  self._get_status_from_first_flight_html_resp(html)
    return res

  def _get_status_from_first_flight_html_resp(self, html):
    #Logic: We are going to parse the stripped html
    #1. Find docket number
    #2. All following lines are status till line having </tr>
    recordingStatus = False
    status = ""
    for eachLine in html.split("\n"):
      if not eachLine: continue
      bareLine = StripHTMLTags(eachLine.strip())
      if bareLine.lower().find(self.bill.docketNumber.lower()) != -1:
        recordingStatus = True
      if recordingStatus and eachLine.lower().strip().find("</tr>") != -1:
        return status
      if recordingStatus:
        status += " " + bareLine

    raise Exception("Cannot parse firstflight response for bill: {}".format(self.bill))

  def StoreSnapshot(self):
    StoreSnapshotWithPhantomScript(self.bill, "courier\\firstflight_snapshot.js", self.FORM_DATA, self.reqUrl)

class BluedartCourier():
  def __init__(self, bill):
    self.bill = bill
    self.reqUrl = "http://www.bluedart.com/servlet/RoutingServlet"

  def GetStatus(self):
    self.FORM_DATA = GetRawOption("COURIER_FORM_DATA", "Bluedart").format(docket=self.bill.docketNumber)
    req = urllib2.Request(self.reqUrl)
    req.add_header("Content-Type" , "application/x-www-form-urlencoded")
    req.add_header('Referer', 'http://www.bluedart.com/')
    req.add_header('Origin', 'http://www.bluedart.com')
    resp = urllib2.urlopen(req, self.FORM_DATA)
    html = resp.read()
    if resp.code != 200 :
      raise Exception("Got {} reponse from Bluedart server for bill: {}".format(resp.code, self.bill))
    res =  self._get_status_from_bluedart_html_resp(html)
    return res

  def _get_status_from_bluedart_html_resp(self, html):
    #Logic: We are going to parse the stripped html
    #1. Find word status
    #2. All following lines are status till line having phrase "your email id"
    recordingStatus = False
    status = ""
    for eachLine in html.split("\n"):
      bareLine = StripHTMLTags(eachLine.strip())
      if bareLine.strip().lower() == "status":
        recordingStatus = True
      if bareLine.lower().strip().startswith("your email id"):
        return status
      if recordingStatus:
        status += " " + bareLine

    raise Exception("Cannot parse bluedart response for bill: {}".format(self.bill))

  def StoreSnapshot(self):
    StoreSnapshotWithPhantomScript(self.bill, "courier\\bluedart_snapshot.js", self.FORM_DATA, self.reqUrl)

class OverniteCourier():
  def __init__(self, bill):
    self.bill = bill
    self.reqUrl = "http://www.overnitenet.com/WebTrack.aspx"

  def GetStatus(self):
    self.FORM_DATA = GetRawOption("COURIER_FORM_DATA", "Overnite").format(docket=self.bill.docketNumber)
    if not hasattr(self, "reqUrl"):
      self.reqUrl = "http://www.overnitenet.com/WebTrack.aspx"
    req = urllib2.Request(self.reqUrl)
    req.add_header("Host" , "www.overnitenet.com")
    req.add_header("Content-Type" , "application/x-www-form-urlencoded")
    req.add_header('Referer', self.reqUrl)
    req.add_header('Origin', 'http://www.overnitenet.com')
    resp = urllib2.urlopen(req, self.FORM_DATA)
    html = resp.read()
    if resp.code != 200 :
      raise Exception("Got {} reponse from Overnite server for bill: {}".format(resp.code, self.bill))
    res =  self._get_status_from_overnite_html_resp(html)
    return res

  def _get_status_from_overnite_html_resp(self, html):
    resultsId = "ctl00_CntPlaceHolderDetails_GridViewOuter_ctl02_lblStatus"
    for eachLine in html.split("\n"):
      if eachLine.find(resultsId) != -1:
        return StripHTMLTags(eachLine.strip())
    else:
      raise Exception("Cannot parse overnite response for bill: {}".format(self.bill))

  def StoreSnapshot(self):
    StoreSnapshotWithPhantomScript(self.bill, "courier\\overnite_snapshot.js", self.FORM_DATA, self.reqUrl)

MAPPING = {
    "overn": OverniteCourier,
    "trac" : TrackonCourier,
    "bluedart": BluedartCourier,
    "first": FirstFlightCourier,
    "profess" :ProfessionalCourier,
    "nitco": NitcoTransport,
    "lalji": LaljiMuljiTransport,
    "vrl": VRLLogistics,
    }

if __name__ == '__main__':
  DOCKET = "8037705270"
  RESULTS = "res.html"
  with open(RESULTS, "w") as f:
    pass
