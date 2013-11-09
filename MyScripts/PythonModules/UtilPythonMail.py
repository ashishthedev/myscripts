##########################################################################
##
## This file contains a routine to send files to specific email address
##
## Author: Ashish Anand
##
##########################################################################
TESTING = False
from UtilDecorators import RetryFor5TimesIfFailed

@RetryFor5TimesIfFailed
def SendMail(emailSubject, zfilename, SMTP_SERVER, SMTP_PORT, FROM_EMAIL, TO_EMAIL_LIST, CC_EMAIL_LIST, MPASS, BODYTEXT="File Attached", textType="plain", fromDisplayName="Hello"):
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders
    from email.mime.multipart import MIMEMultipart
    import os
    import smtplib

    COMMASPACE = ", "

    msg = MIMEMultipart()

    finalReciepients = list()

    msg['From'] = fromDisplayName + "<" + FROM_EMAIL + ">"

    if TO_EMAIL_LIST:
        #Support both: python list as well as comma separated lists
        #TODO: Duplicate code. Refactor later.
        if isinstance(TO_EMAIL_LIST, list):
            msg['To'] = COMMASPACE.join(TO_EMAIL_LIST)
            finalReciepients.extend(TO_EMAIL_LIST)
        elif isinstance(TO_EMAIL_LIST, basestring):
            msg['To'] = TO_EMAIL_LIST
            finalReciepients.extend(TO_EMAIL_LIST.split(','))


    if CC_EMAIL_LIST:
        #Support both: python list as well as comma separated lists
        if isinstance(CC_EMAIL_LIST, list):
            msg['CC'] = COMMASPACE.join(CC_EMAIL_LIST)
            finalReciepients.extend(CC_EMAIL_LIST)
        elif isinstance(CC_EMAIL_LIST, basestring):
            msg['CC'] = CC_EMAIL_LIST
            finalReciepients.extend(CC_EMAIL_LIST.split(','))

    msg['Subject'] = emailSubject

    msg.attach(MIMEText(BODYTEXT, textType))

    if zfilename is not None:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(zfilename, 'rb').read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(zfilename))
        msg.attach(part)

    mailServer = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.login(FROM_EMAIL, MPASS)
    if not TESTING:
        mailServer.sendmail(FROM_EMAIL, finalReciepients, msg.as_string())
    mailServer.close()    # Should be mailServer.quit(), but that crashes...
    return
