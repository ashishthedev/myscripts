###############################################################################
## Author: Ashish Anand
## Date: 15 Dec 2011
## Intent: To read bills.xlsx and provide some utility functions to deal
## with it
## Requirement: Python Interpretor must be installed
###############################################################################
from UtilException import MyException
from UtilConfig import GetOption, GetAppDir
from UtilExcelReader import LoadIterableWorkbook
from UtilMisc import GetPickledObject, ParseDateFromString, DD_MM_YYYY
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


class CompaniesDict(dict):
    """Base Class which is basically a dictionary. Key is compName and Value is a list of single bills of that company"""
    def __init__(self):
        super(CompaniesDict, self).__init__(dict())

    def AddBill(self, b):
        """
        The only method through which this master database is prepared.
        Find out if the company exists already. If it does, add the bill to that company.
        If it doesnt, create the company and add the bill to that company.
        """
        if b.compName in self.keys():
            self[b.compName].append(b)
        else:
            self[b.compName] = Company(b.compName)
            self[b.compName].append(b)


class CandidateCompaniesDict(CompaniesDict):
    """This class represents the resultant companies of WhoPaid() operation, i.e companies who can pay the particular amount.
    It is basically a dictonary just like the base class. Key is company and value is its bills that has been paid"""
    def __init__(self):
        super(CandidateCompaniesDict, self).__init__()

    def __str__(self):
        """This function contains all the formatting in which the results should be shown."""
        result = ""
        if(len(self) > 0):
            for eachComp in self.values():
                result += "\n" + str(eachComp)
        else:
            result += "Cannot detect who paid amount"
        return result

def GetAllCompaniesDict():
    workbookPath = GetWorkBookPath()
    def _CreateAllCompaniesDict(workbookPath):
        return _AllCompaniesDict(workbookPath)
    return GetPickledObject(workbookPath, _CreateAllCompaniesDict)

class _AllCompaniesDict(CompaniesDict):
    """
    This class represents the heart of logic.
    It is an aggregation of all companies.
    It is a dictonary having company names as keys and list of all bills as values.
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
            if rowNumber < MIN_ROW:
                continue
            if rowNumber >= MAX_ROW:
                break
            b = CreateSingleBillForRow(row)
            self.AddBill(b)


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


class SingleBill:
    """
    This class represents a single row in the excel sheet which in effect represents a single bill
    """
    def __init__(self):
        self.compName = None
        self.billingCategory = None
        self.billNumber = None
        self.invoiceDate = None
        self.goodsValue = None
        self.tax = None
        self.courier = None
        self.billAmount = None
        self.paymentReceivingDate = None
        self.paymentStatus = None

    def __str__(self):
        paymentDate = self.paymentReceivingDate
        if not paymentDate:
            paymentDate = "-----------"
        else:
            paymentDate = DD_MM_YYYY(self.PaymentReceivingDate)

        return "Rs.{:<5} Bill:{:<5} {} {:<5} {}".format(
            int(self.billAmount),
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
            if(intx(self.billAmount) != (intx(self.goodsValue) + intx(self.tax) + intx(self.courier))):
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
    allCompaniesDict = GetAllCompaniesDict()
    totalBillList = list()
    for compBillList in allCompaniesDict.values():
        totalBillList.extend(compBillList)
    totalBillList = RemoveMinusOneBills(totalBillList)
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

def RemoveMinusOneBills(billList):
    return [b for b in billList if b.billNumber != str(int(-1))]


class BillsCol:
    """
    This class is used as Enum.
    If and when the format of excel file changes just change the column bindings in this class
    """
    CompanyFriendlyNameCol = "A"
    BillingCategory        = "B"
    BillNumber             = "C"
    InvoiceDate            = "D"
    MaterialDesc           = "E"
    GoodsValue             = "F"
    Tax                    = "G"
    Courier                = "H"
    BillAmount             = "I"
    DocketNumber           = "J"
    DocketDate             = "K"
    CourierName            = "L"
    PaymentReceivingDate   = "M"
    PaymentStatus          = "N"
    FormCReceivingDate     = "O"

def CreateSingleBillForRow(row):
    b = SingleBill()
    for cell in row:
        col = cell.column
        val = cell.internal_value

        if col == BillsCol.BillAmount: b.billAmount = val
        elif col == BillsCol.BillingCategory: b.billingCategory = val
        elif col == BillsCol.BillNumber:
            if not val: raise Exception("Row:{} seems not to have any bill number.".format(cell.row))
            b.billNumber = str(int(val))
        elif col == BillsCol.CompanyFriendlyNameCol:
            if not val: raise Exception("Row:{} seems empty. Please fix the database".format(cell.row))
            b.compName = val
        elif col == BillsCol.Courier: b.courier = val
        elif col == BillsCol.InvoiceDate:
            if val is not None:
                b.invoiceDate = ParseDateFromString(val)
            else:
                b.invoiceDate = val
        elif col == BillsCol.GoodsValue: b.goodsValue = val
        elif col == BillsCol.PaymentReceivingDate:
            if val is not None:
                b.paymentReceivingDate = ParseDateFromString(val)
            else:
                b.paymentReceivingDate = val
        elif col == BillsCol.Tax: b.tax = val
        elif col == BillsCol.PaymentStatus: b.paymentStatus = val
        elif col == BillsCol.DocketNumber:
            if type(val) == float:
                b.docketNumber = str(int(val))
            elif type(val) == int:
                b.docketNumber = str(val)
            else:
                b.docketNumber = val
        elif col == BillsCol.DocketDate:
            if val:
                b.docketDate = ParseDateFromString(val)
            else:
                b.docketDate = val
        elif col == BillsCol.CourierName: b.courierName = val
        elif col == BillsCol.MaterialDesc:
            if val is not None:
                b.materialDesc = val
            else:
                b.materialDesc = "--"
        elif col == BillsCol.FormCReceivingDate:
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
                return eachComp
    else:
        raise MyException("{} does not exist. Try a shorter string".format(token))


def TotalAmountDueForThisCompany(allCompaniesDict, compName):
    """Returns the sum of total unpaid amount for this company"""
    newBillList = SelectUnpaidBillsFrom(allCompaniesDict[compName])
    return int(sum([b.billAmount for b in newBillList]))


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

