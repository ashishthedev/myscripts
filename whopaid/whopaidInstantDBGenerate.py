######################################################################
## Author: Ashish Anand
## Date: 2013-03-11 Mon 04:47 PM
## Intent: To read bills.xlsx and create a database with keys as
##         possible amounts and values as the list of companies who can pay
## Requirement: Python Interpretor must be installed
######################################################################
from whopaid.UtilWhoPaid import SelectUnpaidBillsFrom, GetAllCompaniesDict, Company, SelectBillsBeforeDate, SelectBillsAfterDate, datex
from Util.Misc import  OpenFileForViewing, PrintInBox
from Util.Config import GetOption

from contextlib import closing
from collections import defaultdict
from itertools import combinations
import shelve

class SlicedCompany(Company):
    def __init__(self, name):
        super(SlicedCompany, self).__init__(name)
        self.missingBillPayments = list()

    def PrintAsStr(self):
        PrintInBox("M/s " + self.compName)
        for eachBill in self:
            print(eachBill)
        if self.missingBillPayments:
            #If he has missed payment for some bills, then show them too.
            #These were calculated at the time of db generation.
            PrintInBox("M/s {} forgot to pay for following bills:".format(self.compName))
            for b in self.missingBillPayments:
                print(b)


def ListOfMissingBills(slicedCompany, unpaidBillList):
    minDate = min([datex(b.invoiceDate) for b in slicedCompany])
    maxDate = max([datex(b.invoiceDate) for b in slicedCompany])
    prunedUnpaidList = SelectBillsBeforeDate(unpaidBillList, maxDate)
    prunedUnpaidList = SelectBillsAfterDate(prunedUnpaidList, minDate)
    missingBillPayments = list()
    for eachBill in prunedUnpaidList:
        if eachBill not in slicedCompany:
            missingBillPayments.append(eachBill)
    return missingBillPayments


def DifferentStrAmountsThatCanBePaidByThisCompany(company):
    d = defaultdict(list)  # Keys are the amounts that can be paid and value is a company(ie. list of bills)
    unpaidBillList = SelectUnpaidBillsFrom(company)
    for i in range(1, len(unpaidBillList)+1):
        cmbns = combinations(unpaidBillList, i)
        for eachBillListTuple in cmbns:
            amt = 0
            slicedCompany = SlicedCompany(name=company.compName) #slicedCompany is a company with selective bills.
            for eachBill in eachBillListTuple:
                amt += eachBill.amount
                slicedCompany.append(eachBill)
            slicedCompany.missingBillPayments = ListOfMissingBills(slicedCompany, unpaidBillList)
            d[str(int(amt))].append(slicedCompany)

    return d

def PrintShelveDB(shelfFilePath, fd):
    with closing(shelve.open(shelfFilePath)) as sh:
        for eachPossibleAmount in sh.keys():
            fd.write("Rs.%s\n"%(str(eachPossibleAmount)))
            companies = sh[eachPossibleAmount]
            for eachCompany in companies:
                fd.write("\n")
                fd.write(str(eachCompany))
                fd.write("\n")
            fd.write("_________________________________________________")
            fd.write("\n")


def StartDBGeneration(shelfFilePath, DumpDBAsTextAtThisLocation=None):
    allBillsDict = GetAllCompaniesDict().GetAllBillsOfAllCompaniesAsDict()
    with closing(shelve.open(shelfFilePath)) as sh:
        sh.clear()
        for eachCompName, eachComp in allBillsDict.items():
            if len(SelectUnpaidBillsFrom(eachComp)) > int(GetOption("CONFIG_SECTION", "MaxUnpaidBills")):
                print("Skipping :" + str(eachCompName))
                continue
            d = DifferentStrAmountsThatCanBePaidByThisCompany(eachComp)
            for eachAmt, listOfComps in d.items():
                if sh.has_key(eachAmt):
                    l = sh[eachAmt]
                    l.extend(listOfComps)
                    sh[eachAmt] = l  # Somehow sh[eachAmt].extend(listOfComps) doesn't work. Seems like a Bug in Python
                else:
                    assert listOfComps is not None, "This should not happen. If there is an amount present, it should have been paid by some company"
                    sh[eachAmt] = listOfComps

    if DumpDBAsTextAtThisLocation:
        print("Dumping database at " + DumpDBAsTextAtThisLocation)
        with open(DumpDBAsTextAtThisLocation, "w") as fd:
            PrintShelveDB(shelfFilePath, fd)
        OpenFileForViewing(DumpDBAsTextAtThisLocation)
