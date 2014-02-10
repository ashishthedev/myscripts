###############################################################################
## Author: Ashish Anand
## Date: 2014-Feb-10 Mon 02:02 PM
## Intent: To generate address slip for a specific company
## Requirement: Python 3 Interpretor must be installed
##              Openpyxl for Python 3 must be installed
###############################################################################

from UtilWhoPaid import GuessCompanyName
from UtilException import MyException
from UtilMisc import PrintInBox, OpenFileForViewing
from CustomersInfo import GetAllCustomersInfo
from UtilDecorators import timeThisFunction
from SanityChecks import CheckConsistency
from UtilConfig import GetOption

from string import Template
import argparse
import os


def ParseOptions():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--comp", dest='comp', type=str, default=None,
            help="Company name or part of it.")
    return parser.parse_args()


def GenerateAddressSlipForThisCompany(compName):
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

    tempPath = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), companyOfficialName + ".html")

    d = dict()
    d['tAddWidth'] = "10.0cm"
    d['tCompanyOfficialName'] = companyOfficialName
    d['tCompanyDeliveryAddress'] = companyDeliveryAddress
    d['tcompanyDeliveryPhNo'] = companyDeliveryPhNo
    d['tcompanyPinCode'] = companyPinCode

    addressSnippet = Template("""
    <table>
    <tr><td>Name</td><td><strong>$tCompanyOfficialName</strong></td></tr>
    <tr><td>Address:</td><td>$tCompanyDeliveryAddress - PIN - $tcompanyPinCode</td></tr>
    <tr><td>Phone</td><td>$tcompanyDeliveryPhNo</td></tr>
    </table>
    """).substitute(d)


    d['tAddressSnippet'] = addressSnippet

    html = Template("""
    <html>
    <head>
    <style>
    #mydiv {
     width: $tAddWidth;
     border:1px solid black;
    }
    </style>
    </head>
    <body>
    <div id="mydiv"> $tAddressSnippet </div>
    <br>
    <div id="mydiv"> $tAddressSnippet </div>
    </body>
    </html>
    """).substitute(d)

    with open(tempPath, "w") as f:
        f.write(html)

    OpenFileForViewing(tempPath)


@timeThisFunction
def main():

    args = ParseOptions()
    chosenComp = GuessCompanyName(args.comp)
    GenerateAddressSlipForThisCompany(chosenComp)
    return
>>>>>>> addSlip

if __name__ == '__main__':
    try:
        CheckConsistency()
        main()
    except MyException as ex:
        PrintInBox(str(ex))
        raise ex
