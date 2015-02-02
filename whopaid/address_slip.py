###############################################################################
## Author: Ashish Anand
## Date: 2014-Feb-10 Mon 02:02 PM
## Intent: To generate address slip for a specific company
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from Util.Config import GetOption
from Util.Exception import MyException
from Util.Misc import PrintInBox, OpenFileForViewing, MakeSureDirExists, DD_MM_YYYY
from Util.Persistent import Persistent

from whopaid.util_whopaid import GuessCompanyName, GetAllCompaniesDict, SelectBillsAfterDate
from whopaid.customers_info import GetAllCustomersInfo
from whopaid.sanity_checks import CheckConsistency


from string import Template

import argparse
import datetime
import os

def ParseOptions():
    parser = argparse.ArgumentParser()

    parser.add_argument("-sa", "--show-all", dest='showAll', action="store_true",
        default=False, help="If present, will show how many envelopes are left")
    parser.add_argument("-hml", "--how--many-left", dest='howManyLeft', action="store_true",
        default=False, help="If present, will show how many envelopes are left")
    parser.add_argument("-c", "--comp", dest='comp', type=str, default=None,
            help="Company name or part of it.")
    parser.add_argument("-n", dest='num', type=int, default=2,
            help="Number of times an address has to be printed.")
    parser.add_argument("-fa", "--from-address", dest="fromAddress", action="store_true",
            default=False, help="Print from address too")
    parser.add_argument("-l", "--longEnv", dest="longEnvelope", action="store_true",
            default=False, help="Do not print company name")
    parser.add_argument("-r", "--remove", dest="removeCompName", type=str, default=None,
        help="Remove the company from listing.")

    return parser.parse_args()


def GenerateAddressSlipForThisCompany(compName, args):
    allCustInfo = GetAllCustomersInfo()
    companyOfficialName = allCustInfo.GetCompanyOfficialName(compName)
    if not companyOfficialName:
      raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

    companyDeliveryAddress= allCustInfo.GetCustomerDeliveryAddress(compName)
    if not companyDeliveryAddress:
      raise MyException("\nM/s {} doesnt have a delivery address. Please feed it in the database".format(compName))

    companyDeliveryState= allCustInfo.GetDeliveryState(compName)
    if not companyDeliveryState:
      raise MyException("\nM/s {} doesnt have a delivery state. Please feed it in the database".format(compName))

    companyDeliveryPhNo = allCustInfo.GetDeliveryPhoneNumber(compName)
    if not companyDeliveryPhNo:
      raise MyException("\nM/s {} doesnt have a phone number. Please feed it in the database".format(compName))

    companyPinCode = allCustInfo.GetDeliveryPinCode(compName)
    if not companyPinCode:
      raise MyException("\nM/s {} doesnt have a pin code. Please feed it in the database".format(compName))

    x = allCustInfo.GetMsOrNomsForCustomer(compName)
    noms = True if x and x.lower().strip() == "noms" else False

    preferredCourierForThisComp = allCustInfo.GetCustomerPreferredCourier(compName)

    tempPath = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), "AddressSlips", companyOfficialName + ".html")
    MakeSureDirExists(os.path.dirname(tempPath))

    def constant_factory(value):
      from itertools import repeat
      return repeat(value).next

    from collections import defaultdict
    d = defaultdict(constant_factory(""))
    if noms:
      companyOfficialName = companyOfficialName
    else:
      companyOfficialName = "M/s " + companyOfficialName
    d['tCompanyOfficialName'] = companyOfficialName
    d['tCompanyDeliveryAddress'] = companyDeliveryAddress
    d['tcompanyDeliveryPhNo'] = companyDeliveryPhNo
    d['tDeliveryState'] = companyDeliveryState
    d['tcompanyPinCode'] = str(int(companyPinCode))
    d['tOptionalParams'] = ""
    if preferredCourierForThisComp:
      d['tOptionalParams'] += "<tr><td>Courier: {}</td></tr>".format(preferredCourierForThisComp)
    d['tCSSClass'] = "horizontalCompany"
    d['tOurCompCSSClass'] = "ourCompanyHorizontal"

    if args.longEnvelope:
      d['tCSSClass'] = "verticalCompany"
      d['tOurCompCSSClass'] = "ourCompanyVertical"

    singleAddressSnippet = Template("""
    <div class="noboder">
    <small>To,</small>
    <div class=$tCSSClass>
    <table>
    <tr><td><strong>$tCompanyOfficialName</strong></td></tr>
    <tr><td>$tCompanyDeliveryAddress $tDeliveryState - PIN - $tcompanyPinCode</td></tr>
    <tr><td>Ph# $tcompanyDeliveryPhNo</td></tr>
    $tOptionalParams
    </table>
    </div>
    </div>
    """).substitute(d)

    addressSnippet = singleAddressSnippet
    if args.fromAddress:
        d['tocName'] = 'slooT dnA seiD dradnatS'[::-1]
        d['tocAdd'] = 'dabaizahG ,ragaN ayrA dlO ,105'[::-1]
        d['tocPh'] = '5962682-0210'[::-1]
        d['tocPin'] = '100102'[::-1]

        ourCompAddSnippet = Template("""
        <div class="$tOurCompCSSClass">
         From:
        <table>
        <tr><td><u>$tocName</u></td></tr>
        <tr><td>$tocAdd - $tocPin</td></tr>
        <tr><td>Ph# $tocPh</td></tr>
        </table>
        </div>
        """).substitute(d)

        addressSnippet += ourCompAddSnippet

    for i in range(1, args.num):
        addressSnippet += "<br>" + singleAddressSnippet

    d['tAddressSnippet'] = addressSnippet

    html = Template("""
    <html>
    <head>
        <style>

        .noboder {
             width: 10cm;
             margin-left: 150px;
        }

        .horizontalCompany {
        /* Its a short envelope. Style it appropriately */
             border:1px solid black;
         }

        .ourCompanyHorizontal {
             margin-top: 1cm;
             margin-left: 30px;
         }

         .verticalCompany {
             margin-top: 10cm;
             margin-left: 0px;
             margin-right: -2.5cm;
             -webkit-transform: rotate(90deg);
             border:1px solid black;
             float: right;
             height: auto;
             width: auto;
             padding: 5px;
         }

         .ourCompanyVertical {
             margin-top: 6cm;
             margin-left: 0px;
             margin-right: -2.5cm;
             -webkit-transform: rotate(90deg);
             float: right;
             height: auto;
             width: auto;
             padding: 5px;
         }

        </style>
    </head>
    <body onload="window.print()">
    $tAddressSnippet
    </body>
    </html>
    """).substitute(d)

    with open(tempPath, "w") as f:
        f.write(html)

    OpenFileForViewing(tempPath)
    return



class PersistentEnvelopes(Persistent):
  def __init__(self):
    self.allBills = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict() #For speed imporovement, made a class member
    super(self.__class__, self).__init__(self.__class__.__name__)

  def __str__(self):
    s = ""
    for eachComp in self:
      obj = self[eachComp]
      num = obj[0]
      date = obj[1]
      s += "{:<5} {:<20} {:<20}\n".format(num, DD_MM_YYYY(date), eachComp)
    return s

  def MarkPrinted(self, compName, numOfEnv, date):
    if numOfEnv > 1:
      obj = (numOfEnv, date)
      self[compName] = obj
    return


  def HowManyLeftForThisCompany(self, compName):
    (numOfEnv, date) = self[compName]
    if not self.allBills.has_key(compName):
      return 0
    billList = self.allBills[compName]
    billList = SelectBillsAfterDate(billList, date)
    return numOfEnv - len(billList)

  def PrintAllInfo(self):
    l = sorted(self.allKeys[:], key=lambda compName: self.HowManyLeftForThisCompany(compName), reverse=True)
    for compName in l:
      print("{} envelopes for {}".format(self.HowManyLeftForThisCompany(compName), compName))
    return

  def PredictFuturePrints(self):
    compNames = [c for c in self if self.HowManyLeftForThisCompany(c) <=1 ]
    if compNames:
      PrintInBox("Please print the envelopes for following companies:")
      for i, name in enumerate(compNames):
        print("{:<5} {}".format(i, name))
    return


def RemoveCompFromList(pe, args):
    from copy import copy
    keyList = sorted(copy(pe.allKeys))
    compName = args.removeCompName.lower()
    keyList = [k for k in keyList if k.replace(" ", "").lower().find(compName) != -1]
    if not keyList:
      print("No such company: {}".format(args.removeCompName))
      return
    for i, key in enumerate(keyList, start=1):
      print("{}. {}".format(i, key))
    sno = raw_input("Enter s.no for key which has to be deleted: ")
    if not sno: return
    k = keyList[int(sno) -1]
    print("Will try to delete {}".format(k))
    del pe[k]
    return

def main():
  args = ParseOptions()
  pe = PersistentEnvelopes()
  if args.showAll:
    pe.PrintAllInfo()
    return

  if args.removeCompName:
    return RemoveCompFromList(pe, args)



  chosenComp = GuessCompanyName(args.comp)
  if args.howManyLeft:
    print("{} envelopers left for {}".format(pe.HowManyLeftForThisCompany(chosenComp), chosenComp))
    return

  t = args.num
  GenerateAddressSlipForThisCompany(chosenComp, args)


  from time import sleep
  sleep(2) # This sleep is so that browser can render the generated file coz next html will be generated in same filename and will overwrite previous one.

  args.num = t

  args.num = 1
  GenerateAddressSlipForThisCompany(chosenComp, args)


  pe.MarkPrinted(chosenComp, args.num, datetime.date.today())
  pe.PredictFuturePrints()
  return

if __name__ == '__main__':
  try:
    CheckConsistency()
    main()
  except MyException as ex:
    PrintInBox(str(ex))
    raise ex
