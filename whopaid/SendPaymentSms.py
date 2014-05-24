#WIP do it later try ti imitate payment reminders email.
from UtilWhoPaid import GetBillsListForThisCompany, 
from UtilSms import SendSms, CanSendSmsAsOfNow
def SendSmsToThisCompany(compName):
    allCustInfo = GetAllCustomersInfo()
    smsNo = allCustInfo.GetSmsDispatchNumber(compName)
    if not smsNo:
        raise Exception("No sms no. feeded for customer: {}".format(compName))


    optionalAmount = ""
    if allCustInfo.IncludeBillAmountInEmails(compName):
        optionalAmount = str(int(bill.amount)) + "/-"

    companyOfficialName = allCustInfo.GetCompanyOfficialName(compName)
    if not companyOfficialName:
        raise Exception("\nM/s {} doesnt have a displayable 'name'. Please feed it in the database".format(compName))

    d = dict()

    d["tFromName"] = "From: {}".format(GetOption("SMS_SECTION", 'FromDisplayName'))
    d["toName"] = "To: {}".format(companyOfficialName)
    if optionalAmount:
      d["tAmount"] = "Total amount: Rs.{}".format(optionalAmount)

    smsTemplate = Template("""$tFromName
_____

$toName
Through: $tThrough
Material: $tMaterialDescription
$tAmount
Thanks.
""")
    smsContents = smsTemplate.substitute(d)

    COMMA = ","
    smsNo = smsNo.replace(';', ',').strip()
    listOfNos = [x.strip() for x in smsNo.split(COMMA)]
    anyAdditionalSmsNo = GetOption("SMS_SECTION", "CC_NO")
    if anyAdditionalSmsNo:
        anyAdditionalSmsNo = anyAdditionalSmsNo.replace(';', ',').strip()
        listOfNos.extend([x.strip() for x in anyAdditionalSmsNo.split(COMMA)])

    for x in listOfNos:
        print("Sending to this number: {}".format(x))
        SendSms(x, smsContents)

    return

def main():


if __name__ == "__main__":
  main()
