#######################################################
## Author: Ashish Anand
## Date: 25-Dec-2012
## Intent: To read bills.xlsx and store company info
## Requirement: Python Interpretor must be installed
## Openpyxl must be installed
#######################################################
from Util.Misc import GetPickledObject
from Util.Config import GetOption, GetAppDir
from Util.ExcelReader import GetRows, GetCellValue

import os


class CustomerInfoCol:
    """
    This class is used as Enum.
    If and when the format of excel file changes just change the column bindings in this class
    """
    CompanyFriendlyNameCol    = "A"
    CompanyGroupCol           = "B"
    BillingAddressCol         = "C"
    TinNumberCol              = "D"
    PhoneNumberCol            = "E"
    DeliveryPhoneNumberCol    = "F"
    SmsDispatchNumberCol      = "G"
    PaymentReminderSmsNoCol   = "H"
    MDNumbers                 = "I"
    MsorNoMSCol               = "J"
    CompanyOfficialNameCol    = "K"
    CourierAddressCol         = "L"
    DeliveryPinCodeCol        = "M"
    PreferredCourierCol       = "N"
    CityCol                   = "O"
    EmailForPayment           = "P"
    KindAttentionCol          = "Q"
    EmailForFormC             = "R"
    TrustCol                  = "S"
    IncludeDaysCol            = "T"
    CreditLimitCol            = "U"
    SendAutomaticMails        = "V"
    MinDaysGapCol             = "W"
    IncludeBillAmountInEmails = "X"
    CompanyCodeCol            = "Y"


def CreateSingleCustomerInfo(row):
    c = SingleCompanyInfo()
    for cell in row:
        col = cell.column
        val = GetCellValue(cell)

        if col == CustomerInfoCol.CompanyFriendlyNameCol:
            c.companyFriendlyName = val
        elif col == CustomerInfoCol.BillingAddressCol:
            c.billingAddress = val
        elif col == CustomerInfoCol.TinNumberCol:
            c.tinNumber = val
        elif col == CustomerInfoCol.PhoneNumberCol:
            c.phoneNumber = val
        elif col == CustomerInfoCol.DeliveryPinCodeCol:
            c.deliveryPinCode = val
        elif col == CustomerInfoCol.SmsDispatchNumberCol:
            c.smsDispatchNo = val
        elif col == CustomerInfoCol.PaymentReminderSmsNoCol:
            c.paymentSMSNo = val
        elif col == CustomerInfoCol.MDNumbers:
            c.MDNumbers = val
        elif col == CustomerInfoCol.DeliveryPhoneNumberCol:
            c.deliveryPhNo = val
        elif col == CustomerInfoCol.MsorNoMSCol:
            c.msOrNoms = val
        elif col == CustomerInfoCol.CompanyOfficialNameCol:
            c.companyOfficialName = val
        elif col == CustomerInfoCol.CourierAddressCol:
            c.courierAddress = val
        elif col == CustomerInfoCol.PreferredCourierCol:
            c.preferredCourier = val
        elif col == CustomerInfoCol.CityCol:
            c.city = val
        elif col == CustomerInfoCol.EmailForPayment:
            c.emailForPayment = val.replace("\n","") if val else val
        elif col == CustomerInfoCol.EmailForFormC:
            c.emailForFormC = val.replace("\n", "") if val else val
        elif col == CustomerInfoCol.KindAttentionCol:
            c.kindAttentionPerson = val
        elif col == CustomerInfoCol.TrustCol:
            c.trust = val or 1
        elif col == CustomerInfoCol.IncludeDaysCol:
            c.includeDays = val
        elif col == CustomerInfoCol.CreditLimitCol:
            c.creditLimit = val
        elif col == CustomerInfoCol.SendAutomaticMails:
            c.includeInAutomaticMails = val
        elif col == CustomerInfoCol.CompanyCodeCol:
            c.companyCode = val
        elif col == CustomerInfoCol.MinDaysGapCol:
            c.minDaysGapBetweenAutomaticMails = val
        elif col == CustomerInfoCol.IncludeBillAmountInEmails:
            c.includeBillAmountinEmails = val
        elif col == CustomerInfoCol.CompanyGroupCol:
            c.companyGroupName = val
    return c


class SingleCompanyInfo():
    """This represents a single row in Cust sheet of Bills.xlsx"""
    pass


class _AllCustomersInfo(dict):
    """Base Class which is basically a dictionary. Key is compName and Value is a list of info"""
    def __init__(self, custDBwbPath):
        super(_AllCustomersInfo, self).__init__(dict())
        for row in GetRows(
            workbookPath=custDBwbPath,
            sheetName=GetOption("CONFIG_SECTION", "NameOfCustSheet"),
            firstRow=GetOption("CONFIG_SECTION", "CustomerDataStartsAtRow"),
            includeLastRow=False):
              c = CreateSingleCustomerInfo(row)
              self[c.companyFriendlyName] = c

    def GetListOfCompNamesForThisGrp(self, grpName):
        res = []
        for compName in self:
            if self[compName].companyGroupName == grpName:
                res.append(compName)
        return res

    def GetTrustForCustomer(self, compName):
        return self[compName].trust

    def GetCreditLimitForCustomer(self, compName):
        return self[compName].creditLimit

    def GetCompanyOfficialName(self, compName):
        return self[compName].companyOfficialName

    def GetCompanyGroupName(self, compName):
        return self[compName].companyGroupName

    def GetDeliveryPinCode(self, compName):
        return self[compName].deliveryPinCode

    def GetSmsDispatchNumber(self, compName):
        return self[compName].smsDispatchNo

    def GetPaymentSMSNumber(self, compName):
        return self[compName].paymentSMSNo

    def GetMDPhoneNumbers(self, compName):
        return self[compName].MDNumbers

    def GetDeliveryPhoneNumber(self, compName):
        return self[compName].deliveryPhNo

    def GetMsOrNomsForCustomer(self, compName):
        return self[compName].msOrNoms

    def GetCustomerPhoneNumber(self, compName):
        return self[compName].phoneNumber

    def GetCustomerDeliveryAddress(self, compName):
        return self[compName].courierAddress

    def GetCustomerPreferredCourier(self, compName):
        return self[compName].preferredCourier

    def GetCustomerCity(self, compName):
        return self[compName].city

    def GetPaymentReminderEmailsForCustomer(self, compName):
        return self[compName].emailForPayment

    def GetFormCEmailsForCustomer(self, compName):
        return self[compName].emailForFormC

    def GetCustomerKindAttentionPerson(self, compName):
        return self[compName].kindAttentionPerson

    def GetIncludeDaysOrNot(self, compName):
        return self[compName].includeDays

    def IncludeBillAmountInEmails(self, compName):
        val = self[compName].includeBillAmountinEmails
        return val.lower() in ["yes", "y"]

    def IncludeCustInAutomaticMails(self, compName):
        val = self[compName].includeInAutomaticMails
        return val.lower() in ["yes", "y"]

    def GetMinDaysGapBetweenMails(self, compName):
        return self[compName].minDaysGapBetweenAutomaticMails

    def GetFormCEmailAsListForCustomer(self, compName):
        toMailStr = self.GetFormCEmailsForCustomer(compName)
        if not toMailStr: return None
        toMailList = toMailStr.replace(';', ',').replace(' ', '').split(',')
        #Remove spaces from eachMail in the list and create a new list
        return [x for x in toMailList if x]

    def GetPaymentReminderEmailAsListForCustomer(self, compName):
        toMailStr = self.GetPaymentReminderEmailsForCustomer(compName)
        if not toMailStr: return None
        toMailList = toMailStr.replace(';', ',').replace(' ', '').split(',')
        #Remove spaces from eachMail in the list and create a new list
        return [x for x in toMailList if x]


def GetAllCustomersInfo():
    custDBwbPath = os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "CustDBRelativePath"))
    def _CreateAllCustomersInfoObject(custDBwbPath):
        return _AllCustomersInfo(custDBwbPath)
    return GetPickledObject(custDBwbPath, createrFunction=_CreateAllCustomersInfoObject)
