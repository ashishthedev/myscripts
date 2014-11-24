###############################################################################
## Author: Ashish Anand
## Date: 2014-May-08 Thu 12:51 PM
## Intent: To do all kind of automatic notification stuff that might be useful
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from Util.Config import GetOption
from Util.Misc import PrintInBox, DD_MMM_YYYY, GetFirstDateOfThisFinancialYear
from Util.Persistent import Persistent
from Util.Sms import SendSms

from whopaid.util_whopaid import SelectBillsAfterDate, SelectBillsBeforeDate, GetAllBillsInLastNDays
from whopaid.customers_info import GetAllCustomersInfo

from collections import OrderedDict
from string import Template

import calendar
import datetime

SMALL_NAME = GetOption("CONFIG_SECTION", "SmallName")

def GetTopFiveClientsAsString(bills):
  d = dict()

  allCustomersInfo = GetAllCustomersInfo()
  for b in bills:
    grpName = allCustomersInfo.GetCompanyGroupName(b.compName)
    if grpName not in d.keys():
      d[grpName] = 0
    d[grpName] += int(b.amount)

  od = OrderedDict(sorted(d.iteritems(), key=lambda t: t[1], reverse=True))
  res = ""
  i=1
  for compName, amount in od.items()[:5]:
    res += "\n{}. Rs.{} {}".format(i, amount, compName)
    i+=1
  return res


def CalculateProjectedSaleForThisYear():
  firstApril = GetFirstDateOfThisFinancialYear()
  bills = SelectBillsAfterDate(GetAllBillsInLastNDays(365), firstApril)
  t = datetime.date.today()
  previousMonthLastDate = t - datetime.timedelta(days=t.day+1)
  bills = SelectBillsBeforeDate(bills, previousMonthLastDate)
  projectedSaleForThisYear = sum([b.goodsValue for b in bills if b.billingCategory.lower() in ["up", "central", "export"]])
  daysPassedInThisYear = (previousMonthLastDate - firstApril).days
  projectedSaleForThisYear = (projectedSaleForThisYear/daysPassedInThisYear)*365
  return projectedSaleForThisYear

class PersistentMonthlySmsDetails(Persistent):

  def __init__(self):
    super(PersistentMonthlySmsDetails, self).__init__(self.__class__.__name__)

  def wasSmsSentForMonthHavingThisDate(self, date):
    if date in self:
      return True
    return False

  def sendSmsForMonthHavingThisDate(self, date):
    PrintInBox("Sending monthly sale sms")
    if raw_input("Send (y/n) ?").lower() != "y":
      return
    d = dict()
    bills = [b for b in GetAllBillsInLastNDays(90)]
    firstDay = datetime.date(date.year, date.month, 1)
    nextMonthDate = firstDay + datetime.timedelta(days=32) #Force jump one month, this will solve dec-jan problem
    lastDay = datetime.date(nextMonthDate.year, nextMonthDate.month, 1) - datetime.timedelta(days=1)

    bills = SelectBillsAfterDate(bills, firstDay)
    bills = SelectBillsBeforeDate(bills, lastDay)
    totalSale = sum([b.goodsValue for b in bills])

    d["compSmallName"] = SMALL_NAME
    d["month"] = "{}-{}".format(firstDay.strftime("%b"), firstDay.year)
    d["totalSale"] = str(int(totalSale))
    d["projectedSaleForThisYear"] = str(round(CalculateProjectedSaleForThisYear()/10000000.0, 2))
    d["topFiveStrList"] = GetTopFiveClientsAsString(bills)
    smsContents = Template(
"""M/s $compSmallName
$month: Rs.$totalSale/-
Projected: Rs.$projectedSaleForThisYear Cr
Top customers:
$topFiveStrList
""").substitute(d)

    nos = GetOption("SMS_SECTION", "OwnersR").replace(";", ",").split(",")
    nos = [n.strip()[::-1] for n in nos]

    for n in nos:
      print("Sending sms to {}".format(n))
      print("{}".format(smsContents))
      SendSms(n, smsContents)

    self[date] = DD_MMM_YYYY(datetime.date.today())
    return


class PersistentWeeklySmsDetails(Persistent):
  def __init__(self):
    super(PersistentWeeklySmsDetails, self).__init__(self.__class__.__name__)

  def wasSMSSentForWeekStartingFrom(self, day):
    if day in self:
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

    self[firstDay] =  DD_MMM_YYYY(datetime.date.today())

    return


class DAYS(object):
  MONDAY = 0
  TUESDAY = 1
  WEDNESDAY = 2
  THURSDAY = 3
  FRIDAY = 4
  SATURDAY =5
  SUNDAY = 6

def _SendWeeklySalesAsSmsIfNotSentAlready():
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
  pwsd = PersistentWeeklySmsDetails()

  if not pwsd.wasSMSSentForWeekStartingFrom(previousMonday):
    pwsd.sendSmsForWeekStartingFrom(previousMonday)


  return

def _SendMonthlySaleAsSmsIfNotSentAlready():
  PrintInBox("Sending monthly sale sms if not already sent")
  t = datetime.date.today()

  ALLOWED_DAYS = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
  if t.day not in ALLOWED_DAYS: return #Too early or too late to send sms. All bills might have not been entered

  previousMonthLastDate  = t - datetime.timedelta(days=t.day+1)

  pmsd = PersistentMonthlySmsDetails()

  if not pmsd.wasSmsSentForMonthHavingThisDate(previousMonthLastDate):
    pmsd.sendSmsForMonthHavingThisDate(previousMonthLastDate)

  return

def SendAutomaticSmsReportsIfRequired():
  #_SendWeeklySalesAsSmsIfNotSentAlready()
  _SendMonthlySaleAsSmsIfNotSentAlready()
  _ArrangeNewBillBookMsg()
  return

class _PersistentBillBookSms(Persistent):
  def __init__(self):
    super(self.__class__, self).__init__(self.__class__.__name__)

  def _keyForBill(self, bill):
    return "{}{}".format(bill.billNumber, DD_MMM_YYYY(bill.invoiceDate))

  def _wasSMSSentForBill(self, bill):
    return self._keyForBill(bill) in self

  def sendSmsIfRequired(self):
    bills = [b for b in GetAllBillsInLastNDays(30)]
    bills = sorted(bills, key = lambda b: b.invoiceDate, reverse=True)
    BILL_BOOK_SIZE = 50
    BUFFER = 5
    for b in bills:
      if int(b.billNumber) % BILL_BOOK_SIZE == (BILL_BOOK_SIZE - BUFFER): #Send the sms when 5 bills are remaining
        if not self._wasSMSSentForBill(b):
          firstBillInNextBillBook = int(b.billNumber) + BUFFER + 1
          if firstBillInNextBillBook in [b.billNumber for b in bills]: print("a bill has been issued in new billbook"); continue #A bill in new bill book has been issued. Ignore and move on in life.
          PrintInBox("Sending bill book arrangement sms")
          self._sendSMSForNewBillBookStartingFromBill(int(b.billNumber) + BUFFER + 1)
          k = self._keyForBill(b)
          self[k] = DD_MMM_YYYY(datetime.date.today())
          return

  def _sendSMSForNewBillBookStartingFromBill(self, firstBillNumber):
    d = dict()
    d["compSmallName"] = SMALL_NAME
    d["firstBillNumber"] = str(int(firstBillNumber))

    smsContents = Template(
"""M/s $compSmallName
New bill book required starting from bill# $firstBillNumber
""").substitute(d)

    smsFunctionality = GetOption("CONFIG_SECTION", "NewBillBookMsgFunctionalityEnabled").lower() == "true"
    if not smsFunctionality:
      PrintInBox(smsContents, waitForEnterKey=True)
    else:
      nos = GetOption("SMS_SECTION", "OwnersR").replace(";", ",").split(",")
      nos = [n.strip()[::-1] for n in nos]

      for n in nos:
        print("Sending sms to {}".format(n))
        print("{}".format(smsContents))
        SendSms(n, smsContents)
    return

def _ArrangeNewBillBookMsg():
  _PersistentBillBookSms().sendSmsIfRequired()


if __name__ == "__main__":
  #_SendMonthlySaleAsSmsIfNotSentAlready()
  #_ArrangeNewBillBookMsg()
  print(CalculateProjectedSaleForThisYear())
