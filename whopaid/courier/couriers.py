import urllib2
from HTMLParser import HTMLParser
from UtilMisc import YYYY_MM_DD
from UtilConfig import GetAppDir, GetOption
import subprocess
import os

class Courier():
    """
    If a new courier gets added, implement that class and instantiate in __init__
    """
    def __init__(self, b):
        if b.courierName.lower().strip().startswith("overn"):
            self.courier = OverniteCourier(b)
        elif b.courierName.lower().strip().startswith("trac"):
            self.courier = TrackonCourier(b)
        elif b.courierName.lower().strip().startswith("bluedart"):
            self.courier = BluedartCourier(b)
        else:
            print("We do not know how to track: {}. Will mark it as delivered".format(b.courierName))
            self.courier = DummyCourier(b)

    def GetStatus(self):
        return self.courier.GetStatus()

    def StoreSnapshot(self):
        self.courier.StoreSnapshot()

class DummyCourier():
    def __init__(self, b):
        self.b = b

    def GetStatus(self):
        return "Dummy Courier is delivered" #This status should have the word delivered

    def StoreSnapshot(self):
        return None

class TrackonCourier():
    def __init__(self, bill):
        self.bill = bill
    def GetStatus(self):
        FORM_DATA="""__VIEWSTATE=%2FwEPDwUKMTM2ODMyNjQ5NA9kFgJmD2QWAgICD2QWCAIFDw8WAh4HVmlzaWJsZWhkZAIHDw8WAh8AaGRkAgkPDxYCHgRUZXh0ZWRkAgsPZBYEAgEPZBYCAgEPFgIeA3NyYwUafi9pbWFnZXMvdHJhY2tTaGlwbWVudC5qcGdkAgMPFgIeC18hSXRlbUNvdW50AgEWAgIBD2QWBGYPFQQJMzQ1MTM4MDAwCURFTElWRVJFRAswMSBKdWwgMjAxMw53aXRoIFNJR05BVFVSRWQCAQ8WAh8DAgMWBgIBD2QWAmYPFQYJR0hBWklBQkFEABFERUxISSBIRUFEIE9GRklDRQwxMDAzNDA5NDkxNDkKMjkvMDYvMjAxMwUxOTozOWQCAg9kFgJmDxUGCkRFTEhJIEguTy4AFVBBVEhBTktPVC0wMTg2MjIzNDM1MgwxMDAwMzA0MTIyMjAKMzAvMDYvMjAxMwUyMDowN2QCAw9kFgJmDxUGCVBBVEhBTktPVAAFICAtICABMAowMS8wNy8yMDEzBTE1OjA2ZBgBBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAQUdY3RsMDAkTG9naW4yJGltZ3RyYWNrb25TdWJtaXRTjdVBMrmra84ziY%2F00Eqw1oHLhA%3D%3D&ctl00%24Login2%24txtUsername=&ctl00%24Login2%24txtPassword=&ctl00%24ContentPlaceHolder1%24Tracking1%24hidAWB=1{docket}&ctl00%24ContentPlaceHolder1%24Tracking1%24trackno={docket}&ctl00%24ContentPlaceHolder1%24Tracking1%24trackonSubmit=&ctl00%24ContentPlaceHolder1%24Tracking1%24primetrackno=&__EVENTVALIDATION=%2FwEWCQLUq4iMCAK00vXCBwLx3cW8DwKtpJblAwL4ya2YBgK5jN%2BIBgL8nsXZCgLCs5bTDALIlpeaCdsVYmlvDIpNyXh9yAT0H9sQIYi4
        """.format(docket=self.bill.docketNumber)
        req = urllib2.Request("http://trackoncourier.com/TrackonConsignment.aspx")
        req.add_header("Content-Type" , "application/x-www-form-urlencoded")
        req.add_header('Referer', 'http://trackoncourier.com/Default.aspx')
        req.add_header('Origin', 'http://trackoncourier.com')
        resp = urllib2.urlopen(req, FORM_DATA)
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
        b = self.bill
        #TODO: Remove hardcoding of path
        PHANTOM = "B:\\Tools\\PhantomJS\\phantomjs-1.9.1-windows\\phantomjs.exe"
        SCRIPT = "Courier\\trackon_snapshot.js"
        PREFERRED_FILEFORMAT = ".jpeg"
        fileName = "{date}_{compName}_BillNo#{billNumber}_{docketNumber}".format(date=YYYY_MM_DD(b.docketDate),
                compName=b.compName, billNumber=b.billNumber, docketNumber = b.docketNumber)

        fileName.replace(" ", "_")
        fileName = "".join([x for x in fileName if x.isalnum() or x in['_', '-']])
        fileName = fileName + PREFERRED_FILEFORMAT
        DESTINATION_FILE = os.path.normpath(os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "DocketSnapshotsRelPath"),fileName))

        if os.path.exists(DESTINATION_FILE):
            i = DESTINATION_FILE.rfind(".")
            DESTINATION_FILE ="{}_new{}".format(DESTINATION_FILE[:i], DESTINATION_FILE[i:])

        for p in [PHANTOM, SCRIPT]:
            if not os.path.exists(p): raise Exception("Path not present : {}".format(p))

        args = [PHANTOM, SCRIPT, DESTINATION_FILE, b.docketNumber]
        subprocess.check_call(args)

        if not os.path.exists(DESTINATION_FILE):
            raise Exception("Could not store the snapshot at location: {}".format(DESTINATION_FILE))

        return
class BluedartCourier():
    def __init__(self, bill):
        self.bill = bill

    def GetStatus(self):
        FORM_DATA="""handler=tnt&action=awbquery&awb=awb&numbers={docket}""".format(docket=self.bill.docketNumber)
        req = urllib2.Request("http://www.bluedart.com/servlet/RoutingServlet")
        req.add_header("Content-Type" , "application/x-www-form-urlencoded")
        req.add_header('Referer', 'http://www.bluedart.com/')
        req.add_header('Origin', 'http://www.bluedart.com')
        resp = urllib2.urlopen(req, FORM_DATA)
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
            if bareLine.lower() == "status":
                recordingStatus = True
            if bareLine.lower().startswith("your email id"):
                return status
            if recordingStatus:
                status += " " + bareLine

        raise Exception("Cannot parse bluedart response for bill: {}".format(self.bill))

    def StoreSnapshot(self):
        b = self.bill
        #TODO: Remove hardcoding of path
        PHANTOM = "B:\\Tools\\PhantomJS\\phantomjs-1.9.1-windows\\phantomjs.exe"
        SCRIPT = "courier\\bluedart_snapshot.js"
        PREFERRED_FILEFORMAT = ".jpeg"
        fileName = "{date}_{compName}_BillNo#{billNumber}_{docketNumber}".format(date=YYYY_MM_DD(b.docketDate),
                compName=b.compName, billNumber=b.billNumber, docketNumber = b.docketNumber)

        fileName.replace(" ", "_")
        fileName = "".join([x for x in fileName if x.isalnum() or x in['_', '-']])
        fileName = fileName + PREFERRED_FILEFORMAT
        DESTINATION_FILE = os.path.normpath(os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "DocketSnapshotsRelPath"),fileName))

        if os.path.exists(DESTINATION_FILE):
            i = DESTINATION_FILE.rfind(".")
            DESTINATION_FILE ="{}_new{}".format(DESTINATION_FILE[:i], DESTINATION_FILE[i:])

        for p in [PHANTOM, SCRIPT]:
            if not os.path.exists(p): raise Exception("Path not present : {}".format(p))

        args = [PHANTOM, SCRIPT, DESTINATION_FILE, b.docketNumber]
        subprocess.check_call(args)

        if not os.path.exists(DESTINATION_FILE):
            raise Exception("Could not store the snapshot at location: {}".format(DESTINATION_FILE))

        return

class OverniteCourier():
    def __init__(self, bill):
        self.bill = bill

    def GetStatus(self):
        FORM_DATA="""__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=%2FwEPDwUINjI1NjcyOTQPZBYCZg9kFgICAw9kFgICCQ9kFgYCAQ9kFgICAQ9kFgQCDA9kFgJmD2QWAgIBDzwrAA0AZAISDw8WAh4HVmlzaWJsZWhkZAICDw8WAh4EVGV4dGVkZAIDDw8WAh8BZWRkGAMFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYBBSdjdGwwMCRDbnRQbGFjZUhvbGRlckRldGFpbHMkaW1nYnRuVHJhY2sFJmN0bDAwJENudFBsYWNlSG9sZGVyRGV0YWlscyRNdWx0aVZpZXcxDw9kZmQFKWN0bDAwJENudFBsYWNlSG9sZGVyRGV0YWlscyRHcmlkVmlld091dGVyD2dkyjnzKNlK1F0lha2VPD203I0wnWY%3D&__EVENTVALIDATION=%2FwEWBwL5m5XfBgL49YzrBwL59YzrBwL3mqaFCwLjvLD3DQLX57OEBgKA6qoFptDBWKLK0LmchCP7GBi3QkiQbAA%3D&ctl00%24CntPlaceHolderDetails%24rdbListTrackType=1&ctl00%24CntPlaceHolderDetails%24txtAWB={docket}&ctl00%24CntPlaceHolderDetails%24ValidatorCalloutExtender6_ClientState=&ctl00%24CntPlaceHolderDetails%24imgbtnTrack.x=29&ctl00%24CntPlaceHolderDetails%24imgbtnTrack.y=7""".format(docket=self.bill.docketNumber)

        req = urllib2.Request("http://www.overnitenet.com/WebTrack.aspx")
        req.add_header("Content-Type" , "application/x-www-form-urlencoded")
        req.add_header('Referer', 'http://www.overnitenet.com/WebTrack.aspx')
        req.add_header('Origin', 'http://www.overnitenet.com')
        resp = urllib2.urlopen(req, FORM_DATA)
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
        b = self.bill
        #TODO: Remove hardcoding of path
        PHANTOM = "B:\\Tools\\PhantomJS\\phantomjs-1.9.1-windows\\phantomjs.exe"
        SCRIPT = "courier\\overnite_snapshot.js"
        PREFERRED_FILEFORMAT = ".jpeg"
        fileName = "{date}_{compName}_BillNo#{billNumber}_{docketNumber}".format(date=YYYY_MM_DD(b.docketDate),
                compName=b.compName, billNumber=b.billNumber, docketNumber = b.docketNumber)

        fileName.replace(" ", "_")
        fileName = "".join([x for x in fileName if x.isalnum() or x in['_', '-']])
        fileName = fileName + PREFERRED_FILEFORMAT
        DESTINATION_FILE = os.path.normpath(os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "DocketSnapshotsRelPath"),fileName))
        if os.path.exists(DESTINATION_FILE):
            i = DESTINATION_FILE.rfind(".")
            DESTINATION_FILE ="{}_new{}".format(DESTINATION_FILE[:i], DESTINATION_FILE[i:])

        for p in [PHANTOM, SCRIPT]:
            if not os.path.exists(p): raise Exception("Path not present : {}".format(p))

        args = [PHANTOM, SCRIPT, DESTINATION_FILE, b.docketNumber]
        subprocess.check_call(args)
        if not os.path.exists(DESTINATION_FILE):
            raise Exception("Could not store the snapshot at location: {}".format(DESTINATION_FILE))

        return

def StripHTMLTags(html):
    class MLStripper(HTMLParser):
        def __init__(self):
            self.reset()
            self.fed = []
        def handle_data(self, d):
            self.fed.append(d)
        def get_data(self):
            return ''.join(self.fed)

    s = MLStripper()
    s.feed(html)
    return s.get_data()

if __name__ == '__main__':
    DOCKET = "8037705270"
    RESULTS = "res.html"
    with open(RESULTS, "w") as f:
        pass
