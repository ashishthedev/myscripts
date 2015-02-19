#######################################################
## Author: Ashish Anand
## Date: 2014-Aug-30 Sat 01:46 PM
## Intent: To run this background processing script
## through scheduler
## As of now, a task is created in windows scheduler
## which runs this script at regular intervals
## Requirement: Python Interpretor must be installed
## Openpyxl must be installed
#######################################################


import datetime
import os

LOG_FILE_PATH = "b:\\desktop\\lastrun.txt"

def DeleteLogIfExists():
  if os.path.exists(LOG_FILE_PATH):
    os.remove(LOG_FILE_PATH)

def log(msg):
  with open(LOG_FILE_PATH, "a") as f:
    f.write("\n{}: {}".format(datetime.datetime.now(), msg))

def main():
  #DeleteLogIfExists()
  try:
    log("Initiating {}".format(__file__))

    from whopaid.sanity_checks import SendAutomaticHeartBeat #This should be within the try block so that we can see the exception if it happens.
    log("SendAutomaticHeartBeat() started")
    t = datetime.datetime.now()
    SendAutomaticHeartBeat()
    log("SendAutomaticHeartBeat() over")
    dt = datetime.datetime.now() - t
    log("SendAutomaticHeartBeat() took {} seconds".format(dt.seconds))

    from Util.Misc import cd, PrintInBox

    import subprocess
    pythonApp = os.path.abspath(os.path.join(".", "shipments.py"))
    shipmentsTrackCmd = "python \"{app}\" --track".format(app=pythonApp)
    with cd(os.path.dirname(pythonApp)):
      PrintInBox("Running: {}".format(shipmentsTrackCmd))
      trackTime = datetime.datetime.now()
      log("TrackAllShipments() started")
      subprocess.check_call(shipmentsTrackCmd)
      log("TrackAllShipments() over")
      dt = datetime.datetime.now() - trackTime
      log("Tracking all shipments took {} seconds".format(dt.seconds))


  except Exception as ex:
    log("Following error occurred:\n{}".format(str(ex)))
    print(str(ex))
    raise

main()
