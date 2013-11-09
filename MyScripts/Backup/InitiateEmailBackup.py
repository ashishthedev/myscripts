#This Python script is intended to zip certain folders and send them over designated emails.
#Requirements: Python interpretor must be installed.
#Author: Ashish Anand
#Date: 24-Nov-2011

from UtilBackup import AllBackupLocations, SingleBackupLocation, Backup, Config
from UtilConfig import GetOption, GetConfigFilePath
from ConfigParser import SafeConfigParser
from UtilException import MyException
import os


def PrepBackupLocations():
    #Take a parent folder and add the first level child nodes as separate folders to be backedup
    configFilePath = GetConfigFilePath()
    parser = SafeConfigParser()
    parser.read(configFilePath)

    pathSection = "BACKUP_PATHS_LIST"
    if not parser.has_section(pathSection):
        raise MyException("%s doesnot have a section named %s" % (configFilePath, pathSection))

    folderPathList = list()
    for option in parser.options(pathSection):
        folderPathList.append(parser.get(pathSection, option))

    section = "BACKUP_SECTION"
    sdatToSdat = Config(
                server=GetOption(section, 'Server'),
                port=GetOption(section, 'Port'),
                username=GetOption(section, 'FromEmailAddress'),
                toEmail=GetOption(section, "ToEmailList"),
                ccEmail=GetOption(section, "CCEmailList"),
                mpass=GetOption(section, 'Mpass'),
                successNotification=GetOption(section, "SuccessNotificationMailList"),
                fromDisplayName=GetOption(section, "FromDisplayName"),
                )

    backupLocations = AllBackupLocations()


    for eachFolderPath in folderPathList:
        eachFolderPath = os.path.normpath(eachFolderPath)
        for fileName in os.listdir(eachFolderPath):
            backupLocations.append(SingleBackupLocation(
                sub=GetOption("BACKUP_SECTION", "SubjectPrefix") + fileName,
                path=os.path.join(eachFolderPath, fileName),
                config=sdatToSdat
                ))
    backupLocations.successMsg = "Backup succesfful for: " + ",\n".join(folderPathList)

    return backupLocations

if __name__ == '__main__':
    ignoreTheseFiles = ['~*.xlsx', '.git*', '.git\*', '__pycache__*', '.ropeproject*', '*.pyc', '*.pkl', '*.dot', '*.swp']
    Backup(PrepBackupLocations(), ignorePatternList=ignoreTheseFiles)
