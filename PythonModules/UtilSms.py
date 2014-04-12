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

def CanSendSmsAsOfNow():
    configPath = os.path.join(os.path.dirname(GNOKII_PATH), "gnokii.ini")
    configParams = " --config {}".format(configPath)
    gnokiiCmd = GNOKII_PATH + configParams + " --identify "
    with open(os.devnull, 'w') as tempf:
        #x = subprocess.call(gnokiiCmd, stdout=tempf, shell=True) #Hide standard output
        x = subprocess.call(gnokiiCmd, stderr=tempf, shell=True)  #Hide error
        if x==0:
            return True
        else:
            return False

def SendSms(toThisNumber, smsContents):
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

if __name__ == "__main__":
    import datetime
    d = datetime.datetime.now()
    if CanSendSmsAsOfNow():
        PrintInBox("SMS can now be sent")
    else:
        PrintInBox("Sorry. There is some problem and smses cannot be sent as of now.")
    #s=""
    #for x in range(200):
    #    s += str(x) + " "
    #SendSms("7599120471", s)
