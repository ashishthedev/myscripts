###############################################################################
## Author: Ashish Anand
## Date: 15 Dec 2011
## Intent: To read bills.xlsx and provide some utility functions to deal
## with it
## Requirement: Python Interpretor must be installed
###############################################################################
from Util.Config import GetOption, GetAppDir
from Util.Decorators import memoize
from Util.ExcelReader import GetRows, GetCellValue
from Util.Exception import MyException
from Util.Misc import GetPickledObject, ParseDateFromString, DD_MM_YYYY, PrintInBox
from Util.Persistent import Persistent

from whopaid.customers_info import GetAllCustomersInfo

import os
import datetime
ALLOWED_TAXATION_RATES = GetOption("CONFIG_SECTION", "ALLOWED_TAXATION_RATES").replace(";", ",").split(",")

ALL_CUST_INFO = GetAllCustomersInfo()

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
        self[KIND.OPENING_BALANCE] = dict()


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

    def AddOpeningBalance(self, o):
        self._AddEntry(KIND.OPENING_BALANCE, o)


    @memoize
    def GetAllBillsOfAllCompaniesAsDict(self):
        return self[KIND.BILL]

    def GetAllPaymentsByAllCompaniesAsDict(self):
        return self[KIND.PAYMENT]

    def GetAllAdjustmentsOfAllCompaniesAsDict(self):
        return self[KIND.ADJUSTMENT]

    def GetAllOrdersOfAllCompaniesAsDict(self):
        return self[KIND.ORDER]

    def GetAllOpeningBalancesOfAllCompaniesAsDict(self):
        return self[KIND.OPENING_BALANCE]


    def GetBillsListForThisCompany(self, compName):
        return self.GetAllBillsOfAllCompaniesAsDict().get(compName, [])

    def GetPaymentsListForThisCompany(self, compName):
        return self.GetAllPaymentsByAllCompaniesAsDict().get(compName, [])

    def GetUnAccountedAdjustmentsListForCompany(self, compName):
      adjustmentList = self.GetAllAdjustmentsOfAllCompaniesAsDict().get(compName, [])
      return SelectUnAccountedAdjustmentsFrom(adjustmentList)

    def GetOrdersListForCompany(self, compName):
        return self.GetAllOrdersOfAllCompaniesAsDict().get(compName, [])

    def GetOpeningBalanceListForCompany(self, compName):
        return self.GetAllOpeningBalancesOfAllCompaniesAsDict().get(compName, [])


@memoize
def GetAllCompaniesDict():
  workbookPath = GetWorkBookPath()
  def _CreateAllCompaniesDict(workbookPath):
    return _AllCompaniesDict(workbookPath)
  try:
    return GetPickledObject(workbookPath, _CreateAllCompaniesDict)
  except MyException as ex:
    PrintInBox("Exception occurred: " + str(ex))
    raise ex
  return

class KIND(object):
  BILL            = 1
  PAYMENT         = 2
  ADJUSTMENT      = 3
  ORDER           = 4
  PUNTED_ORDER    = 5
  OPENING_BALANCE = 6

def _GuessKindFromValue(val):
  if val:
    val = val.lower()
    if val == "bill": return KIND.BILL
    elif val == "payment": return KIND.PAYMENT
    elif val == "adjustment": return KIND.ADJUSTMENT
    elif val == "order": return KIND.ORDER
    elif val == "punted": return KIND.PUNTED_ORDER
    elif val == "openingbalance": return KIND.OPENING_BALANCE
  return None

def GuessKindFromRow(row):
  for cell in row:
    col = cell.column
    val = GetCellValue(cell)

    if col == SheetCols.KindOfEntery:
      return _GuessKindFromValue(val)
  return None

def ShrinkWorkingArea():
  return FirstReadablePersistentRow().SetFirstRow()

class FirstReadablePersistentRow(Persistent):
  """
  It keeps a Persistent track of the first row where meaningful data should be read from
  """
  identifier = "firstRow"
  def __init__(self):
    super(self.__class__, self).__init__(self.__class__.__name__)

  def _SetFirstRow(self, rowNumber):
    self[self.identifier] = rowNumber

  def GetFirstRow(self):
    if GetOption("CONFIG_SECTION", "ShrinkWorkingArea").lower() == "true":
      if self.identifier in self:
        return self[self.identifier]
    return None

  def SetFirstRow(self):
    """
    This does not run all the time but only sometimes
    """
    if GetOption("CONFIG_SECTION", "ShrinkWorkingArea").lower() != "true": return

    import random
    probabilityToExecute = 30
    if random.randint(1, round(100/probabilityToExecute)) != 1:
      print("Not shrinking. May be next time")
      return
    print("Shrinking working area. This can take time...")
    import datetime
    initial = datetime.datetime.now()

    allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
    c, billList = allBillsDict.popitem()
    firstRow = billList[0].rowNumber + 100000
    allBills = list()
    for c, billList in allBillsDict.iteritems():
      allBills.extend(billList)

    allBills = [b for b in allBills if b.billingCategory.lower() in ["central"]]

    for b in allBills:
      if b.rowNumber < firstRow: # We only look at rows which have are lower than which is already found.
        if b.formCReceivingDate is None:
          firstRow = b.rowNumber
        if b.paymentReceivingDate is None:
          firstRow = b.rowNumber

    print("Identified first row is : {}".format(firstRow))
    self[self.identifier] = firstRow

    delta = datetime.datetime.now() - initial
    print("Took {} seconds".format(delta.seconds))

    return



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

    rows = GetRows(workbookPath=workbookPath,
        sheetName = GetOption("CONFIG_SECTION", "NameOfSaleSheet"),
        firstRow = GetOption("CONFIG_SECTION", "DataStartsAtRow"),
        includeLastRow=False)

    for row in rows:
      kind = GuessKindFromRow(row)
      if kind == KIND.BILL:
        self.AddBill(_CreateSingleBillRow(row))
      elif kind == KIND.PAYMENT:
        self.AddPayment(CreateSinglePaymentRow(row))
      elif kind == KIND.ADJUSTMENT:
        self.AddAdjustment(CreateSingleAdjustmentRow(row))
      elif kind == KIND.ORDER:
        self.AddOrder(CreateSingleOrderRow(row))
      elif kind == KIND.PUNTED_ORDER:
        pass #DO NOT DO ANYTHING FOR PUNTED ORDERS
      elif kind == KIND.OPENING_BALANCE:
        self.AddOpeningBalance(CreateOpeningBalanceRow(row))
      else:
        firstCell = row[0]
        raise MyException("Error in row number: {} Kind of entry is invalid".format(firstCell.row))



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


  def CheckRateSanity(self):
    ALL_CUST_INFO.GetCompanyRateMap7Dec17(self.compName) #If GetItemRateMapFromRateString returns, everything went well.
    return

  def CheckEachBillsCalculation(self):
    for b in self:
      b.CheckCalculation()

  def CheckCoordinatesPresent(self):
      return ALL_CUST_INFO.GetCompanyLatitude(self.compName) and ALL_CUST_INFO.GetCompanyLongitude(self.compName)

  def CheckEachBillsBillingCategory(self):
    uniqueCategory = set()
    #Create a unique set
    for b in self:
      if b.billingCategory.lower() not in ["jobwork", "tracking", "gr"]:
        uniqueCategory.add(b.billingCategory.lower())

    if len(uniqueCategory) > len(["central/up", "gst"]):
      for u in uniqueCategory:
        print(u)
      raise MyException("Bills are issued in more than two category for company:{} - {} ".format(self.compName, uniqueCategory))


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

    @property
    def isUnpaid(self):
      return  not (self.adjustmentAccountedFor or self.adjustmentPaidFor)

class SingleOrderRow(SingleRow):
    def __str__(self):
        return "ORDER: {cn:}\n{dt}\n{md} ".format(
                dt = DD_MM_YYYY(self.orderDate),
                cn = self.compName,
                md = self.materialDesc
                )

class SingleOpeningBalanceRow(SingleRow):
    def __str__(self):
        return "OPENING_BALANCE: {cn:}\n{dt}\n{amt} ".format(
                dt  = DD_MM_YYYY(self.orderDate),
                cn  = self.compName,
                amt = self.amount
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
            paymentDate = DD_MM_YYYY(self.paymentReceivingDate)

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
      taxLevied = floatx(self.tax) + floatx(self.cgstAmount) + floatx(self.sgstAmount) + floatx(self.igstAmount)
      if intx(self.goodsValue) != 0:
        if(abs(floatx(self.amount) - (floatx(self.goodsValue) + taxLevied + floatx(self.courier))) > .01):
          import pprint
          print("self.amount ={}".format(self.amount))
          print("self.goodsValue ={}".format(self.goodsValue))
          print("taxLevied ={}".format(taxLevied))
          print("self.courier ={}".format(self.courier))

          raise MyException("Calculation error in {} bill#{} - data{}".format(self.billingCategory, self.billNumber, pprint.pformat(vars(self))))
      #If the bill has been issued in last one year, check its taxation rate also
      if self.billingCategory.lower() in set(["tracking", "export", "jobwork", "gr"]):
        return
      if self.compName.lower().startswith("yasmin"):
        return
      if (datetime.date.today() - self.invoiceDate).days < 365:
        for taxRate in ALLOWED_TAXATION_RATES:
          expectedTax = self.goodsValue*float(taxRate)/100
          if abs(expectedTax - taxLevied) < 1:
            break
        else:
          zeroTaxationRateCompanies = ["elmr"]
          for zeroTaxComp in zeroTaxationRateCompanies:
            if self.compName.lower().startswith(zeroTaxComp):
              break
          else:
              pass
              # Mixed tax rates bill like  diamond paste 28% AND other stuff at
              # 18% creates false alarm. Silencing it though it should be on.
              # Try to create an exempted field in data and do selective
              # silencing.
              #raise MyException("Calculated sales tax in bill#{} dt {} issued to {} is probably wrong. Expected tax:{}. taxLevied: {}. The expected taxation rates are: {}".format(self.billNumber, DD_MM_YYYY(self.invoiceDate), self.compName, expectedTax , taxLevied, ALLOWED_TAXATION_RATES))
      return



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


@memoize
def GetAllBillsInLastNDays(nDays):
    allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
    totalBillList = list()
    for compName, compBillList in allBillsDict.iteritems():
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
    return [a for a in adjustmentList if a.isUnpaid]

def RemoveTrackingBills(billList):
    return [b for b in billList if not b.billingCategory.lower().startswith("tracking")]

def RemoveGRBills(billList):
    return [b for b in billList if not b.billingCategory.lower().startswith("gr")]

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
    CGSTCol                = "L"
    SGSTCol                = "M"
    IGSTCol                = "N"
    InvoiceAmount          = "O"
    DocketNumber           = "P"
    DocketDate             = "Q"
    CourierName            = "R"
    PaymentReceivingDate   = "S"
    PaymentStatus          = "T"
    PaymentAccountedFor    = "U"

    FormCReceivingDate     = "X"

def CreateSingleOrderRow(row):
  r = SingleOrderRow()
  for cell in row:
    col = cell.column
    val = GetCellValue(cell)

    if col == SheetCols.CompanyFriendlyNameCol:
      if not val: raise MyException("Row: {} seems empty. Please fix the database".format(cell.row))
      r.compName = val
    elif col == SheetCols.KindOfEntery:
      r.kindOfEntery = val
    elif col == SheetCols.MaterialDesc:
      if not val: raise MyException("Order in row: {} seems empty. Please fix the database".format(cell.row))
      r.materialDesc = val
    elif col == SheetCols.InstrumentDateCol:
      if not val: raise MyException("Date in row: {} seems empty. Please fix the database".format(cell.row))
      r.orderDate = ParseDateFromString(val)
    elif col == SheetCols.InstrumentNumberCol:
      r.orderNumber = val or "--"
  return r

def CreateOpeningBalanceRow(row):
  r = SingleOpeningBalanceRow()
  for cell in row:
    col = cell.column
    val = GetCellValue(cell)

    if col == SheetCols.CompanyFriendlyNameCol:
      if not val: raise MyException("Row: {} seems empty. Please fix the database".format(cell.row))
      r.compName = val
    elif col == SheetCols.KindOfEntery:
      if not val: raise MyException("Kind of entry in row: {} seems empty. Please fix the database".format(cell.row))
      r.kindOfEntery = val
    elif col == SheetCols.InstrumentDateCol:
      if not val: raise MyException("Date in row: {} seems empty. Please fix the database".format(cell.row))
      r.openingBalanceDate = ParseDateFromString(val)
    elif col == SheetCols.InvoiceAmount:
      if val == None: raise MyException("Amount in row: {} seems empty. Please fix the database".format(cell.row))
      r.amount = val
  return r

def CreateSingleAdjustmentRow(row):
    r = SingleAdjustmentRow()
    for cell in row:
        col = cell.column
        val = GetCellValue(cell)

        if col == SheetCols.CompanyFriendlyNameCol:
            if not val: raise MyException("No company name in row: {} and col: {}".format(cell.row, col))
            r.compName = val
        elif col == SheetCols.KindOfEntery:
            if not val: raise MyException("No type of entery in row: {} and col: {}".format(cell.row, col))
            r.kindOfEntery = val
        elif col == SheetCols.InvoiceAmount:
            if not val: raise MyException("No adjustment amount in row: {} and col: {}".format(cell.row, col))
            r.amount = int(val)
        elif col == SheetCols.InvoiceDateCol:
            r.invoiceDate = val
            if val is not None:
                r.invoiceDate = ParseDateFromString(val)
        elif col == SheetCols.PaymentStatus:
            r.adjustmentPaidFor = False
            if val is not None:
                r.adjustmentPaidFor = val.lower()=="paid"
        elif col == SheetCols.PaymentAccountedFor:
            r.adjustmentAccountedFor = False
            if val is not None:
                r.adjustmentAccountedFor = val.lower()=="yes"
        elif col == SheetCols.InvoiceNumberCol:
          r.adjustmentNo = val
          if val is not None:
            r.adjustmentNo = int(val)
    return r

def CreateSinglePaymentRow(row):
    r = SinglePaymentRow()
    for cell in row:
        col = cell.column
        val = GetCellValue(cell)

        if col == SheetCols.InvoiceAmount:
            if not val: raise MyException("No cheque amount in row: {} and col: {}".format(cell.row, col))
            r.amount = int(val)
        elif col == SheetCols.KindOfEntery:
            if not val: raise MyException("No type of entery in row: {} and col: {}".format(cell.row, col))
            r.kindOfEntery = _GuessKindFromValue(val)
        elif col == SheetCols.BillingCategory:
            if not val: raise MyException("No bank name in row: {} and col: {}".format(cell.row, col))
            r.bankName = val
        elif col == SheetCols.InstrumentNumberCol:
            if not val: raise MyException("No cheque number in row: {} and col: {}".format(cell.row, col))
            r.chequeNumber = val
        elif col == SheetCols.CompanyFriendlyNameCol:
            if not val: raise MyException("No company name in row: {}".format(cell.row))
            r.compName = val
        elif col == SheetCols.InstrumentDateCol:
            if not val: raise MyException("No cheque date in row: {}".format(cell.row))
            r.pmtDate = ParseDateFromString(val)
        elif col == SheetCols.PaymentAccountedFor:
            r.paymentAccountedFor = False
            if val is not None:
                r.paymentAccountedFor = True if val.lower()=="yes" else False
    return r


def _CreateSingleBillRow(row):
  b = SingleBillRow()
  for cell in row:
    col = cell.column
    val = GetCellValue(cell)

    b.rowNumber = cell.row
    if col == SheetCols.SGSTCol:
      b.sgstAmount = floatx(val)
    elif col == SheetCols.CGSTCol:
      b.cgstAmount = floatx(val)
    elif col == SheetCols.IGSTCol:
      b.igstAmount = floatx(val)
    elif col == SheetCols.InvoiceAmount:
      if val==None: raise MyException("No amount mentioned in row: {} and col: {}".format(cell.row, col))
      b.amount = float(val)
    elif col == SheetCols.InstrumentNumberCol:
      if not val: raise MyException("No PO mentioned in row: {} and col: {}".format(cell.row, col))
      b.poNumber = val
    elif col == SheetCols.InstrumentDateCol:
      if not val: raise MyException("No PO date mentioned in row: {} and col: {}".format(cell.row, col))
      b.poDate = ParseDateFromString(val)
    elif col == SheetCols.KindOfEntery:
      if not val: raise MyException("No type of entery in row: {} and col: {}".format(cell.row, col))
      b.kindOfEntery = val
    elif col == SheetCols.BillingCategory:
      b.billingCategory = val
    elif col == SheetCols.InvoiceNumberCol:
      if not val: raise MyException("Row: {} seems not to have any bill number.".format(cell.row))
      b.billNumber = int(val)
    elif col == SheetCols.CompanyFriendlyNameCol:
      if not val: raise MyException("Row: {} seems empty. Please fix the database".format(cell.row))
      b.compName = val
    elif col == SheetCols.Courier:
      b.courier = val
    elif col == SheetCols.InvoiceDateCol:
      if not val: raise MyException("No invoice date in row: {} and col: {}".format(cell.row, col))
      b.invoiceDate = ParseDateFromString(val)
    elif col == SheetCols.GoodsValue:
      #if not val: raise MyException("No goods value in row: {} and col: {}".format(cell.row, col))
      b.goodsValue = val
    elif col == SheetCols.PaymentReceivingDate:
      if val is not None:
        b.paymentReceivingDate = ParseDateFromString(val)
      else:
        b.paymentReceivingDate = val
    elif col == SheetCols.Tax:
      #if not val: raise MyException("No tax in row: {} and col: {}".format(cell.row, col))
      b.tax = val
    elif col == SheetCols.PaymentStatus:
      b.paymentStatus = val
    elif col == SheetCols.DocketNumber:
      if type(val) in [float, int]:
        b.docketNumber = str(int(val))
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
        raise MyException("The material description should be string and not {} in row: {} and col: {}".format(type(val), cell.row, col))
    elif col == SheetCols.FormCReceivingDate:
      if val is not None:
        try:
          b.formCReceivingDate = ParseDateFromString(val)
        except:
          b.formCReceivingDate = val
      else:
        b.formCReceivingDate = val
  return b


def AllCompanyGroupNamesWhichHaveBeenBilledInPast():
  allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
  uniqueCompGrpNames = []
  for eachCompName, _ in allBillsDict.iteritems():
    uniqueCompGrpNames = [ALL_CUST_INFO.GetCompanyGroupName(eachComp) for eachComp, _ in allBillsDict.iteritems()]

  uniqueCompGrpNames = list(set(uniqueCompGrpNames))
  return uniqueCompGrpNames

def AllCompanyGroupNames():
  allCustomersInfo = ALL_CUST_INFO
  uniqueCompGrpNames = [allCustomersInfo.GetCompanyGroupName(eachComp) for eachComp in allCustomersInfo]
  uniqueCompGrpNames = [u for u in uniqueCompGrpNames if u]
  uniqueCompGrpNames = list(set(uniqueCompGrpNames))
  return uniqueCompGrpNames

def GuessCompanyGroupName(token):
  """Take a small string from user and try to guess the companyGroupName.
  Return None if it doesn't exist"""

  if not token:
    token = raw_input("Enter company name:")

  token.replace(' ', '')
  for eachGrp in AllCompanyGroupNames():
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



def ShowPendingOrdersOnScreen():
  allOrdersDict = GetAllCompaniesDict().GetAllOrdersOfAllCompaniesAsDict()
  for eachComp, orders in allOrdersDict.iteritems():
    for eachOrder in orders:
      print(type(eachOrder))
      PrintInBox(str(eachOrder))
  return

def GetPayableBillsAndAdjustmentsForThisComp(compName):
  unpaidBillsList = SelectUnpaidBillsFrom(GetAllCompaniesDict().GetBillsListForThisCompany(compName))
  unpaidBillsList = RemoveTrackingBills(unpaidBillsList)
  unpaidBillsList = RemoveGRBills(unpaidBillsList)
  unpaidBillsList.sort(key=lambda b: datex(b.invoiceDate))

  adjustmentBills = GetAllCompaniesDict().GetUnAccountedAdjustmentsListForCompany(compName)
  if adjustmentBills:
    if len(adjustmentBills) > 1:
      #TODO: Currently we are accomodating only one adjustment bill
      raise MyException("There should be only one adjustment for M/s {}".format(compName))
    for a in adjustmentBills:
      a.billNumber = -1
      a.invoiceDate = a.invoiceDate or datetime.date.today()

  return unpaidBillsList, adjustmentBills


if __name__ == "__main__":
    ShowPendingOrdersOnScreen()
