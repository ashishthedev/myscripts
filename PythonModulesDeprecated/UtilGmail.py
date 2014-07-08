'''
File: UtilGmail.py
Author: Ashish Anand
Description: UtilGmail.py is a python library for interacting with Gmail.
It makes the basic impalib necessities like searching and labeling of emails
simpler.
Date: 2013-May-14 Tue 03:17 PM
'''
import imaplib
import datetime
from UtilException import MyException

class Gmail:
    """
    The Gmail Object. It represents a single connection.
    Usage: with Gmail(u, p) as gmail:
    """
    IMAP_HOST = 'imap.gmail.com'
    IMAP_PORT = 993

    def __init__(self, username, password):
        if '@' not in username: username += '@gmail.com'

        self.imap = imaplib.IMAP4_SSL(host=self.IMAP_HOST, port = self.IMAP_PORT)
        self.imap.login(user=username, password=password)

        self.search = Search(self)
        self.labels = LabelSet(self)

    def logout(self):
        self.imap.close()
        self.imap.logout()
        self.imap = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.logout()

class Search:
    """
    Single view representative of search results.
    """
    partialCriterion = ""

    def __init__(self, gmail):
        self.gmail = gmail
        self.uids = set()
        self.modified = False

    @property
    def messages(self):
        return [Message(self.gmail, uid, self.gmail.imap) for uid in self.uids]

    def clear(self):
        self.uids = set()
        self.modified = False

    def execute(self):
        finalCriteria = "({})".format(self.partialCriterion.strip())
        self.partialCriterion = ""
        #print("Final Criterion: '{}'".format(finalCriteria))
        typ, uidList = self.gmail.imap.uid('search', None, finalCriteria)
        if typ != 'OK':
            raise MyException("Received a bad response {} from server while searching for messages with criterion {}".format(typ, finalCriteria))

        searchedUIDs = set([uid.strip() for uid in uidList[0].split() if len(uid)>0]) # Do not add empty elements ''
        if self.modified:
            self.uids.intersection_update(searchedUIDs) #Keep only those elements which are also present in new search result
        else:
            self.uids = searchedUIDs
        self.modified = True
        return self

    def _addSearchClause(self, *criterion):
        for eachCriteria in criterion:
            self.partialCriterion += " " + eachCriteria
        return self

    def after(self, date):
        if type(date) != str and type(date) != datetime.date:
            raise MyException("Date must be a string or datetime.date")
        if type(date) == datetime.date:
            date = date.strftime("%d-%b-%Y")
        return self._addSearchClause("ALL SINCE {}".format(date))

    def hasAttachement(self):
        return self._addSearchClause("X-GM-RAW has:attachment")

    def sizeGreateThan(self, sizeInMB):
        minSize = str((int(sizeInMB)-1)*1024*1024)
        maxSize = str(int(sizeInMB)*1024*1024)
        return self._addSearchClause("SMALLER {} LARGER {}".format(maxSize, minSize))

    def __str__(self):
        return "\n".join(self.uids)

class LabelSet:
    def __init__(self, gmail):
        self.gmail = gmail
        self.labels = None
        self.switch("all")
        return

    def exists(self, label):
        if self.labels is None: self.refreshLabels()
        return label in self.labels

    def refreshLabels(self):
        _, ret = self.gmail.imap.list()
        self.labels = [a.split('"')[-2] for a in ret]
        return

    def switch(self, label, shortcuts_on=True):
        shortcuts = {
                'inbox'  : 'Inbox',
                'all'    : '[Gmail]/All Mail',
                'drafts' : '[Gmail]/Drafts',
                'sent'   : '[Gmail]/Sent Mail',
                'spam'   : '[GMail]/Spam',
                'starred': '[GMail]/Starred',
                'trash'  : '[GMail]/Trash',
                }
        if shortcuts_on and label.lower() in shortcuts:
            label = shortcuts[label.lower()]

        self.gmail.imap.select(label)
        self.current = label
        self.gmail.search.clear()
        return

    def create(self, label):
        self.gmail.imap.create(label)
        self.refreshLabels()
        return


class Message:
    def __init__(self, gmail, uid, imap):
        self.gmail = gmail
        self.uid = uid

    def flag(self, flag): self.gmail.imap.store(self.id, '+FLAGS', flag)
    def unflag(self, flag): self.gmail.imap.store(self.id, '-FLAGS', flag)

    def read(self): self.flag('\\Seen')
    def unread(self): self.unflag('\\Seen')

    def star(self): self.addLabel('[Gmail]/Starred')
    def unstar(self): self.unflag('\\Flagged')

    def delete(self): self.flag('\\Deleted')
    def archive(self): self.move_to('[Gmail]/All Mail')
    def spam(self): self.move_to('[Gmail]/Spam')

    def addLabel(self, label):
        if not self.gmail.labels.exists(label):
            print("Creating label '{}'".format(label))
            self.gmail.labels.create(label)
        print("Marking: {}".format(label))
        self.gmail.imap.uid('COPY', self.uid, label)
        return

    def move_to(self, label):
        self.addLabel(label)
        self.delete()
        return
