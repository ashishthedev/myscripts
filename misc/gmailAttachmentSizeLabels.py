###############################################################################
##
## Intent: To read messages from Gmail and label them according to their size
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
###############################################################################
from Util.Exception import MyException
from Util.Config import GetOption
from Util.Misc import PrintInBox
from Util.Gmail import Gmail

SINCE_DATE = GetOption("GMAIL_ATT_SIZE", "SINCE_DATE")
UNAME = GetOption("GMAIL_ATT_SIZE", "UNAME")
UPASS = GetOption("GMAIL_ATT_SIZE", "UPASS")


def main():
    print("Connecting ... " + UNAME)
    gmail = Gmail(UNAME, UPASS)
    for i in range(50, 1, -1):
        print("Looking for {} mb".format(i))
        gmail.search.clear()

        searchRes = gmail.search.after(SINCE_DATE).hasAttachement().sizeGreateThan(i).execute()
        for each in searchRes.messages:
            each.addLabel(".{}MB".format(i))

    gmail.logout()

if __name__ == '__main__':
    try:
        main()
    except MyException as ex:
        PrintInBox(str(ex))
