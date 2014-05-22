###############################################################################
## Author: Ashish Anand
## Date: 2014-Feb-10 Mon 02:02 PM
## Intent: To generate address slip for a specific company
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from UtilWhoPaid import GuessCompanyName, GetAllCompaniesDict, SelectBillsAfterDate
from UtilMisc import PrintInBox, OpenFileForViewing, MakeSureDirExists, DD_MM_YYYY
from CustomersInfo import GetAllCustomersInfo
from SanityChecks import CheckConsistency
from UtilException import MyException
from UtilPersistant import Persistant
from UtilConfig import GetOption

from string import Template
import argparse
import os
import datetime



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
    parser.add_argument("-noms", dest="noms", action="store_true",
            default=False, help="Do not print M/s")
    parser.add_argument("-fa", "--from-address", dest="fromAddress", action="store_true",
            default=False, help="Print from address too")
    parser.add_argument("-noComp", dest="noComp", action="store_true",
            default=False, help="Do not print company name")
    parser.add_argument("-l", "--longEnv", dest="longEnvelope", action="store_true",
            default=False, help="Do not print company name")

    return parser.parse_args()


def GenerateAddressSlipForThisCompany(compName, args):
    allCustInfo = GetAllCustomersInfo()
    companyOfficialName = allCustInfo.GetCompanyOfficialName(compName)
    if not companyOfficialName:
        raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

    companyDeliveryAddress= allCustInfo.GetCustomerDeliveryAddress(compName)
    if not companyDeliveryAddress:
        raise MyException("\nM/s {} doesnt have a delivery address. Please feed it in the database".format(compName))

    companyDeliveryPhNo = allCustInfo.GetDeliveryPhoneNumber(compName)
    if not companyDeliveryPhNo:
        raise MyException("\nM/s {} doesnt have a phone number. Please feed it in the database".format(compName))

    companyPinCode = allCustInfo.GetDeliveryPinCode(compName)
    if not companyPinCode:
        raise MyException("\nM/s {} doesnt have a pin code. Please feed it in the database".format(compName))

    preferredCourierForThisComp = allCustInfo.GetCustomerPreferredCourier(compName)

    tempPath = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), "AddressSlips", companyOfficialName + ".html")
    MakeSureDirExists(os.path.dirname(tempPath))

    def constant_factory(value):
        from itertools import repeat
        return repeat(value).next

    from collections import defaultdict
    d = defaultdict(constant_factory(""))
    if not args.noComp:
        if not args.noms:
            companyOfficialName = "M/s " + companyOfficialName
        d['tCompanyOfficialName'] = companyOfficialName
    d['tCompanyDeliveryAddress'] = companyDeliveryAddress
    d['tcompanyDeliveryPhNo'] = companyDeliveryPhNo
    d['tcompanyPinCode'] = companyPinCode
    d['tOptionalParams'] = ""
    if preferredCourierForThisComp:
      d['tOptionalParams'] += "<tr><td>Courier: {}</td></tr>".format(preferredCourierForThisComp)
    d['tCSSClass'] = "horizontalCompany"
    d['tOurCompCSSClass'] = "ourCompanyHorizontal"

    if args.longEnvelope:
        d['tCSSClass'] = "verticalCompany"
        d['tOurCompCSSClass'] = "ourCompanyVertical"

    singleAddressSnippet = Template("""
    <div class=$tCSSClass>
    <table>
    <tr><td><strong>$tCompanyOfficialName</strong></td></tr>
    <tr><td>$tCompanyDeliveryAddress - PIN - $tcompanyPinCode</td></tr>
    <tr><td>Ph# $tcompanyDeliveryPhNo</td></tr>
    $tOptionalParams
    </table>
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
        addressSnippet += "<br><br>" + singleAddressSnippet

    d['tAddressSnippet'] = addressSnippet

    html = Template("""
    <html>
    <head>
        <style>

        .horizontalCompany {
        /* Its a short envelope. Style it appropriately */
             width: 10cm;
             border:1px solid black;
             margin-left: 250px;
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



class PersistantEnvelopes(Persistant):
    def __init__(self):
        super(PersistantEnvelopes, self).__init__(self.__class__.__name__)

    def __str__(self):
        s = ""
        for eachComp in self.allKeys:
            obj = self.get(eachComp)
            num = obj[0]
            date = obj[1]
            s += "{:<5} {:<20} {:<20}\n".format(num, DD_MM_YYYY(date), eachComp)

        return s

    def MarkPrinted(self, compName, numOfEnv, date):
        if numOfEnv > 1:
            obj = (numOfEnv, date)
            self.put(compName, obj)
        return


    def HowManyLeftForThisCompany(self, compName):
        if compName in self.allKeys:
          return self.get(compName)[0]
        return 0

    def PrintAllInfo(self):
      l = list()
      for compName in self.allKeys:
        n = self.get(compName)[0]
        l.append((n, "{} envelopes for {}".format(n, compName)))
      l = sorted(l, key=lambda x: x[0], reverse=True)
      for x in l:
        print(x[1])


    def PredictFuturePrints(self):
        allBills = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
        compNames = list()
        for eachComp in self.allKeys:
            numOfEnv, date = self.get(eachComp)
            if not allBills.has_key(eachComp): continue
            billList = allBills[eachComp]
            billList = SelectBillsAfterDate(billList, date)
            envInHand = numOfEnv - len(billList)
            if envInHand <=1 :
                compNames.append(eachComp)
        if compNames:
            PrintInBox("Please print the envelopes for following companies:")
            for i, name in enumerate(compNames):
                print("{:<5} {}".format(i, name))

        return




def main():
    args = ParseOptions()
    pe = PersistantEnvelopes()
    if args.showAll:
      pe.PrintAllInfo()
      return

    chosenComp = GuessCompanyName(args.comp)
    if args.howManyLeft:
      print("{} envelopers left for {}".format(pe.HowManyLeftForThisCompany(chosenComp), chosenComp))
      return

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
