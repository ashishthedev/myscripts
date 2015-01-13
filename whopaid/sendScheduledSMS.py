##########################################################################
##
## This file allows you to send scheduled SMSes.
## The SMS are stored as JSON nodes with complete information and 
## repeating schedules
##
## Author: Ashish Anand
## 2015-Jan-01 Thu 02:21 PM
##
##########################################################################

from Util.Config import GetOption, GetAppDirPath, HasOption
from Util.Persistent import Persistent
from Util.Misc import PrintInBox
from Util.Sms import SendSms
import os
import datetime

import json

def ParseArguments():
  import argparse
  p = argparse.ArgumentParser()
  args = p.parse_args()
  return args

class _PersistentSMS(Persistent):
  def __init__(self):
    super(self.__class__, self).__init__(self.__class__.__name__)

  def SendMsgForThisNodeIfRequired(self, msgNode):
    if msgNode.has_key("stop"):
      return
    key = msgNode["startingDate"] + "-" + "-".join([str(n) for n in msgNode["toTheseNumbers"]])

    shouldSendMsg = False

    if key not in self:
      #Newly entered node
      shouldSendMsg = True
    else:
      #Preexisting node
      td = (datetime.datetime.now() - self[key])
      currentGapInMinutes = td.total_seconds()/60
      minimumGapInMinutes = int(msgNode["frequencyInDays"])*24*60
      #We are dealing in minutes so that logic doesn't change if we switch to granularity of minutes later instead of days
      if currentGapInMinutes > minimumGapInMinutes:
        shouldSendMsg = True


    if shouldSendMsg:
      for eachNumber in msgNode["toTheseNumbers"]:
        PrintInBox(msgNode["content"] + "\n" + eachNumber)
        if raw_input("Send this msg (y/n)").lower() != "y":
          print("Not sending...")
          continue
        else:
          print("Sending...")
          SendSms(eachNumber, msgNode["content"])
          #Save time
          self[key] = datetime.datetime.now()


def SendScheduledSMS():
  if not HasOption("SMS_SECTION", "RepeatingSMSJsonFilePath"):
    return
  smsJsonPath = os.path.join(GetAppDirPath(), GetOption("SMS_SECTION", "RepeatingSMSJsonFilePath"))

  with open(smsJsonPath) as f:
    jsonData = json.load(f)

  for msgNode in jsonData["msgs"]:
    p = _PersistentSMS()
    p.SendMsgForThisNodeIfRequired(msgNode)

if __name__ == "__main__":
  args = ParseArguments()
  SendScheduledSMS()
