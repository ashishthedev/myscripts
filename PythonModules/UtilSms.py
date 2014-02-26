##########################################################################
##
## This file contains a routine to send files to specific email address
##
## Author: Ashish Anand
##
##########################################################################

import subprocess
import os
from UtilConfig import GetAppDirPath
from UtilMisc import PrintInBox
def SendSms(toThisNumber, smsContents):
    """
    Uses gnokii to send messages.

    """
    gnokiiPath = os.path.join(GetAppDirPath(), "myscripts", "misc", "gnokii", "gnokii.exe")
    gnokiiCmd = gnokiiPath + " --sendsms " + toThisNumber

    if not os.path.exists(gnokiiPath):
        raise Exception("{} does not exist".format(gnokiiPath))

    if not isinstance(smsContents, str):
        raise Exception("smsContents should be of type string but instead got type {}".format(type(smsContents)))

    PrintInBox("SMS\nSending sms to {}:\n{}".format(toThisNumber, smsContents))
    subprocess.call("echo {} | {}".format(smsContents, gnokiiCmd), shell=True)

    return

if __name__ == "__main__":
    import datetime
    d = datetime.datetime.now()
    SendSms("7599120471", str(d))
