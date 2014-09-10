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
    t = datetime.datetime.now()
    log("Initiating {}".format(__file__))
    from whopaid.SanityChecks import SendAutomaticHeartBeat #This should be within the try block so that we can see the exception if it happens.
    SendAutomaticHeartBeat()
    dt = datetime.datetime.now() - t
    log("Ran successfully. Took {} seconds".format(dt.seconds))
  except Exception as ex:
    log("Following error occurred:\n{}".format(str(ex)))
    print(str(ex))
    raise

main()
