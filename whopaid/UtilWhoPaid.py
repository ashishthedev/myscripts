###############################################################################
## Author: Ashish Anand
## Date: 15 Dec 2011
## Intent: To read bills.xlsx and provide some utility functions to deal
## with it
## Requirement: Python Interpretor must be installed
###############################################################################
from Util.Exception import MyException
from Util.Config import GetOption, GetAppDir
from Util.ExcelReader import LoadIterableWorkbook
from Util.Misc import GetPickledObject, ParseDateFromString, DD_MM_YYYY, PrintInBox
from CustomersInfo import GetAllCustomersInfo

import os
import shelve
import datetime
from contextlib import closing

BILLS_FILE_LAST_CHANGE_SHELF_ID = "BillsFileLastChangedAt"
PERSISTENT_STORAGE_PATH = os.path.join(
        GetOption("CONFIG_SECTION", "TempPath"),
        GetOption("CONFIG_SECTION", "PersistentStorageDB"))

def GetWorkBookPath():
    return os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "WorkbookRelativePath"))

def intx(i):
    return(0 if i is None else int(i))

def floatx(i):
    return(0.0 if i is None else float(i))

def datex(d):
    return(datetime.date.today() if d is None else d)


class CompaniesDict(dict):#TODO: Name it as DB
    """Base Class which is basically a dictionary. Key is compName and Value is a list of single bills of that company"""
    def __init__(self):
        super(CompaniesDict, self).__init__(dict())
        self[KIND.BILL] = dict()
        self[KIND.PAYMENT] = dict()
        self[KIND.ADJUSTMENT] = dict()
        self[KIND.ORDER] = dict()
        self[KIND.PUNTED_ORDER] = dict()


    def _AddEntry(self, typ, r):
        """
        The only method through which this master database is prepared.
        Find out if the company exists already. If it does, add the bill to that company.
        If it doesnt, create the company and add the bill to that company.
        typ = KIND.ORDER/BILL/PAYMENT/ADJUSTMENT
        """
        if r.compName in self[typ].keys():
            self[typ][r.compName].append(r)
        else:
            #If for this type there is no entry for this company, create it.
            self[typ][r.compName] = Company(r.compName) #TODO: Remove after testing
            self[typ][r.compName].append(r)

    def AddBill(self, b):
        self._AddEntry(KIND.BILL, b)

    def AddPayment(self, p):
        self._AddEntry(KIND.PAYMENT, p)

    def AddAdjustment(self, a):
        self._AddEntry(KIND.ADJUSTMENT, a)

    def AddOrder(self, o):
        self._AddEntry(KIND.ORDER, o)


    def GetAllBillsOfAllCompaniesAsDict(self):
        return self[KIND.BILL]

    def GetAllPaymentsByAllCompaniesAsDict(self):
        return self[KIND.PAYMENT]

    def GetAllAdjustmentsOfAllCompaniesAsDict(self):
        return self[KIND.ADJUSTMENT]

    def GetAllOrdersOfAllCompaniesAsDict(self):
        return self[KIND.ORDER]


    def GetBillsListForThisCompany(self, compName):
        return self.GetAllBillsOfAllCompaniesAsDict().get(compName, None)

    def GetPaymentsListForThisCompany(self, compName):
        return self.GetAllPaymentsByAllCompaniesAsDict().get(compName, None)

    def GetUnAccountedAdjustmentsListForCompany(self, compName):
      adjustmentList = self.GetAllAdjustmentsOfAllCompaniesAsDict().get(compName, [])
      return [a for a in adjustmentList if not a.adjustmentAccountedFor]

    def GetOrdersListForCompany(self, compName):
        return self.GetAllOrdersOfAllCompaniesAsDict().get(compName, None)


def GetAllCompaniesDict():
    workbookPath = GetWorkBookPath()
    def _CreateAllCompaniesDict(workbookPath):
        return _AllCompaniesDict(workbookPath)
    return GetPickledObject(workbookPath, _CreateAllCompaniesDict)

class KIND(object):
    BILL = 1
    PAYMENT = 2
    ADJUSTMENT = 3
    ORDER = 4
    PUNTED_ORDER = 5

def GuessKindFromValue(val):
    if val:
        val = val.lower()
        if val.lower() == "bill": return KIND.BILL
        elif val.lower() == "payment": return KIND.PAYMENT
        elif val.lower() == "adjustment": return KIND.ADJUSTMENT
        elif val.lower() == "order": return KIND.ORDER
        elif val.lower() == "punted": return KIND.PUNTED_ORDER
    return None

def GuessKindFromRow(row):
    for cell in row:
        col = cell.column
        val = cell.internal_value

        if col == SheetCols.KindOfEntery:
            return GuessKindFromValue(val)
    return None

class _AllCompaniesDict(CompaniesDict):
    """
    This class represents the heart of logic.
    It is an aggregation of all companies.
    It is a dictonary of dict. Ist level ["BILL"/"PAYMENT"]. Second level company names. Values are list of all bills or payments.
    Each member in the dict is a single company.
    Each Single company holds the list of all bills ever issued to them.
    """
    def __init__(self, workbookPath):
        super(_AllCompaniesDict, self).__init__()
        wb = LoadIterableWorkbook(workbookPath)
        ws = wb.get_sheet_by_name(GetOption("CONFIG_SECTION", "NameOfSaleSheet"))
        MAX_ROW = ws.get_highest_row()
        MIN_ROW = int(GetOption("CONFIG_SECTION", "DataStartsAtRow"))
        rowNumber = 0

        for row in ws.iter_rows():
            #TODO: Can we give a range to it with MIN_ROW and MAX_ROW?
            rowNumber += 1
            if rowNumber < MIN_ROW: continue
            if rowNumber >= MAX_ROW: break

            kind = GuessKindFromRow(row)
            if kind == KIND.BILL:
                self.AddBill(CreateSingleBillRow(row))
            elif kind == KIND.PAYMENT:
                self.AddPayment(CreateSinglePaymentRow(row))
            elif kind == KIND.ADJUSTMENT:
                self.AddAdjustment(CreateSingleAdjustmentRow(row))
            elif kind == KIND.ORDER:
                self.AddOrder(CreateSingleOrderRow(row))
            elif kind == KIND.PUNTED_ORDER:
                pass #DO NOT DO ANYTHING FOR PUNTED ORDERS
            else:
                raise Exception("Error in row number: {} Kind of entry is invalid".format(rowNumber))

class Company(list):
    """
    For us, the company is same as the list of all bills. If any further info is required, it needs some overhauling.
    """
    def __init__(self, name):
        super(Company, self).__init__(list())
        self.compName = name  # Use this name. Do not pick name from first bill.

    def __eq__(self, other):
        """
        Crude Check. If sum of bill numbers is same, then the two lists are same.
        """
        return sum([int(b.billNumber) for b in self]) == sum ([int(b.billNumber) for b in other])

    def __str__(self):
        res = "Company: M/s " + self.compName
        if len(self) > 0:
            for b in self:
                res += "\n" + str(b)
        else:
            res +=  " has no bills"

        return res

    def CheckEachBillsCalculation(self):
        for b in self:
            b.CheckCalculation()

    def CheckEachBillsBillingCategory(self):
        uniqueCategory = set()
        #Create a unique set
        for b in self:
            if b.billingCategory.lower() not in ["jobwork", "tracking"]:
                uniqueCategory.add(b.billingCategory.lower())

        if len(uniqueCategory) > 1:
            for u in uniqueCategory:
                print(u)
            raise MyException("Bills are issued in more than two category for company: " + str(self.compName))


class SingleRow(object):
    pass
class SinglePaymentRow(SingleRow):
    pass
class SingleAdjustmentRow(SingleRow):
    @property
    def daysOfCredit(self):
        assert self.isUnpaid, "This function should only be called on unpaid bills"
        timeDelta = datetime.date.today() - datex(self.invoiceDate)
        return timeDelta.days
    pass

class SingleOrderRow(SingleRow):
    def __str__(self):
        return "ORDER: {cn:}\n{dt}\n{md} ".format(
                dt = DD_MM_YYYY(self.orderDate),
                cn = self.compName,
                md = self.materialDesc
                )


class SingleBillRow(SingleRow):
    """
    This class represents a single row in the excel sheet which in effect represents a single bill
    """
    def __init__(self):
        pass

    def __str__(self):
        paymentDate = self.paymentReceivingDate
        if not paymentDate:
            paymentDate = "-----------"
        else:
            paymentDate = DD_MM_YYYY(self.PaymentReceivingDate)

        return "Rs.{:<5} Bill:{:<5} {} {:<5} {}".format(
            int(self.amount),
            int(self.billNumber),
            DD_MM_YYYY(datex(self.invoiceDate)),
            str(self.paymentStatus),
            paymentDate
            )

    def __lt__(self, other): # Helps in just using sorted over a list of bills
        if self.invoiceDate < other.invoiceDate:
            return True
        elif self.invoiceDate == other.invoiceDate:
            return self.billNumber < other.billNumber
        else:
            return False

    def CheckCalculation(self):
        if intx(self.goodsValue) != 0:
            if(intx(self.amount) != (intx(self.goodsValue) + intx(self.tax) + intx(self.courier))):
                raise MyException("Calculation error in " + str(self.billingCategory) + " bill# " + str(self.billNumber))

    @property
    def isPaid(self):
        return True if self.paymentStatus and self.paymentStatus.lower() == "paid" else False
        #return True if self.paymentDate #TODO

    @property
    def isUnpaid(self):
        return not self.isPaid

    @property
    def daysOfCredit(self):
        assert self.isUnpaid, "This function should only be called on unpaid bills"
        timeDelta = datetime.date.today() - datex(self.invoiceDate)
        return timeDelta.days

    @property
    def uid_string(self):
        #Assumption: A particular bill number and invoice date are enough to single out any bill and they will never produce a collision
        return "{}{}{}".format(str(self.billNumber), DD_MM_YYYY(self.invoiceDate), str(self.docketNumber))


def GetAllBillsInLastNDays(nDays):
    #TODO:Super slow needs optimization
    allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
    totalBillList = list()
    for compName, compBillList in allBillsDict.items():
        totalBillList.extend(compBillList)
    dateObject = datetime.date.today() - datetime.timedelta(days=nDays)
    return SelectBillsAfterDate(totalBillList, dateObject)

def SelectBillsBeforeDate(billList, dateObject):
    if not dateObject:
        import pdb; pdb.set_trace()
    return [b for b in billList if dateObject >= ParseDateFromString(b.invoiceDate)]

def SelectBillsAfterDate(billList, dateObject):
    return [b for b in billList if dateObject <= ParseDateFromString(b.invoiceDate)]

def SelectUnpaidBillsFrom(billList):
    return [b for b in billList if b.isUnpaid]

def SelectUnAccountedAdjustmentsFrom(adjustmentList):
    return [a for a in adjustmentList if not a.adjustmentAccountedFor]

def RemoveTrackingBills(billList):
    return [b for b in billList if not b.billingCategory.lower().startswith("tracking")]

class SheetCols:
    """
    This class is used as Enum.
    If and when the format of excel file changes just change the column bindings in this class
    """
    CompanyFriendlyNameCol = "A"
    KindOfEntery           = "B"
    InstrumentNumberCol    = "C"
    InstrumentDateCol      = "D"
    BillingCategory        = "E"
    InvoiceNumberCol       = "F"
    InvoiceDateCol         = "G"
    MaterialDesc           = "H"
    GoodsValue             = "I"
    Tax                    = "J"
    Courier                = "K"
    InvoiceAmount          = "L"
    DocketNumber           = "M"
    DocketDate             = "N"
    CourierName            = "O"
    PaymentReceivingDate   = "P"
    PaymentStatus          = "Q"
    PaymentAccountedFor    = "R"
    FormCReceivingDate     = "S"

def CreateSingleOrderRow(row):
    r = SingleOrderRow()
    for cell in row:
        col = cell.column
        val = cell.internal_value

        if col == SheetCols.CompanyFriendlyNameCol:
            if not val: raise Exception("Row: {} seems empty. Please fix the database".format(cell.row))
            r.compName = val
        elif col == SheetCols.KindOfEntery:
            r.kindOfEntery = val
        elif col == SheetCols.MaterialDesc:
            if not val: raise Exception("Order in row: {} seems empty. Please fix the database".format(cell.row))
            r.materialDesc = val
        elif col == SheetCols.InstrumentDateCol:
            if not val: raise Exception("Date in row: {} seems empty. Please fix the database".format(cell.row))
            r.orderDate = ParseDateFromString(val)
        elif col == SheetCols.InstrumentNumberCol:
            if not val: raise Exception("Row: {} seems empty. Please fix the database".format(cell.row))
            r.orderNumber = val
    return r

def CreateSingleAdjustmentRow(row):
    r = SingleAdjustmentRow()
    for cell in row:
        col = cell.column
        val = cell.internal_value

        if col == SheetCols.CompanyFriendlyNameCol:
            if not val: raise Exception("No company name in row: {} and col: {}".format(cell.row, col))
            r.compName = val
        elif col == SheetCols.KindOfEntery:
            if not val: raise Exception("No type of entery in row: {} and col: {}".format(cell.row, col))
            r.kindOfEntery = val
        elif col == SheetCols.InvoiceAmount:
            if not val: raise Exception("No adjustment amount in row: {} and col: {}".format(cell.row, col))
            r.amount = val
        elif col == SheetCols.InvoiceDateCol:
            if val is not None:
                r.invoiceDate = ParseDateFromString(val)
            else:
                r.invoiceDate = val
        elif col == SheetCols.PaymentAccountedFor:
            r.adjustmentAccountedFor = False
            if val is not None:
                r.adjustmentAccountedFor = val.lower()=="yes"
        elif col == SheetCols.InvoiceNumberCol:
            r.adjustmentNo = val

    return r

def CreateSinglePaymentRow(row):
    r = SinglePaymentRow()
    for cell in row:
        col = cell.column
        val = cell.internal_value

        if col == SheetCols.InvoiceAmount:
            if not val: raise Exception("No cheque amount in row: {} and col: {}".format(cell.row, col))
            r.amount = val
        elif col == SheetCols.KindOfEntery:
            if not val: raise Exception("No type of entery in row: {} and col: {}".format(cell.row, col))
            r.kindOfEntery = GuessKindFromValue(val)
        elif col == SheetCols.BillingCategory:
            if not val: raise Exception("No bank name in row: {} and col: {}".format(cell.row, col))
            r.bankName = val
        elif col == SheetCols.InstrumentNumberCol:
            if not val: raise Exception("No cheque number in row: {} and col: {}".format(cell.row, col))
            r.chequeNumber = val
        elif col == SheetCols.CompanyFriendlyNameCol:
            if not val: raise Exception("No company name in row: {}".format(cell.row))
            r.compName = val
        elif col == SheetCols.InstrumentDateCol:
            if not val: raise Exception("No cheque date in row: {}".format(cell.row))
            r.pmtDate = ParseDateFromString(val)
        elif col == SheetCols.PaymentAccountedFor:
            if val is not None:
                r.paymentAccountedFor = True if val.lower()=="yes" else False
            else:
                r.paymentAccountedFor = False
    return r


def CreateSingleBillRow(row):
    b = SingleBillRow()
    for cell in row:
        col = cell.column
        val = cell.internal_value

        if col == SheetCols.InvoiceAmount:
            b.amount = val
        elif col == SheetCols.KindOfEntery:
            if not val: raise Exception("No type of entery in row: {} and col: {}".format(cell.row, col))
            b.kindOfEntery = val
        elif col == SheetCols.BillingCategory:
            b.billingCategory = val
        elif col == SheetCols.InvoiceNumberCol:
            if not val: raise Exception("Row: {} seems not to have any bill number.".format(cell.row))
            b.billNumber = val
        elif col == SheetCols.CompanyFriendlyNameCol:
            if not val: raise Exception("Row: {} seems empty. Please fix the database".format(cell.row))
            b.compName = val
        elif col == SheetCols.Courier:
            b.courier = val
        elif col == SheetCols.InvoiceDateCol:
            if not val: raise Exception("No invoice date in row: {} and col: {}".format(cell.row, col))
            b.invoiceDate = ParseDateFromString(val)
        elif col == SheetCols.GoodsValue:
            #if not val: raise Exception("No goods value in row: {} and col: {}".format(cell.row, col))
            b.goodsValue = val
        elif col == SheetCols.PaymentReceivingDate:
            if val is not None:
                b.paymentReceivingDate = ParseDateFromString(val)
            else:
                b.paymentReceivingDate = val
        elif col == SheetCols.Tax:
            #if not val: raise Exception("No tax in row: {} and col: {}".format(cell.row, col))
            b.tax = val
        elif col == SheetCols.PaymentStatus:
            b.paymentStatus = val
        elif col == SheetCols.DocketNumber:
            if type(val) == float:
                b.docketNumber = str(int(val))
            elif type(val) == int:
                b.docketNumber = str(val)
            else:
                b.docketNumber = val
        elif col == SheetCols.DocketDate:
            if val:
                b.docketDate = ParseDateFromString(val)
            else:
                b.docketDate = val
        elif col == SheetCols.CourierName:
            b.courierName = val
        elif col == SheetCols.MaterialDesc:
            if isinstance(val, basestring):
              b.materialDesc = val
            elif val is None:
              b.materialDesc = "--"
            else:
              raise Exception("The material description should be string and not {} in row: {} and col: {}".format(type(val), cell.row, col))
        elif col == SheetCols.FormCReceivingDate:
            if val is not None:
                b.formCReceivingDate = ParseDateFromString(val)
            else:
                b.formCReceivingDate = val
    return b


def GuessCompanyGroupName(token):
    """Take a small string from user and try to guess the companyGroupName.
    Return None if it doesn't exist"""
    allCustomersInfo = GetAllCustomersInfo()
    uniqueCompGrpNames = [allCustomersInfo.GetCompanyGroupName(eachComp) for eachComp in allCustomersInfo]

    if not token:
        token = raw_input("Enter company name:")

    token.replace(' ', '')
    uniqueCompGrpNames = [u for u in uniqueCompGrpNames if u]
    uniqueCompGrpNames = list(set(uniqueCompGrpNames))
    for eachGrp in uniqueCompGrpNames:
        if eachGrp.lower().replace(' ', '').find(token.lower()) != -1:
            if raw_input("You mean: {0}\n(y/n):".format(eachGrp)).lower() == 'y':
                return eachGrp
    else:
        raise MyException("{} does not exist. Try a shorter string".format(token))

def GuessCompanyName(token):
    """Take a small string from user and try to guess the companyName.
    Return None if it doesn't exist"""

    allCustomersInfo = GetAllCustomersInfo()
    uniqueCompNames = [x for x in allCustomersInfo if x]

    if not token:
        token = raw_input("Enter company name:")

    token.replace(' ', '')
    for eachComp in uniqueCompNames:
        if eachComp.lower().replace(' ', '').find(token.lower()) != -1:
            if raw_input("You mean: {0}\n(y/n):".format(eachComp)).lower() == 'y':
                return eachComp
    else:
        raise MyException("{} does not exist. Try a shorter string".format(token))


def TotalAmountDueForThisCompany(allBillsDict, compName):
    """Returns the sum of total unpaid amount for this company"""
    allBillsForThisComp = allBillsDict[compName]
    newBillList = SelectUnpaidBillsFrom(allBillsForThisComp)
    return int(sum([b.amount for b in newBillList]))


def BillsFileChangedSinceLastTime():
    """
    This function will read the last stored time and let the user know if file has been changed since last time it was read.
    """
    with closing(shelve.open(PERSISTENT_STORAGE_PATH)) as sh:
        if sh.has_key(BILLS_FILE_LAST_CHANGE_SHELF_ID):
            return sh[BILLS_FILE_LAST_CHANGE_SHELF_ID] != os.path.getmtime(GetWorkBookPath())
    return True

def StoreNewTimeForBillsFile():
    """
    This function will store new time for bills file.
    """
    with closing(shelve.open(PERSISTENT_STORAGE_PATH)) as sh:
        sh[BILLS_FILE_LAST_CHANGE_SHELF_ID] = os.path.getmtime(GetWorkBookPath())
    return

def ShowPendingOrdersOnScreen():
  allOrdersDict = GetAllCompaniesDict().GetAllOrdersOfAllCompaniesAsDict()
  for eachComp, orders in allOrdersDict.items():
    for eachOrder in orders:
      print(type(eachOrder))
      PrintInBox(str(eachOrder))
  return

def SendSMSToThisCompany(compName, msg, sendToCCNumbers=False):
  from Util.Sms import SendSms
  from string import Template
  allCustInfo = GetAllCustomersInfo()
  smsNo = allCustInfo.GetSmsDispatchNumber(compName)
  if not smsNo: raise Exception("No sms no. feeded for customer: {}".format(compName))

  companyOfficialName = allCustInfo.GetCompanyOfficialName(compName)
  if not companyOfficialName: raise Exception("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

  d = dict()
  d["tFromName"] = "From: {}".format(GetOption("SMS_SECTION", 'FromDisplayName'))
  d["toName"] = "To: {}".format(companyOfficialName)
  d["msg"] = msg

  smsTemplate = Template("""$tFromName
$toName
$msg"""
)
  smsContents = smsTemplate.substitute(d)

  COMMA = ","
  smsNo = smsNo.replace(';', COMMA).strip()
  listOfNos = [x.strip() for x in smsNo.split(COMMA) if x.strip()]

  if sendToCCNumbers:
    additionalSmsNo = GetOption("SMS_SECTION", "CC_NO")
    if additionalSmsNo:
      additionalSmsNo = additionalSmsNo.replace(';', COMMA).strip()
      listOfNos.extend([x.strip() for x in additionalSmsNo.split(COMMA) if x.strip()])

  PrintInBox(smsContents)
  for x in listOfNos:
    print("Sending to this number: {}".format(x))
    SendSms(x, smsContents)
  return

if __name__ == "__main__":
    ShowPendingOrdersOnScreen()
