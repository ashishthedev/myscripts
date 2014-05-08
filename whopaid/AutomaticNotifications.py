###############################################################################
## Author: Ashish Anand
## Date: 2014-May-08 Thu 12:51 PM
## Intent: To do all kind of automatic notification stuff that might be useful
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from UtilMisc import PrintInBox, DD_MMM_YYYY
from UtilPersistant import Persistant
from UtilSms import SendSms
import datetime
import calendar
from UtilConfig import GetOption
from string import Template
from UtilWhoPaid import SelectBillsAfterDate, SelectBillsBeforeDate, GetAllBillsInLastNDays
SMALL_NAME = GetOption("CONFIG_SECTION", "SmallName")

class PersistantWeeklySmsDetails(Persistant):
  def __init__(self):
    super(PersistantWeeklySmsDetails, self).__init__(self.__class__.__name__)

  def wasSMSSentForWeekStartingFrom(self, day):
    if PersistantWeeklySmsDetails.Key(day) in self.allKeys:
      return True
    return False

  def sendSmsForWeekStartingFrom(self, firstDay):
    PrintInBox("Sending weekly sale sms")
    d = dict()

    bills = [b for b in GetAllBillsInLastNDays(30)]
    bills = SelectBillsAfterDate(bills, firstDay)
    sixDays = datetime.timedelta(days=6)
    lastDay = firstDay + sixDays # including
    bills = SelectBillsBeforeDate(bills, lastDay)
    bills = sorted(bills, key = lambda b: b.amount, reverse=True)
    totalSale = sum([b.goodsValue for b in bills])
    firstComp = bills[0].compName
    secondComp = bills[1].compName

    d["compSmallName"] = SMALL_NAME
    d["date"] = DD_MMM_YYYY(firstDay)
    d["totalSale"] = str(int(totalSale))
    d["firstComp"] = firstComp
    d["secondComp"] = secondComp

    smsContents = Template(
"""M/s $compSmallName
Last week sale: Rs.$totalSale/-
Top Two:
1. $firstComp
2. $secondComp
""").substitute(d)

    nos = GetOption("SMS_SECTION", "OwnersR").replace(";", ",").split(",")
    nos = [n.strip()[::-1] for n in nos]

    for n in nos:
      print("Sending sms to {}".format(n))
      print("{}".format(smsContents))
      SendSms(n, smsContents)

    self.put(PersistantWeeklySmsDetails.Key(firstDay), DD_MMM_YYYY(datetime.date.today()))

    return

  @classmethod
  def Key(cls, day):
    return "Weekly-{}".format(DD_MMM_YYYY(day))



class DAYS(object):
  MONDAY = 0
  TUESDAY = 1
  WEDNESDAY = 2
  THURSDAY = 3
  FRIDAY = 4
  SATURDAY =5
  SUNDAY = 6

def SendWeeklySalesAsSmsIfNotSentAlready():
  minusOne = datetime.timedelta(days=-1)
  t = datetime.date.today() + minusOne #Start from yesterday

  if calendar.weekday(t.year, t.month, t.day) in [DAYS.MONDAY, DAYS.TUESDAY]:
    #Too early to send sms. All bills might have not been entered
    return

  while calendar.weekday(t.year, t.month, t.day) != DAYS.SATURDAY:
    t = t + minusOne

  while calendar.weekday(t.year, t.month, t.day) != DAYS.MONDAY:
    t = t + minusOne

  previousMonday = t
  pwsd = PersistantWeeklySmsDetails()

  if not pwsd.wasSMSSentForWeekStartingFrom(previousMonday):
    pwsd.sendSmsForWeekStartingFrom(previousMonday)


  return

def SendMonthlySaleAsSmsIfNotSentAlready():
  #TODO
  return

def SendAutomaticSmsReportsIfRequired():
  #TODO: Try to invoke it through Heartbeat which is invoked from Global Observer
  SendWeeklySalesAsSmsIfNotSentAlready()
  SendMonthlySaleAsSmsIfNotSentAlready()
  return


if __name__ == "__main__":
  SendWeeklySalesAsSmsIfNotSentAlready()
