###############################################################################
## Author: Ashish Anand
## Date: 2014-May-08 Thu 12:51 PM
## Intent: To do all kind of automatic notification stuff that might be useful
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from Util.Misc import PrintInBox, DD_MMM_YYYY
from Util.Persistant import Persistant
from Util.Sms import SendSms
import datetime
import calendar
from Util.Config import GetOption
from string import Template
from UtilWhoPaid import SelectBillsAfterDate, SelectBillsBeforeDate, GetAllBillsInLastNDays
from CustomersInfo import GetAllCustomersInfo
SMALL_NAME = GetOption("CONFIG_SECTION", "SmallName")

def GetTopFiveClientsAsString(bills):
  d = dict()

  allCustomersInfo = GetAllCustomersInfo()
  for b in bills:
    grpName = allCustomersInfo.GetCompanyGroupName(b.compName)
    if grpName not in d.keys():
      d[grpName] = 0
    d[grpName] += int(b.amount)

  from collections import OrderedDict
  od = OrderedDict(sorted(d.items(), key=lambda t: t[1], reverse=True))
  res = ""
  i=1
  for compName, amount in od.items()[:5]:
    res += "\n{}. Rs.{} {}".format(i, amount, compName)
    i+=1
  return res


class PersistantMonthlySmsDetails(Persistant):
  @classmethod
  def Key(cls, date):
    return date.strftime("%b-%y")

  def __init__(self):
    super(PersistantMonthlySmsDetails, self).__init__(self.__class__.__name__)

  def wasSmsSentForMonthHavingThisDate(self, date):
    if self.Key(date) in self.allKeys:
      return True
    return False

  def sendSmsForMonthHavingThisDate(self, date):
    PrintInBox("Sending monthly sale sms")
    d = dict()
    bills = [b for b in GetAllBillsInLastNDays(60)]
    firstDay = datetime.date(date.year, date.month, 1)
    nextMonthDate = firstDay + datetime.timedelta(days=32) #Force jump one month, this will solve dec-jan problem
    lastDay = datetime.date(nextMonthDate.year, nextMonthDate.month, 1) - datetime.timedelta(days=1)

    bills = SelectBillsAfterDate(bills, firstDay)
    bills = SelectBillsBeforeDate(bills, lastDay)
    totalSale = sum([b.goodsValue for b in bills])

    d["compSmallName"] = SMALL_NAME
    d["month"] = "{}-{}".format(firstDay.strftime("%b"), firstDay.year)
    d["totalSale"] = str(int(totalSale))
    d["topFiveStrList"] = GetTopFiveClientsAsString(bills)
    smsContents = Template(
"""M/s $compSmallName
Sale for $month: Rs.$totalSale/-
Top customers:
$topFiveStrList
""").substitute(d)

    nos = GetOption("SMS_SECTION", "OwnersR").replace(";", ",").split(",")
    nos = [n.strip()[::-1] for n in nos]

    for n in nos:
      print("Sending sms to {}".format(n))
      print("{}".format(smsContents))
      SendSms(n, smsContents)

    k = self.Key(date)
    self.put(k, DD_MMM_YYYY(datetime.date.today()))
    return


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
      #raw_input("About to send sms but will not send because of testing...");return #TODO: Delete this line
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
  t = datetime.date.today()

  if calendar.weekday(t.year, t.month, t.day) in [DAYS.MONDAY, DAYS.TUESDAY]:
    #Too early to send sms. All bills might have not been entered
    return

  t = t + minusOne #Start from yesterday

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
  PrintInBox("Sending monthly sale sms if not already sent")
  t = datetime.date.today()

  ALLOWED_DAYS = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
  if t.day not in ALLOWED_DAYS:
    #Too early or too late to send sms. All bills might have not been entered
    return

  lastMonthDate  = t - datetime.timedelta(days=t.day+1)

  pmsd = PersistantMonthlySmsDetails()

  if not pmsd.wasSmsSentForMonthHavingThisDate(lastMonthDate):
    pmsd.sendSmsForMonthHavingThisDate(lastMonthDate)

  return

def SendAutomaticSmsReportsIfRequired():
  #SendWeeklySalesAsSmsIfNotSentAlready()
  SendMonthlySaleAsSmsIfNotSentAlready()
  return


if __name__ == "__main__":
  SendMonthlySaleAsSmsIfNotSentAlready()
