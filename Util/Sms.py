##########################################################################
##
## This file contains a routine to send files to specific email address
##
## Author: Ashish Anand
##
##########################################################################

from Util.Config import GetAppDirPath, GetOption
from Util.Decorators import RetryNTimes
from Util.Misc import PrintInBox

import os
import subprocess
import urllib2

GNOKII_PATH = os.path.join(GetAppDirPath(), "code", "misc", "gnokii", "gnokii.exe")
if not os.path.exists(GNOKII_PATH):
    raise Exception("{} does not exist".format(GNOKII_PATH))

class AndriodSMSGateway(object):
    SERVER = GetOption("SMS_SECTION", "SELF_IP")
    PORT = GetOption("SMS_SECTION", "SELF_PORT")
    TIMEOUT = 10 #seconds
    PING_TIMEOUT = .1
    def __init__(self):
        self.name = "Andriod SMS Gateway"

    def PrefetchResources(self):
        """ A very short duration timeout. And will always return True.
        Intent is to prefetch the resources."""
        try:
            url = "http://{server}:{port}".format(server=self.SERVER, port=self.PORT)
            urllib2.urlopen(url, timeout=self.PING_TIMEOUT)
        except urllib2.URLError:
            #DO not do anything here. The idea is to prefetch the resources and leave abruptly so that few seconds later when the resources are required for actual sending, they are already loaded.
            pass

    def CanSendSmsAsOfNow(self):
        #We dont know how to check connection. May be ping?
        try:
            url = "http://{server}:{port}".format(server=self.SERVER, port=self.PORT)
            print(url)
            resp = urllib2.urlopen(url, timeout=self.TIMEOUT)
            responseCode = resp.getcode()
            return responseCode == 200
        except urllib2.URLError as ex:
            print(ex.reason)

        return False

    def SendSms(self, toThisNumber, smsContents):
        """ Send SMS using SMS GATEWAY installed on Andriod """
        import urllib
        params = urllib.urlencode({'phone': toThisNumber, 'text': smsContents, 'password': ''})
        #Read IP and port at the time of sending so that in case of retries they are reread from the files and any immediate updates are reflected.
        def smsUrl(server, port, params):
          return "http://{server}:{port}/sendsms?{params}".format(server=server, port=port, params=params)

        ip_labels = ["SELF_IP", "SELF_IP2", "SELF_IP3", "SELF_IP4"]
        sms_urls = [smsUrl(GetOption("SMS_SECTION", x), GetOption("SMS_SECTION", "SELF_PORT"),  params) for x in ip_labels]
        for url in sms_urls:
          try:
            import urllib2
            f = urllib2.urlopen(url, timeout=3)
            break
          except Exception as ex:
            continue
        else:
          raise ex



        if False:
          try:
            f = urllib.urlopen(smsUrl(GetOption("SMS_SECTION", "SELF_IP"), GetOption("SMS_SECTION", "SELF_PORT"),  params))
          except Exception:
            try:
              f = urllib.urlopen(smsUrl(GetOption("SMS_SECTION", "SELF_IP2"), GetOption("SMS_SECTION", "SELF_PORT2"),  params))
            except Exception:
              raise

        htmlText = f.read()
        print(htmlText)
        print(StripHTMLTags(htmlText))
        return

class SonyEricssonPhone():
    def __init__(self):
        self.name = "Sony Ericsson Phone"

    def PrefetchResources(self):
        #TODO: Find out if we can prefetch resources in Sony Ericsson.
        return

    def CanSendSmsAsOfNow(self):
        SUCCESS = 0
        configPath = os.path.join(os.path.dirname(GNOKII_PATH), "gnokii.ini")
        configParams = " --config {}".format(configPath)
        gnokiiCmd = GNOKII_PATH + configParams + " --identify "
        with open(os.devnull, 'w') as tempf:
            #x = subprocess.call(gnokiiCmd, stdout=tempf, shell=True) #Hide standard output
            #x = subprocess.call(gnokiiCmd, stderr=tempf, shell=True)  #Hide error
            #x = subprocess.call(gnokiiCmd, stdout=tempf, stderr=tempf, shell=True)  #Hide both
            x = subprocess.call(gnokiiCmd, stdout=tempf, stderr=tempf, shell=True)  #Hide both
            if x == SUCCESS:
                return True
            else:
                return False

    def SendSms(self, toThisNumber, smsContents):
        """
        Uses gnokii to send messages.
        """
        configPath = os.path.join(os.path.dirname(GNOKII_PATH), "gnokii.ini")
        configParams = " --config {}".format(configPath)
        gnokiiCmd = GNOKII_PATH + configParams + " --sendsms " + toThisNumber

        from types import StringTypes
        if not isinstance(smsContents, StringTypes):
            raise Exception("smsContents should be of type string but instead got type {}".format(type(smsContents)))

        PrintInBox("Sending sms to {}:\n{}".format(toThisNumber, smsContents))

        fPath = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), "smsContents.txt")
        if os.path.exists(fPath): os.remove(fPath)
        with open(fPath,"w") as f:
            f.write(smsContents)

        cmd = "{gcmd} < {fPath} ".format(fPath=fPath, gcmd=gnokiiCmd)
        subprocess.check_call(cmd, shell=True)

        return



#Global object which tells which Gateway will be used to send SMS.
SMSOBJECT = AndriodSMSGateway()
#SMSOBJECT = SonyEricssonPhone()

@RetryNTimes(5)
def CanSendSmsAsOfNow():
  return SMSOBJECT.CanSendSmsAsOfNow()

@RetryNTimes(5)
def SendSms(toThisNumber, smsContents):
  return SMSOBJECT.SendSms(toThisNumber, smsContents)

def PrefetchResources():
  return SMSOBJECT.PrefetchResources()

def StripHTMLTags(html):
  from HTMLParser import HTMLParser
  class MLStripper(HTMLParser):
    def __init__(self):
      self.reset()
      self.fed = []
    def handle_data(self, d):
      self.fed.append(d)
    def get_data(self):
      SPACE = ' '
      return SPACE.join(self.fed)

  s = MLStripper()
  s.feed(html)
  return s.get_data()

if __name__ == "__main__":
  TEST_NUMBER = "4430890569"[::-1]
  if SMSOBJECT.CanSendSmsAsOfNow():
    pass
    #SMSOBJECT.SendSms(TEST_NUMBER, "Hi this is from program")
