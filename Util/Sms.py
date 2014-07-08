##########################################################################
##
## This file contains a routine to send files to specific email address
##
## Author: Ashish Anand
##
##########################################################################

import subprocess
import os
from Util.Config import GetAppDirPath, GetOption
from Util.Misc import PrintInBox
import urllib2
from Util.Decorators import RetryFor2TimesIfFailed

GNOKII_PATH = os.path.join(GetAppDirPath(), "myscripts", "misc", "gnokii", "gnokii.exe")
if not os.path.exists(GNOKII_PATH):
    raise Exception("{} does not exist".format(GNOKII_PATH))

class AndriodSMSGateway(object):
    SERVER = "192.168.1.18"
    PORT = "9191"
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
            resp = urllib2.urlopen(url, timeout=self.TIMEOUT)
            responseCode = resp.getcode()
            if responseCode == 200:
                return True
        except urllib2.URLError as ex:
            print(ex.reason)

        return False

    def SendSms(self, toThisNumber, smsContents):
        """ Send SMS using SMS GATEWAY installed on Andriod """
        import urllib
        params = urllib.urlencode({'phone': toThisNumber, 'text': smsContents, 'password': ''})
        url = "http://{server}:{port}/sendsms?{params}".format(server=self.SERVER, port=self.PORT, params=params)
        f = urllib.urlopen(url)
        print(StripHTMLTags(f.read()))
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

def CanSendSmsAsOfNow():
    return SMSOBJECT.CanSendSmsAsOfNow()

@RetryFor2TimesIfFailed
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
    SMSOBJECT = AndriodSMSGateway()
    if SMSOBJECT.CanSendSmsAsOfNow():
        SMSOBJECT.SendSms(TEST_NUMBER, "Hi this is from program")
    #for i in range(2):
    #    #Send 2 sms and see if there is any problem in sending them very fast
    #    d = datetime.datetime.now()
    #    msg = "Sending at {}".format(d)
    #    SendSmsFromAndriodUsingSMSGateway(TEST_NUMBER, msg)



    #if CanSendSmsAsOfNow():
    #    PrintInBox("SMS can now be sent")
    #else:
    #    PrintInBox("Sorry. There is some problem and smses cannot be sent as of now.")
    #s=""
    #for x in range(200):
    #    s += str(x) + " "
    #SendSms("7599120471", s)

