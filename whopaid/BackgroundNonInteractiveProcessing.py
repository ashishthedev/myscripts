#######################################################
## Author: Ashish Anand
## Date: 2014-Aug-30 Sat 01:46 PM
## Intent: To run this background processing script through scheduler
## Requirement: Python Interpretor must be installed
## Openpyxl must be installed
#######################################################

import datetime
def main():
  with open("b:\\desktop\\lastrun.txt", "w") as f:
    f.write("I was last run at {}".format(datetime.datetime.now()))
  return


main()
