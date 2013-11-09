import smtpd, asyncore

def main():
    print 'Mailserver is on port 8025. Press ctrl-c to stop.'
    server = smtpd.DebuggingServer(('localhost', 8025), None)
    asyncore.loop()

if __name__ == '__main__':
    main()
