from UtilPythonMail import SendMail
from UtilConfig import GetOption

def ShootMailToAdmin(emailSubject, mailBody):
    section = "ADMIN_ALERT"
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

