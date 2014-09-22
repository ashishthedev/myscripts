
from Util.Misc import DD_MM_YYYY, GetMsgInBox
from Util.Config import GetOption

from whopaid.util_whopaid import SelectUnpaidBillsFrom, GetAllCompaniesDict, RemoveTrackingBills

SMALL_NAME = GetOption("CONFIG_SECTION", "SmallName")

def ReportBillOnScreenWhichShouldBeMarkAsPaid():
    msg = ReportBillOnScreenWhichShouldBeMarkAsPaid()
    if msg:
        print(msg)

def ReportBillWhichShouldBeMarkAsPaid():
  allCompaniesDict = GetAllCompaniesDict()

  allPaymentsDict = GetAllCompaniesDict().GetAllPaymentsByAllCompaniesAsDict()
  finalText = ""
  for eachCompName, paymentList in allPaymentsDict.iteritems():
    paymentList = [p for p in paymentList if not p.paymentAccountedFor]
    if not paymentList: continue
    unpaidBillList = allCompaniesDict.GetBillsListForThisCompany(eachCompName)
    if not unpaidBillList: continue #i.e it was an advance payment by a new company

    unpaidBillList = RemoveTrackingBills(unpaidBillList)
    unpaidBillList = SelectUnpaidBillsFrom(unpaidBillList)
    unpaidBillList = sorted(unpaidBillList, key=lambda b:b.invoiceDate)

    totalPayment = sum([p.amount for p in paymentList])

    billsThatShouldBeMarkedAsPaid = []
    totalInvoiceAmount = 0
    for b in unpaidBillList:
      totalInvoiceAmount += b.amount
      if totalInvoiceAmount > totalPayment:
        break
      billsThatShouldBeMarkedAsPaid.append(b)
    if billsThatShouldBeMarkedAsPaid:
      s = "Rs.{} paid by {} in\n{}\n Please mark following bills as paid\n".format(totalPayment, b.compName, SMALL_NAME)
      for b in billsThatShouldBeMarkedAsPaid:
        s += "Rs.{:<10} {:<15} Bill#{:<15}\n".format(b.amount, DD_MM_YYYY(b.invoiceDate), b.billNumber)
      finalText += GetMsgInBox(s, myWidth=79, outliner="_")

  if finalText:
    return finalText
  return None


if __name__ == "__main__":
    ReportBillOnScreenWhichShouldBeMarkAsPaid()
