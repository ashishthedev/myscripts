from UtilSms import SendSms, CanSendSmsAsOfNow
from UtilMisc import PrintInBox
import os

def GuessNumber(smsContents):
    NEWLINE = "\n"
    lines = smsContents.split(NEWLINE)
    lines = [l.strip() for l in lines if l.strip() != "\n"] #remove blank lines
    fLine = lines[0].lower()
    fLine = fLine.replace("to", "").replace(":", "").strip()
    if fLine[0] not in "+0123456789":
        raise Exception("Cannot deciper telephone number from this line:{}".format(smsContents.split()[0]))

    return fLine, "\n".join(smsContents.split(NEWLINE)[1:])

if __name__ == "__main__":

    print("Checking if sms can be sent ...")
    if not CanSendSmsAsOfNow():
        errorMsg = "Sorry the connection with phone cannot be established..."
        PrintInBox(errorMsg)
        raise Exception(errorMsg)
    else:
        print("Connection established...\nPlease enter the number and text")
        toThisNumber = None
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

            toThisNumber, smsContents = GuessNumber(smsContents)

            if smsContents and toThisNumber:
                line = "_"*70
                msg = "{l}\nTo: {to}\n{con}{l}\nSend: (y/n)".format(to=toThisNumber, l=line, con=smsContents)
                if raw_input(msg).lower() == "y":
                    SendSms(toThisNumber, smsContents)
                else:
                    print("Not sending message...")

        except Exception as ex:
            if smsContents:
                print("The sms contents typed by you were:\n{}\n{}".format("_"*70, toThisNumber + "\n" +smsContents))
            raise ex
