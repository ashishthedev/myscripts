##########################################################################
##
## This file contains a routine to send files to specific email address
##
## Author: Ashish Anand
##
##########################################################################

import subprocess
import os
from UtilConfig import GetAppDirPath, GetOption
from UtilMisc import PrintInBox

GNOKII_PATH = os.path.join(GetAppDirPath(), "myscripts", "misc", "gnokii", "gnokii.exe")
if not os.path.exists(GNOKII_PATH):
    raise Exception("{} does not exist".format(GNOKII_PATH))

class AndriodSMSGateway(object):
    def __init__(self):
        self.name = "Andriod SMS Gateway"

    def CanSendSmsAsOfNow(self):
        #We dont know how to check connection. May be ping?
        return True

    def SendSms(self, toThisNumber, smsContents):
        """ Send SMS using SMS GATEWAY installed on Andriod """
        #TODO: Make these class variables
        import urllib
        SERVER = "192.168.1.18"
        PORT = "9191"
        params = urllib.urlencode({'phone': toThisNumber, 'text': smsContents, 'password': ''})
        url = "http://{server}:{port}/sendsms?{params}".format(server=SERVER, port=PORT, params=params)
        f = urllib.urlopen(url)
        print(StripHTMLTags(f.read()))
        return

class SonyEricssonPhone():
    def __init__(self):
        self.name = "Sony Ericsson Phone"

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



SMSOBJECT = AndriodSMSGateway()
#SMSOBJECT = SonyEricssonPhone()

def CanSendSmsAsOfNow():
    return SMSOBJECT.CanSendSmsAsOfNow()

def SendSms(toThisNumber, smsContents):
    SMSOBJECT.SendSms(toThisNumber, smsContents)

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

