from __future__ import unicode_literals
from Util.Config import GetAppDir, GetOption
from Util.Misc import YYYY_MM_DD

import os
import subprocess

def _EDDProofFileNameForBill(b, estimatedDateObj):
  """All the information considered in filename is immutable"""
  PREFERRED_FILEFORMAT = ".jpeg"
  fileName = "{edd}_{docketNumber}_{compName}".format(edd=YYYY_MM_DD(estimatedDateObj),
      compName=b.compName, docketNumber=b.docketNumber)
  fileName.replace(" ", "_")
  fileName = "".join([x for x in fileName if x.isalnum() or x in['_', '-']])
  fileName = fileName + PREFERRED_FILEFORMAT
  return fileName

def FileNameForBill(b):
  """All the information considered in filename is immutable"""
  PREFERRED_FILEFORMAT = ".jpeg"
  fileName = "{date}_{compName}_BillNo#{billNumber}_{docketNumber}".format(date=YYYY_MM_DD(b.docketDate),
      compName=b.compName, billNumber=b.billNumber, docketNumber = b.docketNumber)
  fileName.replace(" ", "_")
  fileName = "".join([x for x in fileName if x.isalnum() or x in['_', '-']])
  fileName = fileName + PREFERRED_FILEFORMAT
  return fileName

def FullPathForPODofBill(b):
  fileName = FileNameForBill(b)
  fullPath = os.path.normpath(os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "DocketSnapshotsRelPath"),fileName))
  return fullPath

def FullPathForEDDProofForBill(b, estimatedDateObj):
  fileName = _EDDProofFileNameForBill(b)
  fullPath = os.path.normpath(os.path.join(GetAppDir(), GetOption("CONFIG_SECTION", "EstimatedDeliveryDateRelPath"),fileName))
  return fullPath

def StoreEDDProofWithPhantomScript(b, scriptPath, formData, reqUrl):
  fullPath = FullPathForEDDProofForBill(b)
  _StoreSnapshot(b, scriptPath, formData, reqUrl, fullPath)
  return

def StoreDeliveryProofWithPhantomScript(b, scriptPath, formData, reqUrl):
  fullPath = FullPathForPODofBill(b)
  _StoreSnapshot(b, scriptPath, formData, reqUrl, fullPath)
  return

def _StoreSnapshot(b, scriptPath, formData, reqUrl, fullPath):
  #TODO: Remove hardcoding of path
  PHANTOM = "B:\\Tools\\PhantomJS\\phantomjs-1.9.8-windows\\phantomjs.exe"

  if os.path.exists(fullPath):
    i = fullPath.rfind(".")
    fullPath ="{}_new{}".format(fullPath[:i], fullPath[i:])

  for p in [PHANTOM, scriptPath]:
    if not os.path.exists(p): raise Exception("Path not present : {}".format(p))

  args = [PHANTOM, scriptPath, fullPath, b.docketNumber, formData, reqUrl]

  args.append("--ignore-ssl-errors=true")
  args.append("--ssl-protocol=tlsv1")
  args.append("--debug=true")
  args.append("--web-security=false")
  #args.append("--ssl-protocol=any")

  #from pprint import pprint; pprint(args)
  subprocess.check_call(args)



