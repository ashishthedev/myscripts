##########################################################################
##
## This file contains a routine to send files to specific email address
##
## Author: Ashish Anand
##
##########################################################################
TESTING = False
from Util.Decorators import RetryNTimes
from Util.Misc import flattenList

@RetryNTimes(5)
def SendMail(emailSubject, zfilename, SMTP_SERVER, SMTP_PORT, FROM_EMAIL, TO_EMAIL_LIST, CC_EMAIL_LIST, BCC_EMAIL_LIST, MPASS, BODYTEXT, textType, fromDisplayName):
  from email import encoders
  from email.mime.base import MIMEBase
  from email.mime.multipart import MIMEMultipart
  from email.mime.text import MIMEText

  import os
  import smtplib

  if isinstance(TO_EMAIL_LIST, basestring):
    TO_EMAIL_LIST = TO_EMAIL_LIST.replace(";", ",").split(",")

  if isinstance(CC_EMAIL_LIST, basestring):
    CC_EMAIL_LIST = CC_EMAIL_LIST.replace(";", ",").split(",")

  if isinstance(BCC_EMAIL_LIST, basestring):
    BCC_EMAIL_LIST = BCC_EMAIL_LIST.replace(";", ",").split(",")


  COMMASPACE = ", "

  msg = MIMEMultipart()

  finalReciepients = list()

  #Support both: python list as well as comma separated lists
  flattenedToList = flattenList(TO_EMAIL_LIST)
  flattenedCCList = flattenList(CC_EMAIL_LIST)
  flattenedBCCList = flattenList(BCC_EMAIL_LIST) # At this point we are sure either these are None or a valid list

  msg['From'] = fromDisplayName + "<" + FROM_EMAIL + ">"

  if flattenedToList:
    msg['To'] = COMMASPACE.join(flattenedToList)
    finalReciepients.extend(flattenedToList)
  if flattenedCCList:
    msg['CC'] = COMMASPACE.join(flattenedCCList)
    finalReciepients.extend(flattenedCCList)
  if flattenedBCCList:
    msg['BCC'] = COMMASPACE.join(flattenedBCCList)
    finalReciepients.extend(flattenedBCCList)

  print("TO  | {}".format(msg['To']))
  print("CC  | {}".format(msg['CC']))
  print("BCC | {}".format(msg['BCC']))

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
