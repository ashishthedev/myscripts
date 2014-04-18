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

    if CanSendSmsAsOfNow():
        toThisNumber = None
        smsContents = None
        TEMP_FILE_NAME = "temp.txt"
        if os.path.exists(TEMP_FILE_NAME):
            #Delete bofore proceeding to work on empty file. Fall back safety mechanism.
            os.remove(TEMP_FILE_NAME)

        with open(TEMP_FILE_NAME, "w"):
            #Just create the file
            pass

        try:
        #Open the file and enter the sms contents
            import subprocess
            subprocess.call([os.path.join(os.path.expandvars("%windir%"),"gvim.bat") , "-f", "+0", TEMP_FILE_NAME])
            #OpenFileForViewing(TEMP_FILE_NAME)
            with open(TEMP_FILE_NAME) as f:
                smsContents = f.read()

            if os.path.exists(TEMP_FILE_NAME):
                #Delete after job is done
                os.remove(TEMP_FILE_NAME)

            if not smsContents:
                errorMsg = "No sms contents. Bailing out"
                PrintInBox(errorMsg)
                raise Exception(errorMsg)

            toThisNumber, smsContents = GuessNumber(smsContents)

            if smsContents and toThisNumber:
                line = "_"*70
                msg = "To: {to}\n{l}\n{con}\n{l}\n(y/n)".format(to=toThisNumber, l=line, con=smsContents)
                if raw_input(msg).lower() == "y":
                    SendSms(toThisNumber, smsContents)
                else:
                    print("Not sending message...")

        except Exception as ex:
            if smsContents:
                print("The sms contents typed by you were:\n{}\n{}".format("_"*70, smsContents))
            raise ex
