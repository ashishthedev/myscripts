##########################################################################
##
## This file contains a routine to send files to specific email address
##
## Author: Ashish Anand
##
##########################################################################

from Util.Sms import SendSms, CanSendSmsAsOfNow
from Util.Misc import PrintInBox

def ParseArguments():
  import argparse
  p = argparse.ArgumentParser()
  p.add_argument("-sc", "--sms-contents", dest='smsContents', type=str, default=None,
          help="Company name or part of it.")

  p.add_argument("-n", "--phone-num", dest='phoneNumber', type=str, default=None,
          help="Company name or part of it.")

  args = p.parse_args()
  return args

if __name__ == "__main__":
  args = ParseArguments()
  if args.smsContents and args.phoneNumber:
    SendSms(args.phoneNumber, args.smsContents)
    #if CanSendSmsAsOfNow():
    #  SendSms(args.phoneNumber, args.smsContents)
    #else:
    #  PrintInBox("For some reason, sms cannot be sent now", waitForEnterKey=True)

