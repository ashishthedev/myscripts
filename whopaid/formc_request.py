###############################################################################
## Author: Ashish Anand
## Date: 2012-09-11 Tue 06:16 PM
## Intent: To read database and generate FORM-C Reminders with proper quarters
##         The mail addresses are picked up from CUST_SHEETNAME in the
##         WRKBK_PATH excel file
## Requirement: Python Interpretor must be installed
##              Openpyxl for Python must be installed
###############################################################################

from Util.Config import GetOption
from Util.Decorators import timeThisFunction
from Util.Exception import MyException
from Util.Misc import ParseDateFromString, PrintInBox, OpenFileForViewing, MakeSureDirExists
from Util.PythonMail import SendMail

from whopaid.customers_info import GetAllCustomersInfo
from whopaid.sanity_checks import CheckConsistency
from whopaid.util_formc import QuarterlyClubbedFORMC
from whopaid.util_whopaid import GetAllCompaniesDict, SelectBillsAfterDate,\
        SelectBillsBeforeDate, GuessCompanyName, RemoveTrackingBills


import argparse
import datetime
import os

DEST_FOLDER = "B:\\Desktop\\FCR"

def ParseArguments():
    p = argparse.ArgumentParser()
    p.add_argument("-c", "--comp", dest='comp', type=str, default=None,
            help="Company name or part of it.")

    p.add_argument("-ka", "--kind-attention", dest='kindAttentionPerson',
            type=str, default=None, help="Name of any specific person."
            "Can be left out")

    p.add_argument("-al", "--additional-line", dest='additional_line',
            type=str, default=None, help="Any additional line that should be"
            "supplied.")

    p.add_argument("-o", "--OpenFileForViewing", dest='open',
            action="store_true", default=False, help="If present, file will"
            " be opened")

    p.add_argument("-l", "--letterHead", dest='letterHead', action="store_true",
            default=False, help="If present, margin will be left on top for"
            " the letterhead.")

    p.add_argument("-s", "--sms", dest='sendSMS', action="store_true",
            default=False, help="If present email will be sent to company else"
            " a file will be saved to desktop.")

    p.add_argument("-e", "--email", dest='sendEmail', action="store_true",
            default=False, help="If present email will be sent to company else"
            " a file will be saved to desktop.")

    p.add_argument("-rem", "--remarks-column", dest='remarksColumn',
            action="store_true", default=False, help="If present, an additional"
            "column for remarks will be added")

    p.add_argument("-d", "--demo", "--desktopOnly", "--noEmail", dest='isDemo',
            action="store_true", default=False, help="If present, no email"
            "will be sent. This option will override email option.")

    p.add_argument("-sd", "--start-date", dest='sdate', metavar="Start-date",
            required=False, default=None, type=str,
            help="Starting Date for FORM-C requests.")

    p.add_argument("-ed", "--end-date", dest='edate', metavar="End-date",
            required=False, type=str, default=str(datetime.date.today()),
            help="End Date for Form-C Requests. If ommitted Form-C till date "
            "will be asked for")

    args = p.parse_args()
    return args


@timeThisFunction
def main():
    args = ParseArguments()
    print("Churning data...")

    chosenComp = GuessCompanyName(args.comp)
    SendFORMCMailToCompany(chosenComp, args)
    SendFORMCSMSToCompany(chosenComp, args)
    CheckConsistency()


def ShouldSendEmail(args):
  return False if args.isDemo else args.sendEmail

def ShouldSendSMS(args):
  return False if args.isDemo else args.sendSMS



def SendFORMCSMSToCompany(compName, args):
  if ShouldSendSMS(args):
    from whopaid.off_comm import SendOfficialSMSAndMarkCC
    SendOfficialSMSAndMarkCC(compName, """Dear Sir,
Kindly issue the FORM-C. The details have been sent to your email address.
Thanks.
""")
  else:
    PrintInBox("Not sending SMS to company")
  return


def SendFORMCMailToCompany(compName, args):
    billList = GetAllCompaniesDict().GetBillsListForThisCompany(compName)
    if not billList:
      raise MyException("\nM/s {} has no bills".format(compName))

    #TODO: Remove args and take separate params
    sdate = args.sdate or min([b.invoiceDate for b in billList if not b.formCReceivingDate])
    edate = args.edate or max([b.invoiceDate for b in billList if not b.formCReceivingDate])

    sdateObject = ParseDateFromString(sdate)  # Start Date Object
    edateObject = ParseDateFromString(edate)  # End Date Object

    FORMCBillList = SelectBillsAfterDate(billList, sdateObject)
    FORMCBillList = SelectBillsBeforeDate(FORMCBillList, edateObject)
    FORMCBillList = RemoveTrackingBills(FORMCBillList)


    if not FORMCBillList:
        raise MyException("\nM/s {} has no FORM-C due".format(compName))

    FORMCBillList = [b for b in FORMCBillList if not b.formCReceivingDate]

    formC = QuarterlyClubbedFORMC(FORMCBillList)
    companyOfficialName = GetAllCustomersInfo().GetCompanyOfficialName(compName)
    if not companyOfficialName:
        raise MyException("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

    if ShouldSendEmail(args):
        mailBody = formC.GenerateFORMCMailContent(args)
        print("Sending mail...")
        #First prefrence to FormCEmails. If not present use payment emails.
        toMailList = GetAllCustomersInfo().GetFormCEmailAsListForCustomer(compName) or GetAllCustomersInfo().GetPaymentReminderEmailAsListForCustomer(compName)
        if not toMailList:
            raise  Exception("\nNo mail feeded. Please insert a proper email in 'Cust' sheet of 'Bills.xlsx'")

        print("Sending to: " + str(toMailList))

        section = "EMAIL_REMINDER_SECTION"
        requestingCompanyName = GetOption("CONFIG_SECTION", 'CompName')
        emailSubject = "FORM-C request - M/s {} - from M/s {}".format(companyOfficialName, requestingCompanyName)
        SendMail(emailSubject=emailSubject,
                zfilename=None,
                SMTP_SERVER=GetOption(section, 'Server'),
                SMTP_PORT=GetOption(section, 'Port'),
                FROM_EMAIL=GetOption(section, 'FromEmailAddress'),
                TO_EMAIL_LIST=toMailList,
                CC_EMAIL_LIST=GetOption(section, 'CCEmailList').split(','),
                BCC_EMAIL_LIST=GetOption(section, 'BCCEmailList').split(','),
                MPASS=GetOption(section, 'Mpass'),
                BODYTEXT=mailBody,
                textType="html",
                fromDisplayName = GetOption(section, "formCRequest")
                )
    else:
        fileHTMLContent = formC.GenerateFORMCMailContent(args)
        #Save to an html file

        MakeSureDirExists(DEST_FOLDER)
        filePath = os.path.join(DEST_FOLDER, companyOfficialName) + ".html"
        print("Saving FORM-C to local file: " + filePath)

        with open(filePath, "w") as f:
            f.write(fileHTMLContent)

        if args.open: OpenFileForViewing(filePath)
    return


if __name__ == '__main__':
    try:
        main()
    except MyException as ex:
        PrintInBox(str(ex))
