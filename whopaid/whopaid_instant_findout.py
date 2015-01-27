#############################################################################
## Author: Ashish Anand
## Date: 2013-03-11 Mon 06:44 PM
## Intent: To read the instant database and query for who paid this amount
## Requirement: Python Interpretor must be installed
#############################################################################
from Util.Config import GetOption
from Util.Decorators import timeThisFunction
from Util.Exception import MyException
from Util.Misc import PrintInBox, GetSizeOfFileInMB, AnyFundooProcessingMsg
from Util.Persistent import Persistent

from whopaid.sanity_checks import CheckConsistency
from whopaid.util_whopaid import GetWorkBookPath
from whopaid.whopaid_instant_db_generate import StartDBGeneration

from argparse import ArgumentParser
from contextlib import closing
import os
import shelve

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
  pt = PersitentTimeBillsFileChangeAt()
  if pt.HasBillsFileChangedSinceLastTime():
    startAfresh = True

  dumpFilePath = None
  if args.dumpDB:
    dumpFilePath = "B:\\desktop\\DB.txt"

  if startAfresh:
    PrintInBox("But wait... Things have changed since last time. Searching thoroughly now.")
    StartDBGeneration(shelfFilePath, dumpDBAsTextAtThisLocation=dumpFilePath)
    PrintInBox("Size of newly created DB is : {}Mb".format(GetSizeOfFileInMB(shelfFilePath)))
    slCompList2 = FindOutWhoPaidFromDB(shelfFilePath, paymentMade)
    if slCompList2 != slCompList:
      for c in slCompList2:
        c.PrintAsStr()
    pt.StoreNewTimeForBillsFile()

  return

def FindOutWhoPaidFromDB(shelfFileName, paymentMade):
  paymentMade = str(int(paymentMade))
  with closing(shelve.open(shelfFileName)) as sh:
    if sh.has_key(paymentMade):
      slicedCompaniesList = sh[paymentMade]  # More than once company can pay this amount. We need to show both.
      return slicedCompaniesList
    else:
      PrintInBox("Cannot detect from already stored records who made the payment of Rs." + paymentMade)
      return None
  return

class PersitentTimeBillsFileChangeAt(Persistent):
  identifier = "lastChangeTime"
  def __init__(self):
    super(self.__class__, self).__init__(self.__class__.__name__)

  def HasBillsFileChangedSinceLastTime(self):
    if self.identifier in self:
      return self[self.identifier] != os.path.getmtime(GetWorkBookPath())
    return False

  def StoreNewTimeForBillsFile(self):
    self[self.identifier] = os.path.getmtime(GetWorkBookPath())


if __name__ == '__main__':
  PrintInBox(AnyFundooProcessingMsg())
  try:
    main()
    CheckConsistency()
  except MyException as ex:
    PrintInBox(str(ex))
