#######################################################
## Author: Ashish Anand
## Date: 2014-Aug-27 Wed 12:00 PM
## Intent: To read Kennametal Pending Orders
## Requirement: Python Interpretor must be installed
## Openpyxl must be installed
#######################################################
from Util.Misc import GetPickledObject, ParseDateFromString, DD_MMM_YYYY
from Util.Config import GetOption, GetAppDir

import os

class KMInfoCol:
  """
  This class is used as Enum.
  If and when the format of excel file changes just change the column bindings in this class
  """
  RowNoCol = "A"
  PODateCol = "B"
  PelletSizeCol = "C"
  BoreSizeCol = "D"
  QuantityCol = "E"
  GradeCol = "F"
  DeliveryInstructionsCol = "G"
  InvoiceDateCol = "H"
  OANumberCol = "I"


from Util.ExcelReader import GetCellValue
def CreateSingleKMOrder(row):
  c = SingleKMOrderInfo()
  for cell in row:
    col = cell.column
    val = GetCellValue(cell)

    if col == KMInfoCol.RowNoCol:
      c.rowNumberInTable = val
    elif col == KMInfoCol.PODateCol:
      if not val: raise Exception("No PO Date in row: {} and col: {}".format(cell.row, col))
      c.poDate = ParseDateFromString(val)
    elif col == KMInfoCol.PelletSizeCol:
      c.pelletSize = val
    elif col == KMInfoCol.BoreSizeCol:
      c.boreSize = val
    elif col == KMInfoCol.QuantityCol:
      c.quantity = int(val)
    elif col == KMInfoCol.GradeCol:
      c.grade = val
    elif col == KMInfoCol.DeliveryInstructionsCol:
      c.deliveryInstructions = val
    elif col == KMInfoCol.InvoiceDateCol:
      if val is not None:
        c.invoiceDate = ParseDateFromString(val)
      else:
        c.invoiceDate = None
    elif col == KMInfoCol.OANumberCol:
      c.oaNumber = val
  return c


class SingleKMOrderInfo():
  """This represents a single km order"""
  pass


class _AllKMOrdersObject(list):
  """Base Class which is basically a list."""
  def __init__(self, kmOrdersDBPath):
    super(_AllKMOrdersObject, self).__init__()
    from Util.ExcelReader import GetRows
    rows = GetRows(workbookPath=kmOrdersDBPath,
      sheetName=GetOption("KM_TRANS_SECTION", "SheetName"),
      firstRow= GetOption("KM_TRANS_SECTION", "DataStartsAtRow"),
      includeLastRow=False)

    for row in rows:
      c = CreateSingleKMOrder(row)
      self.append(c)
    return

def GetAllReceivedOrders(orderList):
  return [po for po in orderList if po.invoiceDate]

def GetAllPendingOrders(orderList):
  po = [po for po in orderList if not po.invoiceDate]
  return sorted(po, key=lambda po: (po.pelletSize, po.boreSize, po.poDate))

def GetAllKMOrders():
  kmOrdersDBPath = os.path.join(GetAppDir(), GetOption("KM_TRANS_SECTION", "WorkbookRelativePath"))
  def _CreateAllKMOrdersObject(kmOrdersDBPath):
    return _AllKMOrdersObject(kmOrdersDBPath)
  return GetPickledObject(kmOrdersDBPath, createrFunction=_CreateAllKMOrdersObject)


if  __name__ == "__main__":
  po = GetAllKMOrders()
  po = GetAllPendingOrders(po)
  for o in po:
    print("{:<15} {:<15} {:<15} {:<15} {:<15}".format(o.pelletSize, o.boreSize, DD_MMM_YYYY(o.poDate), o.grade, o.quantity))
