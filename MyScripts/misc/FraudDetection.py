###################################################################
##
## Intent: To read messages from Yahoo mail and tell which of them
##         are not present on next poll(i.e. deleted)
##         To tell if trash has any deleted items.
##         Tell if there are any new sent messages that were not
##         there when polled last time
## Date: 2013-04-04 Thu 01:52 PM
##
## Ref: http://pymotw.com/2/imaplib/
##      Time based searches: http://stackoverflow.com/questions/5621341/search-before-after-with-pythons-imaplib?rq=1
##
## Author : Ashish Anand
###################################################################
import os
import re
import email
import shelve
import imaplib
import argparse

from contextlib import closing
from UtilPythonMail import SendMail
from UtilException import MyException
from UtilConfig import GetOption
from UtilMisc import PrintInBox

SINCE_DATE = GetOption("YMAIL", "SINCE_DATE")
ALL_SINCE_CRITERION="(ALL SINCE %s)"%SINCE_DATE
USE_TEST_MAIL_IDS = True

DONOT_SEND_EMAIL = False
STARTING_AFRESH = False #When we are establishing a db on a fresh machine, we will set it to True so that no false positive notifications are sent while setting up because nothing will be present on that machine.
HOSTNAME = GetOption("YMAIL", "Hostname")
UNAME = ""
UPASS = ""

DBPATH = ""


VERBOSE = True

def OpenConnection():
    connection = imaplib.IMAP4_SSL(HOSTNAME)
    connection.login(UNAME, UPASS)
    return connection

def parse_list_response(line):
    list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')
    flags, delimiter, mailboxName = list_response_pattern.match(line).groups()
    mailboxName = mailboxName.strip('"')
    return (flags, delimiter, mailboxName)

def GetStoredUIDsForCategory(category):
    result = list()
    with closing(shelve.open(DBPATH)) as sh:
        for uid in sh.keys():
            emailMsg, storedCategory, reportedOnce, deletedOnServer = sh[uid]
            if storedCategory == category:
                result.append(uid)
    return result

def IsMessageStored(uid):
    with closing(shelve.open(DBPATH)) as sh:
        return sh.has_key(uid)

def IsMessageAlreadyReported(uid):
    with closing(shelve.open(DBPATH)) as sh:
        assert type(uid) == type("")
        emailMsg, category, reportedOnce, deletedOnServer = sh[uid]
        return reportedOnce

def MarkMessageAsDeletedOnServer(uid, category):
    assert IsMessageStored(uid), "uid:%s not present in database" % uid
    with closing(shelve.open(DBPATH)) as sh:
        assert type(uid) == type("")
        emailMsg, category, reportedOnce, deletedOnServer = sh[uid]
        deletedOnServer = True
        sh[uid] = (emailMsg, category, reportedOnce, deletedOnServer)
    return

def MarkMessageAsReported(uid, category):
    assert IsMessageStored(uid), "uid:%s not present in database" % uid
    with closing(shelve.open(DBPATH)) as sh:
        assert type(uid) == type("")
        emailMsg, category, reportedOnce, deletedOnServer = sh[uid]
        reportedOnce = True
        sh[uid] = (emailMsg, category, reportedOnce, deletedOnServer)
    return

def StoreMessage(c, uid, category, reportedOnce=False, deletedOnServer=False):
    """
    Given a category like Sent/Inbox/Foobar the emailMsg will be saved with key as uid.
    Database is a shelf with uid as key.
    Value is a tuple of (emailMsg, category).
    This way even if the number of messages become huge, we are not storing everythign in RAM.
    """
    emailMsg = MakeEmailMessageFromUID(c, uid)
    assert not IsMessageStored(uid), "uid:%s already present in database" % uid
    with closing(shelve.open(DBPATH)) as sh:
        assert type(uid) == type("")
        #TODO: Store the value as a class. The existing database will be rendered useless after that.
        sh[uid] = (emailMsg, category, reportedOnce, deletedOnServer)
    return

def MsgObjAsString(msg):
    result = ""
    for header in ['to', 'from', 'subject', 'date']:
       result += "%-8s:  %s\n" % (header.upper(), msg[header])
    for part in msg.walk():
       if part.get_content_type().lower()=="text/plain":
           result += "%-8s:  \n<HTML>\n%s\n</HTML>\n" % ("BODY", part.get_payload(decode=True))
       if part.get_content_type().lower()=="text/html":
           result += "%-8s:  %s" % ("BODY", part.get_payload(decode=True))
    return result

def GetStoredMessageAsStringForUID(uid):
    """
    Whenever you want to inspect a message just print it using this function.
    """
    with closing(shelve.open(DBPATH)) as sh:
        msg, category, reportedOnce, deletedOnServer = sh[uid]
    return MsgObjAsString(msg)

def GetUIDsFromMailBox(c, mailboxName, criterion):
    """
    Return a list of UIDs for the specific criterion(for ex/- ALL) in a specific mailbox
    """
    c.select(mailboxName, readonly=True)
    if VERBOSE: import random; print("Making network call for fetching all UIDs" + "."*random.randint(1,6))
    typ, uidList = c.uid('search', None, criterion)
    if typ != "OK":
        raise MyException("Received a bad response %s from server while searching for messages with criterion %s" % (typ, criterion))

    return [uid.strip() for uid in uidList[0].split() if len(uid)>0] # Do not add empty elements ''

def MakeEmailMessageFromUID(c, uid):
    """
    Given a message number, return the email message.
    """
    if VERBOSE: import random; print("Making network call for making message" + "."*random.randint(1,6))
    typ, msgData = c.uid('fetch', uid, '(RFC822)')
    if typ != "OK":
        raise MyException("Received a bad response %s from server while getting a message with uid %s" % (typ, uid))
    for respPart in msgData:
        if isinstance(respPart, tuple):
            msg = email.message_from_string(respPart[1])
            return msg

def DetectNewSentMessages(c):
    mailboxName = "Sent"
    _DetectNewMessagesInThisMailBox(c, mailboxName)
    return

def DetectInboxDeletedMessages(c):
    mailboxName = "Inbox"
    _DetectDeletedMessagesInThisMailBox(c, mailboxName, criterion=ALL_SINCE_CRITERION)
    return

def DetectSentDeletedMessages(c):
    mailboxName = "Sent"
    _DetectDeletedMessagesInThisMailBox(c, mailboxName)
    return

def _DetectNewMessagesInThisMailBox(c, mailboxName, criterion=ALL_SINCE_CRITERION, report=True):
    """
    Scan all the messages in this folder and report any new ones
    """
    uidList = GetUIDsFromMailBox(c, mailboxName, criterion)
    for uid in uidList:
        if IsMessageStored(uid):
            continue
        StoreMessage(c, uid, category=mailboxName)
        assert not IsMessageAlreadyReported(uid), "uid: %s is already reported once"%uid
        if report:
            ShootAlertMailForStoredEmail(
                    emailSubject="New %s Message"%mailboxName,
                    uid=uid,
                    category=mailboxName)
    return

def _DetectDeletedMessagesInThisMailBox(c, mailboxName, criterion=ALL_SINCE_CRITERION):
    """
    Detect any messages that were previously in this folder but are not present now
    """
    #TODO: Write it using generator expression and use a for loop to process each message
    #http://python-history.blogspot.in/2010/06/from-list-comprehensions-to-generator.html
    serverUIDs = GetUIDsFromMailBox(c, mailboxName, criterion)
    seenUIDs = GetStoredUIDsForCategory(mailboxName)
    for eachUID in seenUIDs:
        if eachUID not in serverUIDs:
            if IsMessageAlreadyReported(eachUID):
                continue
            ShootAlertMailForStoredEmail(
                    emailSubject="A message has been deleted from {} messages".format(mailboxName),
                    uid=eachUID,
                    category=mailboxName)
            MarkMessageAsDeletedOnServer(eachUID, category=mailboxName)
    return


def DetectMessagesInTrash(c):
    mailboxName = "Trash"
    serverUIDs = GetUIDsFromMailBox(c, mailboxName, criterion=ALL_SINCE_CRITERION)

    for uid in serverUIDs:
        if IsMessageStored(uid):
            continue
        StoreMessage(c, uid, category=mailboxName)
        assert not IsMessageAlreadyReported(uid), "uid: %s is already reported once"%uid
        ShootAlertMailForStoredEmail(
                emailSubject="New Trash Message",
                uid=uid,
                category=mailboxName)
    return

def _DetectSpecialWordsInThisMsg(c, uid):
    assert IsMessageStored(uid) == True, "Msg with uid: %s should have been stored when calling this function"%uid
    highAlertwords = GetOption("YMAIL", "HighAlertWords").split(',')
    highAlertwords = [x.strip().lower() for x in highAlertwords]

    msgStr = GetStoredMessageAsStringForUID(uid).lower()
    for eachWord in highAlertwords:
        if not msgStr.find(eachWord) == -1:
            return eachWord
    return None

def StoreNewInboxMessages(c):
    mailboxName = "Inbox"
    uidList = GetUIDsFromMailBox(c, mailboxName, criterion=ALL_SINCE_CRITERION)
    for uid in uidList:
        if IsMessageStored(uid): continue #Ignore already seen messages
        StoreMessage(c, uid, category=mailboxName)
        assert not IsMessageAlreadyReported(uid), "uid: %s is already reported once"%uid
        specialWord = _DetectSpecialWordsInThisMsg(c, uid)
        if specialWord:
            ShootAlertMailForStoredEmail(emailSubject="High Alert word %s found in inbox"%specialWord,
                    uid=uid,
                    category=mailboxName)
    return

def DeleteReportedMessages():
    """
    Delete messages which are reported and not present on server. Frees up your disk space.
    """
    with closing(shelve.open(DBPATH)) as sh:
        for uid in sh.keys():
            emailMsg, storedCategory, reportedOnce, deletedOnServer = sh[uid]
            if reportedOnce and deletedOnServer:
                print("Deleting this message")
                del sh[uid] #TODO: Untested. Test by checking filesize of shlef file.


def _ShootAlertMail(emailSubject, mailBody):
    if VERBOSE: import random; PrintInBox("Sending mail over network" + "."*random.randint(1,6))
    section = "YMAIL"
    SendMail(emailSubject,
            None,
            GetOption(section, 'Server'),
            GetOption(section, 'Port'),
            GetOption(section, 'FromEmailAddress'),
            GetOption(section, 'NotifyAtEmail'),
            GetOption(section, 'CCEmailList').split(','),
            GetOption(section, 'Mpass'),
            mailBody,
            textType="html",
            fromDisplayName = GetOption(section, "FromDisplayName")
            )

def ShootAlertMailForUnstoredEmail(emailSubject, mailBody):
    _ShootAlertMail(emailSubject, mailBody)

def ShootAlertMailForStoredEmail(emailSubject, uid, category):
    mailBody = GetStoredMessageAsStringForUID(uid)
    if STARTING_AFRESH: return
    if DONOT_SEND_EMAIL:
        #If you are debugging, then just print the message and return.
        print("Subject: {}".format(emailSubject))
        print(mailBody)
        return
    if IsMessageAlreadyReported(uid):
        print(GetStoredMessageAsStringForUID(uid))
        raw_input("This message was already reported once. Just letting you know there is a bug in program.")
        #Instead of using assert which fails we can tolerate the false positive after letting the user know.
    _ShootAlertMail(emailSubject, mailBody)
    MarkMessageAsReported(uid, category)
    return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--freshComp", dest='setupFreshComp', action='store_true', help="If present, the existing database will be erased and will be treated as a new machine")
    parser.add_argument("-ne", "--no-emails", dest='noEmails', action='store_true', help="If present, the existing database will be populated but no notification will be sent")
    parser.add_argument("-d", "--delete-reported", dest='deleteReported', action='store_true', help="If present, the messages which have been deleted from server but are present in existing database will be deleted. Mainly to free up disk space")
    parser.add_argument("-nv", "--no-verbose", dest='noverbose', action='store_true', help="If present, some helpful messages will be printed")
    parser.add_argument("-t", "--test", dest='useTestMails', action='store_true', help="If present, some helpful messages will be printed")
    args = parser.parse_args()


    if args.useTestMails:
        global UNAME, UPASS
        print("Using Testmail ids")
        UNAME = GetOption("YMAIL", "TUName")
        UPASS = GetOption("YMAIL", "TUPass")
    else:
        UNAME = GetOption("YMAIL", "UName")
        UPASS = GetOption("YMAIL", "UPass")
    global DBPATH
    DBPATH = os.path.join(GetOption("CONFIG_SECTION", "TempPath"), UNAME.replace('@', '-')[::-1] + "shelf.db")


    if args.noverbose:
        global VERBOSE
        VERBOSE=False

    if args.setupFreshComp:
        if (raw_input("Really delete the database and start afresh(y/n)?").lower() == 'y'):
            if os.path.exists(DBPATH):
                os.remove(DBPATH)

    if args.noEmails:
        global DONOT_SEND_EMAIL
        DONOT_SEND_EMAIL = True
        print("Supressing Email Notifications in this run")

    if args.deleteReported:
        if (raw_input("Delete already reported messages which are not on server anymore and free up the disk space(y/n)?").lower() == 'y'):
            DeleteReportedMessages()
            return #TODO: Remove

    if not os.path.exists(DBPATH):
        #Irrespective of what the user has asked for, if the database is not there, we will assume we are starting afresh.
        global STARTING_AFRESH
        STARTING_AFRESH = True
        print("Starting afresh. Email notifications will not be sent.")

    try:
        print("Connecting... "+FudgedID(UNAME))
        c = OpenConnection()
        PrintInBox("Detecting new sent messages")
        DetectNewSentMessages(c)
        PrintInBox("Detecting messages that have been deleted from inbox")
        DetectInboxDeletedMessages(c)
        PrintInBox("Detecting messages that have been deleted from sent folder")
        DetectSentDeletedMessages(c)
        PrintInBox("Detecting messages in Trash folder...")
        DetectMessagesInTrash(c)
        PrintInBox("Scanning inbox...")
        StoreNewInboxMessages(c)

    except MyException as ex:
        print(str(ex))

    finally:
        try:
            c.close()
        except MyException as ex:
            print(str(ex))
        finally:
            c.logout()

def FudgedID(emailId):
    assert type(emailId) == type("")
    result = ""
    pos = emailId.find('@')
    chars = 2
    result = emailId[:chars] + (pos-chars)*'*' + emailId[pos:]
    return result

if __name__ == '__main__':
    main()


    #TODO: Deal with one folder at one time. That will optimize the number of network calls you are making.
