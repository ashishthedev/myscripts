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
def SendSms(toThisNumber, smsContents):
    """
    Uses gnokii to send messages.
    """
    gnokiiPath = os.path.join(GetAppDirPath(), "myscripts", "misc", "gnokii", "gnokii.exe")
    gnokiiCmd = gnokiiPath + " --sendsms " + toThisNumber

    if not os.path.exists(gnokiiPath):
        raise Exception("{} does not exist".format(gnokiiPath))

    from types import StringTypes
    if not isinstance(smsContents, StringTypes):
        raise Exception("smsContents should be of type string but instead got type {}".format(type(smsContents)))

    PrintInBox("Sending sms to {}:\n{}".format(toThisNumber, smsContents))
    fPath = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), "smsContents.txt")
    os.remove(fPath)
    with open(fPath,"w") as f:
        f.write(smsContents)

    cmd = "{gcmd} < {fPath} ".format(fPath=fPath, gcmd=gnokiiCmd)
    subprocess.check_call(cmd, shell=True)

    return

if __name__ == "__main__":
    import datetime
    d = datetime.datetime.now()
    s=""
    for x in range(200):
        s += str(x) + " "
    SendSms("7599120471", s)
