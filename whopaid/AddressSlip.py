###############################################################################
## Author: Ashish Anand
## Date: 2014-Feb-10 Mon 02:02 PM
## Intent: To generate address slip for a specific company
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from UtilWhoPaid import GuessCompanyName
from UtilException import MyException
from UtilMisc import PrintInBox, OpenFileForViewing, MakeSureDirExists
from CustomersInfo import GetAllCustomersInfo
from SanityChecks import CheckConsistency
from UtilConfig import GetOption

from string import Template
import argparse
import os


def ParseOptions():
    parser = argparse.ArgumentParser()
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
             margin-left: 300px;
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

def main():
    args = ParseOptions()
    chosenComp = GuessCompanyName(args.comp)
    GenerateAddressSlipForThisCompany(chosenComp, args)
    return

if __name__ == '__main__':
    try:
        CheckConsistency()
        main()
    except MyException as ex:
        PrintInBox(str(ex))
        raise ex
