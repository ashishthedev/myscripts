#############################################################################
## Author: Ashish Anand
## Date: 2013-03-11 Mon 06:44 PM
## Intent: To read the instant database and query for who paid this amount
## Requirement: Python Interpretor must be installed
#############################################################################
from UtilDecorators import timeThisFunction
from SanityChecks import CheckConsistency
from UtilMisc import printNow, PrintInBox, GetSizeOfFileInMB
from UtilConfig import GetOption
from UtilException import MyException
from whopaidInstantDBGenerate import StartDBGeneration
from UtilWhoPaid import BillsFileChangedSinceLastTime, StoreNewTimeForBillsFile
from argparse import ArgumentParser
from contextlib import closing
import shelve
import os

@timeThisFunction
def main():
    parser = ArgumentParser()
    parser.add_argument("-f", "--fresh", dest='freshDB', action='store_true', help="If present database will be created afresh. Takes more time to execute when present.")
    parser.add_argument("-d", "--dumpDB", dest='dumpDB', action='store_true', help="If present database will be dumped as a text file.")
    parser.add_argument("paymentMade", type=int, help="Amount paid by unknown company.")
    args = parser.parse_args()

    paymentMade = args.paymentMade
    shelfFilePath = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), GetOption("CONFIG_SECTION", "WhoPaidDatabase"))

    slCompList = FindOutWhoPaidFromDB(shelfFilePath, paymentMade)
    if slCompList:
        for c in slCompList:
            c.PrintAsStr()

    startAfresh = False
    if args.freshDB:
        startAfresh = True
    if not os.path.exists(shelfFilePath):
        startAfresh = True
    if BillsFileChangedSinceLastTime():
        startAfresh = True

    dumpFilePath = None
    if args.dumpDB:
        dumpFilePath = "B:\\desktop\\DB.txt"

    if startAfresh:
        PrintInBox("Wait... Things have changed since last time. Searching thoroughly now.")
        StartDBGeneration(shelfFilePath, DumpDBAsTextAtThisLocation=dumpFilePath)
        PrintInBox("Size of newly created DB is : {}Mb".format(GetSizeOfFileInMB(shelfFilePath)))
        slCompList2 = FindOutWhoPaidFromDB(shelfFilePath, paymentMade)
        if slCompList2 != slCompList:
            for c in slCompList2:
                c.PrintAsStr()
        StoreNewTimeForBillsFile()

    return

def FindOutWhoPaidFromDB(shelfFileName, paymentMade):
    paymentMade = str(int(paymentMade))
    with closing(shelve.open(shelfFileName)) as sh:
        if sh.has_key(paymentMade):
            slicedCompaniesList = sh[paymentMade]  # More than once company can pay this amount. We need to show both.
            return slicedCompaniesList
        else:
            PrintInBox("Cannot detect who made the payment of Rs." + paymentMade)
            return None


if __name__ == '__main__':
    printNow("Churning data...")
    try:
        main()
        CheckConsistency()
    except MyException as ex:
        PrintInBox(str(ex))
