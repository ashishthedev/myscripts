###############################################################################
## Author: Ashish Anand
## Date: 2017-Sep-05 Tue 07:58 PM
## Intent: To generate address slip for a specific company
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from Util.Config import GetOption
from Util.Exception import MyException
from Util.Misc import PrintInBox, OpenFileForViewing, MakeSureDirExists, DD_MM_YYYY
from Util.Persistent import Persistent
from urllib import urlencode
from urllib2 import urlopen
import json
from pprint import pprint


from whopaid.util_whopaid import GuessCompanyName, GetAllCompaniesDict, SelectBillsAfterDate
from whopaid.customers_info import GetAllCustomersInfo
from whopaid.sanity_checks import CheckConsistency


import argparse

def ParseOptions():
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--comp", dest='comp', type=str, default=None,
            help="Company name or part of it.")

    return parser.parse_args()


ALL_CUST_INFO = GetAllCustomersInfo()

def GenerateCoordinatesForThisCompany(compName):
    companyOfficialName = ALL_CUST_INFO.GetCompanyOfficialName(compName)
    if not companyOfficialName:
      raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

    companyBillingAddress = ALL_CUST_INFO.GetCompanyBillingAddress(compName)
    if not companyBillingAddress:
      raise MyException("\nM/s {} doesnt have a billing address. Please feed it in the database".format(compName))
    companyBillingAddress = companyBillingAddress.strip()

    companyDeliveryState = ALL_CUST_INFO.GetDeliveryState(compName)
    if not companyDeliveryState:
      raise MyException("\nM/s {} doesnt have a devliery state. Please feed it in the database".format(compName))

    companyPinCode = ALL_CUST_INFO.GetDeliveryPinCode(compName)
    if not companyPinCode:
      raise MyException("\nM/s {} doesnt have a pin code. Please feed it in the database".format(compName))

    d = dict()
    COMMA = ", "
    addresses = [companyOfficialName + COMMA + companyDeliveryState,
            companyOfficialName + COMMA + companyBillingAddress + COMMA + companyDeliveryState,
            companyOfficialName + COMMA + companyBillingAddress + COMMA + companyDeliveryState + COMMA + companyPinCode,
            ]
    for a in addresses:
        d["address"] = a
        apiUrl = "https://maps.googleapis.com/maps/api/geocode/json?" + urlencode(d)
        try:
            resp = json.load(urlopen(apiUrl))

            location = resp["results"][0]["geometry"]["location"]
            pprint({a: (location["lat"], location["lng"])})
        except Exception as ex:
            pprint(resp)
            pprint(ex)
    return






def main():
  args = ParseOptions()

  chosenComp = GuessCompanyName(args.comp)

  companyOfficialName = ALL_CUST_INFO.GetCompanyOfficialName(chosenComp)
  if not companyOfficialName:
    raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(chosenComp))

  GenerateCoordinatesForThisCompany(chosenComp)
  return

if __name__ == '__main__':
  try:
    main()
  except MyException as ex:
    PrintInBox(str(ex))
    raise ex
