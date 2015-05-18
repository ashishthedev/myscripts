import smtpd, asyncore

import os

EMAIL_AS_HTML_PATH = os.path.abspath(os.path.join("B:\\desktop", "email.html"))
class CustomSMTPServer(smtpd.SMTPServer):

    def process_message(self, peer, mailfrom, rcpttos, data):
      with open(EMAIL_AS_HTML_PATH, "w") as fd:
        fd.write("Receiving From: {}<br>".format(peer))
        fd.write("Addressed From: {}<br>".format(mailfrom))
        fd.write("To: {}<br>".format(rcpttos))
        fd.write("<u>Data</u>:<br>{}<br>".format(data))
        return

def main():
    print 'Mailserver is on port 8025. Press ctrl-c to stop.'
    #server = smtpd.DebuggingServer(('localhost', 8025), None)
    server = CustomSMTPServer(('localhost', 8025), None)
    asyncore.loop()

if __name__ == '__main__':
    main()
