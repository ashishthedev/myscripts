from UtilSms import SendSms, CanSendSmsAsOfNow
from UtilMisc import PrintInBox
import os

def GuessNumber(smsContents):
    NEWLINE = "\n"
    lines = smsContents.split(NEWLINE)
    lines = [l.strip() for l in lines if l.strip() != "\n"] #remove blank lines
    fLine = lines[0].lower()
    fLine = fLine.replace("to", "").replace(":", "").strip()
    if fLine[0] not in "+0123456789;":
        raise Exception("Cannot deciper telephone number from this line:{}".format(smsContents.split()[0]))
    nos = fLine.replace(',', ';').split(';')


    return tuple(nos), "\n".join(smsContents.split(NEWLINE)[1:])

if __name__ == "__main__":

    print("Checking if sms can be sent ...")
    if not CanSendSmsAsOfNow():
        errorMsg = "Sorry the connection with phone cannot be established..."
        PrintInBox(errorMsg)
        raise Exception(errorMsg)
    else:
        print("Connection established...\nPlease enter the number and text")
        toTheseNumbers = None
        smsContents = None
        TEMP_FILE_NAME = "temp.txt"

        try:
            import subprocess
            #Open the file and enter the sms contents
            blockingCommandForGvim = [os.path.join(os.path.expandvars("%windir%"),"gvim.bat") , "-f", "+0", TEMP_FILE_NAME]
            subprocess.call(blockingCommandForGvim)
            with open(TEMP_FILE_NAME) as f:
                smsContents = f.read()


            if not smsContents:
                errorMsg = "No sms contents. Bailing out"
                PrintInBox(errorMsg)
                raise Exception(errorMsg)

            toTheseNumbers, smsContents = GuessNumber(smsContents)

            if smsContents and toTheseNumbers:
                line = "_"*70
                msg = "{l}\nTo: {to}\n{con}{l}\nSend: (y/n)".format(to=toTheseNumbers, l=line, con=smsContents)
                if not raw_input(msg).lower() == "y":
                    print("Not sending message...")
                else:
                    for singleNumber in toTheseNumbers:
                        try:
                            SendSms(singleNumber, smsContents)
                        except Exception as ex:
                            print("Could not send to: {}\n{}".format("_"*70, singleNumber))

        except Exception as ex:
            if smsContents:
                print("The sms contents typed by you were:\n{}\n{}".format("_"*70, toTheseNumbers + "\n" +smsContents))
            raise ex
