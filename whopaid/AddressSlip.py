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
    if not companyDeliveryPhNo:
        raise MyException("\nM/s {} doesnt have a pin code. Please feed it in the database".format(compName))

    tempPath = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), "AddressSlips", companyOfficialName + ".html")
    MakeSureDirExists(os.path.dirname(tempPath))

    d = dict()
    d['tAddWidth'] = "10.0cm"
    if not args.noms:
        companyOfficialName = "M/s " + companyOfficialName
    d['tCompanyOfficialName'] = companyOfficialName
    d['tCompanyDeliveryAddress'] = companyDeliveryAddress
    d['tcompanyDeliveryPhNo'] = companyDeliveryPhNo
    d['tcompanyPinCode'] = companyPinCode

    singleAddressSnippet = Template("""
    <div id="mydiv">
    <table>
    <tr><td><strong>$tCompanyOfficialName</strong></td></tr>
    <tr><td>$tCompanyDeliveryAddress - PIN - $tcompanyPinCode</td></tr>
    <tr><td>Ph# $tcompanyDeliveryPhNo</td></tr>
    </table>
    </div>
    """).substitute(d)

    finalAddressSnippet = singleAddressSnippet
    for i in range(1, args.num):
        finalAddressSnippet += "<br><br>" + singleAddressSnippet

    d['tStyle'] = Template("""
    <style>
    #mydiv {
     width: $tAddWidth;
     border:1px solid black;
    }
    </style>
    """).substitute(d)

    d['tfinalAddressSnippet'] = finalAddressSnippet

    html = Template("""
    <html>
    <head> $tStyle </head>
    <body onload="window.print()">
    $tfinalAddressSnippet
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
