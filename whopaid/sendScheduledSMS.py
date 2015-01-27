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
    mobileNumbersList = [str(x) for x in str(msgNode.mobileNumbers).replace(",", ";").split(";")]
    if msgNode.shouldStop:
      print("stopping")
      return

    if datetime.datetime.now() < msgNode.startedOnDate:
      print(str(msgNode.startedOnDate) + " is in future. Skipping {} ...".format(msgNode.title))
      return

    key = str(msgNode.startedOnDate) + "-" + "-".join([(n) for n in mobileNumbersList])

    shouldSendMsg = False

    if key not in self:
      #Newly entered node
      shouldSendMsg = True
    else:
      #Preexisting node
      td = (datetime.datetime.now() - self[key])
      currentGapInMinutes = td.total_seconds()/60
      minimumGapInMinutes = int(msgNode.frequencyInDays)*24*60
      #We are dealing in minutes so that logic doesn't change if we switch to granularity of minutes later instead of days
      if currentGapInMinutes > minimumGapInMinutes:
        shouldSendMsg = True


    if shouldSendMsg:
      PrintInBox(msgNode.title + "\n" + msgNode.content + "\n")
      for eachNumber in mobileNumbersList:
        if raw_input("Send this msg to {}\n(y/n)".format(eachNumber)).lower() != "y":
          print("Not sending...")
          continue
        else:
          print("Sending...")
          SendSms(eachNumber, msgNode.content)
          #Save time
          self[key] = datetime.datetime.now()
    return


def SendScheduledSMS():
  nodes = GetScheduledReminderNodesList()
  for n in nodes:
    p = _PersistentSMS()
    p.SendMsgForThisNodeIfRequired(n)

def SendScheduledSMSForJson():
  if not HasOption("SMS_SECTION", "RepeatingSMSJsonFilePath"):
    return
  smsJsonPath = os.path.join(GetAppDirPath(), GetOption("SMS_SECTION", "RepeatingSMSJsonFilePath"))

  with open(smsJsonPath) as f:
    jsonData = json.load(f)

  for msgNode in jsonData["msgs"]:
    if msgNode.has_key("stop"):
      msgNode.shouldStop = True
    msgNode.startingDate = msgNode["startingDate"]
    msgNode.mobileNumbers = msgNode["toTheseNumbers"]
    msgNode.frequencyInDays = msgNode["frequencyInDays"]
    msgNode.content = msgNode["content"]
    p = _PersistentSMS()
    p.SendMsgForThisNodeIfRequired(msgNode)

class SingleMsgNode():
    """This represents a single msg node"""
    pass

class MsgNodeCol:
  TitleCol           = "A"
  StartedOnDateCol   = "B"
  FrequencyInDaysCol = "C"
  MobileNumbersCol   = "D"
  ContentsCol        = "E"
  StopCol            = "F"


def CreateSingleNode(row):
  from Util.ExcelReader import GetCellValue
  n = SingleMsgNode()
  for cell in row:
    col = cell.column
    val = GetCellValue(cell)
    if col == MsgNodeCol.TitleCol:
      n.title = val
    elif col == MsgNodeCol.StartedOnDateCol:
      n.startedOnDate = val
    elif col == MsgNodeCol.FrequencyInDaysCol:
      n.frequencyInDays = val
    elif col == MsgNodeCol.MobileNumbersCol:
      n.mobileNumbers = val
    elif col == MsgNodeCol.ContentsCol:
      n.content = val
    elif col == MsgNodeCol.StopCol:
      n.shouldStop = val != None
  return n

def GetScheduledReminderNodesList():
  from Util.ExcelReader import GetRows
  from Util.Config import GetOption, GetAppDir
  workbookPath =  os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "ScheduledRemindersRelativePath"))
  nodes = list()
  for row in GetRows(
      workbookPath=workbookPath,
      sheetName=GetOption("CONFIG_SECTION", "NameOfScheduledSMSSheet"),
      firstRow=GetOption("CONFIG_SECTION", "ScheduledRemindersDataStartsAtRow"),
      includeLastRow=True):
        nodes.append(CreateSingleNode(row))
  return nodes


if __name__ == "__main__":
  args = ParseArguments()
  SendScheduledSMS()
