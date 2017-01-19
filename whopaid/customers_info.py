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
    FORMCSMSNoCol             = "I"
    MDNumbers                 = "J"
    CasingSizeCol             = "K"
    MsorNoMSCol               = "L"
    CompanyOfficialNameCol    = "M"
    CourierAddressCol         = "N"
    DeliveryStateCol          = "O"
    DeliveryPinCodeCol        = "P"
    PreferredCourierCol       = "Q"
    CityCol                   = "R"
    EmailForPayment           = "S"
    KindAttentionCol          = "T"
    EmailForFormC             = "U"
    TrustCol                  = "V"
    IncludeDaysCol            = "W"
    CreditLimitCol            = "X"
    FormNameCol               = "Y"
    MinDaysGapCol             = "Z"
    IncludeBillAmountInEmails = "AA"
    CompanyCodeCol            = "AB"


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
            c.deliveryPinCode = str(int(val)) if val else ""
        elif col == CustomerInfoCol.DeliveryStateCol:
            c.deliveryState = val
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
        elif col == CustomerInfoCol.FormNameCol:
            c.formName = val
        elif col == CustomerInfoCol.CompanyCodeCol:
            c.companyCode = val
        elif col == CustomerInfoCol.CasingSizeCol:
            c.casingSize = val
        elif col == CustomerInfoCol.MinDaysGapCol:
            c.minDaysGapBetweenAutomaticMails = val
        elif col == CustomerInfoCol.IncludeBillAmountInEmails:
            c.includeBillAmountinEmails = val
        elif col == CustomerInfoCol.CompanyGroupCol:
            c.companyGroupName = val
    return c


class SingleCompanyInfo():
  """This represents a single row in Cust sheet of Bills.xlsx"""
  @property
  def jsonNode(self):
    singleComp = dict()
    singleComp["companyFriendlyName"] = self.companyFriendlyName
    singleComp["billingAddress"] = self.billingAddress
    singleComp["tinNumber"] = self.tinNumber
    singleComp["phoneNumber"] = self.phoneNumber
    singleComp["deliveryPinCode"] = self.deliveryPinCode
    singleComp["deliveryState"] = self.deliveryState
    singleComp["smsDispatchNo"] = self.smsDispatchNo
    singleComp["paymentSMSNo"] = self.paymentSMSNo
    singleComp["MDNumbers"] = self.MDNumbers
    singleComp["deliveryPhNo"] = self.deliveryPhNo
    singleComp["casingSize"] = self.casingSize
    singleComp["msOrNoms"] = self.msOrNoms
    singleComp["companyOfficialName"] = self.companyOfficialName
    singleComp["courierAddress"] = self.courierAddress
    singleComp["preferredCourier"] = self.preferredCourier
    singleComp["city"] = self.city
    singleComp["emailForPayment"] = self.emailForPayment
    singleComp["emailForFormC"] = self.emailForFormC
    singleComp["kindAttentionPerson"] = self.kindAttentionPerson
    singleComp["trust"] = self.trust
    singleComp["includeDays"] = self.includeDays
    singleComp["creditLimit"] = self.creditLimit
    singleComp["formName"] = self.formName
    singleComp["minDaysGapBetweenAutomaticMails"] = self.minDaysGapBetweenAutomaticMails
    singleComp["includeBillAmountinEmails"] = self.includeBillAmountinEmails
    singleComp["companyGroupName"] = self.companyGroupName
    return singleComp


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

    def CanSendSMS(self, compName):
      if self.GetSmsDispatchNumber(compName):
        return True
      return False

    def CanSendEmail(self, compName):
      if GetToCCBCCForFORMCforCompany(compName)[0]:
        return True
      return False

    def GetListOfCompNamesInThisGroup(self, grpName):
      res = []
      for compName in self:
        if self[compName].companyGroupName == grpName:
          res.append(compName)
      return res

    def GetListOfAllCompNames(self):
      return self.keys()

    def GetTrustForCustomer(self, compName):
        return self[compName].trust

    def GetCreditLimitForCustomer(self, compName):
        return self[compName].creditLimit

    def GetCompanyOfficialName(self, compName):
        return self[compName].companyOfficialName

    def GetCompanyGroupName(self, compName):
        return self[compName].companyGroupName

    def GetDeliveryState(self, compName):
        return self[compName].deliveryState

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

    def GetCasingSize(self, compName):
        return self[compName].casingSize

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

    def GetFormName(self, compName):
        return self[compName].formName

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

def GenerateCustomerInfoJsonNodesFile():
  ALL_CUST_INFO = GetAllCustomersInfo()
  jsonData = [ALL_CUST_INFO[compName].jsonNode for compName in ALL_CUST_INFO.GetListOfAllCompNames()]
  jsonFileName = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), GetOption("CONFIG_SECTION", "CustomerInfoJson"))
  with open(jsonFileName, "w") as j:
    import json
    json.dump(jsonData, j, indent=2)
  return

def GetToCCBCCForFORMCforCompany(compName):
    toMailList = GetAllCustomersInfo().GetFormCEmailAsListForCustomer(compName) or GetAllCustomersInfo().GetPaymentReminderEmailAsListForCustomer(compName)
    if not toMailList:
      print("\nNo mail feeded for {}. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'".format(compName))
      #raise  Exception("\nNo mail feeded for {}. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'".format(compName))
    section = "EMAIL_REMINDER_SECTION"
    return toMailList, GetOption(section, 'CCEmailList').split(','), GetOption(section, 'BCCEmailList').split(',')


def GetAllCustomersInfo():
    custDBwbPath = os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "CustDBRelativePath"))
    def _CreateAllCustomersInfoObject(custDBwbPath):
        return _AllCustomersInfo(custDBwbPath)
    return GetPickledObject(custDBwbPath, createrFunction=_CreateAllCustomersInfoObject)

def main():
  GenerateCustomerInfoJsonNodesFile()

if __name__ == "__main__":
  main()
