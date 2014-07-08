from Util.PythonMail import SendMail
from Util.Config import GetOption

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

