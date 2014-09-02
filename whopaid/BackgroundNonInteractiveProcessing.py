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

if os.path.exists(LOG_FILE_PATH):
  os.remove(LOG_FILE_PATH)

def log(msg):
  with open(LOG_FILE_PATH, "w+") as f:
    f.write(msg)

def main():
  try:
    log("Attempting to run  at time: {} ".format(datetime.datetime.now()))
    from whopaid.SanityChecks import SendAutomaticHeartBeat #This should be within the try block so that we can see the exception if it happens.
    SendAutomaticHeartBeat()
    log("Ran successfully last at time: {} ".format(datetime.datetime.now()))
  except Exception as ex:
    log("At time: {} following error occurred:\n{}".format(datetime.datetime.now(), str(ex)))
    print(str(ex))
    raw_input("...")
    raise

main()
